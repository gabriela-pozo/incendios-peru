"""Construye index.html y README.md a partir de los CSV de outputs/.

Todas las cifras del texto, las tablas y los gráficos SVG salen de outputs/, para que la página,
el README y los CSV digan exactamente lo mismo. Correr después de los pasos 1 a 13.
"""
from pathlib import Path

import pandas as pd

OUT = Path("outputs")
NOMBRES = {"RioTambo": "Río Tambo", "Callaria": "Callería", "Iparia": "Iparía", "NuevaRequena": "Nueva Requena",
           "SanCristobal": "San Cristóbal", "SantaCruz": "Santa Cruz", "SanJuandeJarpa": "San Juan de Jarpa",
           "SanMiguel": "San Miguel"}
DEPTO = {"Junín": "Junín", "Apurímac": "Apurímac", "Huánuco": "Huánuco"}
FIRMA = "Gabriela Pozo · Reto C"
# fecha de descarga de data/raw/firms_*_SA_7d.csv (hora de modificación de los archivos: 21 oct 2026, 21:11 hora de Lima)
DESCARGA_FIRMS = ("21 oct 2026", "21 de octubre de 2026")
NAV = [("resultado", "Resultado"), ("nacional", "Mapa nacional"), ("chichas", "Chichas"), ("reto", "Qué se quemó"),
       ("hipotesis", "Hipótesis"), ("robustez", "Robustez"), ("validacion", "Validación"), ("metodo", "Método")]


def leer(nombre):
    return pd.read_csv(OUT / nombre)


def num(v, d=0, html=True):
    """Número con coma decimal y espacio fino de miles."""
    s = f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("-", "−")
    return s.replace("X", "&nbsp;" if html else " ")


def nombre(d):
    return NOMBRES.get(d, d)


# ----------------------------------------------------------------------------- datos
top = leer("medicion_top20.csv")
reg = leer("top20_exito_region.csv").set_index("region")
pru = leer("top20_pruebas.csv")
res = leer("top20_medidos_resumen.csv")
nac = leer("comportamiento_nacional.csv").set_index("indicador").valor
rec = leer("recurrencia_chichas.csv")
noc = leer("recurrencia_noche_chichas.csv").set_index("indicador").valor
cob = leer("cobertura_quemada_chichas_detalle.csv")
sev = leer("severidad_chichas.csv")
sen = leer("sensibilidad_umbral_chichas.csv")
tor = leer("tornado_chichas.csv")
rob = leer("robustez_chichas.csv")
diag = leer("robustez_diagnostico.csv").set_index("diagnostico").ha
val = leer("validacion_resumen.csv")
vcand = leer("validacion_candidatos.csv")
vsel = set(leer("validacion_mcd64a1.csv").grupo)
gini = leer("gini_maup.csv")
lz = leer("lorenz_maup.csv")
img = leer("imagenes_chichas.csv")
est = leer("fuentes_estaticas_candidatos.csv")

N = len(top)
med = top[top.medible]
no_med = top[~top.medible]
n_med = len(med)
n_nubes = int((top.categoria_motivo == "nubes").sum())
n_sinpasada = int((top.categoria_motivo == "sin imagen posterior").sum())
n_pref = int((top.categoria_motivo == "prefiltro de escena").sum())
p_fisher = float(pru[pru.prueba.str.startswith("Fisher: medidos")].valor.iloc[0])
am, an = reg.loc["Amazonía"], reg.loc["Andes"]
pref = top[top.categoria_motivo == "prefiltro de escena"].iloc[0]
limpio_pref = 100 - pref.despues_invalido_zona_pct
paracas = est[est.excluido_fuente_estatica].iloc[0]

ch = top[top.incendio == 1052].iloc[0]
ch_ha = ch.area_quemada_ha
zona_ch = sev.hectareas.sum()                 # 5 399,4 ha: suma de todas las clases, incluido sin dato
pct_zona_ch = 100 * ch_ha / zona_ch
dist_ha = nac["área del distrito de Chichas según GADM 4.1 (ha)"]
pct_dist = nac["% del distrito de Chichas quemado (1 689,5 ha)"]
hist = rec[rec.anio < 2026]
r26 = rec[rec.anio == 2026].iloc[0]
dias_min, dias_max = hist.dias_con_datos.min(), hist.dias_con_datos.max()
anillo = hist[hist.focos_poligono_mas_1km > 0]
pct_noche_ch = noc["% focos nocturnos, Chichas 2026 (3 satélites)"]
rango_noche = int(noc["lugar de Chichas en % nocturno dentro del top 20 (1 = más nocturno)"])
ORDINAL = {1: "primera", 2: "segunda", 3: "tercera", 4: "cuarta", 5: "quinta"}

pasto = res[res.cobertura_dominante == "pastizal"]
bosque = res[res.cobertura_dominante == "bosque"].iloc[0]
dif = res.set_index("distrito").diferencia_pct
rt = tor.set_index(tor.decision.str.split(" \\(").str[0]).rango_ha
umbral_r = rt["Umbral de dNBR"]
otros_r = rt.drop("Umbral de dNBR").sum()
ratio035 = res.set_index("distrito").ratio_035_010
mask_quita = rt["Máscara SCL"]
v21 = val[val.muestra.str.contains("candidatos")].iloc[0]
v3 = val[val.muestra.str.startswith("3 casos")].iloc[0]
vp = val[val.muestra.str.startswith("solo pastizal")].iloc[0]
g_min, g_max = gini[["gini_solo_con_focos", "gini_todas_las_unidades"]].min().min(), \
    gini[["gini_solo_con_focos", "gini_todas_las_unidades"]].max().max()
antes = img[(img.momento == "antes") & img.elegida].iloc[0]
despues = img[(img.momento == "despues") & img.elegida].iloc[0]
n_largos = int(nac["incendios de más de 3 días entre el primer y el último foco"])
n_inc = int(nac["incendios (grupos de focos)"])

MOTIVO = {"nubes": "Nubes sobre la zona", "sin imagen posterior": "Sin pasada de Sentinel-2",
          "prefiltro de escena": "Descartada por el prefiltro"}


# ----------------------------------------------------------------------------- SVG
def svg_ini(w, h, etiqueta):
    return [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="{etiqueta}">']


def svg_recurrencia():
    W, H, L, R, T, B = 640, 300, 44, 12, 34, 52
    ymax = 70
    sy = lambda v: T + (1 - v / ymax) * (H - T - B)
    bw = (W - L - R) / len(rec)
    o = svg_ini(W, H, "Focos S-NPP por año en el área quemada de Chichas, 2012 a 2026")
    o.append(f'<rect class="b-pol" x="{L}" y="6" width="12" height="12" rx="2"/><text class="tick" x="{L + 17}" y="16">dentro del área quemada</text>'
             f'<rect class="b-ani" x="{L + 200}" y="6" width="12" height="12" rx="2"/><text class="tick" x="{L + 217}" y="16">anillo de 1&#160;km</text>')
    for v in range(0, ymax + 1, 10):
        o.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{sy(v):.1f}" y2="{sy(v):.1f}"/>'
                 f'<text class="tick" x="{L - 6}" y="{sy(v) + 4:.1f}" text-anchor="end">{v}</text>')
    for i, r in enumerate(rec.itertuples()):
        x, w = L + i * bw + bw * 0.15, bw * 0.7
        et = "2026*" if r.anio == 2026 else str(r.anio)
        dentro, total = r.focos_poligono, r.focos_poligono_mas_1km
        tip = f"{et}: {dentro} focos dentro del área, {total - dentro} en el anillo de 1 km"
        if dentro:
            o.append(f'<rect class="b-pol" x="{x:.1f}" y="{sy(dentro):.1f}" width="{w:.1f}" height="{sy(0) - sy(dentro):.1f}"><title>{tip}</title></rect>')
        if total - dentro:
            o.append(f'<rect class="b-ani" x="{x:.1f}" y="{sy(total):.1f}" width="{w:.1f}" height="{sy(dentro) - sy(total) - (1 if dentro else 0):.1f}"><title>{tip}</title></rect>')
        if not total:
            o.append(f'<rect class="hit" x="{x:.1f}" y="{T}" width="{w:.1f}" height="{sy(0) - T:.1f}"><title>{tip}</title></rect>')
        o.append(f'<text class="{"val strong" if r.anio == 2026 else "val"}" x="{x + w / 2:.1f}" y="{sy(total) - 5:.1f}" text-anchor="middle">{total}</text>')
        o.append(f'<text class="tick" x="{x + w / 2:.1f}" y="{H - B + 16}" text-anchor="end" transform="rotate(-45 {x + w / 2:.1f} {H - B + 16})">{et}</text>')
    o.append("</svg>")
    return "\n".join(o)


def svg_severidad():
    W, L, R, T, fila = 640, 150, 16, 34, 46
    m = res.sort_values("pct_sev_baja", ascending=False).merge(top[["incendio", "pct_sev_baja", "pct_sev_moderada_baja",
                                                                    "pct_sev_moderada_alta", "pct_sev_alta"]],
                                                               on="incendio", suffixes=("_r", ""))
    H = T + fila * len(m) + 34
    sx = lambda p: L + p / 100 * (W - L - R)
    o = svg_ini(W, H, "Distribución de severidad del área quemada en los cuatro incendios medidos")
    leg = [("Baja", "sev-b"), ("Moderada-baja", "sev-mb"), ("Moderada-alta", "sev-ma"), ("Alta", "sev-a")]
    x = L
    for nom, c in leg:
        o.append(f'<rect class="{c}" x="{x}" y="8" width="12" height="12" rx="2"/><text class="tick" x="{x + 17}" y="18">{nom}</text>')
        x += 17 + len(nom) * 7.4 + 18
    for v in (0, 25, 50, 75, 100):
        o.append(f'<line class="grid" x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{T}" y2="{H - 30}"/>'
                 f'<text class="tick" x="{sx(v):.1f}" y="{H - 12}" text-anchor="middle">{v}&#160;%</text>')
    cols = ["pct_sev_baja", "pct_sev_moderada_baja", "pct_sev_moderada_alta", "pct_sev_alta"]
    for i, r in enumerate(m.itertuples()):
        y = T + i * fila + 8
        o.append(f'<text class="lbl" x="{L - 10}" y="{y + 13}" text-anchor="end">{nombre(r.distrito)}</text>'
                 f'<text class="tick" x="{L - 10}" y="{y + 29}" text-anchor="end">{r.cobertura_dominante}</text>')
        acc = 0
        for (nom, c), col in zip(leg, cols):
            p = getattr(r, col)
            if p > 0:
                o.append(f'<rect class="{c}" x="{sx(acc):.1f}" y="{y}" width="{max(sx(acc + p) - sx(acc) - 1, 0.5):.1f}" height="28">'
                         f'<title>{nombre(r.distrito)} · {nom}: {num(p, 1, False)} %</title></rect>')
            acc += p
    o.append("</svg>")
    return "\n".join(o)


