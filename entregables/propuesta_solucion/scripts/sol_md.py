import sys, json, datetime as dt
sys.path.insert(0, sys.argv[3])
from content import *

plan = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
it = {x["id"]: x for x in plan["items"]}
H = plan["hitos"]
f = lambda s: dt.date.fromisoformat(s).strftime("%d/%m/%Y") if s else "—"


def var(i):
    x = it[i]
    if not x["fin_act"]:
        return "Nueva"
    d = (dt.date.fromisoformat(x["fin_prop"]) - dt.date.fromisoformat(x["fin_act"])).days
    return f"{d:+d}" if d else "0"


md = []
A = md.append

A("## 1. Situación actual")
A("**El diagnóstico se confirma en lo esencial, pero se corrige en nueve puntos antes de proponer la solución.** "
  "El cronograma integrado (374 filas, corte 21/10/2026) no tiene vínculos, línea base ni fechas de construcción. "
  "Sus fechas son de diseño funcional (MFD): el fin de un MFD no es la disponibilidad del sistema construido.")
A("Se revisaron críticamente las 22 dependencias, las 19 alertas y los 12 ajustes del diagnóstico. El resultado:")
A("- **Dependencias:** 13 se mantienen, 9 se corrigen y aparecen 2 nuevas que el diagnóstico no vio: la certificación de crédito que necesitan las Actuaciones preparatorias (D23) y el modelo de devengado que necesita Pagos (D24).")
A("- **Ajustes:** 3 se mantienen, 6 se modifican y 3 se retiran porque comprimían duraciones sin datos de capacidad.")
A("- **Problemas reales de secuencia:** 10 de 24 dependencias. Las demás son solapamientos de diseño que se resuelven con entregas parciales o vínculos con desfase.")
A("**Cuadro 1. Principales correcciones al diagnóstico**")
A("| Tema | Qué se corrige | Resultado |")
A("| --- | --- | --- |")
for t in CORRECCIONES[:7]:
    A(f"| {t[0]} | {t[1]} | {t[2]} |")

A("## 2. Solución integral recomendada")
A(">>>Se recomienda el **Escenario 2 – Integración optimizada**: articula los siete sistemas mediante 87 vínculos, 9 tareas nuevas y 8 entregas parciales, sin mover el fin del proyecto (28/12/2029). Las 2 alertas críticas quedan resueltas en la propuesta, condicionadas a validar la capacidad de los CAF de Tesorería y Presupuesto.")
A("[[KPI]]")
A("La solución sigue una regla: **adelantar o dividir el insumo antes que retrasar al receptor**, y nunca comprimir una duración sin capacidad comprobada. Cuando el receptor solo necesita la estructura del dato, se crea un hito de entrega parcial en lugar de mover el proceso completo.")
A("**Cuadro 2. Solución por caso**")
A("| Caso | Problema confirmado | Solución recomendada | Efecto en fechas |")
A("| --- | --- | --- | --- |")
rows = [
    ("1 · Tesorería", "Los pagos de 2027 (236, 234) se diseñan antes que la cuota de pago (163, may 2028): 350 días.",
     "B · Cuota de pago v1 mínima (N1) con los flujos proyectados (161); 163 pasa a ser la v2 completa.",
     f"N1: {f(it['N1']['ini_prop'])} – {f(it['N1']['fin_prop'])}. Sin retrasos."),
    ("2 · Abastecimiento – Presupuesto", "Compromiso y devengado se diseñan antes que la orden (196) y la Conformidad (197); falta la certificación.",
     "B · Dividir la ejecución en certificación y modelo de datos (N2), compromiso (181) y devengado (N3), con entregas parciales M1 y M2.",
     f"181: {var('181')} días; N3 termina {f(it['N3']['fin_prop'])}."),
    ("3 · Contabilidad", "Cierres y estados (355–360) se diseñan antes que la ejecución AFSP.",
     "A · Fuente de transición SIAF-SP (ya integrada en 344) + adecuación de cierres (N5) en 2028.",
     f"Sin cambios en 2026–2027; N5: {f(it['N5']['ini_prop'])} – {f(it['N5']['fin_prop'])}."),
    ("4 · Clasificadores y Catálogos", "Formulación (144) cierra su MFD antes que metas, catálogos v2 y clasificadores temáticos.",
     "B · Versión mínima (estructura) al 15/01/2027 (M3, M4, M8, M9); versión completa en su fecha; temáticos desde la Formulación 2028.",
     "Sin compresiones. 6 catálogos al 99 % se cierran al 13/11/2026."),
    ("5 · Inversiones – Presupuesto", "La PMI (147) está en StandBy y bloquea el registro de proyectos (149) y la formulación por proyecto (150).",
     "A · Reactivar 147, mover 149 y crear la Formulación v2 (N4) en lugar de adelantar 150.",
     f"149: {var('149')} días; N4: {f(it['N4']['ini_prop'])} – {f(it['N4']['fin_prop'])}."),
    ("6 · Endeudamiento – Contabilidad", "El motor contable se actualiza por última vez en sep 2028; Endeudamiento diseña hasta dic 2029.",
     "B · Actualizaciones 3 (N6) y 4 (N7) del motor, por bloques.",
     f"N6: abr–jun 2029; N7 termina {f(it['N7']['fin_prop'])} (con el proyecto)."),
    ("7 · Evaluación transversal", "Cuatro sistemas no tienen procesos de Evaluación.",
     "B · Evaluar vía Presupuesto, Inversiones y Contabilidad (CGR, EFP), con una validación final (N10). No se crean módulos nuevos.",
     f"N10: oct–dic 2029."),
]
for r in rows:
    A("| " + " | ".join(r) + " |")
