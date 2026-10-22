"""Propuesta de reprogramación (Escenario 2 – Integración optimizada).
Calcula fechas con el calendario del .mpp, valida la red de vínculos y exporta plan.json."""
import sys, json, datetime as dt
import jpype, mpxj
jpype.startJVM()
from org.mpxj.reader import UniversalProjectReader
from org.mpxj import Duration, TimeUnit
from java.time import LocalDateTime

MPP, OUT = sys.argv[1], sys.argv[2]
proj = UniversalProjectReader().read(MPP)
cal = proj.getDefaultCalendar()
T = {int(t.getID()): t for t in proj.getTasks() if t.getID() is not None}


def ld(s):
    y, m, d = map(int, s.split("-"))
    return LocalDateTime.of(y, m, d, 9, 0)


def iso(j):
    return str(j)[:10]


def finish(start, days):
    return iso(cal.getDate(ld(start), Duration.getInstance(days, TimeUnit.DAYS)))


def addwd(date, days):
    """fecha (inicio de jornada) a 'days' días hábiles de 'date' (puede ser negativo)."""
    d = dt.date.fromisoformat(date)
    step = 1 if days >= 0 else -1
    n = abs(days)
    while n:
        d += dt.timedelta(days=step)
        if d.weekday() < 5:
            n -= 1
    return d.isoformat()


def nextwd(date):
    return addwd(date, 1)


def dur(t):
    return float(str(t.getDuration())[:-1])


def info(i):
    t = T[i]
    sysname = t.get(mpxj.TaskField.TEXT1) if hasattr(mpxj, "TaskField") else None
    return t


from org.mpxj import TaskField
def tsys(i):
    v = T[i].get(TaskField.TEXT1)
    return str(v) if v else ""


def macro(i):
    t = T[i]
    while t.getParentTask() is not None and int(t.getOutlineLevel()) > 2:
        t = t.getParentTask()
    return {"Macroproceso de Programación": "Programación", "Macroproceso de Gestión": "Gestión",
            "Macroproceso de Evaluación": "Evaluación", "Clasificadores y Catálogos": "Clasificadores y Catálogos",
            "Aplicativos de uso común": "Aplicativos"}.get(str(t.getName()), str(t.getName()))


def cur(i):
    t = T[i]
    return iso(t.getStart()), iso(t.getFinish())


CUT = "2026-11-02"   # primer lunes hábil después del corte (21/10/2026) + 1 semana de aprobación
items = []           # filas de la matriz maestra

# ----------------------------------------------------------------- utilidades de registro
def change(i, start=None, days=None, fin=None, kind="Mover", case="", prio="Alta", resp="", status="Tentativa",
           just="", name=None, scen="E2"):
    s0, f0 = cur(i)
    d0 = dur(T[i])
    ns = start or s0
    nd = days if days is not None else d0
    nf = fin or finish(ns, nd)
    items.append(dict(id=str(i), uid=int(T[i].getUniqueID()), sistema=tsys(i), macro=macro(i),
                      actividad=name or str(T[i].getName()), ini_act=s0, fin_act=f0, ini_prop=ns, fin_prop=nf,
                      dur_act=d0, dur_prop=nd, tipo=kind, caso=case, prioridad=prio, responsable=resp,
                      estado=status, justificacion=just, escenario=scen, pct=float(T[i].getPercentageComplete() or 0)))
    return nf


def new(code, parent, sistema, macro_, name, start, days, kind="Nueva tarea", case="", prio="Alta", resp="",
        status="Tentativa", just="", milestone=False, scen="E2"):
    nf = start if milestone else finish(start, days)
    items.append(dict(id=code, uid=None, parent=parent, sistema=sistema, macro=macro_, actividad=name,
                      ini_act="", fin_act="", ini_prop=start, fin_prop=nf, dur_act=None,
                      dur_prop=0 if milestone else days, tipo="Hito" if milestone else kind, caso=case,
                      prioridad=prio, responsable=resp, estado=status, justificacion=just, escenario=scen,
                      milestone=milestone, pct=0.0))
    return nf


