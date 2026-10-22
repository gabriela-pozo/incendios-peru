"""Paso 10: robustez.
a) MAUP: Gini de concentración de focos con distrito, provincia y grilla de 10 x 10 km.
b) Sensibilidad multiparamétrica de Chichas: umbral, par de imágenes, máscara SCL y zona.
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from paso1_focos import cargar_distritos
from paso2_4_medir import OUT, NUBES, SIN_DATO, AGUA
from medicion import zona_puntos, buscar_par, medir_par, UMBRALES

EQUIAREA = 6933   # EASE-Grid 2.0: celdas de igual área en todo el Perú
CELDA = 10_000
MASCARAS = {"permisiva": [8, 9] + SIN_DATO,                         # solo nube media/alta
            "usada": NUBES + SIN_DATO + [AGUA],                      # sombra, nubes, cirros, agua
            "estricta": NUBES + SIN_DATO + [AGUA, 2, 7, 11]}         # + zonas oscuras, sin clasificar, nieve


def gini(x):
    x = np.sort(np.asarray(x, float)); n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


def grilla(peru, desfase=0):
    minx, miny, maxx, maxy = peru.total_bounds
    xs = np.arange(np.floor(minx / CELDA) * CELDA - desfase, maxx + CELDA, CELDA)
    ys = np.arange(np.floor(miny / CELDA) * CELDA - desfase, maxy + CELDA, CELDA)
    celdas = gpd.GeoDataFrame(geometry=[box(x, y, x + CELDA, y + CELDA) for x in xs for y in ys], crs=EQUIAREA)
    return celdas[celdas.intersects(peru.union_all())].reset_index(drop=True)


def maup():
    f = pd.read_csv(OUT / "focos_peru.csv")
    dist = cargar_distritos()
    filas = []
    for unidad, claves in [("distrito", ["departamento", "provincia", "distrito"]),
                           ("provincia", ["departamento", "provincia"])]:
        con = f.groupby(claves).size()
        todas = dist.groupby(claves).size().rename("u").to_frame().join(con.rename("n")).fillna(0).n
        filas.append({"unidad": unidad, "unidades_totales": len(todas), "unidades_con_focos": len(con),
                      "gini_solo_con_focos": gini(con), "gini_todas_las_unidades": gini(todas)})
    pts = gpd.GeoDataFrame(f, geometry=gpd.points_from_xy(f.longitude, f.latitude), crs=4326).to_crs(EQUIAREA)
    peru = dist.to_crs(EQUIAREA)
    for desfase, nombre in [(0, "grilla 10 x 10 km"), (CELDA // 2, "grilla 10 x 10 km desplazada 5 km")]:
        g = grilla(peru, desfase)
        n = gpd.sjoin(pts, g, predicate="within").groupby("index_right").size()
        todas = n.reindex(g.index, fill_value=0)
        filas.append({"unidad": nombre, "unidades_totales": len(g), "unidades_con_focos": len(n),
                      "gini_solo_con_focos": gini(n), "gini_todas_las_unidades": gini(todas)})
    t = pd.DataFrame(filas).round(3)
    t.to_csv(OUT / "gini_maup.csv", index=False)
    print(t.to_string(index=False))


def sensibilidad():
    f = pd.read_csv(OUT / "focos_peru.csv", parse_dates=["fecha_utc"])
    g = f[f.incendio == 1052]
    pts = gpd.GeoDataFrame(g, geometry=gpd.points_from_xy(g.longitude, g.latitude), crs=4326)
    aoi, rejilla, dentro = zona_puntos(pts, 1000)
    antes, despues = buscar_par(pts, aoi, rejilla, dentro, "2026-10-21")
    orden = lambda df: df.sort_values(["invalido_zona_pct", "fecha"], ascending=[True, False])
    antes, despues = orden(antes), orden(despues)
    a, d = antes.iloc[0], despues.iloc[0]
    filas = []

    def caso(decision, opcion, a_, d_, rej, den, aoi_, mascara="usada", umbral=0.10, base=False):
        r, _, _ = medir_par(a_["item"], d_["item"], rej, den, excluir=MASCARAS[mascara], umbral=umbral)
        filas.append({"decision": decision, "opcion": opcion, "base": base, "area_quemada_ha": r["area_quemada_ha"],
                      "zona_ha": r["zona_ha"], "sin_dato_ha": r["sin_dato_ha"],
                      "antes": f"{a_.fecha} {a_.tile} ({a_.invalido_zona_pct}% inválido)",
                      "despues": f"{d_.fecha} {d_.tile} ({d_.invalido_zona_pct}% inválido)"})
        print(f"{decision:<10} {opcion:<34} {r['area_quemada_ha']:>8.1f} ha", flush=True)

    caso("base", "0,10 · mejor par · SCL usada · 1 km", a, d, rejilla, dentro, aoi, base=True)
    base_r, _, _ = medir_par(a["item"], d["item"], rejilla, dentro)
    for u in UMBRALES:
        if u != 0.10:
            filas.append({"decision": "umbral", "opcion": f"dNBR ≥ {u:.2f}".replace(".", ","), "base": False,
                          "area_quemada_ha": base_r[f"ha_umbral_{u:.2f}"], "zona_ha": base_r["zona_ha"],
                          "sin_dato_ha": base_r["sin_dato_ha"]})
    caso("par", f"2.ª mejor posterior: {despues.iloc[1].fecha} ({despues.iloc[1].invalido_zona_pct}% inv.)",
         a, despues.iloc[1], rejilla, dentro, aoi)
    caso("par", f"2.ª mejor previa: {antes.iloc[1].fecha} ({antes.iloc[1].invalido_zona_pct}% inv.)",
         antes.iloc[1], d, rejilla, dentro, aoi)
    for m in ["permisiva", "estricta"]:
        caso("mascara", f"SCL {m}", a, d, rejilla, dentro, aoi, mascara=m)
    for b in [500, 2000]:
        aoi_b, rej_b, den_b = zona_puntos(pts, b)
        caso("zona", f"focos + {b} m" if b < 1000 else f"focos + {b // 1000} km", a, d, rej_b, den_b, aoi_b)
    # diagnóstico: qué explica las diferencias de máscara y de par
    from paso2_4_medir import leer
    _, dnbr, val = medir_par(a["item"], d["item"], rejilla, dentro)
    q = val & (dnbr >= 0.10)
    scl_d = leer(d["item"].assets["SCL"].href, rejilla)
    _, dnbr2, val2 = medir_par(a["item"], despues.iloc[1]["item"], rejilla, dentro)
    comun = val & val2
    diag = pd.DataFrame([
        {"diagnostico": "quemado base marcado SCL 2 (zona oscura) en la imagen posterior", "ha": (q & (scl_d == 2)).sum() * 0.04},
        {"diagnostico": "quemado base marcado SCL 7 (sin clasificar) en la imagen posterior", "ha": (q & (scl_d == 7)).sum() * 0.04},
        {"diagnostico": "área válida en ambas imágenes posteriores", "ha": comun.sum() * 0.04},
        {"diagnostico": "quemado en esa área común, mejor posterior", "ha": (comun & (dnbr >= 0.10)).sum() * 0.04},
        {"diagnostico": "quemado en esa área común, 2.ª mejor posterior", "ha": (comun & (dnbr2 >= 0.10)).sum() * 0.04},
    ]).round(1)
    diag.to_csv(OUT / "robustez_diagnostico.csv", index=False)
    print(diag.to_string(index=False))
    t = pd.DataFrame(filas)
    base_ha = t[t.base].area_quemada_ha.iloc[0]
    t["diferencia_ha"] = (t.area_quemada_ha - base_ha).round(1)
    t["diferencia_pct"] = (100 * t.diferencia_ha / base_ha).round(1)
    t.to_csv(OUT / "robustez_chichas.csv", index=False)

    # tornado: rango (mín-máx) que mueve cada decisión, con la base al centro
    nombres = {"umbral": "Umbral de dNBR (0,05–0,35)", "zona": "Zona (500 m – 2 km)",
               "par": "Par de imágenes (2.ª mejor)", "mascara": "Máscara SCL (permisiva – estricta)"}
    rangos = []
    for dec, grp in t[~t.base].groupby("decision"):
        vals = list(grp.area_quemada_ha) + [base_ha]
        rangos.append((nombres[dec], min(vals), max(vals)))
    rangos.sort(key=lambda r: r[2] - r[1])
    pd.DataFrame(rangos, columns=["decision", "min_ha", "max_ha"]).assign(
        rango_ha=lambda x: (x.max_ha - x.min_ha).round(1)).to_csv(OUT / "tornado_chichas.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 3.4), dpi=150)
    for i, (nom, lo, hi) in enumerate(rangos):
        ax.barh(i, base_ha - lo, left=lo, color="#a85c32", height=0.55)
        ax.barh(i, hi - base_ha, left=base_ha, color="#0d6e5d", height=0.55)
        ax.text(lo - 25, i, f"{lo:,.0f}".replace(",", " "), va="center", ha="right", fontsize=8)
        ax.text(hi + 25, i, f"{hi:,.0f}".replace(",", " "), va="center", ha="left", fontsize=8)
    ax.axvline(base_ha, color="#14201d", lw=1)
    ax.set_yticks(range(len(rangos))); ax.set_yticklabels([r[0] for r in rangos], fontsize=9)
    ax.set_xlim(-250, 2400)
    ax.set_xlabel(f"Hectáreas quemadas en Chichas (base: {base_ha:,.1f} ha)".replace(",", " ").replace(".", ","))
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_title("Cuánto mueve cada decisión el área quemada", fontsize=10)
    fig.tight_layout(); fig.savefig(OUT / "tornado_chichas.png"); plt.close(fig)
    print(pd.DataFrame(rangos, columns=["decision", "min_ha", "max_ha"]).to_string(index=False))


if __name__ == "__main__":
    maup()
    sensibilidad()