A("**Cuadro 3. Comparación de escenarios**")
A("| Criterio | Escenario 1 – Conservador | Escenario 2 – Integración optimizada | Escenario 3 – Integración prioritaria |")
A("| --- | --- | --- | --- |")
for e in ESCENARIOS:
    A("| " + " | ".join(e) + " |")
A("El Escenario 1 deja sin resolver las dos alertas críticas. El Escenario 3 resuelve más, pero exige recursos que el .mpp no permite verificar y pone en riesgo el cierre. El Escenario 2 resuelve todas las dependencias críticas con una carga adicional acotada.")

A("## 3. Principales ajustes de fechas")
A("**Se modifican 16 actividades existentes y se crean 9 tareas nuevas; ninguna actividad completada cambia de fecha.** Todas las fechas se calcularon con el calendario del .mpp y se verificaron contra la red de 87 vínculos: no hay conflictos ni dependencias circulares.")
A("**Cuadro 4. Ajustes principales (detalle completo en la Matriz Maestra)**")
A("| ID | Sistema | Actividad | Actual | Propuesto | Variación del fin (días) | Estado |")
A("| --- | --- | --- | --- | --- | --- | --- |")
for i in ["N1", "N2", "181", "N3", "186", "147", "149", "N4", "N5", "N6", "N7", "N10"]:
    x = it[i]
    act = f"{f(x['ini_act'])} – {f(x['fin_act'])}" if x["ini_act"] else "No existe"
    A(f"| {i} | {x['sistema']} | {x['actividad']} | {act} | {f(x['ini_prop'])} – {f(x['fin_prop'])} | {var(i)} | {x['estado']} |")
A("Además: 6 catálogos vencidos al 99 % se cierran formalmente al 13/11/2026 (25, 46, 59, 60, 62 y 63), y 6 actividades que debieron empezar y siguen en 0 % inician el 02/11/2026 con su misma duración (48, 51, 81, 130, 250 y 251).")
A("**Gráfico 1. Detalle de la reprogramación**")
A("[[IMG:gantt_detalle.png]]")

A("## 4. Hitos de integración")
A("**Siete hitos permiten comprobar que los sistemas quedan articulados, desde los catálogos (15/01/2027) hasta la integración completa (28/12/2029).** Son hitos de aprobación del diseño. Los hitos de software y puesta en uso no son verificables: el .mpp no programa la construcción (C3), y se solicitará a la fábrica alinearla a estos siete hitos.")
A("**Cuadro 5. Hitos de integración del diseño funcional**")
A("| Hito | Sistemas | Entregables | Fecha objetivo | Criterio de aceptación | Responsable |")
A("| --- | --- | --- | --- | --- | --- |")
for h in HITOS:
    A(f"| {h[0]} · {h[1]} | {h[2]} | {h[3]} | {f(H[h[0]])} | {h[4]} | {h[5]} |")