# ================================================================= CASO 1 · TESORERÍA
f161 = cur(161)[1]
fN1 = new("N1", 158, "Tesorería", "Programación", "Asignación de pago – versión mínima (cuota de pago v1 con reglas vigentes)",
          "2027-05-03", 23, case="C1", resp="CAF Tesorería",
          just="Habilita los pagos que se diseñan desde el 16/06/2027 (236) usando los flujos de caja proyectados (161). "
               "Se conserva la duración de la fila 163 (23 días).")
change(163, kind="Sin cambio de fechas (pasa a v2)", case="C1", prio="Media", resp="CAF Tesorería", status="Calculada",
       name="Asignación de pago – versión 2 (incorpora flujos de caja diarios)",
       just="Se mantiene en mayo de 2028 como versión completa; ya no bloquea a los pagos de 2027.")

# ================================================================= CASO 2 · ABASTECIMIENTO – PRESUPUESTO
fN2 = new("N2", 180, "Presupuesto", "Gestión", "Certificación y modelo común de datos del gasto (certificación, compromiso y devengado)",
          "2027-02-01", 45, case="C2", resp="CAF Presupuesto + CAF Abastecimiento + CAF Tesorería",
          just="Las Actuaciones preparatorias (195) requieren la certificación de crédito, y Pagos (234, 236) requiere el modelo del devengado. "
               "Duración igual a la de la fila 181 (45 días).")
mOC = addwd(cur(196)[0], 32)
new("M1", 194, "Abastecimiento", "Gestión", "Hito: interfaz de contrato, OC y OS aprobada (entrega parcial de 196)",
    mOC, 0, milestone=True, case="C2", resp="CAF Abastecimiento",
    just="Entrega parcial de 196: estructura de datos del contrato y de la orden, suficiente para diseñar el compromiso.")
f181 = change(181, start=nextwd(mOC), kind="Mover y renombrar", case="C2", resp="CAF Presupuesto",
              name="Compromiso de gastos de bienes, servicios y obras",
              just="Se diseña con la interfaz de la orden (M1) aprobada. Conserva su duración (45 días).")
mCF = addwd(cur(197)[0], 42)
new("M2", 194, "Abastecimiento", "Gestión", "Hito: interfaz de Conformidad aprobada (entrega parcial de 197)",
    mCF, 0, milestone=True, case="C2", resp="CAF Abastecimiento",
    just="Entrega parcial de 197: datos de la conformidad que habilitan el devengado.")
fN3 = new("N3", 180, "Presupuesto", "Gestión", "Devengado de gastos de bienes, servicios y obras",
          nextwd(mCF), 40, case="C2", resp="CAF Presupuesto + CAF Abastecimiento",
          just="Separa el devengado del compromiso para alinearlo con la Conformidad (197).")

# ================================================================= CASO 3 · CONTABILIDAD (escenario A recomendado)
fN5 = new("N5", 353, "Contabilidad", "Evaluación", "Adecuación de cierres y estados presupuestales a las fuentes AFSP",
          nextwd(fN3), 40, case="C3", prio="Media", resp="CAF Contabilidad + CAF Presupuesto",
          just="Escenario A: los cierres de 2026–2027 usan el SIAF-SP (integración 344 concluida). "
               "Esta tarea adapta 355, 358, 359 y 360 cuando exista la ejecución AFSP, antes de la Cuenta General (363).")

# ================================================================= CASO 6 · ENDEUDAMIENTO – CONTABILIDAD
fN6 = new("N6", 342, "Contabilidad", "Gestión", "Actualización 3 de Catálogo de Eventos y Motor de Contabilización",
          "2029-04-02", 45, case="C6", prio="Media", resp="CAF Contabilidad + CAF Endeudamiento",
          just="Cubre los eventos de Endeudamiento etapa 2 y de Abastecimiento diseñados entre oct 2028 y mar 2029.")
