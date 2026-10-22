import json, sys, datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager as fm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

for f in fm.findSystemFonts(fontpaths=["/root/.fonts"]):
    fm.fontManager.addfont(f)
plt.rcParams["font.family"] = "Montserrat"

T2, PLAN, OUTDIR = sys.argv[1:4]
r = json.load(open(T2))
plan = json.load(open(PLAN))
AZUL, TURQ, SALMON, ROJO, GRIS, VERDE, MOSTAZA = "#004899", "#0093F8", "#E6375D", "#ED3237", "#4B4B4D", "#3BB4AA", "#F5BB47"
GHOST = "#C9CED6"
MCOL = {"Clasificadores y Catálogos": VERDE, "Programación": TURQ, "Gestión": AZUL, "Evaluación": SALMON}
D = lambda s: dt.date.fromisoformat(s[:10])

byid = {t["id"]: t for t in r}
def macro_of(t):
    p = t
    while p and p["lvl"] > 2:
        p = byid.get(p["parent"])
    return {"Macroproceso de Programación": "Programación", "Macroproceso de Gestión": "Gestión",
            "Macroproceso de Evaluación": "Evaluación", "Clasificadores y Catálogos": "Clasificadores y Catálogos"}.get(p["name"]) if p else None

leaf = {str(t["id"]): dict(sys=t["custom"].get("TEXT1"), mac=macro_of(t), s=t["start"][:10], f=t["finish"][:10], name=t["name"])
        for t in r if not t["summary"] and t["name"] and t["lvl"] >= 3 and t["id"] not in (141, 142, 133)}
prop = {k: dict(v) for k, v in leaf.items()}
for it in plan["items"]:
    if it.get("milestone") or it["sistema"] == "Transversal" or it["id"] == "N11":
        continue
    prop[it["id"]] = dict(sys=it["sistema"], mac=it["macro"], s=it["ini_prop"], f=it["fin_prop"], name=it["actividad"])

SYS = ["Presupuesto", "Inversiones", "Abastecimiento", "GFRH", "Tesorería", "Endeudamiento", "Contabilidad"]
MACS = ["Clasificadores y Catálogos", "Programación", "Gestión", "Evaluación"]

def spans(src):
    out = {}
    for v in src.values():
        if v["sys"] in SYS and v["mac"] in MACS:
            k = (v["sys"], v["mac"])
            s, f = D(v["s"]), D(v["f"])
            if k in out:
                out[k] = (min(out[k][0], s), max(out[k][1], f))
            else:
                out[k] = (s, f)
    return out

A, P = spans(leaf), spans(prop)

# ------------------------------------------------------------- Gantt consolidado
rows = [(s, m) for s in SYS for m in MACS if (s, m) in A or (s, m) in P]
fig, ax = plt.subplots(figsize=(13.3, 9.2), dpi=200)
y = 0
yt, yl = [], []
sys_start = {}
for s, m in rows:
    if s not in sys_start:
        sys_start[s] = y
    a, p = A.get((s, m)), P.get((s, m))
    if a:
        ax.barh(y + 0.18, (a[1] - a[0]).days, left=a[0], height=0.3, color=GHOST, edgecolor="none")
    if p:
        ax.barh(y - 0.16, (p[1] - p[0]).days, left=p[0], height=0.3, color=MCOL[m], edgecolor="none")
        if a and (p[1] != a[1] or p[0] != a[0]):
            ax.text(p[1] + dt.timedelta(days=12), y - 0.16, f"{'+' if (p[1]-a[1]).days>=0 else ''}{(p[1]-a[1]).days} d en el fin",
                    va="center", fontsize=8, color=SALMON, fontweight="bold")
    yt.append(y); yl.append(m)
    y += 1
# carril de hitos
yh = y + 0.4
for n_, (k, v) in enumerate(sorted(plan["hitos"].items())):
    d = D(v)
    ax.scatter(d, yh, marker="D", s=70, color=SALMON, zorder=5)
    ax.text(d, yh + (0.7 if n_ % 2 == 0 else -0.55), k, ha="center", va="center", fontsize=9, color=SALMON, fontweight="bold")