A("**Gráfico 2. Cronograma integrado: actual frente a propuesto**")
A("[[IMG:gantt_consolidado.png]]")

A("## 5. Riesgos residuales")
A("**De 21 hallazgos, 7 quedan resueltos en la propuesta, 9 condicionados a validación, 4 pendientes de decisión y 1 sin resolver.** No se declara resuelto lo que depende de una decisión o de recursos no confirmados.")
A("**Cuadro 6. Riesgos que siguen abiertos**")
A("| Hallazgo | Riesgo inicial | Solución | Riesgo residual | Estado |")
A("| --- | --- | --- | --- | --- |")
for r in ANTES_DESPUES:
    if r[5] != "Resuelto en la propuesta":
        A(f"| {r[0]} | {r[1]} | {r[2]} | {r[4]} | {r[5]} |")
A("**Restricciones conocidas:** el .mpp no tiene recursos (la capacidad de los CAF se estimó con el número de actividades simultáneas); las tareas 165 y 170 mantienen la restricción «No finalizar antes del 29/01/2027»; la carga de Presupuesto sube de 7 a 9 actividades simultáneas en febrero de 2027 y la de Tesorería de 4 a 5 en mayo de 2027.")

A("## 6. Decisiones necesarias")
A("**La reprogramación necesita nueve decisiones; las cinco primeras deben tomarse antes del 15/12/2026.** La matriz completa, con alternativas y consecuencias, está en el Entregable 4 (hoja «Decisiones» del Excel).")
A("**Cuadro 7. Decisiones para la Coordinación y la UCP**")
A("| Código | Decisión | Alternativa recomendada | Si no se decide | Responsable | Fecha límite |")
A("| --- | --- | --- | --- | --- | --- |")
order = ["DEC-4", "DEC-3", "DEC-5", "DEC-6", "DEC-9", "DEC-1", "DEC-2", "DEC-7", "DEC-8"]
dmap = {d[0]: d for d in DECISIONES}
for c in order:
    d = dmap[c]
    alt = [a for a in d[3].split(" · ") if a.startswith(d[4] + ":")]
    A(f"| {c} | {d[1]} | {alt[0] if alt else d[4]} | {d[5]} | {d[7]} | {d[8]} |")

A("## 7. Conclusión sobre la viabilidad")
A("**La integración funcional de los siete sistemas es viable dentro del plazo actual (28/12/2029), con el Escenario 2 y bajo cuatro condiciones.**")
A("1. **Decidir a tiempo:** reactivar la PMI (DEC-4, 30/10/2026) y confirmar la fuente contable de transición (DEC-3, 30/11/2026).")
A("2. **Confirmar capacidad:** el CAF de Tesorería para la cuota de pago v1 (may 2027) y el CAF de Presupuesto para la certificación y el modelo común de datos (feb–abr 2027).")
A("3. **Formalizar la red en Microsoft Project:** cargar los 87 vínculos, las tareas nuevas y los hitos; guardar la línea base 1 antes del 04/12/2026.")
A("4. **Programar la construcción (C3):** sin ella, los hitos de software y la puesta en uso no pueden verificarse.")
A("Si estas condiciones no se cumplen, el proyecto mantiene sus fechas, pero vuelve al riesgo del Escenario 1: dos ciclos críticos (pago y gasto en bienes y servicios) diseñados sin sus insumos.")
A("**Entregables que acompañan este resumen:** Matriz Maestra de Reprogramación (Excel con 11 hojas y filtros), cronograma propuesto en formato XML de Microsoft Project (el .mpp original no fue modificado) y los gráficos del cronograma integrado.")

import re
txt = "\n\n".join(md)
txt = re.sub(r"(\|[^\n]*)\n\n(?=\|)", r"\1\n", txt)
txt = re.sub(r"(\|[^\n]*)\n\n(?=\|)", r"\1\n", txt)
open(OUT, "w").write(txt)
print("ok")