fN7 = new("N7", 342, "Contabilidad", "Gestión", "Actualización 4 de Catálogo de Eventos y Motor de Contabilización",
          "2029-10-01", 65, case="C6", prio="Media", resp="CAF Contabilidad + CAF Endeudamiento + CAF Abastecimiento",
          just="Cierra la cobertura contable de los procesos diseñados hasta dic 2029; termina con el proyecto (FF con 296).")

# ================================================================= CASO 5 · INVERSIONES – PRESUPUESTO
s147, f147 = cur(147)
rem = round(dur(T[147]) * (1 - float(T[147].getPercentageComplete()) / 100))
f147n = change(147, start=s147, fin=finish(CUT, rem), kind="Reactivar y extender", case="C5", resp="CAF Inversiones",
               status="Pendiente de decisión",
               just=f"Sale de StandBy el {CUT}; le quedan unos {rem} días (38 % de 65). Es predecesora de 149.")
f149 = change(149, start=nextwd(f147n), kind="Mover", case="C5", resp="CAF Inversiones",
              just="Empieza cuando la PMI esté aprobada (147). Conserva su duración.")
fN4 = new("N4", 143, "Presupuesto", "Programación", "Actualización del MFD de Formulación para proyectos de inversión (Formulación v2)",
          nextwd(cur(150)[1]), 30, case="C5", prio="Media", resp="CAF Presupuesto + CAF Inversiones",
          just="Incorpora al MFD de Formulación (144) el presupuesto por proyecto diseñado en 150, en lugar de adelantar 150.")

# ================================================================= CASO 4 · CLASIFICADORES Y CATÁLOGOS
for i in (25, 46, 59, 60, 62, 63):
    change(i, start=cur(i)[0], fin="2026-11-13", kind="Regularizar cierre", case="C4", prio="Alta",
           resp="CAF Presupuesto", status="Calculada",
           just="Vencida al 99 %. Se fija el cierre formal del MFD para que pueda usarse como insumo.")
for i in (48, 51, 130, 250, 251, 81):
    change(i, start=CUT, kind="Reprogramar por avance real", case="C4" if i in (48, 51, 130) else "Calidad",
           prio="Media", resp={48: "CAF Presupuesto", 51: "CAF Presupuesto", 130: "CAF Presupuesto", 250: "CAF Tesorería",
                               251: "CAF Tesorería", 81: "CAF GFRH"}[i], status="Calculada",
           just="Debió iniciar antes del corte y sigue en 0 %. Se mueve el inicio al corte y se conserva la duración.",
           name="Catálogo GFRH por definir (antes «<Tarea nueva>»)" if i == 81 else None)
mCat = "2027-01-15"
new("M3", 15, "Presupuesto", "Clasificadores y Catálogos", "Hito: versión mínima de catálogos para Programación (estructura aprobada)",
    mCat, 0, milestone=True, case="C4", resp="CAF Presupuesto",
    just="Estructura (atributos y relaciones) aprobada de 46, 47, 65, 66 y 128–132. El poblado completo puede seguir después.")
new("M4", 135, "Presupuesto", "Programación", "Hito: estructura de metas v1 aprobada (entrega parcial de 140)",
    "2027-01-15", 0, milestone=True, case="C4", resp="CAF Presupuesto",
    just="La Formulación (144) cierra su MFD con la estructura de metas; el Administrador de Metas (140) se completa para la Apertura.")
new("M5", 15, "Endeudamiento", "Clasificadores y Catálogos", "Hito: estructura del Catálogo relacional Deuda–Inversión aprobada",
    "2026-11-30", 0, milestone=True, case="C5", resp="CAF Endeudamiento + CAF Inversiones",
    just="Entrega parcial de 82 que necesitan 149 y 256.")
new("M8", 164, "Endeudamiento", "Programación", "Hito: proyección preliminar del servicio de deuda para la Formulación",
    "2027-01-15", 0, milestone=True, case="C4", resp="CAF Endeudamiento",
    just="Versión preliminar de 167/169 para que la Formulación (144) cierre con el dato de deuda. Se mantiene la restricción de 165 y 170.")
