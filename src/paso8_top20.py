"""Paso 8: el mismo pipeline de Chichas sobre los 20 incendios con más focos (n=1 -> n=20).

Criterio de exclusión, fijado y aplicado a todos los candidatos por igual: un grupo de focos
no es un incendio si más de la mitad de las detecciones S-NPP 2012-2025 dentro de su zona
(focos + 1 km) son de tipo 2 en FIRMS ("otra fuente estática terrestre": plantas industriales,
quemadores de gas). Requiere el archivo anual que descarga el paso 6.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

from paso2_4_medir import OUT, cat
from medicion import medir_incendio

CACHE = Path("data/cache/top20"); CACHE.mkdir(parents=True, exist_ok=True)
FIN_DESPUES = "2026-10-21"   # fecha de descarga: no hay imágenes posteriores a ese día
N = 20
N_REVISAR = 40               # candidatos que se revisan con el criterio de fuente estática
ARCHIVO = Path("data/raw/firms_archivo")
# Región declarada: Andes si el centroide está a >= 1500 m; por debajo, Costa si el
# departamento no tiene selva, si no Amazonía.
SIN_SELVA = {"Ica", "Lima", "Piura", "Tumbes", "Lambayeque", "LaLibertad", "La Libertad", "Áncash", "Arequipa",
             "Moquegua", "Tacna"}


def altitud(lon, lat):
    it = next(cat.search(collections=["cop-dem-glo-30"], intersects={"type": "Point", "coordinates": [lon, lat]}).items())
    with rasterio.open(it.assets["data"].href) as src:
        return float(next(src.sample([(lon, lat)]))[0])


def region(elev, depto):
    if elev >= 1500:
        return "Andes"
    return "Costa" if depto in SIN_SELVA else "Amazonía"


def uno(inc, focos):
    ruta = CACHE / f"{inc.incendio}.json"
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    g = focos[focos.incendio == inc.incendio]
    pts = gpd.GeoDataFrame(g, geometry=gpd.points_from_xy(g.longitude, g.latitude), crs=4326)
    fila = {"incendio": int(inc.incendio), "distrito": inc.distrito, "provincia": inc.provincia,
            "departamento": inc.departamento, "focos": int(inc.focos), "envolvente_ha": inc.envolvente_ha,
            "pct_focos_noche": round(100 * (g.daynight == "N").mean(), 1),
            "frp_total_MW": inc.frp_total_MW, "lon": inc.lon, "lat": inc.lat}
    fila["altitud_m"] = round(altitud(inc.lon, inc.lat))
    fila["region"] = region(fila["altitud_m"], inc.departamento)
    fila |= medir_incendio(pts, FIN_DESPUES)
    ruta.write_text(json.dumps(fila, default=str, ensure_ascii=False), encoding="utf-8")
    return fila


def fuentes_estaticas(inc, focos):
    arch = pd.concat([pd.read_csv(ARCHIVO / f"viirs-snpp_{y}_Peru.csv", usecols=["latitude", "longitude", "type", "acq_date"])
                      for y in range(2012, 2026)])
    a = gpd.GeoDataFrame(arch, geometry=gpd.points_from_xy(arch.longitude, arch.latitude), crs=4326).to_crs(32718)
    filas = []
    for r in inc.itertuples():
        g = focos[focos.incendio == r.incendio]
        zona = gpd.GeoSeries(gpd.points_from_xy(g.longitude, g.latitude), crs=4326).to_crs(32718)             .union_all().convex_hull.buffer(1000)
        h = a[a.within(zona)]
        n2 = int((h["type"] == 2).sum())
        filas.append({"incendio": r.incendio, "distrito": r.distrito, "focos": r.focos,
                      "detecciones_2012_2025": len(h), "dias_con_deteccion": h.acq_date.nunique(),
                      "detecciones_tipo2": n2, "pct_tipo2": round(100 * n2 / len(h), 1) if len(h) else 0.0})
    t = pd.DataFrame(filas)
    t["excluido_fuente_estatica"] = t.pct_tipo2 > 50
    t.to_csv(OUT / "fuentes_estaticas_candidatos.csv", index=False)
    print(t[t.excluido_fuente_estatica].to_string(index=False))
    return set(t[t.excluido_fuente_estatica].incendio)


def main():
    t = time.time()
    focos = pd.read_csv(OUT / "focos_peru.csv", parse_dates=["fecha_utc"])
    cand = pd.read_csv(OUT / "incendios_peru.csv").head(N_REVISAR)
    excluir = fuentes_estaticas(cand, focos)
    inc = cand[~cand.incendio.isin(excluir)].head(N)
    filas = []
    with ThreadPoolExecutor(6) as ex:
        futuros = {ex.submit(uno, r, focos): r.incendio for r in inc.itertuples()}
        for fu in as_completed(futuros):
            f = fu.result()
            filas.append(f)
            print(f"[{time.time() - t:5.0f}s] {f['distrito']:<16} {'MEDIDO' if f['medible'] else 'NO: ' + f['motivo']}"
                  + (f"  {f['area_quemada_ha']} ha" if f["medible"] else ""), flush=True)
    df = pd.DataFrame(filas).set_index("incendio").loc[inc.incendio].reset_index()
    df["rango_focos"] = range(1, len(df) + 1)
    df["area_sobre_envolvente"] = (df.area_quemada_ha / df.envolvente_ha).round(3)
    df.to_csv(OUT / "medicion_top20.csv", index=False)
    print(f"\n{df.medible.sum()} de {len(df)} medibles  |  {time.time() - t:.0f} s")


if __name__ == "__main__":
    main()
