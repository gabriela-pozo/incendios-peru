"""Paso 12: validación del MÉTODO contra MCD64A1 (MODIS, área quemada mensual, 500 m).

MCD64A1 de octubre de 2026 aún no existe, así que se valida el método en incendios de 2024-2025.
Regla de selección fijada antes de ver resultados: grupos de focos S-NPP (confianza nominal/alta,
tipo 0 = vegetación) de junio a noviembre, ordenados por número de focos; se corre el pipeline en
ese orden y se toman los 3 primeros medibles. Ambas cifras se comparan en la misma zona
(focos + 1 km) y sobre los mismos píxeles válidos (sin nubes en ninguna de las dos imágenes).
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import mapping

from paso1_focos import agrupar
from paso2_4_medir import OUT, CRS, cat, leer
from medicion import zona_puntos, buscar_par, motivo, medir_par, fila_imagen, HA_PX
from paso2_4_medir import mejor

ARCHIVO = Path("data/raw/firms_archivo")
CACHE = Path("data/cache/validacion"); CACHE.mkdir(parents=True, exist_ok=True)
N_CASOS, N_CANDIDATOS, DIAS_DESPUES = 3, 24, 20


def grupos():
    partes = []
    for y in (2024, 2025):
        d = pd.read_csv(ARCHIVO / f"viirs-snpp_{y}_Peru.csv")
        d = d[d.confidence.astype(str).str[0].isin(["n", "h"]) & (d.type == 0)]
        d["fecha_utc"] = pd.to_datetime(d.acq_date + " " + d.acq_time.astype(str).str.zfill(4), format="%Y-%m-%d %H%M")
        d = d[d.fecha_utc.dt.month.between(6, 11)].reset_index(drop=True)
        g = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.longitude, d.latitude), crs=4326)
        g["grupo"] = [f"{y}-{e}" for e in agrupar(g)]
        partes.append(g)
    g = pd.concat(partes, ignore_index=True)
    top = g.grupo.value_counts().head(N_CANDIDATOS).index
    return g, list(top)


def mcd64a1(aoi, rejilla, desde, hasta):
    """Máscara de píxeles con fecha de quema MCD64A1 entre desde y hasta (remuestreo vecino a 20 m)."""
    geom = mapping(gpd.GeoSeries([aoi], crs=CRS).to_crs(4326).iloc[0])
    tr, w, h = rejilla
    quem = np.zeros((h, w), bool)
    items = list(cat.search(collections=["modis-64A1-061"], intersects=geom,
                            datetime=f"{desde:%Y-%m-01}/{hasta:%Y-%m-%d}").items())
    for it in items:
        bd = leer(it.assets["Burn_Date"].href, rejilla).astype(int)
        anio = pd.Timestamp(it.properties["start_datetime"]).year
        fecha = np.datetime64(f"{anio}-01-01") + (np.clip(bd, 1, 366) - 1).astype("timedelta64[D]")
        quem |= (bd > 0) & (fecha >= np.datetime64(desde.date())) & (fecha <= np.datetime64(hasta.date()))
    return quem, len(items)


def uno(gid, g):
    ruta = CACHE / f"{gid}.json"
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    pts = g[g.grupo == gid]
    aoi, rejilla, dentro = zona_puntos(pts)
    fin = (pts.fecha_utc.max() + pd.Timedelta(days=DIAS_DESPUES)).date()
    antes, despues = buscar_par(pts, aoi, rejilla, dentro, fin)
    a, d = mejor(antes), mejor(despues)
    m = motivo(a, d)
    fila = {"grupo": gid, "focos": len(pts), "inicio_utc": str(pts.fecha_utc.min()), "fin_utc": str(pts.fecha_utc.max()),
            "lon": round(pts.longitude.mean(), 4), "lat": round(pts.latitude.mean(), 4),
            "envolvente_ha": round(pts.to_crs(CRS).union_all().convex_hull.area / 1e4, 0),
            "medible": m is None, "motivo": m or ""}
    fila |= {k: str(v) for k, v in (fila_imagen("antes", a) | fila_imagen("despues", d)).items()}
    if m is None:
        r, dnbr, valido = medir_par(a["item"], d["item"], rejilla, dentro, aoi=aoi)
        quem, n_items = mcd64a1(aoi, rejilla, pd.Timestamp(a.fecha), pd.Timestamp(d.fecha))
        fila |= {k: r[k] for k in ["zona_ha", "sin_dato_ha", "area_quemada_ha", "pct_sev_baja", "cobertura_dominante",
                                   "pct_cob_bosque", "pct_cob_pastizal", "pct_cob_matorral"]}
        fila["mcd64a1_items"] = n_items
        fila["mcd64a1_ha"] = round((quem & valido).sum() * HA_PX, 1)
        ours = valido & (dnbr >= 0.10)
        fila["ambos_ha"] = round((ours & quem).sum() * HA_PX, 1)
        fila["solo_nuestro_ha"] = round((ours & ~quem).sum() * HA_PX, 1)
        fila["solo_mcd64a1_ha"] = round((~ours & quem & valido).sum() * HA_PX, 1)
    ruta.write_text(json.dumps(fila, default=str, ensure_ascii=False), encoding="utf-8")
    return fila


def main():
    g, top = grupos()
    with ThreadPoolExecutor(6) as ex:
        filas = list(ex.map(lambda gid: uno(gid, g), top))
    todos = pd.DataFrame(filas)
    todos["rango"] = range(1, len(todos) + 1)
    todos.to_csv(OUT / "validacion_candidatos.csv", index=False)
    print(todos[["rango", "grupo", "focos", "inicio_utc", "medible", "motivo"]].to_string(index=False))
    v = todos[todos.medible].head(N_CASOS).copy()
    v["razon_nuestro_mcd"] = (v.area_quemada_ha / v.mcd64a1_ha).round(3)
    v["diferencia_pct"] = (100 * (v.area_quemada_ha / v.mcd64a1_ha - 1)).round(1)
    v.to_csv(OUT / "validacion_mcd64a1.csv", index=False)
    print(v[["grupo", "lat", "lon", "antes_fecha", "despues_fecha", "cobertura_dominante", "area_quemada_ha",
             "mcd64a1_ha", "ambos_ha", "solo_nuestro_ha", "solo_mcd64a1_ha", "razon_nuestro_mcd"]].to_string(index=False))

    # Resumen: los 3 de la regla y, como robustez, todos los candidatos medibles (misma regla, sin elegir)
    med = todos[todos.medible].copy()
    med["razon_nuestro_mcd"] = (med.area_quemada_ha / med.mcd64a1_ha).round(3)
    chichas = 1689.5
    filas = []
    for nombre, x in [("3 casos (regla fijada)", v), (f"{len(med)} candidatos medibles", med),
                      ("solo pastizal dominante", med[med.cobertura_dominante == "pastizal"])]:
        r = x.razon_nuestro_mcd
        filas.append({"muestra": nombre, "n": len(x), "razon_mediana": r.median(), "razon_media": r.mean(),
                      "razon_min": r.min(), "razon_max": r.max(),
                      "razon_p25": r.quantile(0.25), "razon_p75": r.quantile(0.75),
                      "sesgo_mediano_pct": 100 * (r.median() - 1),
                      "chichas_corregida_ha": chichas / r.median()})
    res = pd.DataFrame(filas).round(3)
    res.to_csv(OUT / "validacion_resumen.csv", index=False)
    print(res.to_string(index=False))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.5, 6), dpi=150)
    lim = max(med.area_quemada_ha.max(), med.mcd64a1_ha.max()) * 1.08
    ax.plot([0, lim], [0, lim], color="#5c6b66", lw=1, ls="--")
    elegidos = med.grupo.isin(v.grupo)
    for sel, col, lab in [(~elegidos & (med.cobertura_dominante != "pastizal"), "#9aaba5", "Otros candidatos (bosque)"),
                          (med.cobertura_dominante == "pastizal", "#a85c32", "Pastizal dominante"),
                          (elegidos, "#0d6e5d", "Los 3 de la regla")]:
        ax.scatter(med[sel].mcd64a1_ha, med[sel].area_quemada_ha, s=55, color=col, edgecolor="white", lw=1.2,
                   label=lab, zorder=3)
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.set_xlabel("MCD64A1 (ha, misma zona y píxeles válidos)"); ax.set_ylabel("Nuestro método, dNBR ≥ 0,10 (ha)")
    ax.grid(color="#d9e0dc", lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    ax.set_title(f"Validación contra MCD64A1 — incendios de 2024 (n = {len(med)})", fontsize=10)
    fig.tight_layout(); fig.savefig(OUT / "validacion_mcd64a1.png"); plt.close(fig)


if __name__ == "__main__":
    main()