new("M9", 158, "Tesorería", "Programación", "Hito: estimación preliminar de ingresos por OOC, RO y RD para la Formulación",
    "2027-01-15", 0, milestone=True, case="C4", resp="CAF Tesorería",
    just="Versión preliminar de 160 para la Formulación (144).")

# ================================================================= ENDEUDAMIENTO → PRESUPUESTO (ejecución deuda)
s186, f186 = cur(186)
f269 = cur(270)[1]
change(186, start=addwd(f269, -int(dur(T[186])) + 1), kind="Mover", case="C2", prio="Media", resp="CAF Presupuesto + CAF Endeudamiento",
       status="Calculada", just="Debe cerrar junto con las instrucciones de pago de deuda (270 y 272). Conserva su duración.")

# ================================================================= CASO 7 · EVALUACIÓN TRANSVERSAL
new("M6", 180, "GFRH", "Gestión", "Hito: interfaz planilla–compromiso–devengado–pago validada con GFRH",
    addwd(cur(182)[0], 40), 0, milestone=True, case="C7", prio="Media", resp="CAF GFRH + CAF Presupuesto + CAF Tesorería",
    just="GFRH concluyó su diseño en 2026; se valida su interfaz dentro de la Ejecución de gestión fiscal (182).")
fN10 = new("N10", 348, "Contabilidad", "Evaluación", "Validación de la integración Gestión 2028–2029 con Cuenta General y Estadísticas de Finanzas Públicas",
           "2029-10-01", 65, case="C7", prio="Media", resp="CAF Contabilidad + CAF Endeudamiento + CAF Abastecimiento",
           just="Evaluación termina en 2028, pero Endeudamiento y Abastecimiento diseñan hasta 2029: se valida que sus datos lleguen a 363 y 364.")
new("N11", 15, "Abastecimiento", "Clasificadores y Catálogos", "Revisión de catálogos de almacén antes de Logística (versión 2)",
    "2028-10-02", 20, case="C4", prio="Baja", resp="CAF Abastecimiento",
    just="Los catálogos 70–74 se cerraron en 2026 y se usan desde 2029: se revisan antes del diseño de almacén.")

# ================================================================= HITOS DE INTEGRACIÓN (diseño funcional)
H = {}
H["H1"] = mCat
H["H2"] = max(f149, cur(145)[1], cur(169)[1], cur(160)[1], cur(153)[1], cur(138)[1])
H["H3"] = max(cur(173)[1], cur(175)[1], cur(176)[1])
H["H4"] = max(fN3, cur(236)[1], cur(234)[1], f181)
H["H5"] = cur(347)[1]
H["H6"] = max(cur(363)[1], cur(373)[1], cur(352)[1])
H["H7"] = max(fN7, fN10, cur(296)[1])
hnames = {
    "H1": "H1 · Clasificadores y Catálogos (versión mínima) disponibles para Programación",
    "H2": "H2 · Programación integrada entre sistemas",
    "H3": "H3 · Programación y Gestión articuladas (Apertura y cuotas)",
    "H4": "H4 · Ciclo certificación–compromiso–devengado–pago integrado (diseño)",
    "H5": "H5 · Gestión y Contabilidad articuladas (motor contable v2)",
    "H6": "H6 · Gestión y Evaluación articuladas",
    "H7": "H7 · Integración funcional completa de los siete sistemas (diseño)",
}
for k, v in H.items():
    new(k, 2, "Transversal", "Integración", hnames[k], v, 0, milestone=True, case="Hitos", resp="Coordinación del Proyecto",
        status="Calculada", just="Hito de aprobación del diseño funcional integrado (MFD).")

# ================================================================= VÍNCULOS PROPUESTOS
L = []
def link(a, b, typ="FC", lag=0, just="", val="", ref=""):
    L.append(dict(origen=str(a), destino=str(b), tipo=typ, desfase=lag, justificacion=just, validacion=val, ref=ref))

