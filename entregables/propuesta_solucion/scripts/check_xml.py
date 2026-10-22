import sys, jpype, mpxj
jpype.startJVM()
from org.mpxj.reader import UniversalProjectReader
p = UniversalProjectReader().read(sys.argv[1])
ts=[t for t in p.getTasks() if t.getID() is not None]
print("tareas", len(ts), "vínculos", sum(len(list(t.getPredecessors())) for t in ts))
byid={int(t.getID()):t for t in ts}
for i in (2,163,181,186,147,149,376,377,378,386,395,401,374,375):
    t=byid.get(i)
    if t: print(i, str(t.getName())[:70], str(t.getStart())[:10], str(t.getFinish())[:10], t.getMilestone(), [ (int(r.getPredecessorTask().getID()), str(r.getType()), str(r.getLag())) for r in t.getPredecessors()][:4])
print("fin proyecto", byid[0].getFinish() if 0 in byid else None)