def svg_envolvente():
    W, H, L, R, T, B = 640, 420, 64, 20, 20, 50
    lim = 3400
    sx = lambda v: L + v / lim * (W - L - R)
    sy = lambda v: T + (1 - v / lim) * (H - T - B)
    o = svg_ini(W, H, "Envolvente de focos frente a área medida en los cuatro incendios medidos")
    for v in range(0, lim + 1, 500):
        o.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{sy(v):.1f}" y2="{sy(v):.1f}"/>'
                 f'<text class="tick" x="{L - 8}" y="{sy(v) + 4:.1f}" text-anchor="end">{num(v)}</text>'
                 f'<text class="tick" x="{sx(v):.1f}" y="{H - B + 18}" text-anchor="middle">{num(v)}</text>')
    o.append(f'<line class="ref" x1="{sx(0)}" y1="{sy(0)}" x2="{sx(lim)}" y2="{sy(lim)}"/>'
             f'<text class="tick" x="{sx(2700):.1f}" y="{sy(2780):.1f}" transform="rotate(-38 {sx(2700):.1f} {sy(2780):.1f})">medida = envolvente</text>'
             f'<text class="axis" x="{(L + W - R) / 2}" y="{H - 8}" text-anchor="middle">Envolvente de los focos (ha)</text>'
             f'<text class="axis" x="14" y="{(T + H - B) / 2}" text-anchor="middle" transform="rotate(-90 14 {(T + H - B) / 2})">Área medida (ha)</text>')
    for r in res.itertuples():
        cl = "pt-pasto" if r.cobertura_dominante == "pastizal" else "pt-bosque"
        n = nombre(r.distrito)
        dy = 18 if n == "Iparía" else -10
        signo = "+" if r.diferencia_pct > 0 else "−"
        o.append(f'<circle class="{cl}" cx="{sx(r.envolvente_ha):.1f}" cy="{sy(r.area_quemada_ha):.1f}" r="7">'
                 f'<title>{n}: envolvente {num(r.envolvente_ha, 0, False)} ha, medida {num(r.area_quemada_ha, 1, False)} ha</title></circle>'
                 f'<text class="lbl" x="{sx(r.envolvente_ha) + (-12 if n == "Chichas" else 12):.1f}" y="{sy(r.area_quemada_ha) + dy:.1f}" '
                 f'text-anchor="{"end" if n == "Chichas" else "start"}">{n} ({signo}{num(abs(r.diferencia_pct), 1)}&#160;%)</text>')
    o.append("</svg>")
    return "\n".join(o)


def svg_tornado():
    t = tor.iloc[::-1]
    base = float(rob[rob.base].area_quemada_ha.iloc[0])
    W, L, R, T, fila = 640, 210, 50, 14, 52
    H = T + fila * len(t) + 40
    x0, x1 = -260, 2200
    sx = lambda v: L + (v - x0) / (x1 - x0) * (W - L - R)
    o = svg_ini(W, H, "Tornado: cuánto mueve cada decisión el área quemada de Chichas")
    for v in range(0, x1 + 1, 500):
        o.append(f'<line class="grid" x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{T}" y2="{H - 34}"/>'
                 f'<text class="tick" x="{sx(v):.1f}" y="{H - 16}" text-anchor="middle">{num(v)}</text>')
    for i, r in enumerate(t.itertuples()):
        y = T + i * fila + 10
        nom, det = r.decision.split(" (")
        o.append(f'<text class="lbl" x="{L - 10}" y="{y + 12}" text-anchor="end">{nom}</text>'
                 f'<text class="tick" x="{L - 10}" y="{y + 28}" text-anchor="end">({det} · {num(r.rango_ha, 1)}&#160;ha</text>')
        if base - r.min_ha > 0.5:
            o.append(f'<rect class="torn-lo" x="{sx(r.min_ha):.1f}" y="{y}" width="{sx(base) - sx(r.min_ha):.1f}" height="30"><title>{nom}: mínimo {num(r.min_ha, 1, False)} ha</title></rect>')
        if r.max_ha - base > 0.5:
            o.append(f'<rect class="torn-hi" x="{sx(base):.1f}" y="{y}" width="{sx(r.max_ha) - sx(base):.1f}" height="30"><title>{nom}: máximo {num(r.max_ha, 1, False)} ha</title></rect>')
        o.append(f'<text class="tick" x="{sx(r.min_ha) - 5:.1f}" y="{y + 19}" text-anchor="end">{num(r.min_ha)}</text>')
        if r.max_ha - base > 0.5:
            o.append(f'<text class="tick" x="{sx(r.max_ha) + 5:.1f}" y="{y + 19}">{num(r.max_ha)}</text>')
    o.append(f'<line class="base" x1="{sx(base):.1f}" x2="{sx(base):.1f}" y1="{T}" y2="{H - 34}"/>')
    o.append("</svg>")
    return "\n".join(o)


def svg_sensibilidad():
    W, H, L, R, T, B = 640, 330, 62, 20, 24, 50
    x0, x1, ymax = 0.05, 0.35, 2250
    sx = lambda u: L + (u - x0) / (x1 - x0) * (W - L - R)
    sy = lambda v: T + (1 - v / ymax) * (H - T - B)
    o = svg_ini(W, H, "Hectáreas quemadas en Chichas según el umbral de dNBR")
    for v in range(0, ymax + 1, 250):
        o.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{sy(v):.1f}" y2="{sy(v):.1f}"/>'
                 f'<text class="tick" x="{L - 8}" y="{sy(v) + 4:.1f}" text-anchor="end">{num(v)}</text>')
    for u in sen.umbral_dnbr:
        cl = "tick t-opc" if abs(u - 0.08) < 1e-9 else "tick"
        o.append(f'<text class="{cl}" x="{sx(u):.1f}" y="{H - B + 18}" text-anchor="middle">{num(u, 2)}</text>')
    o.append(f'<line class="ref" x1="{sx(0.10):.1f}" x2="{sx(0.10):.1f}" y1="{T}" y2="{H - B}"/>'
             f'<text class="axis" x="{(L + W - R) / 2}" y="{H - 8}" text-anchor="middle">Umbral de dNBR</text>')
    pts = " ".join(f"{sx(u):.1f},{sy(h):.1f}" for u, h in zip(sen.umbral_dnbr, sen.hectareas))
    o.append(f'<polyline class="line s1" points="{pts}"/>')
    for u, h in zip(sen.umbral_dnbr, sen.hectareas):
        o.append(f'<circle class="dot s1" cx="{sx(u):.1f}" cy="{sy(h):.1f}" r="{6 if abs(u - 0.10) < 1e-9 else 4.5}">'
                 f'<title>Umbral {num(u, 2, False)}: {num(h, 1, False)} ha</title></circle>')
    h10 = float(sen[sen.usado].hectareas.iloc[0])
    o.append(f'<text class="lbl" x="{sx(0.10) + 12:.1f}" y="{sy(h10) - 10:.1f}">Umbral usado (0,10): {num(h10)}&#160;ha</text>')
    o.append("</svg>")
    return "\n".join(o)


def svg_validacion():
    v = vcand[vcand.medible]
    W, H, L, R, T, B = 640, 420, 64, 20, 20, 50
    lim = 6300
    sx = lambda x: L + x / lim * (W - L - R)
    sy = lambda y: T + (1 - y / lim) * (H - T - B)
    o = svg_ini(W, H, "Nuestro método frente a MCD64A1 en los incendios de validación de 2024")
    for g in range(0, lim + 1, 1000):
        o.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{sy(g):.1f}" y2="{sy(g):.1f}"/>'
                 f'<text class="tick" x="{L - 8}" y="{sy(g) + 4:.1f}" text-anchor="end">{num(g)}</text>'
                 f'<text class="tick" x="{sx(g):.1f}" y="{H - B + 18}" text-anchor="middle">{num(g)}</text>')
    o.append(f'<line class="ref" x1="{sx(0)}" y1="{sy(0)}" x2="{sx(lim)}" y2="{sy(lim)}"/>'
             f'<text class="axis" x="{(L + W - R) / 2}" y="{H - 8}" text-anchor="middle">MCD64A1 (ha)</text>'
             f'<text class="axis" x="14" y="{(T + H - B) / 2}" text-anchor="middle" transform="rotate(-90 14 {(T + H - B) / 2})">Nuestro método (ha)</text>')
    for r in sorted(v.itertuples(), key=lambda r: r.grupo in vsel):
        cl = "pt-pasto" if r.grupo in vsel else "pt-bosque" if r.cobertura_dominante == "pastizal" else "pt-otro"
        o.append(f'<circle class="{cl}" cx="{sx(r.mcd64a1_ha):.1f}" cy="{sy(r.area_quemada_ha):.1f}" r="6">'
                 f'<title>{r.grupo} ({r.cobertura_dominante}): nuestro {num(r.area_quemada_ha, 1, False)} ha, MCD64A1 {num(r.mcd64a1_ha, 1, False)} ha</title></circle>')
    x = L + 14
    for cl, n in [("pt-pasto", "Los 3 de la regla"), ("pt-bosque", "Pastizal dominante"), ("pt-otro", "Otros (bosque)")]:
        o.append(f'<circle class="{cl}" cx="{x}" cy="{T + 12}" r="6"/><text class="tick" x="{x + 11}" y="{T + 16}">{n}</text>')
        x += 24 + len(n) * 7.2
    o.append("</svg>")
    return "\n".join(o)


def svg_lorenz():
    W, H, L, R, T, B = 640, 440, 56, 20, 20, 50
    sx = lambda p: L + p / 100 * (W - L - R)
    sy = lambda p: T + (1 - p / 100) * (H - T - B)
    g = gini.set_index("unidad").gini_todas_las_unidades
    estilos = {"distrito": "lz-a", "provincia": "lz-b", "grilla 10 x 10 km": "lz-c", "grilla 10 x 10 km desplazada 5 km": "lz-d"}
    o = svg_ini(W, H, "Curvas de Lorenz de los focos con cuatro particiones espaciales")
    for p in range(0, 101, 25):
        o.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{sy(p):.1f}" y2="{sy(p):.1f}"/>'
                 f'<text class="tick" x="{L - 8}" y="{sy(p) + 4:.1f}" text-anchor="end">{p}&#160;%</text>'
                 f'<text class="tick" x="{sx(p):.1f}" y="{H - B + 18}" text-anchor="middle">{p}&#160;%</text>')
    o.append(f'<line class="ref" x1="{sx(0)}" y1="{sy(0)}" x2="{sx(100)}" y2="{sy(100)}"/>'
             f'<text class="tick" x="{sx(55):.1f}" y="{sy(60):.1f}" transform="rotate(-36 {sx(55):.1f} {sy(60):.1f})">igualdad perfecta</text>'
             f'<text class="axis" x="{(L + W - R) / 2}" y="{H - 8}" text-anchor="middle">% de unidades, de menos a más focos</text>'
             f'<text class="axis" x="14" y="{(T + H - B) / 2}" text-anchor="middle" transform="rotate(-90 14 {(T + H - B) / 2})">% acumulado de focos</text>')
    y = T + 16
    for u, sub in lz.groupby("unidad", sort=False):
        pts = " ".join(f"{sx(a):.1f},{sy(b):.1f}" for a, b in zip(sub.pct_unidades, sub.pct_focos))
        o.append(f'<polyline class="line {estilos[u]}" points="{pts}"><title>{u}: Gini {num(g[u], 3, False)}</title></polyline>')
        o.append(f'<line class="line {estilos[u]}" x1="{L + 14}" x2="{L + 40}" y1="{y - 4}" y2="{y - 4}"/>'
                 f'<text class="tick" x="{L + 46}" y="{y}">{u.replace("10 x 10", "10×10")} · Gini {num(g[u], 3)}</text>')
        y += 20
    o.append("</svg>")
    return "\n".join(o)