link(161, "N1", just="La cuota v1 se calcula con los flujos de caja proyectados.", val="CAF Tesorería", ref="D1")
link("N1", 236, just="Los pagos entre CUT requieren la cuota de pago.", val="CAF Tesorería", ref="D1")
link("N1", 234, just="La operativización del pago requiere la cuota de pago.", val="CAF Tesorería", ref="D1")
link("N1", 235, just="El pago por transferencia requiere la cuota de pago.", val="CAF Tesorería", ref="D1")
link("N1", 233, just="El pago con cheque requiere la cuota de pago.", val="CAF Tesorería", ref="D1")
link(161, 162, just="Los flujos diarios parten de los proyectados.", val="CAF Tesorería", ref="D1")
link(162, 163, just="La cuota v2 incorpora los flujos de caja diarios.", val="CAF Tesorería", ref="D1")
link("N2", 195, "FF", just="Las Actuaciones preparatorias no cierran su MFD sin la certificación de crédito.", val="CAF Presupuesto y CAF Abastecimiento", ref="D23 (nueva)")
link("N2", 181, just="El compromiso usa el modelo común de datos del gasto.", val="CAF Presupuesto", ref="D2")
link("N2", 182, just="La ejecución de gestión fiscal usa el modelo común de datos.", val="CAF Presupuesto", ref="D2")
link("N2", 236, just="Los pagos usan el modelo del devengado.", val="CAF Tesorería y CAF Presupuesto", ref="D24 (nueva)")
link("N2", 234, just="Los pagos usan el modelo del devengado.", val="CAF Tesorería y CAF Presupuesto", ref="D24 (nueva)")
link(196, "M1", "CC", 32, just="Entrega parcial de 196 a 32 días de su inicio.", val="CAF Abastecimiento", ref="D2")
link("M1", 181, just="El compromiso se diseña con la interfaz de la orden aprobada.", val="CAF Presupuesto", ref="D2")
link(175, 181, just="El compromiso requiere las cuotas de compromiso.", val="CAF Presupuesto", ref="D20")
link(176, 181, just="El compromiso requiere la asignación de cuotas.", val="CAF Presupuesto", ref="D20")
link(197, "M2", "CC", 42, just="Entrega parcial de 197 a 42 días de su inicio.", val="CAF Abastecimiento", ref="D3")
link("M2", "N3", just="El devengado se diseña con la interfaz de Conformidad aprobada.", val="CAF Presupuesto", ref="D3")
link(181, "N3", just="El devengado sigue al compromiso.", val="CAF Presupuesto", ref="D3")
link(270, 186, "FF", just="La ejecución de gastos de deuda cierra con las instrucciones de pago de deuda externa.", val="CAF Presupuesto y CAF Endeudamiento", ref="D12")
link(272, 186, "FF", just="La ejecución de gastos de deuda cierra con las instrucciones de pago de deuda interna.", val="CAF Presupuesto y CAF Endeudamiento", ref="D12")
link("N3", "N5", just="La adecuación contable se hace sobre la ejecución AFSP diseñada.", val="CAF Contabilidad", ref="D4")
link("N5", 363, just="La Cuenta General usa cierres adecuados.", val="CAF Contabilidad", ref="D4/D5")
link("N3", 369, "FF", just="El informe global de gestión presupuestaria cierra después del devengado.", val="CAF Presupuesto", ref="D13")
link(347, "N6", just="Secuencia de actualizaciones del motor contable.", val="CAF Contabilidad", ref="D6")
link("N6", "N7", just="Secuencia de actualizaciones del motor contable.", val="CAF Contabilidad", ref="D6")
link(296, "N7", "FF", just="El motor cierra junto con el último proceso de Endeudamiento.", val="CAF Contabilidad y CAF Endeudamiento", ref="D6")
link(363, "N10", just="La validación usa la Cuenta General diseñada.", val="CAF Contabilidad", ref="Caso 7")
link("N7", "N10", "FF", just="La validación cierra con la última actualización del motor.", val="CAF Contabilidad", ref="Caso 7")
link(147, 149, just="El registro de proyectos parte de la PMI aprobada.", val="CAF Inversiones", ref="D11")
link("M5", 149, just="El registro de proyectos usa la relación deuda–inversión.", val="CAF Inversiones", ref="D14")
link("M5", 257, just="La concertación usa la relación deuda–inversión.", val="CAF Endeudamiento", ref="D14")
link(82, "M5", "CC", 20, just="Entrega parcial de 82.", val="CAF Endeudamiento", ref="D14")
link(149, 150, just="La formulación por proyecto usa la estructura registrada.", val="CAF Inversiones", ref="D7")
link(150, "N4", just="La Formulación v2 incorpora el presupuesto por proyecto.", val="CAF Presupuesto y CAF Inversiones", ref="D7")
link(144, "N4", just="La Formulación v2 parte del MFD de Formulación v1.", val="CAF Presupuesto", ref="D7")
for i in (46, 65, 66, 129, 130, 131):
    link(i, "M3", just="Catálogo necesario para la estructura mínima de Programación.", val="CAF Presupuesto", ref="D10")
