import sys, json
import jpype, mpxj
jpype.startJVM()
from org.mpxj.reader import UniversalProjectReader
from org.mpxj.mspdi import MSPDIWriter
from org.mpxj import Duration, TimeUnit, RelationType, Relation, TaskField, TaskMode
from java.time import LocalDateTime

MPP, PLAN, OUT, IDMAP = sys.argv[1:5]
proj = UniversalProjectReader().read(MPP)
plan = json.load(open(PLAN))
T = {int(t.getID()): t for t in proj.getTasks() if t.getID() is not None}
cal = proj.getDefaultCalendar()


def ld(s, end=False):
    y, m, d = map(int, s.split("-"))
    return LocalDateTime.of(y, m, d, 19 if end else 9, 0)


# alias de campos personalizados
proj.getCustomFields().getOrCreate(TaskField.TEXT2).setAlias("Cambio propuesto")
proj.getCustomFields().getOrCreate(TaskField.TEXT3).setAlias("Código propuesta")

root = T[2]  # Proyecto AFSP
grp = root.addTask()
grp.setName("Propuesta de integración – tareas nuevas, entregas parciales e hitos (Escenario 2)")
grp.setTaskMode(TaskMode.MANUALLY_SCHEDULED)
sub = {}
for key, label in [("N", "Tareas nuevas"), ("M", "Entregas parciales (hitos)"), ("H", "Hitos de integración")]:
    s = grp.addTask()
    s.setName(label)
    s.setTaskMode(TaskMode.MANUALLY_SCHEDULED)
    sub[key] = s

code2task = {}
for it in plan["items"]:
    if it["id"][0].isalpha():
        t = sub[it["id"][0]].addTask()
        t.setName(it["actividad"] if it["actividad"].startswith(it["id"]) else f'{it["id"]} · {it["actividad"]}')
        t.setTaskMode(TaskMode.MANUALLY_SCHEDULED)
        t.setStart(ld(it["ini_prop"]))
        if it.get("milestone"):
            t.setFinish(ld(it["fin_prop"]))
            t.setDuration(Duration.getInstance(0, TimeUnit.DAYS))
            t.setMilestone(True)
        else:
            t.setFinish(ld(it["fin_prop"], True))
            t.setDuration(Duration.getInstance(it["dur_prop"], TimeUnit.DAYS))
        t.set(TaskField.TEXT1, it["sistema"])
        t.set(TaskField.TEXT2, it["tipo"])
        t.set(TaskField.TEXT3, it["id"])
        t.setNotes(it["justificacion"])
        code2task[it["id"]] = t
    else:
        t = T[int(it["id"])]
        if it["ini_prop"] != it["ini_act"] or it["fin_prop"] != it["fin_act"]:
            t.setStart(ld(it["ini_prop"]))
            t.setFinish(ld(it["fin_prop"], True))
        if it["actividad"] != str(t.getName()):
            t.setName(it["actividad"])
        t.set(TaskField.TEXT2, it["tipo"])
        prev = str(t.getNotes() or "")
        t.setNotes((prev + "\n" if prev else "") + "Propuesta: " + it["justificacion"])
        code2task[it["id"]] = t

for k, t in T.items():
    code2task.setdefault(str(k), t)

RT = {"FC": RelationType.FINISH_START, "CC": RelationType.START_START, "FF": RelationType.FINISH_FINISH}
for l in plan["links"]:
    a, b = code2task[l["origen"]], code2task[l["destino"]]
    b.addPredecessor(Relation.Builder().predecessorTask(a).type(RT[l["tipo"]]).lag(Duration.getInstance(l["desfase"], TimeUnit.DAYS)))

# numerar las tareas nuevas sin alterar los ID existentes
nxt = max(T) + 1
for t in [grp] + list(sub.values()):
    pass
def walk(t):
    yield t
    for c in t.getChildTasks():
        yield from walk(c)
for t in walk(grp):
    t.setID(jpype.JInt(nxt)); nxt += 1
    t.setUniqueID(jpype.JInt(100000 + nxt))

def rollup(t):
    kids = list(t.getChildTasks())
    if not kids:
        return t.getStart(), t.getFinish()
    ss, ff = zip(*[rollup(c) for c in kids])
    st, fi = min(x for x in ss if x is not None), max(x for x in ff if x is not None)
    t.setStart(st); t.setFinish(fi)
    return st, fi
rollup(grp)

w = MSPDIWriter()
w.write(proj, OUT)
json.dump({c: int(t.getID()) for c, t in code2task.items() if c[0].isalpha()}, open(IDMAP, "w"))
print("ok", OUT, nxt - 1)