def chart(svg):
    return f'<div class="chart-scroll">\n{svg}\n</div>'


# ----------------------------------------------------------------------------- tablas
def filas_top20_html():
    f = []
    for r in pd.concat([med, no_med]).itertuples():
        n = f"{nombre(r.distrito)} <span class=\"muted\">({r.departamento})</span>"
        if r.medible:
            f.append(f'<tr class="medido"><td>{n}</td><td>{r.region}</td><td class="n">{r.focos}</td>'
                     f'<td class="n">{num(r.envolvente_ha)}</td><td class="n"><strong>{num(r.area_quemada_ha, 1)}</strong></td>'
                     f'<td>Medido · {r.cobertura_dominante}</td></tr>')
        else:
            inv = "" if pd.isna(r.despues_invalido_zona_pct) else f" ({num(r.despues_invalido_zona_pct, 1)}&nbsp;% de la zona inválida)"
            f.append(f'<tr class="dim"><td>{n}</td><td>{r.region}</td><td class="n">{r.focos}</td>'
                     f'<td class="n">{num(r.envolvente_ha)}</td><td class="n">—</td><td>{MOTIVO[r.categoria_motivo]}{inv}</td></tr>')
    return "\n".join("          " + x for x in f)


def filas_top20_md():
    f = []
    for r in pd.concat([med, no_med]).itertuples():
        if r.medible:
            f.append(f"| **{nombre(r.distrito)}** ({r.departamento}) | {r.region} | {r.focos} | {num(r.envolvente_ha, 0, False)} | "
                     f"**{num(r.area_quemada_ha, 1, False)}** | Medido · {r.cobertura_dominante} |")
        else:
            inv = "" if pd.isna(r.despues_invalido_zona_pct) else f" ({num(r.despues_invalido_zona_pct, 1, False)} % de la zona inválida)"
            f.append(f"| {nombre(r.distrito)} ({r.departamento}) | {r.region} | {r.focos} | {num(r.envolvente_ha, 0, False)} | — | "
                     f"{MOTIVO[r.categoria_motivo]}{inv} |")
    return "\n".join(f)


cob_tab = [(r.clase_worldcover, r.hectareas, r.pct) for r in cob.itertuples()]
cob_tab += [("Cultivo", 0.0, 0.0)] if "Cultivo" not in set(cob.clase_worldcover) else []
reg_tab = [(k, int(r.incendios), int(r.medidos), r.pct_medidos, int(r.fallo_nubes), int(r.fallo_sin_imagen_posterior),
            int(r.fallo_prefiltro_de_escena)) for k, r in reg.iterrows()]
val_tab = [(r.muestra, int(r.n), r.razon_mediana, r.razon_min, r.razon_max, r.chichas_corregida_ha) for r in val.itertuples()]
gini_tab = [(r.unidad.replace("10 x 10", "10 × 10"), int(r.unidades_con_focos), int(r.unidades_totales),
             r.gini_solo_con_focos, r.gini_todas_las_unidades) for r in gini.itertuples()]
sen_tab = [(r.umbral_dnbr, r.hectareas, r.pct_zona, bool(r.usado)) for r in sen.itertuples()]
med_tab = [(nombre(r.distrito), r.region, r.cobertura_dominante, r.area_quemada_ha, r.pct_sev_baja, r.pct_moderada_o_mas,
            r.diferencia_pct) for r in res.itertuples()]


# ----------------------------------------------------------------------------- frases compartidas
F = {
    "bajada": f"Intentamos medir el área quemada de los veinte incendios más grandes del Perú. Lo conseguimos con "
              f"{['cero', 'uno', 'dos', 'tres', 'cuatro', 'cinco'][n_med]}. Ese fracaso, y no las hectáreas, es el resultado.",
    "recuadro_sesgo": f"El sesgo no es geográfico sino de calendario. En la Amazonía se midió el {num(am.pct_medidos, 1)}&nbsp;% "
                      f"de los incendios y en los Andes el {num(an.pct_medidos, 1)}&nbsp;%, una diferencia que la prueba exacta de "
                      f"Fisher no distingue del azar (p&nbsp;=&nbsp;{num(p_fisher, 2)}). En octubre empieza la temporada de lluvias en "
                      f"ambas regiones. La consecuencia es incómoda: la temporada de fuego coincide con la temporada en que no se ve el "
                      f"suelo, así que cualquier indicador nacional de área quemada en tiempo casi real mide solo el subconjunto de "
                      f"incendios que las nubes dejaron pasar.",
    "nota_pref": f"Nueva Requena (Ucayali, {pref.focos} focos): la zona estaba limpia en un {num(limpio_pref, 1)}&nbsp;%, pero el "
                 f"pipeline descarta de entrada las escenas con más del 80&nbsp;% de nubes en la escena completa. Es un caso medible "
                 f"perdido por una decisión propia. No se corrigió para no cambiar el método a mitad del análisis.",
    "nota_paracas": f"Se excluyó un grupo de focos en Paracas (Ica, {paracas.focos} focos en 49&nbsp;ha) con un criterio escrito y "
                    f"aplicado a los 40 primeros candidatos: no es un incendio si más de la mitad de las detecciones S-NPP de "
                    f"2012-2025 en su zona son de tipo 2 en FIRMS (fuente estática terrestre, como una planta industrial). En "
                    f"Paracas lo son {num(paracas.detecciones_tipo2)} de {num(paracas.detecciones_2012_2025)} "
                    f"({num(paracas.pct_tipo2, 1)}&nbsp;%), detectadas en {num(paracas.dias_con_deteccion)} días distintos; en los "
                    f"demás candidatos, ninguna. Su lugar lo ocupa San Miguel (Ayacucho), el siguiente por número de focos.",
}


def plano(s):
    """Versión para Markdown de una frase HTML."""
    return s.replace("&nbsp;", " ").replace("&#160;", " ")