link(128, "M3", "CC", 40, just="Estructura de Programas Presupuestales v2 (entrega parcial).", val="CAF Presupuesto", ref="D10")
link(132, "M3", "CC", 40, just="Estructura de Relación Actividad por Finalidad (entrega parcial).", val="CAF Presupuesto", ref="D10")
link("M3", 144, "FF", just="La Formulación no cierra su MFD sin la estructura mínima de catálogos.", val="CAF Presupuesto", ref="D10")
link(65, 137, "FF", just="La modificación de la APM usa el catálogo de versiones de presupuesto.", val="CAF Presupuesto", ref="D10")
link(66, 136, "FF", just="Los reportes de la APM usan el catálogo de archivos APM.", val="CAF Presupuesto", ref="D10")
link(140, "M4", "CC", 30, just="Entrega parcial del Administrador de Metas.", val="CAF Presupuesto", ref="D8")
link("M4", 144, "FF", just="La Formulación cierra con la estructura de metas v1.", val="CAF Presupuesto", ref="D8")
link(140, 173, "FF", just="La Apertura no cierra su MFD sin el Administrador de Metas completo.", val="CAF Presupuesto", ref="D8")
link(132, 173, just="La Apertura requiere la relación actividad–finalidad completa.", val="CAF Presupuesto", ref="D10")
link(144, 173, just="La Apertura parte del presupuesto formulado.", val="CAF Presupuesto", ref="D21")
link(145, 173, just="La Apertura parte del presupuesto aprobado.", val="CAF Presupuesto", ref="D21")
link(173, 175, "CC", just="Las cuotas se diseñan en paralelo con la Apertura.", val="CAF Presupuesto", ref="D20")
link(168, "M8", "FF", -10, just="Versión preliminar de la proyección de deuda.", val="CAF Endeudamiento", ref="D17")
link("M8", 144, "FF", just="La Formulación cierra con el dato de deuda.", val="CAF Presupuesto", ref="D17")
link(160, "M9", "FF", -10, just="Versión preliminar de la estimación de ingresos.", val="CAF Tesorería", ref="D18")
link("M9", 144, "FF", just="La Formulación cierra con la estimación de ingresos.", val="CAF Presupuesto", ref="D18")
link(155, 195, just="Las actuaciones preparatorias parten del PAC.", val="CAF Abastecimiento", ref="D16")
link(153, 195, "FF", just="Las actuaciones preparatorias no cierran antes que el CMN.", val="CAF Abastecimiento", ref="D16")
link(108, 356, "FC", -5, just="Solapamiento aceptado de 5 días hábiles.", val="CAF Contabilidad", ref="D19")
link(109, 357, "FC", -5, just="Solapamiento aceptado de 5 días hábiles.", val="CAF Contabilidad", ref="D19")
link(193, 350, "FF", just="El seguimiento de inversiones cierra después de los reportes de gestión.", val="CAF Inversiones", ref="D15")
link(218, 182, just="La ejecución de gestión fiscal usa la planilla aprobada.", val="CAF GFRH y CAF Presupuesto", ref="D22")
link(182, "M6", "CC", 40, just="Validación de la interfaz con GFRH dentro de 182.", val="CAF GFRH", ref="D22")
link("N11", 204, just="Logística de entrada usa catálogos revisados.", val="CAF Abastecimiento", ref="Alerta 19")

