"""Paso 1: focos VIIRS en Perú agrupados en incendios (<=1 km y <=48 h)."""
from pathlib import Path
import io, zipfile, urllib.request

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import planetary_computer
import pystac_client
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

RAW = Path("data/raw"); RAW.mkdir(parents=True, exist_ok=True)
OUT = Path("outputs"); OUT.mkdir(exist_ok=True)

FIRMS = "https://firms.modaps.eosdis.nasa.gov/data/active_fire"
CSVS = {
    "SNPP": f"{FIRMS}/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_South_America_7d.csv",
    "NOAA20": f"{FIRMS}/noaa-20-viirs-c2/csv/J1_VIIRS_C2_South_America_7d.csv",
    "NOAA21": f"{FIRMS}/noaa-21-viirs-c2/csv/J2_VIIRS_C2_South_America_7d.csv",
}
GADM = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_PER_3.json.zip"
WORLDCOVER = {10: "Bosque", 20: "Matorral", 30: "Pastizal", 40: "Cultivo",
              50: "Urbano", 60: "Suelo desnudo", 70: "Nieve/hielo", 80: "Agua",
              90: "Humedal herbáceo", 95: "Manglar", 100: "Musgo/liquen"}


def descargar(url, destino):
    if not destino.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "incendios-peru"})
        destino.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    return destino


def cargar_focos():
    partes = []
    for sat, url in CSVS.items():
        df = pd.read_csv(descargar(url, RAW / f"firms_{sat}_SA_7d.csv"))
        df["sat"] = sat
        partes.append(df)
    df = pd.concat(partes, ignore_index=True)
    df["confidence"] = df["confidence"].astype(str).str.lower().str[0]
    df = df[df["confidence"].isin(["n", "h"])]
    hhmm = df["acq_time"].astype(int).astype(str).str.zfill(4)
    df["fecha_utc"] = pd.to_datetime(df["acq_date"] + " " + hhmm, format="%Y-%m-%d %H%M")
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs=4326)


def cargar_distritos():
    z = descargar(GADM, RAW / "gadm41_PER_3.json.zip")
    with zipfile.ZipFile(z) as zf:
        nombre = zf.namelist()[0]
        dist = gpd.read_file(io.BytesIO(zf.read(nombre)))
    return dist[["NAME_1", "NAME_2", "NAME_3", "geometry"]].rename(
        columns={"NAME_1": "departamento", "NAME_2": "provincia", "NAME_3": "distrito"})


def agrupar(focos, dist_m=1000, horas=48):
    xy = np.c_[focos.to_crs(32718).geometry.x, focos.to_crs(32718).geometry.y]
    pares = cKDTree(xy).query_pairs(dist_m, output_type="ndarray")
    t = focos["fecha_utc"].values.astype("datetime64[s]").astype(np.int64)
    pares = pares[np.abs(t[pares[:, 0]] - t[pares[:, 1]]) <= horas * 3600]
    n = len(focos)
    g = coo_matrix((np.ones(len(pares)), (pares[:, 0], pares[:, 1])), shape=(n, n))
    _, etiquetas = connected_components(g, directed=False)
    return etiquetas


def cobertura_dominante(puntos):
    cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1",
                                    modifier=planetary_computer.sign_inplace)
    minx, miny, maxx, maxy = puntos.total_bounds
    items = list(cat.search(collections=["esa-worldcover"], bbox=[minx, miny, maxx, maxy],
                            query={"esa_worldcover:product_version": {"eq": "2.0.0"}}).items())
    valores = []
    for it in items:
        with rasterio.open(it.assets["map"].href) as src:
            l, b, r, t = src.bounds
            dentro = puntos.cx[l:r, b:t]
            valores += [v[0] for v in src.sample(zip(dentro.geometry.x, dentro.geometry.y))]
    if not valores:
        return "sin dato", 0.0
    s = pd.Series(valores).map(WORLDCOVER).value_counts(normalize=True)
    return s.index[0], round(100 * s.iloc[0], 1)


def main():
    focos = cargar_focos()
    distritos = cargar_distritos()
    focos = gpd.sjoin(focos, distritos, how="inner", predicate="within").drop(columns="index_right")
    focos = focos.reset_index(drop=True)
    print(f"Focos en Perú (confianza nominal/alta): {len(focos)}  "
          f"[{focos.fecha_utc.min():%Y-%m-%d} a {focos.fecha_utc.max():%Y-%m-%d} UTC]")

    focos["incendio"] = agrupar(focos)
    filas = []
    for inc, g in focos.groupby("incendio"):
        casco = g.to_crs(32718).union_all().convex_hull
        top = g.groupby(["departamento", "provincia", "distrito"]).size().idxmax()
        filas.append({"incendio": inc, "focos": len(g), "departamento": top[0],
                      "provincia": top[1], "distrito": top[2],
                      "inicio_utc": g.fecha_utc.min(), "fin_utc": g.fecha_utc.max(),
                      "envolvente_ha": round(casco.area / 1e4, 0),
                      "frp_total_MW": round(g.frp.sum(), 1),
                      "lon": round(g.longitude.mean(), 4), "lat": round(g.latitude.mean(), 4)})
    inc = pd.DataFrame(filas).sort_values("focos", ascending=False)
    print(f"Incendios (grupos): {len(inc)}  |  con 1 solo foco: {(inc.focos == 1).sum()}")

    top5 = inc.head(5).copy()
    cob = [cobertura_dominante(focos[focos.incendio == i]) for i in top5.incendio]
    top5["cobertura_dominante"] = [c[0] for c in cob]
    top5["pct_focos_en_cobertura"] = [c[1] for c in cob]

    focos.drop(columns="geometry").to_csv(OUT / "focos_peru.csv", index=False)
    inc.to_csv(OUT / "incendios_peru.csv", index=False)
    top5.to_csv(OUT / "top5_incendios.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(top5.drop(columns=["frp_total_MW"]).to_string(index=False))


if __name__ == "__main__":
    main()