ax.text(D("2023-08-01"), yh, "Hitos de integración", va="center", ha="left", fontsize=9.5, color=SALMON, fontweight="bold")
# separadores y nombres de sistema
for s in SYS:
    y0 = sys_start[s]
    n = sum(1 for x in rows if x[0] == s)
    ax.axhline(y0 - 0.5, color="#D0D5DD", lw=0.8)
    ax.text(-0.26, y0 + (n - 1) / 2, s, transform=ax.get_yaxis_transform(), ha="left", va="center",
            fontsize=11, color=AZUL, fontweight="bold")
ax.axhline(y - 0.5, color="#D0D5DD", lw=0.8)
ax.set_yticks(yt)
ax.set_yticklabels(yl, fontsize=8.5, color=GRIS)
ax.tick_params(axis="y", pad=4, length=0)
ax.invert_yaxis()
ax.set_xlim(D("2023-07-01"), D("2030-12-31"))
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(axis="x", labelsize=10, colors=GRIS)
ax.grid(axis="x", color="#E3E6EB", lw=0.8)
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.spines["bottom"].set_color("#D0D5DD")
cut = D("2026-10-21")
ax.axvline(cut, color=SALMON, ls="--", lw=1)
ax.text(cut, -1.1, "Corte 21/10/2026", ha="center", fontsize=8.5, color=SALMON)
handles = [Patch(color=GHOST, label="Actual")] + [Patch(color=c, label=f"Propuesto · {m}") for m, c in MCOL.items()] + \
          [Line2D([0], [0], marker="D", color="w", markerfacecolor=SALMON, markersize=8, label="Hito de integración (diseño)")]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.45, 1.075), ncol=6, frameon=False, fontsize=8.5)
fig.text(0.01, 0.985, "Cronograma integrado: actual frente a propuesto (Escenario 2)", fontsize=15, color=AZUL, fontweight="bold", va="top")
fig.text(0.01, 0.955, "Periodo de diseño (MFD) por sistema y macroproceso. El fin del proyecto se mantiene en 28/12/2029.",
         fontsize=10, color=SALMON, fontweight="bold", va="top")
plt.subplots_adjust(left=0.27, right=0.98, top=0.88, bottom=0.05)
fig.savefig(f"{OUTDIR}/gantt_consolidado.png", dpi=200)
plt.close(fig)

# ------------------------------------------------------------- Gantt de detalle (casos 1, 2, 4 y 5)
it = {x["id"]: x for x in plan["items"]}
def row(code, label, sysn):
    if code in it:
        x = it[code]
        return dict(code=code, label=label, sys=sysn, a=(x["ini_act"], x["fin_act"]) if x["ini_act"] else None,
                    p=(x["ini_prop"], x["fin_prop"]), ms=x.get("milestone", False), new=not x["ini_act"])
    v = leaf[code]
    return dict(code=code, label=label, sys=sysn, a=(v["s"], v["f"]), p=(v["s"], v["f"]), ms=False, new=False)