# ----------------------------------------------------------------------------- HTML
CSS = """
  :root {
    --bg: #f2f5f2; --fg: #14201d; --muted: #5c6b66; --card: #ffffff; --line: #d9e0dc;
    --accent: #0d6e5d; --accent2: #a85c32; --on-accent: #ffffff; --highlight: #dcebe6;
    --header-bg: #14201d; --header-fg: #f2f5f2; --header-muted: #b6c4be;
    --sev-baja: #f2d024; --sev-modbaja: #f08c3a; --sev-modalta: #d93a1f; --sev-alta: #6e1708;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0e1715; --fg: #e4ebe8; --muted: #9aaba5; --card: #16221f; --line: #2a3a35;
      --accent: #45b39d; --accent2: #d98c5f; --on-accent: #0e1715; --highlight: #1b332d;
    }
  }
  * { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; color-scheme: light dark; }
  body { margin: 0; background: var(--bg); color: var(--fg); font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 17px; line-height: 1.6; }
  .wrap { max-width: 920px; margin: 0 auto; padding: 0 16px; }
  header.top { background: var(--header-bg); color: var(--header-fg); padding: 56px 0 44px; border-bottom: 1px solid var(--line); }
  header.top h1 { font-size: clamp(2.2rem, 7vw, 3.6rem); line-height: 1.05; margin: 0 0 16px; letter-spacing: -0.02em; }
  header.top .bajada { font-size: clamp(1.05rem, 2.6vw, 1.3rem); max-width: 40em; margin: 0 0 22px; }
  header.top .firma { font-size: 0.9rem; color: var(--header-muted); border-top: 2px solid #45b39d; padding-top: 10px; display: inline-block; margin: 0; }
  main { padding-bottom: 32px; }
  section { padding: 36px 0 8px; }
  h2 { font-size: 1.5rem; line-height: 1.25; margin: 0 0 14px; }
  h2 .num { color: var(--accent); font-variant-numeric: tabular-nums; margin-right: 6px; }
  h3 { font-size: 1.08rem; margin: 26px 0 6px; }
  p { margin: 0 0 14px; }
  a { color: var(--accent); }
  .muted { color: var(--muted); }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin: 20px 0 8px; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 18px; }
  .card .big { font-size: 2.4rem; font-weight: 750; line-height: 1.05; color: var(--accent); font-variant-numeric: tabular-nums; margin-bottom: 8px; }
  .card p { margin: 0; font-size: 0.95rem; }
  .card h3 { margin-top: 0; color: var(--accent2); }
  figure { margin: 18px 0 0; }
  figure img { width: 100%; height: auto; display: block; border-radius: 8px; border: 1px solid var(--line); background: #fff; }
  figcaption { font-size: 0.9rem; color: var(--muted); margin-top: 8px; }
  .chart-scroll { overflow-x: auto; background: var(--card); border: 1px solid var(--line); border-radius: 8px; }
  svg.chart { width: 100%; min-width: 540px; max-width: 760px; height: auto; display: block; margin: 0 auto; }
  svg.chart .grid { stroke: var(--line); stroke-width: 1; }
  svg.chart .ref { stroke: var(--muted); stroke-width: 1; stroke-dasharray: 4 4; }
  svg.chart text { fill: var(--muted); font-size: 13px; font-family: inherit; }
  svg.chart text.lbl { fill: var(--fg); font-size: 14px; font-weight: 600; }
  svg.chart text.axis { font-size: 14px; }
  svg.chart text.val { font-size: 12px; }
  svg.chart text.val.strong { fill: var(--fg); font-weight: 700; font-size: 14px; }
  svg.chart .hit { fill: transparent; }
  svg.chart .b-pol { fill: var(--accent2); }
  svg.chart .b-ani { fill: var(--accent2); opacity: 0.45; }
  svg.chart .line { fill: none; stroke-width: 2; }
  svg.chart .s1 { stroke: var(--accent); }
  svg.chart .dot.s1 { fill: var(--accent); stroke: var(--card); stroke-width: 2; }
  svg.chart .sev-b { fill: var(--sev-baja); } svg.chart .sev-mb { fill: var(--sev-modbaja); }
  svg.chart .sev-ma { fill: var(--sev-modalta); } svg.chart .sev-a { fill: var(--sev-alta); }
  svg.chart .pt-pasto { fill: var(--accent); stroke: var(--card); stroke-width: 2; }
  svg.chart .pt-bosque { fill: var(--accent2); stroke: var(--card); stroke-width: 2; }
  svg.chart .pt-otro { fill: var(--muted); opacity: 0.55; stroke: var(--card); stroke-width: 1.5; }
  svg.chart .torn-lo { fill: var(--accent2); } svg.chart .torn-hi { fill: var(--accent); }
  svg.chart .base { stroke: var(--fg); stroke-width: 1.5; }
  svg.chart .lz-a { stroke: var(--accent); } svg.chart .lz-b { stroke: var(--accent2); }
  svg.chart .lz-c { stroke: var(--fg); } svg.chart .lz-d { stroke: var(--fg); stroke-dasharray: 2 5; stroke-width: 2.5; }
  .table-scroll { overflow-x: auto; margin: 14px 0 10px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
  th, td { padding: 8px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: middle; }
  th { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); font-weight: 600; }
  td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
  tr.total td { font-weight: 700; border-top: 2px solid var(--fg); }
  tr.dim td { color: var(--muted); }
  tr.medido td { background: var(--highlight); }
  .note { font-size: 0.9rem; color: var(--muted); border-left: 3px solid var(--line); padding-left: 12px; }
  .callout { background: var(--card); border: 1px solid var(--line); border-left: 5px solid var(--accent); border-radius: 8px; padding: 16px 18px; margin: 16px 0; }
  .callout.alt { border-left-color: var(--accent2); }
  .callout p:last-child { margin-bottom: 0; }
  ul.clean, ol.clean { padding-left: 1.2em; margin: 0 0 14px; }
  ul.clean li, ol.clean li { margin-bottom: 6px; }
  code { font-family: ui-monospace, "Cascadia Mono", Consolas, monospace; font-size: 0.9em; overflow-wrap: anywhere; }
  footer { border-top: 1px solid var(--line); padding: 22px 0 40px; font-size: 0.88rem; color: var(--muted); }
  footer p { margin: 0 0 8px; }
  :root { --barra-h: 50px; }
  @media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }
  section[id], header[id] { scroll-margin-top: calc(var(--barra-h) + 12px); }
  .barra { position: sticky; top: 0; z-index: 2000; background: var(--header-bg); color: var(--header-fg); border-bottom: 1px solid #2a3a35; }
  .barra-in { max-width: 1240px; margin: 0 auto; padding: 0 16px; display: flex; align-items: center; gap: 16px; }
  .marca { display: flex; align-items: center; gap: 8px; color: var(--header-fg); text-decoration: none; font-weight: 650; font-size: 0.9rem; white-space: nowrap; }
  .punto { width: 10px; height: 10px; border-radius: 50%; background: #0d6e5d; box-shadow: 0 0 0 2px #45b39d; flex: none; }
  .enlaces { position: relative; flex: 1; min-width: 0; display: flex; overflow-x: auto; scrollbar-width: none; -webkit-overflow-scrolling: touch; }
  .enlaces::-webkit-scrollbar { display: none; }
  .enlaces > :first-child { margin-left: auto; } .enlaces > :last-child { margin-right: auto; }
  .enlaces a { color: var(--header-muted); text-decoration: none; font-size: 0.85rem; padding: 14px 9px 12px; white-space: nowrap; border-bottom: 2px solid transparent; }
  .enlaces a:hover, .enlaces a:focus-visible { color: var(--header-fg); }
  .enlaces a.activo { color: var(--header-fg); border-bottom-color: #45b39d; }
  .barra-fecha { margin: 0; font-size: 0.72rem; line-height: 1.35; color: var(--header-muted); white-space: nowrap; text-align: right; }
  .barra-fecha span { display: block; }
  .corte { font-size: 0.82rem; color: var(--muted); margin: 0; padding-top: 14px; }
  h2 a.num { text-decoration: none; }
  h2 a.num:hover, h2 a.num:focus-visible { text-decoration: underline; }
  .guia .card h3 { font-size: 1rem; margin-bottom: 6px; }
  .sev-lista { list-style: none; padding: 0; margin: 0 0 8px; font-size: 0.95rem; }
  .sev-lista li { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; font-variant-numeric: tabular-nums; }
  .sw { width: 16px; height: 16px; border-radius: 4px; flex: none; border: 1px solid var(--line); }
  @media (max-width: 1120px) {
    :root { --barra-h: 76px; }
    .barra-in { flex-wrap: wrap; gap: 0 12px; }
    .marca { padding-top: 9px; }
    .barra-fecha { margin-left: auto; padding-top: 9px; }
    .barra-fecha span { display: inline; }
    .enlaces { order: 3; flex-basis: 100%; margin: 0 -16px; padding: 0 7px; }
    .enlaces a { padding: 10px 9px 9px; }
  }
  @media (max-width: 560px) {
    :root { --barra-h: 94px; }
    .barra-fecha { flex-basis: 100%; margin-left: 0; padding-top: 2px; text-align: left; }
    body { font-size: 16px; }
    header.top { padding: 40px 0 32px; }
    th, td { padding: 7px 6px; }
    .card .big { font-size: 2rem; }
    svg.chart { min-width: 0; }
    svg.chart text, svg.chart text.axis, svg.chart text.lbl { font-size: 20px; }
    svg.chart text.val { font-size: 18px; }
    svg.chart text.val.strong { font-size: 22px; }
    svg.chart .t-opc { display: none; }
  }
"""


# Resalta en la barra la sección que se está leyendo. Sin JavaScript los enlaces ancla funcionan igual.
SCRIPT_BARRA = r"""
(function () {
  var barra = document.querySelector('.barra');
  if (!barra) return;
  function alto() { document.documentElement.style.setProperty('--barra-h', barra.offsetHeight + 'px'); }
  alto();
  window.addEventListener('resize', alto);
  if (!('IntersectionObserver' in window)) return;
  var nav = barra.querySelector('.enlaces');
  var enlaces = [].slice.call(nav.querySelectorAll('a'));
  var objetivos = enlaces.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
  var actual = null;
  function marcar() {
    var linea = window.innerHeight * 0.3 + 1, k = -1;
    objetivos.forEach(function (s, i) { if (s && s.getBoundingClientRect().top <= linea) k = i; });
    var a = enlaces[k] || null;
    if (a === actual) return;
    if (actual) { actual.classList.remove('activo'); actual.removeAttribute('aria-current'); }
    actual = a;
    if (a) {
      a.classList.add('activo');
      a.setAttribute('aria-current', 'true');
      nav.scrollTo({ left: a.offsetLeft - (nav.clientWidth - a.offsetWidth) / 2, behavior: 'smooth' });
    }
  }
  var io = new IntersectionObserver(marcar, { rootMargin: '-30% 0px -69% 0px' });
  [].forEach.call(document.querySelectorAll('main section[id]'), function (s) { io.observe(s); });
  marcar();
})();
"""


def tabla_html(cabecera, filas, clases=None):
    th = "".join(f'<th{" class=" + chr(34) + "n" + chr(34) if c else ""}>{h}</th>' for h, c in cabecera)
    return (f'<div class="table-scroll">\n      <table>\n        <thead><tr>{th}</tr></thead>\n        <tbody>\n{filas}\n'
            f'        </tbody>\n      </table>\n    </div>')


def html():
    s_cards = f"""
    <div class="cards">
      <div class="card"><div class="big">{n_med} de {N}</div><p>incendios medidos: una tasa de éxito del {num(100 * n_med / N)}&nbsp;%.</p></div>
      <div class="card"><div class="big">{n_nubes}</div><p>descartados por nubes sobre la zona; otros {n_sinpasada} sin ninguna pasada de Sentinel-2 y {n_pref} por el prefiltro.</p></div>
      <div class="card"><div class="big">p&nbsp;=&nbsp;{num(p_fisher, 2)}</div><p>sin diferencia significativa entre Andes y Amazonía en la tasa de éxito.</p></div>
    </div>"""
    t20 = tabla_html([("Incendio", 0), ("Región", 0), ("Focos", 1), ("Envolvente (ha)", 1), ("Quemado (ha)", 1), ("Resultado", 0)],
                     filas_top20_html())
    t_cob = tabla_html([("Cobertura (WorldCover 2021)", 0), ("Hectáreas", 1), ("% de lo quemado", 1)],
                       "\n".join(f'          <tr><td>{c}</td><td class="n">{num(h, 1)}</td><td class="n">{num(p, 1)}&nbsp;%</td></tr>' for c, h, p in cob_tab)
                       + f'\n          <tr class="total"><td>Total</td><td class="n">{num(cob.hectareas.sum(), 1)}</td><td class="n">100&nbsp;%</td></tr>')
    t_reg = tabla_html([("Región", 0), ("Incendios", 1), ("Medidos", 1), ("% medidos", 1), ("Nubes", 1), ("Sin pasada", 1), ("Prefiltro", 1)],
                       "\n".join(f'          <tr><td>{a}</td><td class="n">{b}</td><td class="n">{c}</td><td class="n">{num(d, 1)}&nbsp;%</td>'
                                 f'<td class="n">{e}</td><td class="n">{f}</td><td class="n">{g}</td></tr>' for a, b, c, d, e, f, g in reg_tab))
    t_val = tabla_html([("Muestra", 0), ("n", 1), ("Razón mediana (nuestro / MCD64A1)", 1), ("Rango", 1), ("Chichas corregida (ha)", 1)],
                       "\n".join(f'          <tr><td>{a}</td><td class="n">{b}</td><td class="n">{num(c, 3)}</td><td class="n">{num(d, 3)} – {num(e, 3)}</td>'
                                 f'<td class="n">{num(f)}</td></tr>' for a, b, c, d, e, f in val_tab))
    t_gini = tabla_html([("Partición", 0), ("Unidades con focos", 1), ("Gini (solo con focos)", 1), ("Gini (todas)", 1)],
                        "\n".join(f'          <tr><td>{a}</td><td class="n">{num(b)} de {num(c)}</td><td class="n">{num(d, 3)}</td><td class="n">{num(e, 3)}</td></tr>'
                                  for a, b, c, d, e in gini_tab))
    t_img = tabla_html([("Imagen", 0), ("Fecha", 0), ("Tile", 0), ("Nubes en la zona", 1), ("Nubes en la escena", 1)],
                       f'          <tr><td>Antes</td><td>{antes.fecha}</td><td>{antes.tile}</td><td class="n">{num(antes.nubes_zona_pct, 1)}&nbsp;%</td><td class="n">{num(antes.nubes_escena_pct, 1)}&nbsp;%</td></tr>\n'
                       f'          <tr><td>Después</td><td>{despues.fecha}</td><td>{despues.tile}</td><td class="n">{num(despues.nubes_zona_pct, 1)}&nbsp;%</td><td class="n">{num(despues.nubes_escena_pct, 1)}&nbsp;%</td></tr>')
    anillo_txt = " y ".join(f"{'uno' if r.focos_poligono_mas_1km == 1 else ['', 'uno', 'dos', 'tres', 'cuatro', 'cinco'][r.focos_poligono_mas_1km]} en {r.anio}"
                            for r in anillo.itertuples())
    ext = extras_html()
    enlaces = "\n".join(f'      <a href="#{i}">{t}</a>' for i, t in NAV)

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lo que no se puede medir</title>
<meta name="description" content="{plano(F['bajada'])}">
<style>{CSS}{ext['css']}</style>
{ext['head']}
</head>
<body>