# hitos de integración
for p_ in ("M3",):
    link(p_, "H1", just="Hito de integración.", val="Coordinación", ref="H1")
for p_ in (149, 145, 169, 160, 153, 138):
    link(p_, "H2", just="Hito de integración.", val="Coordinación", ref="H2")
for p_ in (173, 175, 176):
    link(p_, "H3", just="Hito de integración.", val="Coordinación", ref="H3")
for p_ in ("N3", 236, 234, 181):
    link(p_, "H4", just="Hito de integración.", val="Coordinación", ref="H4")
link(347, "H5", just="Hito de integración.", val="Coordinación", ref="H5")
for p_ in (363, 373, 352):
    link(p_, "H6", just="Hito de integración.", val="Coordinación", ref="H6")
for p_ in ("N7", "N10", 296):
    link(p_, "H7", just="Hito de integración.", val="Coordinación", ref="H7")

# ================================================================= VALIDACIÓN DE LA RED (Etapa 9)
P = {}
for i, t in T.items():
    if t.getName() is None:
        continue
    s, f = cur(i)
    P[str(i)] = dict(s=s, f=f, name=str(t.getName()))
for it in items:
    P[it["id"]] = dict(s=it["ini_prop"], f=it["fin_prop"], name=it["actividad"])

def wdiff(a, b):
    """días hábiles de a a b (b-a)."""
    da, db = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    sign = 1 if db >= da else -1
    n = 0
    d = da
    while d != db:
        d += dt.timedelta(days=sign)
        if d.weekday() < 5:
            n += sign
    return n

viol = []
MS = {it["id"] for it in items if it.get("milestone")}
for l in L:
    a, b = P[l["origen"]], P[l["destino"]]
    lag = l["desfase"]
    if l["tipo"] == "FC":
        if l["destino"] in MS:
            slack = wdiff(a["f"], b["s"]) - lag
        else:
            slack = wdiff(a["f"], b["s"]) - 1 - lag
        ok = slack >= 0
    elif l["tipo"] == "CC":
        slack = wdiff(a["s"], b["s"]) - lag
        ok = slack >= 0
    elif l["tipo"] == "FF":
        slack = wdiff(a["f"], b["f"]) - lag
        ok = slack >= 0
    l["holgura_dh"] = slack
    l["cumple"] = ok
    if not ok:
        viol.append((l["origen"], l["destino"], l["tipo"], lag, slack, a["f"], b["s"], b["f"]))

# ciclos
import collections
G = collections.defaultdict(list)
for l in L:
    G[l["origen"]].append(l["destino"])
seen, stack = set(), set()
cyc = []
def dfs(u):
    seen.add(u); stack.add(u)
    for v in G[u]:
        if v in stack:
            cyc.append((u, v))
        elif v not in seen:
            dfs(v)
    stack.discard(u)
for u in list(G):
    if u not in seen:
        dfs(u)

print("items", len(items), "links", len(L))
print("violaciones", len(viol))
for v in viol:
    print("  ", v)
print("ciclos", cyc)
for k in H:
    print(k, H[k])
for it in items:
    print(it["id"], it["tipo"], it["ini_act"], it["fin_act"], "->", it["ini_prop"], it["fin_prop"], it["actividad"][:60])

json.dump(dict(items=items, links=L, hitos=H, names={k: v["name"] for k, v in P.items()},
               cur={k: [v["s"], v["f"]] for k, v in P.items()}), open(OUT, "w"), ensure_ascii=False, indent=1)