DET = [
    ("Caso 1 · Tesorería", [row("161", "161 Flujos de caja proyectados", "T"), row("N1", "N1 Cuota de pago v1 (nueva)", "T"),
                             row("236", "236 Pagos entre CUT", "T"), row("234", "234 Operativización del pago", "T"),
                             row("162", "162 Flujos de caja diarios", "T"), row("163", "163 Cuota de pago v2", "T")]),
    ("Caso 2 · Abastecimiento – Presupuesto", [row("N2", "N2 Certificación y modelo de datos del gasto (nueva)", "P"),
                             row("195", "195 Actuaciones preparatorias", "A"), row("196", "196 Contrato, OC y OS", "A"),
                             row("M1", "M1 Interfaz OC/OS", "A"), row("181", "181 Compromiso de bienes y servicios", "P"),
                             row("197", "197 Conformidad", "A"), row("M2", "M2 Interfaz de Conformidad", "A"),
                             row("N3", "N3 Devengado de bienes y servicios (nueva)", "P"),
                             row("270", "270 Instrucciones de pago de deuda", "E"), row("186", "186 Ejecución de gastos de deuda", "P")]),
    ("Casos 4 y 5 · Catálogos e Inversiones", [row("M3", "M3 Catálogos mínimos (estructura)", "P"),
                             row("M4", "M4 Estructura de metas v1", "P"), row("144", "144 Formulación del presupuesto", "P"),
                             row("147", "147 PMI y PMIE (reactivar)", "I"), row("149", "149 Registro de proyectos", "I"),
                             row("150", "150 Formulación por proyecto", "I"), row("N4", "N4 Formulación v2 (nueva)", "P")]),
]
SYSCOL = {"T": TURQ, "P": AZUL, "A": VERDE, "I": MOSTAZA, "E": GRIS}
nrows = sum(len(g[1]) + 1 for g in DET)
fig, ax = plt.subplots(figsize=(13.3, 9.6), dpi=200)
y = 0
ypos = {}
for gname, rws in DET:
    ax.text(-0.005, y, gname, transform=ax.get_yaxis_transform(), ha="right", fontsize=10.5, color=SALMON, fontweight="bold", va="center")
    y += 1
    for rw in rws:
        ypos[rw["code"]] = y
        ax.text(-0.005, y, rw["label"], transform=ax.get_yaxis_transform(), ha="right", fontsize=8.8, color=AZUL if rw["new"] else GRIS,
                fontweight="bold" if rw["new"] else "normal", va="center")
        col = SYSCOL[rw["sys"]]
        if rw["ms"]:
            ax.scatter(D(rw["p"][0]), y, marker="D", s=60, color=SALMON, zorder=5)
            ax.text(D(rw["p"][0]) + dt.timedelta(days=8), y, D(rw["p"][0]).strftime("%d/%m/%Y"), fontsize=7.5, color=SALMON, va="center")
        else:
            if rw["a"] and rw["a"] != rw["p"]:
                a0, a1 = D(rw["a"][0]), D(rw["a"][1])
                ax.barh(y + 0.2, (a1 - a0).days, left=a0, height=0.22, color=GHOST)
            p0, p1 = D(rw["p"][0]), D(rw["p"][1])
            ax.barh(y - 0.05 if rw["a"] and rw["a"] != rw["p"] else y, (p1 - p0).days, left=p0, height=0.32, color=col)
        y += 1
    y += 0.3
# relaciones principales
REL = [("161", "N1"), ("N1", "236"), ("N1", "234"), ("N2", "195"), ("M1", "181"), ("M2", "N3"), ("181", "N3"), ("270", "186"),
       ("M3", "144"), ("M4", "144"), ("147", "149"), ("149", "150"), ("150", "N4")]
def end(code):
    x = it.get(code)
    return D(x["fin_prop"]) if x else D(leaf[code]["f"])
def start(code):
    x = it.get(code)
    return D(x["ini_prop"]) if x else D(leaf[code]["s"])
for a, b in REL:
    xa, xb = end(a), start(b)
    if xb < xa:
        xb = end(b)
    ax.annotate("", xy=(xb, ypos[b]), xytext=(xa, ypos[a]),
                arrowprops=dict(arrowstyle="-|>", color=ROJO, lw=1.1, connectionstyle="arc3,rad=0.15", shrinkA=2, shrinkB=3))
ax.set_xlim(D("2026-03-01"), D("2028-07-01"))
ax.set_ylim(y, -1)
ax.set_yticks([])
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
ax.tick_params(axis="x", labelsize=9, colors=GRIS)
ax.grid(axis="x", color="#E3E6EB", lw=0.8)
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.axvline(D("2026-10-21"), color=SALMON, ls="--", lw=1)
handles = [Patch(color=GHOST, label="Actual"), Patch(color=AZUL, label="Presupuesto"), Patch(color=TURQ, label="Tesorería"),
           Patch(color=VERDE, label="Abastecimiento"), Patch(color=MOSTAZA, label="Inversiones"), Patch(color=GRIS, label="Endeudamiento"),
           Line2D([0], [0], marker="D", color="w", markerfacecolor=SALMON, markersize=8, label="Entrega parcial"),
           Line2D([0], [0], color=ROJO, lw=1.2, label="Vínculo propuesto")]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.42, 1.06), ncol=4, frameon=False, fontsize=8.5)
fig.text(0.01, 0.985, "Detalle de la reprogramación: casos 1, 2, 4 y 5", fontsize=15, color=AZUL, fontweight="bold", va="top")
fig.text(0.01, 0.955, "Barras grises: fechas actuales. En azul y negrita: tareas nuevas. Flechas: vínculos propuestos.",
         fontsize=10, color=SALMON, fontweight="bold", va="top")
plt.subplots_adjust(left=0.29, right=0.98, top=0.86, bottom=0.05)
fig.savefig(f"{OUTDIR}/gantt_detalle.png", dpi=200)
print("ok")