<nav class="barra" aria-label="Secciones de la página">
  <div class="barra-in">
    <a class="marca" href="#inicio"><span class="punto" aria-hidden="true"></span>Incendios del Perú · Octubre 2026</a>
    <div class="enlaces">
{enlaces}
    </div>
    <p class="barra-fecha"><span>Ventana 14-21 oct 2026 ·</span> <span>FIRMS descargado el {DESCARGA_FIRMS[0]}</span></p>
  </div>
</nav>

<header class="top" id="inicio">
  <div class="wrap">
    <h1>Lo que no se puede medir</h1>
    <p class="bajada">{F['bajada']}</p>
    <p class="firma">{FIRMA}</p>
  </div>
</header>

<main class="wrap">

  <p class="corte">Corte de datos: {DESCARGA_FIRMS[1]} · Trabajo académico independiente, no reemplaza los reportes del COEN, INDECI, SERFOR ni SERNANP.</p>

  <section id="como-leer">
    <h2>Cómo leer esta página</h2>
    <div class="cards guia">
      <div class="card"><h3>Foco de calor</h3><p>Un píxel de unos 375&nbsp;m donde un satélite VIIRS detectó fuego. Incluye quemas agrícolas y de pastos, no solo incendios forestales.</p></div>
      <div class="card"><h3>Incendio</h3><p>Aquí, un grupo de focos vecinos: dos focos van al mismo incendio si están a 1&nbsp;km o menos y a 48&nbsp;h o menos entre sí.</p></div>
      <div class="card"><h3>Envolvente</h3><p>El polígono que rodea los focos de un incendio. Mide la extensión del grupo, <strong>no</strong> el área quemada.</p></div>
      <div class="card"><h3>dNBR</h3><p>La diferencia del índice NBR entre una imagen Sentinel-2 de antes y otra de después. Mide cambio en la vegetación, no fuego.</p></div>
      <div class="card"><h3>«Medible»</h3><p>Que existe un par de imágenes Sentinel-2, antes y después, con poca nube sobre la zona del incendio: como máximo el 30&nbsp;% tapado.</p></div>
      <div class="card"><h3>Colores de severidad</h3>
        <ul class="sev-lista">
          <li><span class="sw" style="background:var(--sev-baja)"></span>Baja · dNBR 0,10–0,27</li>
          <li><span class="sw" style="background:var(--sev-modbaja)"></span>Moderada-baja · 0,27–0,44</li>
          <li><span class="sw" style="background:var(--sev-modalta)"></span>Moderada-alta · 0,44–0,66</li>
          <li><span class="sw" style="background:var(--sev-alta)"></span>Alta · 0,66 o más</li>
        </ul>
        <p>Por debajo de 0,10 se cuenta como no quemado.</p></div>
    </div>
  </section>

  <section id="resultado">
    <h2><a class="num" href="#resultado" aria-label="Enlace a la sección 1">1</a>El resultado principal: el {num(100 - 100 * n_med / N)}&nbsp;% no era medible</h2>
    <p>Sobre cada uno de los {N} incendios con más focos de calor entre el 14 y el 21 de octubre de 2026 se corrió exactamente el mismo procedimiento: buscar una imagen Sentinel-2 antes y otra después del fuego, enmascarar nubes, calcular el dNBR y cruzarlo con un mapa de cobertura. La regla para aceptar una imagen se fijó antes de mirar los datos: como máximo el 30&nbsp;% de la zona tapada.</p>
{s_cards}
    <div class="callout"><p>{F['recuadro_sesgo']}</p></div>
    {t20}
    <p class="note">{F['nota_pref']}</p>
    <p class="note">{F['nota_paracas']}</p>
  </section>

  {ext['rejilla']}

  <section id="nacional">
    <h2><a class="num" href="#nacional" aria-label="Enlace a la sección 2">2</a>El mapa nacional y cómo se comporta el fuego</h2>
    {ext['mapa_nacional']}
    <div class="cards">
      <div class="card"><div class="big">{num(nac['% focos diurnos'], 1)}&nbsp;%</div><p>de los {num(nac['focos (confianza nominal/alta, 14-21 oct 2026)'])} focos fue diurno.</p></div>
      <div class="card"><div class="big">{num(nac['% incendios de menos de 12 h entre el primer y el último foco'], 1)}&nbsp;%</div><p>de los {num(n_inc)} incendios duró menos de 12&nbsp;h entre su primer y su último foco.</p></div>
      <div class="card"><div class="big">{num(nac['FRP mediana por foco (MW)'], 2)}&nbsp;MW</div><p>de potencia radiativa (FRP) mediana por foco.</p></div>
      <div class="card"><div class="big">{n_largos}</div><p>de {num(n_inc)} incendios superaron los 3 días.</p></div>
    </div>
    <p>El fuego peruano de esa semana fue mayoritariamente corto, de baja potencia y de día. VIIRS detecta mejor de noche, cuando el suelo está frío y el contraste térmico es mayor, así que el predominio diurno no se explica por el sensor.</p>
    <p class="note">{num(nac['incendios con un solo foco'])} de los {num(n_inc)} incendios tienen un solo foco; para ellos la duración es cero. La duración mide el tiempo entre la primera y la última detección, no cuánto ardió el fuego.</p>
  </section>

  <section id="chichas">
    <h2><a class="num" href="#chichas" aria-label="Enlace a la sección 3">3</a>El caso medido: Chichas, {num(ch_ha)}&nbsp;ha donde nunca había ardido</h2>
    <figure>
      <img src="outputs/mapa_chichas.png" width="1500" height="1350" loading="lazy" alt="Mapa del área quemada en Chichas, Arequipa: una mancha extensa, mayormente amarilla (severidad baja) con zonas naranjas (moderada-baja), con los 178 focos VIIRS como puntos celestes y la zona analizada rodeada por una línea negra.">
      <figcaption>Severidad (dNBR) sobre el infrarrojo cercano de la imagen Sentinel-2 del 20 de octubre de 2026. Puntos celestes: los 178 focos VIIRS. Línea negra: la zona analizada (focos + 1&nbsp;km). Coordenadas UTM 18S.</figcaption>
    </figure>
    {ext['comparador']}
    <div class="cards">
      <div class="card"><div class="big">{num(ch_ha)}&nbsp;ha</div><p>quemadas (dNBR&nbsp;≥&nbsp;0,10), el {num(pct_zona_ch)}&nbsp;% de las {num(zona_ch)}&nbsp;ha analizadas.</p></div>
      <div class="card"><div class="big">{num(pct_dist, 1)}&nbsp;%</div><p>del distrito de Chichas ({num(dist_ha)}&nbsp;ha según los límites GADM 4.1).</p></div>
      <div class="card"><div class="big">0</div><p>focos dentro del área quemada entre 2012 y 2025.</p></div>
    </div>
    <h3>Recurrencia: catorce años sin un solo foco</h3>
    <figure>
{chart(svg_recurrencia())}
      <figcaption>Focos Suomi-NPP de confianza nominal o alta por año: oscuro, dentro del área que ardió en 2026; claro, en el anillo de 1&nbsp;km alrededor. *2026: solo los ocho días del 14 al 21 de octubre.</figcaption>
    </figure>
    <p>Entre 2012 y 2025, con entre {dias_min} y {dias_max} días de registro al año, el área que ardió en 2026 no registró <strong>ni un solo foco</strong>. En el anillo de 1&nbsp;km hubo {anillo_txt}. En los ocho días de registro de octubre de 2026 hubo {r26.focos_poligono} focos dentro y {r26.focos_poligono_mas_1km} contando el anillo.</p>
    <div class="callout alt"><p><strong>Queda descartada una quema de manejo recurrente.</strong> Una zona de quema habitual aparece en el registro año tras año, y esta no aparece nunca. La salvedad es de escala: una quema muy pequeña o muy rápida puede ocurrir entre dos pasadas del satélite sin dejar foco.</p></div>
    <p>Además, el {num(pct_noche_ch, 1)}&nbsp;% de los focos de Chichas fue nocturno: la {ORDINAL[rango_noche]} firma más nocturna de los veinte, en un país donde el {num(nac['% focos diurnos'], 1)}&nbsp;% de los focos fue diurno.</p>
  </section>

  <section id="reto">
    <h2><a class="num" href="#reto" aria-label="Enlace a la sección 4">4</a>Reto C: qué tipo de suelo ardió</h2>
    {t_cob}
    <div class="callout"><p><strong>Cero hectáreas de cultivo y una décima de bosque.</strong> El daño es pérdida de forraje y el afectado es la ganadería extensiva. Con recurrencia nula, además, no es forraje que se queme en un ciclo de manejo.</p></div>
  </section>

  <section id="hipotesis">
    <h2><a class="num" href="#hipotesis" aria-label="Enlace a la sección 5">5</a>Tres hipótesis que cayeron</h2>
    <h3>a) «En pastizal la severidad sale baja y en bosque alta»: no se sostiene</h3>
    <figure>
{chart(svg_severidad())}
      <figcaption>Distribución de severidad (escala de Key y Benson) del área quemada en los cuatro incendios medidos.</figcaption>
    </figure>
    <p>Los pastizales van del {num(pasto.pct_moderada_o_mas.min(), 1)}&nbsp;% al {num(pasto.pct_moderada_o_mas.max(), 1)}&nbsp;% de severidad moderada o superior, y el único bosque medible, {nombre(bosque.distrito)}, cae dentro de ese rango con {num(bosque.pct_moderada_o_mas, 1)}&nbsp;%. Chichas es el atípico. Con n&nbsp;=&nbsp;{n_med} no se puede concluir que la escala de Key y Benson esté mal calibrada para el pastizal andino; para eso hace falta severidad medida en campo. Y no encontramos ningún estudio de dNBR con validación de campo en puna o páramo: ese vacío es en sí mismo un hallazgo.</p>
    <h3>b) «Los focos sobrestiman de forma sistemática»: no</h3>
    <figure>
{chart(svg_envolvente())}
      <figcaption>Envolvente de los focos frente al área medida. Verde: pastizal dominante; ocre: bosque. Bajo la diagonal, la envolvente sobrestima.</figcaption>
    </figure>
    <p>{num(dif['Iparia'], 1)}&nbsp;% en Iparía, {num(dif['Chichas'], 1)}&nbsp;% en Chichas, {num(dif['Curahuasi'], 1)}&nbsp;% en Curahuasi y +{num(dif['SanCristobal'], 1)}&nbsp;% en San Cristóbal. Tres sobrestiman y uno subestima, en un rango demasiado amplio para un factor de corrección. Lo que queda en pie es que contar focos no mide hectáreas.</p>
    <h3>c) «Las nubes castigan sobre todo a la Amazonía»: no</h3>
    {t_reg}
    <p>Fisher, p&nbsp;=&nbsp;{num(p_fisher, 2)}. Las nubes tumbaron el {num(am.pct_fallo_nubes, 1)}&nbsp;% de los casos amazónicos y el {num(an.pct_fallo_nubes, 1)}&nbsp;% de los andinos.</p>
  </section>

  <section id="robustez">
    <h2><a class="num" href="#robustez" aria-label="Enlace a la sección 6">6</a>Robustez</h2>
    <figure>
{chart(svg_tornado())}
      <figcaption>Rango de hectáreas quemadas en Chichas al cambiar una decisión por vez. La línea vertical es la base ({num(ch_ha, 1)}&nbsp;ha).</figcaption>
    </figure>
    <p>El umbral recorre {num(umbral_r, 1)}&nbsp;ha; el par de imágenes, {num(rt['Par de imágenes'], 1)}; la máscara, {num(rt['Máscara SCL'], 1)}; la zona, {num(rt['Zona'], 1)}. El umbral solo mueve {num(umbral_r / otros_r, 1)} veces más que las otras tres decisiones juntas ({num(otros_r, 1)}&nbsp;ha).</p>
    <figure>
{chart(svg_sensibilidad())}
      <figcaption>Hectáreas quemadas en Chichas según el umbral de dNBR. La línea discontinua marca el umbral usado (0,10).</figcaption>
    </figure>
    <p>La curva colapsa rápido porque los píxeles quemados se apiñan cerca del umbral. Con 0,35, a Chichas le queda el {num(100 * ratio035['Chichas'])}&nbsp;% del área medida con 0,10; a Iparía, el {num(100 * ratio035['Iparia'])}&nbsp;%.</p>
    <div class="callout alt"><p><strong>Más rigor aparente, menos señal.</strong> Endurecer la máscara de nubes <em>reduce</em> el área en {num(mask_quita, 1)}&nbsp;ha, pero no porque quite nubes: la capa SCL de Sentinel-2 clasifica {num(diag['quemado base marcado SCL 2 (zona oscura) en la imagen posterior'], 1)}&nbsp;ha de la propia cicatriz como «zona oscura» y {num(diag['quemado base marcado SCL 7 (sin clasificar) en la imagen posterior'], 1)}&nbsp;ha como «sin clasificar», y la máscara estricta las descarta.</p></div>
  </section>

  <section id="validacion">
    <h2><a class="num" href="#validacion" aria-label="Enlace a la sección 7">7</a>Validación contra MCD64A1</h2>
    <p>MCD64A1, el producto mensual de área quemada de MODIS, aún no existe para octubre de 2026, así que se validó el método en incendios de 2024 con una regla fijada antes de ver resultados.</p>
    <figure>
{chart(svg_validacion())}
      <figcaption>Hectáreas de nuestro método frente a MCD64A1 en los {int(v21.n)} candidatos medibles. Sobre la diagonal, nuestro método da más.</figcaption>
    </figure>
    {t_val}
    <div class="callout"><p><strong>La cifra principal sigue siendo {num(ch_ha)}&nbsp;ha;</strong> las corregidas son alternativas, por tres razones: la validación es casi toda bosque amazónico y el caso es pastizal andino; MCD64A1 usa píxeles de 500&nbsp;m y es otra estimación satelital, no un dato de campo; y varios de los {int(v21.n)} candidatos se solapan en el espacio, así que no son independientes.</p></div>
  </section>

  <section id="maup">
    <h2><a class="num" href="#maup" aria-label="Enlace a la sección 8">8</a>Concentración y MAUP</h2>
    <figure>
{chart(svg_lorenz())}
      <figcaption>Curvas de Lorenz de los {num(nac['focos (confianza nominal/alta, 14-21 oct 2026)'])} focos con cuatro particiones, contando también las unidades sin focos.</figcaption>
    </figure>
    {t_gini}
    <p>El Gini va de {num(g_min, 3)} a {num(g_max, 3)} según la unidad y según si se cuentan las unidades sin fuego. Cualquier índice de concentración que no declare su unidad no significa nada. Lo robusto es otra cosa: la distribución es muy desigual en las cuatro particiones.</p>
  </section>

  <section id="implicaciones">
    <h2><a class="num" href="#implicaciones" aria-label="Enlace a la sección 9">9</a>Implicaciones</h2>
    <ul class="clean">
      <li>No se puede construir un indicador nacional de área quemada en tiempo casi real para el Perú en octubre: con {n_med} de {N}, lo que se reporta es una muestra sesgada.</li>
      <li>Las hectáreas no son comparables entre estudios si no declaran el umbral: en Chichas, solo el umbral las mueve {num(umbral_r, 1)}&nbsp;ha.</li>
      <li>Endurecer la máscara puede empeorar la medición.</li>
      <li>Contar focos no mide daño: la desviación frente al área medida va de {num(dif.min(), 1)}&nbsp;% a +{num(dif.max(), 1)}&nbsp;%.</li>
      <li>El gasto parece rendir más en prevención que en combate: solo {n_largos} de {num(n_inc)} incendios superaron los 3 días.</li>
      <li>Un índice de concentración exige declarar su unidad espacial.</li>
    </ul>
  </section>

  <section id="precio">
    <h2><a class="num" href="#precio" aria-label="Enlace a la sección 10">10</a>Qué haría falta para ponerle precio</h2>
    <ul class="clean">
      <li><strong>Capacidad de carga</strong> del pastizal quemado: cuántos animales sostenía.</li>
      <li><strong>Tiempo de recuperación del forraje</strong>: cuántas temporadas tarda en volver.</li>
      <li><strong>Hogares y cabezas de ganado dependientes</strong> de esas hectáreas.</li>
      <li><strong>Intencionalidad</strong>: si fue una quema deliberada que se escapó o un accidente. Esta sí se pudo acotar en parte: con recurrencia cero queda descartada la quema rutinaria.</li>
    </ul>
    <p>La teledetección acota qué y cuánto se quemó, pero no determina si fue una pérdida.</p>
  </section>

  <section id="metodo">
    <h2><a class="num" href="#metodo" aria-label="Enlace a la sección 11">11</a>Método</h2>
    <ol class="clean">
      <li><strong>Focos</strong>: VIIRS de NASA FIRMS (Suomi-NPP, NOAA-20 y NOAA-21, CSV de 7 días descargado el 21 de octubre de 2026), confianza nominal o alta, filtrados a Perú con GADM 4.1.</li>
      <li><strong>Incendios</strong>: dos focos pertenecen al mismo incendio si están a ≤&nbsp;1&nbsp;km y ≤&nbsp;48&nbsp;h entre sí.</li>
      <li><strong>Par de imágenes</strong>: Sentinel-2 L2A de Microsoft Planetary Computer; se elige la imagen con menos zona inválida, antes y después del fuego.</li>
      <li><strong>dNBR y severidad</strong>: NBR&nbsp;=&nbsp;(B8A&nbsp;−&nbsp;B12)/(B8A&nbsp;+&nbsp;B12); dNBR&nbsp;=&nbsp;NBR antes − NBR después; clases de Key y Benson.</li>
      <li><strong>Cobertura</strong>: ESA WorldCover 2021 cruzado con los píxeles quemados.</li>
      <li><strong>Contraste</strong>: recurrencia con el archivo anual S-NPP 2012-2025, sensibilidad a cada decisión y validación contra MCD64A1.</li>
    </ol>
    {t_img}
    <ul class="clean">
      <li><strong>Umbral</strong>: dNBR&nbsp;≥&nbsp;0,10.</li>
      <li><strong>Máscara SCL</strong>: sombra, nube media, nube alta, cirros, agua y sin dato, en cualquiera de las dos fechas.</li>
      <li><strong>Zona</strong>: envolvente de los focos + 1&nbsp;km&nbsp;=&nbsp;{num(zona_ch)}&nbsp;ha en Chichas, rejilla de 20&nbsp;m.</li>
      <li><strong>Recurrencia solo con S-NPP</strong>, el único con registro continuo desde 2012: sumar NOAA-20 (desde 2018) y NOAA-21 (desde 2023) inflaría los años recientes.</li>
    </ul>
    <p>Código, tablas y cómo reproducir: <code>src/</code>, <code>outputs/</code> y el README del repositorio.</p>
  </section>

  <section id="limitaciones">
    <h2><a class="num" href="#limitaciones" aria-label="Enlace a la sección 12">12</a>Limitaciones y qué no se pudo hacer</h2>
    <ul class="clean">
      <li><strong>n&nbsp;=&nbsp;{n_med}.</strong> Ninguna comparación entre incendios medidos tiene potencia estadística.</li>
      <li><strong>Un foco no es un incendio ni una hectárea</strong>: es un píxel de 375&nbsp;m donde un satélite detectó calor.</li>
      <li><strong>La validación no cubre el bioma del caso</strong>: casi toda es bosque amazónico, contra un producto de 500&nbsp;m.</li>
      <li><strong>La firma diurna no prueba intencionalidad.</strong></li>
      <li><strong>El prefiltro descartó al menos un caso medible</strong> (Nueva Requena).</li>
      <li><strong>Paracas se excluyó</strong> como fuente estática con el criterio escrito de la sección 1; con otro criterio el top 20 cambiaría.</li>
      <li><strong>Una semana no es una temporada.</strong></li>
      <li><strong>WorldCover es de 2021</strong>: la cobertura pudo cambiar antes del incendio.</li>
      <li><strong>Las cifras oficiales no se suman a estas</strong>: usan otros métodos y otras definiciones.</li>
    </ul>
  </section>

</main>

<footer>
  <div class="wrap">
    <p>Herramienta independiente con datos públicos; no reemplaza al COEN, INDECI, SERFOR ni SERNANP.</p>
    <p>Fuentes: NASA FIRMS (VIIRS NRT y archivo anual S-NPP 2012-2025), Copernicus Sentinel-2, ESA WorldCover 2021, Copernicus DEM y MODIS MCD64A1 vía Microsoft Planetary Computer, y GADM 4.1. Ventana analizada: 14-21 de octubre de 2026.</p>
  </div>
</footer>
{ext['scripts']}
<script>{SCRIPT_BARRA}</script>
</body>
</html>
"""


def extras_html():
    """Bloques de los mapas extra; cada uno aparece solo si sus archivos existen."""
    e = {"css": "", "head": "", "scripts": "", "comparador": "", "rejilla": "",
         "mapa_nacional": """<figure>
      <img src="outputs/mapa_nacional.png" width="1200" height="1500" loading="lazy" alt="Mapa del Perú con los 8 637 focos VIIRS del 14 al 21 de octubre de 2026 coloreados por potencia radiativa, concentrados en la selva central y los Andes del sur, y los 20 incendios con más focos marcados con círculos: cuatro verdes (medidos) y dieciséis grises (no medibles).">
      <figcaption>Focos VIIRS por potencia radiativa (FRP) y los 20 incendios con más focos: verde, los 4 medidos; gris, los 16 que no se pudieron medir.</figcaption>
    </figure>"""}
    try:
        import extras_pagina
        extras_pagina.completar(e)
    except ImportError:
        pass
    return e


# ----------------------------------------------------------------------------- README
def md_tabla(cab, filas):
    return "| " + " | ".join(cab) + " |\n|" + "|".join("---:" if c.endswith(":") else "---" for c in cab) \
        .replace("---:", "---:") + "|\n" + "\n".join(filas)


def antes_despues_md():
    if not (OUT / "chichas_rgb_antes.jpg").exists():
        return ""
    return (f"\nSentinel-2 en color real, mismo recorte y ajuste de color: {antes.fecha} (izquierda) y {despues.fecha} "
            f"(derecha). Las manchas blancas y oscuras abajo a la derecha del {despues.fecha} son nubes y sus sombras.\n\n"
            f'<img src="outputs/chichas_rgb_antes.jpg" width="49%" alt="Chichas antes del fuego"> '
            f'<img src="outputs/chichas_rgb_despues.jpg" width="49%" alt="Chichas después del fuego">\n')


def rejilla_md():
    mapas = [OUT / f"mapa_caso_{d.lower()}.png" for d in med.distrito]
    if not all(m.exists() for m in mapas):
        return ""
    filas = "\n".join(f"![{nombre(r.distrito)}: {num(r.area_quemada_ha, 1, False)} ha]({m.as_posix()})"
                      for r, m in zip(med.itertuples(), mapas))
    return f"\n**Los cuatro que sí se pudieron medir** (mismo método y escala de colores):\n\n{filas}\n"


def readme():
    t = lambda x: plano(x)
    cab20 = "| Incendio | Región | Focos | Envolvente (ha) | Quemado (ha) | Resultado |\n|---|---|---:|---:|---:|---|"
    cob_md = "\n".join(f"| {c} | {num(h, 1, False)} | {num(p, 1, False)} % |" for c, h, p in cob_tab)
    reg_md = "\n".join(f"| {a} | {b} | {c} | {num(d, 1, False)} % | {e} | {f} | {g} |" for a, b, c, d, e, f, g in reg_tab)
    val_md = "\n".join(f"| {a} | {b} | {num(c, 3, False)} | {num(d, 3, False)}-{num(e, 3, False)} | {num(f, 0, False)} |" for a, b, c, d, e, f in val_tab)
    gini_md = "\n".join(f"| {a} | {num(b, 0, False)} de {num(c, 0, False)} | {num(d, 3, False)} | {num(e, 3, False)} |" for a, b, c, d, e in gini_tab)
    sen_md = "\n".join(f"| {'**' if u else ''}{num(a, 2, False)}{' (usado)**' if u else ''} | {num(b, 1, False)} | {num(c, 1, False)} % |" for a, b, c, u in sen_tab)
    med_md = "\n".join(f"| {a} | {b} | {c} | {num(d, 1, False)} | {num(e, 1, False)} % | {num(f, 1, False)} % | {'+' if g > 0 else ''}{num(g, 1, False)} % |"
                       for a, b, c, d, e, f, g in med_tab)
    tor_md = "\n".join(f"| {r.decision} | {num(r.min_ha, 1, False)} | {num(r.max_ha, 1, False)} | {num(r.rango_ha, 1, False)} |" for r in tor.iloc[::-1].itertuples())
    anillo_md = " y ".join(f"{['', 'uno', 'dos', 'tres', 'cuatro', 'cinco'][r.focos_poligono_mas_1km]} en {r.anio}" for r in anillo.itertuples())
    return f"""# Lo que no se puede medir

{t(F['bajada'])}

{FIRMA}. La historia completa está en [index.html](index.html) (publicada en
https://gabriela-pozo.github.io/incendios-peru/ cuando se active GitHub Pages).

## 1. El resultado principal: el {num(100 - 100 * n_med / N, 0, False)} % no era medible

Sobre cada uno de los {N} incendios con más focos de calor entre el 14 y el 21 de octubre de 2026 se
corrió exactamente el mismo procedimiento (par Sentinel-2 antes y después, máscara de nubes, dNBR y
cruce con WorldCover). La regla para aceptar una imagen se fijó antes de mirar los datos: como máximo
el 30 % de la zona tapada.

- **{n_med} de {N}** incendios medidos: tasa de éxito del {num(100 * n_med / N, 0, False)} %.
- **{n_nubes}** descartados por nubes sobre la zona; {n_sinpasada} sin ninguna pasada de Sentinel-2 y {n_pref} por el prefiltro.
- **p = {num(p_fisher, 2, False)}**: sin diferencia significativa entre Andes y Amazonía.

> {t(F['recuadro_sesgo'])}

{cab20}
{filas_top20_md()}

{t(F['nota_pref'])}

{t(F['nota_paracas'])}
{rejilla_md()}
Tablas: `outputs/medicion_top20.csv`, `outputs/top20_exito_region.csv`, `outputs/top20_pruebas.csv`,
`outputs/fuentes_estaticas_candidatos.csv`.

## 2. El mapa nacional y cómo se comporta el fuego

![Mapa nacional de focos](outputs/mapa_nacional.png)

- {num(nac['% focos diurnos'], 1, False)} % de los {num(nac['focos (confianza nominal/alta, 14-21 oct 2026)'], 0, False)} focos fue diurno.
- {num(nac['% incendios de menos de 12 h entre el primer y el último foco'], 1, False)} % de los {num(n_inc, 0, False)} incendios duró menos de 12 h entre su primer y su último foco.
- FRP mediana por foco: {num(nac['FRP mediana por foco (MW)'], 2, False)} MW.
- Solo {n_largos} de {num(n_inc, 0, False)} incendios superaron los 3 días.

VIIRS detecta mejor de noche, cuando el suelo está frío y el contraste térmico es mayor, así que el
predominio diurno no se explica por el sensor. {num(nac['incendios con un solo foco'], 0, False)} incendios
tienen un solo foco (duración cero): la duración mide el tiempo entre la primera y la última detección.

Tabla: `outputs/comportamiento_nacional.csv`.

## 3. El caso medido: Chichas, {num(ch_ha, 0, False)} ha donde nunca había ardido

![Área quemada en Chichas](outputs/mapa_chichas.png)
{antes_despues_md()}
- **{num(ch_ha, 0, False)} ha** quemadas (dNBR ≥ 0,10), el {num(pct_zona_ch, 0, False)} % de las {num(zona_ch, 0, False)} ha analizadas.
- **{num(pct_dist, 1, False)} %** del distrito de Chichas ({num(dist_ha, 0, False)} ha según los límites GADM 4.1).
- **0** focos dentro del área quemada entre 2012 y 2025.

![Focos S-NPP por año en el área quemada de Chichas](outputs/recurrencia_chichas.png)

Entre 2012 y 2025, con entre {dias_min} y {dias_max} días de registro al año, el área que ardió en 2026
no registró **ni un solo foco**. En el anillo de 1 km hubo {anillo_md}. En los ocho días de registro de
octubre de 2026 hubo {r26.focos_poligono} focos dentro y {r26.focos_poligono_mas_1km} contando el anillo.

**Queda descartada una quema de manejo recurrente**: una zona de quema habitual aparece en el registro
año tras año, y esta no aparece nunca. La salvedad es de escala: una quema muy pequeña o muy rápida
puede ocurrir entre dos pasadas del satélite sin dejar foco.

El {num(pct_noche_ch, 1, False)} % de los focos de Chichas fue nocturno: la {ORDINAL[rango_noche]} firma más
nocturna de los veinte, en un país donde el {num(nac['% focos diurnos'], 1, False)} % fue diurno.

Tablas: `outputs/recurrencia_chichas.csv`, `outputs/recurrencia_noche_chichas.csv`,
`outputs/severidad_chichas.csv`, `outputs/poligono_quemado_chichas.geojson`.

## 4. Reto C: qué tipo de suelo ardió

| Cobertura (WorldCover 2021) | Hectáreas | % de lo quemado |
|---|---:|---:|
{cob_md}
| **Total** | **{num(cob.hectareas.sum(), 1, False)}** | 100 % |

**Cero hectáreas de cultivo y una décima de bosque.** El daño es pérdida de forraje y el afectado es la
ganadería extensiva. Con recurrencia nula, además, no es forraje que se queme en un ciclo de manejo.

Tabla: `outputs/cobertura_quemada_chichas_detalle.csv`.

## 5. Tres hipótesis que cayeron

![Severidad de los cuatro incendios medidos](outputs/top20_severidad.png)

| Incendio | Región | Cobertura | Quemado (ha) | Severidad baja | Moderada o más | Medida vs envolvente |
|---|---|---|---:|---:|---:|---:|
{med_md}

**a) "En pastizal la severidad sale baja y en bosque alta": no se sostiene.** Los pastizales van del
{num(pasto.pct_moderada_o_mas.min(), 1, False)} % al {num(pasto.pct_moderada_o_mas.max(), 1, False)} % de severidad moderada o superior, y el único bosque medible,
{nombre(bosque.distrito)}, cae dentro de ese rango con {num(bosque.pct_moderada_o_mas, 1, False)} %. Chichas es el atípico. Con n = {n_med} no se
puede concluir que la escala de Key y Benson esté mal calibrada para el pastizal andino, y no
encontramos ningún estudio de dNBR con validación de campo en puna o páramo: ese vacío es en sí mismo
un hallazgo.

**b) "Los focos sobrestiman de forma sistemática": no.** {num(dif['Iparia'], 1, False)} % en Iparía,
{num(dif['Chichas'], 1, False)} % en Chichas, {num(dif['Curahuasi'], 1, False)} % en Curahuasi y +{num(dif['SanCristobal'], 1, False)} % en San Cristóbal. Tres sobrestiman y uno
subestima, en un rango demasiado amplio para un factor de corrección. Lo que queda en pie es que contar
focos no mide hectáreas.

![Envolvente frente a área medida](outputs/top20_envolvente_vs_medida.png)

**c) "Las nubes castigan sobre todo a la Amazonía": no** (Fisher, p = {num(p_fisher, 2, False)}).

| Región | Incendios | Medidos | % medidos | Nubes | Sin pasada | Prefiltro |
|---|---:|---:|---:|---:|---:|---:|
{reg_md}

Tablas: `outputs/top20_medidos_resumen.csv`, `outputs/top20_pruebas.csv`.

## 6. Robustez

![Tornado de decisiones](outputs/tornado_chichas.png)

| Decisión | Mínimo (ha) | Máximo (ha) | Recorrido (ha) |
|---|---:|---:|---:|
{tor_md}

El umbral solo mueve {num(umbral_r / otros_r, 1, False)} veces más que las otras tres decisiones juntas ({num(otros_r, 1, False)} ha).

![Hectáreas según el umbral](outputs/sensibilidad_umbral_chichas.png)

| Umbral dNBR | Hectáreas | % de la zona |
|---|---:|---:|
{sen_md}

La curva colapsa rápido porque los píxeles quemados se apiñan cerca del umbral. Con 0,35, a Chichas le
queda el {num(100 * ratio035['Chichas'], 0, False)} % del área medida con 0,10; a Iparía, el {num(100 * ratio035['Iparia'], 0, False)} %.

> **Más rigor aparente, menos señal.** Endurecer la máscara de nubes *reduce* el área en
> {num(mask_quita, 1, False)} ha, pero no porque quite nubes: la capa SCL de Sentinel-2 clasifica
> {num(diag['quemado base marcado SCL 2 (zona oscura) en la imagen posterior'], 1, False)} ha de la propia cicatriz como "zona oscura" y
> {num(diag['quemado base marcado SCL 7 (sin clasificar) en la imagen posterior'], 1, False)} ha como "sin clasificar", y la máscara estricta las descarta.

Tablas: `outputs/tornado_chichas.csv`, `outputs/robustez_chichas.csv`, `outputs/robustez_diagnostico.csv`,
`outputs/sensibilidad_umbral_chichas.csv`.

## 7. Validación contra MCD64A1

MCD64A1 aún no existe para octubre de 2026, así que se validó el método en incendios de 2024 con una
regla fijada antes de ver resultados (los 3 primeros medibles por número de focos; como robustez, los
21 candidatos medibles).

![Validación contra MCD64A1](outputs/validacion_mcd64a1.png)

| Muestra | n | Razón mediana (nuestro / MCD64A1) | Rango | Chichas corregida (ha) |
|---|---:|---:|---:|---:|
{val_md}

**La cifra principal sigue siendo {num(ch_ha, 0, False)} ha**; las corregidas son alternativas: la validación es casi
toda bosque amazónico y el caso es pastizal andino; MCD64A1 usa píxeles de 500 m y es otra estimación
satelital, no un dato de campo; y varios de los {int(v21.n)} candidatos se solapan y no son independientes.

Tablas: `outputs/validacion_resumen.csv`, `outputs/validacion_mcd64a1.csv`, `outputs/validacion_candidatos.csv`.

## 8. Concentración y MAUP

![Curvas de Lorenz](outputs/lorenz_maup.png)

| Partición | Unidades con focos | Gini (solo con focos) | Gini (todas) |
|---|---:|---:|---:|
{gini_md}

El Gini va de {num(g_min, 3, False)} a {num(g_max, 3, False)} según la unidad y según si se cuentan las unidades sin fuego.
Cualquier índice de concentración que no declare su unidad no significa nada; lo robusto es que la
distribución es muy desigual en las cuatro particiones.

Tablas: `outputs/gini_maup.csv`, `outputs/lorenz_maup.csv`.

## 9. Implicaciones

- No se puede construir un indicador nacional de área quemada en tiempo casi real para el Perú en
  octubre: con {n_med} de {N}, lo que se reporta es una muestra sesgada.
- Las hectáreas no son comparables entre estudios si no declaran el umbral: en Chichas, solo el umbral
  las mueve {num(umbral_r, 1, False)} ha.
- Endurecer la máscara puede empeorar la medición.
- Contar focos no mide daño: la desviación frente al área medida va de {num(dif.min(), 1, False)} % a +{num(dif.max(), 1, False)} %.
- El gasto parece rendir más en prevención que en combate: solo {n_largos} de {num(n_inc, 0, False)} incendios superaron los 3 días.
- Un índice de concentración exige declarar su unidad espacial.

## 10. Qué haría falta para ponerle precio

- **Capacidad de carga** del pastizal quemado.
- **Tiempo de recuperación del forraje.**
- **Hogares y cabezas de ganado dependientes.**
- **Intencionalidad.** Esta sí se pudo acotar en parte: con recurrencia cero queda descartada la quema rutinaria.

La teledetección acota qué y cuánto se quemó, pero no determina si fue una pérdida.

## 11. Método

1. **Focos**: VIIRS de NASA FIRMS (Suomi-NPP, NOAA-20 y NOAA-21, CSV de 7 días descargado el 21-oct-2026),
   confianza nominal o alta, filtrados a Perú con GADM 4.1.
2. **Incendios**: dos focos son del mismo incendio si están a ≤ 1 km y ≤ 48 h entre sí.
3. **Par de imágenes**: Sentinel-2 L2A (Microsoft Planetary Computer), la de menos zona inválida antes y después.
4. **dNBR y severidad**: NBR = (B8A − B12)/(B8A + B12); dNBR = NBR antes − NBR después; clases de Key y Benson.
5. **Cobertura**: ESA WorldCover 2021 cruzado con los píxeles quemados.
6. **Contraste**: recurrencia con el archivo anual S-NPP 2012-2025, sensibilidad a cada decisión y validación contra MCD64A1.

| Imagen | Fecha | Tile | Nubes en la zona | Nubes en la escena |
|---|---|---|---:|---:|
| Antes | {antes.fecha} | {antes.tile} | {num(antes.nubes_zona_pct, 1, False)} % | {num(antes.nubes_escena_pct, 1, False)} % |
| Después | {despues.fecha} | {despues.tile} | {num(despues.nubes_zona_pct, 1, False)} % | {num(despues.nubes_escena_pct, 1, False)} % |

Decisiones declaradas: umbral dNBR ≥ 0,10; máscara SCL (sombra, nube media, nube alta, cirros, agua y
sin dato); zona = focos + 1 km = {num(zona_ch, 0, False)} ha en Chichas, rejilla de 20 m; recurrencia solo con S-NPP,
el único con registro continuo desde 2012.

## 12. Limitaciones y qué no se pudo hacer

- n = {n_med}: ninguna comparación entre incendios medidos tiene potencia estadística.
- Un foco no es un incendio ni una hectárea: es un píxel de 375 m donde un satélite detectó calor.
- La validación no cubre el bioma del caso: casi toda es bosque amazónico, contra un producto de 500 m.
- La firma diurna no prueba intencionalidad.
- El prefiltro descartó al menos un caso medible (Nueva Requena).
- Paracas se excluyó como fuente estática con el criterio escrito de la sección 1; con otro criterio el top 20 cambiaría.
- Una semana no es una temporada.
- WorldCover es de 2021: la cobertura pudo cambiar antes del incendio.
- Las cifras oficiales no se suman a estas: usan otros métodos y otras definiciones.

## Literatura

1. Key, C. H. y Benson, N. C. (2006). *Landscape Assessment (LA)*. FIREMON, USDA Forest Service,
   RMRS-GTR-164-CD. <https://research.fs.usda.gov/treesearch/24066>
2. Miller, J. D. y Thode, A. E. (2007). *Remote Sensing of Environment*, 109(1), 66-80.
   <https://doi.org/10.1016/j.rse.2006.12.006>
3. Roy, D. P., Boschetti, L. y Trigg, S. N. (2006). *IEEE Geoscience and Remote Sensing Letters*, 3(1),
   112-116. <https://doi.org/10.1109/LGRS.2005.858485>
4. Picotte, J. J. y Robertson, K. M. (2011). *International Journal of Wildland Fire*, 20(3), 453-464.
   <https://doi.org/10.1071/WF10013>
5. Cansler, C. A. y McKenzie, D. (2012). *Remote Sensing*, 4(2), 456-483. <https://doi.org/10.3390/rs4020456>
6. Lu, B., He, Y. y Tong, A. (2016). *International Journal of Wildland Fire*, 25(2), 147-157.
   <https://doi.org/10.1071/WF15098>

## Cómo reproducir

Requiere Python 3.14 (probado con 3.14.6) e internet (NASA FIRMS y Microsoft Planetary Computer, sin
clave). Desde la raíz del repositorio:

```bash
python -m venv .venv
.venv/Scripts/activate              # en Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python src/paso1_focos.py           # focos VIIRS → incendios (usa los CSV de 7 días versionados)
python src/paso2_4_medir.py         # Chichas: par Sentinel-2, dNBR, severidad, WorldCover y mapa
python src/paso5_sensibilidad.py    # hectáreas con 7 umbrales
python src/paso6_recurrencia.py     # archivo S-NPP 2012-2025 + polígono quemado
python src/paso7_riotambo.py        # verificación de Río Tambo
python src/paso8_top20.py           # mismo pipeline sobre los 20 incendios (excluye fuentes estáticas)
python src/paso9_analisis_top20.py  # éxito por región, severidad, envolvente, noche
python src/paso10_robustez.py       # tornado y Gini con tres unidades
python src/paso11_recurrencia_noche.py
python src/paso12_validacion.py     # validación contra MCD64A1
python src/paso13_nacional.py       # comportamiento nacional, mapa nacional, Lorenz
python src/construir_pagina.py      # genera index.html y README.md desde outputs/
```

Los CSV de 7 días de FIRMS descargados el 21-oct-2026 están versionados en `data/raw/`, así que el
paso 1 reproduce exactamente los mismos focos e identificadores de incendio. El resto de descargas se
guarda en `data/raw/` y `data/cache/` (no versionados) y no se repite si ya existe. Los pasos 8 y 12
corren en paralelo y tardan unos 2 y 5 minutos.

Herramienta independiente con datos públicos; no reemplaza al COEN, INDECI, SERFOR ni SERNANP.
Ventana analizada: 14-21 de octubre de 2026.
"""


if __name__ == "__main__":
    Path("index.html").write_text(html(), encoding="utf-8")
    Path("README.md").write_text(readme(), encoding="utf-8")
    print("index.html y README.md generados")
