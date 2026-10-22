"""Pasos 2-4: imágenes Sentinel-2 antes/después, dNBR, severidad, WorldCover y mapa."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
import planetary_computer
import pystac_client
from shapely.geometry import mapping
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

OUT = Path("outputs")
CRS, RES = 32718, 20
INCENDIOS = {"calleria": (173, "Callería (Coronel Portillo, Ucayali)"),
             "chichas": (1052, "Chichas (Condesuyos, Arequipa)"),
             "riotambo": (30, "Río Tambo (Satipo, Junín)")}
MAX_INVALIDO = 30  # % máximo de la zona tapada por nube/sombra/sin dato
NUBES = [3, 8, 9, 10]
SIN_DATO = [0, 1]
AGUA = 6
SEVERIDAD = [(-np.inf, 0.10, "Sin quemar"), (0.10, 0.27, "Baja"),
             (0.27, 0.44, "Moderada-baja"), (0.44, 0.66, "Moderada-alta"),
             (0.66, np.inf, "Alta")]
WORLDCOVER = {10: "Bosque", 20: "Matorral", 30: "Pastizal", 40: "Cultivo",
              50: "Urbano", 60: "Suelo desnudo", 70: "Nieve/hielo", 80: "Agua",
              90: "Humedal herbáceo", 95: "Manglar", 100: "Musgo/liquen"}
GRUPO = {"Bosque": "Bosque", "Pastizal": "Pastizal", "Cultivo": "Cultivo"}

cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1",
                                modifier=planetary_computer.sign_inplace)


def zona(incendio_id):
    f = pd.read_csv(OUT / "focos_peru.csv", parse_dates=["fecha_utc"])
    f = f[f.incendio == incendio_id]
    pts = gpd.GeoDataFrame(f, geometry=gpd.points_from_xy(f.longitude, f.latitude), crs=4326)
    aoi = pts.to_crs(CRS).union_all().convex_hull.buffer(1000)
    minx, miny, maxx, maxy = aoi.bounds
    minx, miny = np.floor(minx / RES) * RES, np.floor(miny / RES) * RES
    maxx, maxy = np.ceil(maxx / RES) * RES, np.ceil(maxy / RES) * RES
    w, h = int((maxx - minx) / RES), int((maxy - miny) / RES)
    tr = from_origin(minx, maxy, RES, RES)
    dentro = ~geometry_mask([aoi], (h, w), tr)
    return pts, aoi, (tr, w, h), dentro


def leer(href, rejilla, remuestreo=Resampling.nearest):
    tr, w, h = rejilla
    with rasterio.open(href) as src, WarpedVRT(src, crs=CRS, transform=tr, width=w, height=h,
                                                resampling=remuestreo) as vrt:
        return vrt.read(1)


def candidatas(aoi, desde, hasta, rejilla, dentro, max_items, max_nube_escena=80):
    geom = mapping(gpd.GeoSeries([aoi], crs=CRS).to_crs(4326).iloc[0])
    items = list(cat.search(collections=["sentinel-2-l2a"], intersects=geom,
                            datetime=f"{desde}/{hasta}",
                            query={"eo:cloud_cover": {"lt": max_nube_escena}}).items())
    items = sorted(items, key=lambda i: i.datetime, reverse=True)[:max_items]
    filas = []
    for it in items:
        scl = leer(it.assets["SCL"].href, rejilla)[dentro]
        filas.append({"item": it, "fecha": it.datetime.date(), "tile": it.properties.get("s2:mgrs_tile"),
                      "nubes_escena_pct": round(it.properties["eo:cloud_cover"], 1),
                      "nubes_zona_pct": round(100 * np.isin(scl, NUBES).mean(), 1),
                      "invalido_zona_pct": round(100 * np.isin(scl, NUBES + SIN_DATO).mean(), 1)})
    return pd.DataFrame(filas)


def mejor(df):
    if df.empty:
        return None
    return df.sort_values(["invalido_zona_pct", "fecha"], ascending=[True, False]).iloc[0]


def reflectancia(item, banda, rejilla):
    dn = leer(item.assets[banda].href, rejilla, Resampling.bilinear).astype("float32")
    off = 1000 if float(item.properties.get("s2:processing_baseline", "0")) >= 4 else 0
    r = (dn - off) / 10000
    r[dn == 0] = np.nan
    return r


def nbr(item, rejilla):
    nir, swir = reflectancia(item, "B8A", rejilla), reflectancia(item, "B12", rejilla)
    scl = leer(item.assets["SCL"].href, rejilla)
    valido = ~np.isin(scl, NUBES + SIN_DATO + [AGUA])
    return (nir - swir) / (nir + swir), valido, nir


def elegir_par(clave):
    inc_id, nombre = INCENDIOS[clave]
    pts, aoi, rejilla, dentro = zona(inc_id)
    t0, t1 = pts.fecha_utc.min(), pts.fecha_utc.max()
    antes = candidatas(aoi, (t0 - pd.Timedelta(days=60)).date(), t0.date(), rejilla, dentro, 10)
    despues = candidatas(aoi, (t1 + pd.Timedelta(days=1)).date(), "2026-10-21", rejilla, dentro, 10)
    for etiqueta, df in [("ANTES", antes), ("DESPUÉS", despues)]:
        print(f"\n{nombre} — candidatas {etiqueta}:")
        print(df.drop(columns="item").to_string(index=False) if not df.empty else "  (ninguna)")
    return inc_id, nombre, pts, aoi, rejilla, dentro, mejor(antes), mejor(despues), antes, despues


def usable(fila):
    return fila is not None and fila.invalido_zona_pct <= MAX_INVALIDO


def main():
    clave = "calleria"
    r = elegir_par(clave)
    a, d = r[6], r[7]
    if not (usable(a) and usable(d)):
        motivo = ("no hay imagen posterior" if d is None else
                  f"la mejor posterior tiene {d.invalido_zona_pct}% de la zona inválida" if not usable(d)
                  else "no hay imagen previa usable")
        print(f"\n>>> CAMBIO AUTOMÁTICO: Callería descartado ({motivo}; umbral {MAX_INVALIDO}%). Paso a Chichas.")
        clave = "chichas"
        r = elegir_par(clave)
    inc_id, nombre, pts, aoi, rejilla, dentro, a, d, antes, despues = r
    if a is None or d is None:
        sys.exit("Sin par de imágenes usable tampoco en Chichas.")
    print(f"\nPAR ELEGIDO — {nombre}"
          f"\n  ANTES:   {a.fecha} tile {a.tile}  nubes zona {a.nubes_zona_pct}%  inválido {a.invalido_zona_pct}%"
          f"\n  DESPUÉS: {d.fecha} tile {d.tile}  nubes zona {d.nubes_zona_pct}%  inválido {d.invalido_zona_pct}%")
    tabla = pd.concat([antes.assign(momento="antes"), despues.assign(momento="despues")])
    tabla["elegida"] = tabla["item"].map(lambda it: it.id in (a["item"].id, d["item"].id))
    tabla.drop(columns="item").to_csv(OUT / f"imagenes_{clave}.csv", index=False)

    # Paso 2: NBR, dNBR, severidad
    nbr_a, val_a, _ = nbr(a["item"], rejilla)
    nbr_d, val_d, nir_d = nbr(d["item"], rejilla)
    dnbr = nbr_a - nbr_d
    valido = dentro & val_a & val_d & np.isfinite(dnbr)
    ha_px = RES * RES / 1e4
    clase = np.full(dnbr.shape, -1, dtype=int)
    filas = []
    for k, (lo, hi, nom) in enumerate(SEVERIDAD):
        m = valido & (dnbr >= lo) & (dnbr < hi)
        clase[m] = k
        filas.append({"severidad": nom, "dnbr_min": lo, "dnbr_max": hi, "hectareas": round(m.sum() * ha_px, 1)})
    filas.append({"severidad": "Sin dato (nube/agua/sin imagen)", "dnbr_min": None, "dnbr_max": None,
                  "hectareas": round((dentro & ~valido).sum() * ha_px, 1)})
    sev = pd.DataFrame(filas)
    sev["pct_zona"] = (100 * sev.hectareas / (dentro.sum() * ha_px)).round(1)
    sev.to_csv(OUT / f"severidad_{clave}.csv", index=False)
    quemado = valido & (dnbr >= 0.10)
    print(f"\nZona analizada: {dentro.sum() * ha_px:.0f} ha  |  QUEMADO (dNBR>=0.10): {quemado.sum() * ha_px:.1f} ha")
    print(sev.to_string(index=False))

    # Paso 3: WorldCover
    geom = mapping(gpd.GeoSeries([aoi], crs=CRS).to_crs(4326).iloc[0])
    wc = np.zeros(dnbr.shape, dtype="uint8")
    for it in cat.search(collections=["esa-worldcover"], intersects=geom,
                         query={"esa_worldcover:product_version": {"eq": "2.0.0"}}).items():
        x = leer(it.assets["map"].href, rejilla)
        wc = np.where(wc == 0, x, wc)
    det = pd.Series(wc[quemado]).map(WORLDCOVER).fillna("Sin dato").value_counts()
    cob = pd.DataFrame({"clase_worldcover": det.index, "hectareas": (det.values * ha_px).round(1)})
    cob["grupo"] = cob.clase_worldcover.map(GRUPO).fillna("Otras")
    cob["pct"] = (100 * cob.hectareas / cob.hectareas.sum()).round(1)
    grp = cob.groupby("grupo")[["hectareas", "pct"]].sum() \
        .reindex(["Bosque", "Pastizal", "Cultivo", "Otras"]).fillna(0).reset_index()
    cob.to_csv(OUT / f"cobertura_quemada_{clave}_detalle.csv", index=False)
    grp.to_csv(OUT / f"cobertura_quemada_{clave}.csv", index=False)
    print("\nCobertura del área quemada (WorldCover 2021):")
    print(cob.to_string(index=False))
    print(grp.round(1).to_string(index=False))

    # Paso 4: mapa
    tr, w, h = rejilla
    ext = [tr.c / 1000, (tr.c + w * RES) / 1000, (tr.f - h * RES) / 1000, tr.f / 1000]
    colores = ["#fde725", "#fd8d3c", "#e31a1c", "#67000d"]
    fig, ax = plt.subplots(figsize=(10, 9), dpi=150)
    fondo = np.where(dentro, nir_d, np.nan)
    ax.imshow(fondo, cmap="Greys_r", extent=ext,
              vmin=np.nanpercentile(fondo, 2), vmax=np.nanpercentile(fondo, 98))
    ax.imshow(np.ma.masked_where(clase < 1, clase - 1), cmap=ListedColormap(colores), vmin=0, vmax=3,
              extent=ext, interpolation="nearest")
    ax.imshow(np.ma.masked_where(~(dentro & ~valido), np.ones_like(clase)), cmap=ListedColormap(["#6baed6"]),
              alpha=0.6, extent=ext, interpolation="nearest")
    borde = np.array(aoi.exterior.coords) / 1000
    ax.plot(borde[:, 0], borde[:, 1], color="black", lw=1.2)
    p = pts.to_crs(CRS)
    ax.scatter(p.geometry.x / 1000, p.geometry.y / 1000, s=14, c="#00e5ff", edgecolor="black", lw=0.5, zorder=5)
    leyenda = [Patch(color=c, label=f"Severidad {n.lower()}") for c, (_, _, n) in zip(colores, SEVERIDAD[1:])]
    leyenda += [Patch(color="#6baed6", alpha=0.6, label="Sin dato (nube/agua)"),
                Line2D([], [], marker="o", ls="", mfc="#00e5ff", mec="black", label=f"Focos VIIRS ({len(p)})"),
                Line2D([], [], color="black", lw=1.2, label="Zona analizada (focos + 1 km)")]
    ax.legend(handles=leyenda, loc="lower left", fontsize=9, framealpha=0.9)
    ax.set_title(f"Área quemada (dNBR ≥ 0.10): {quemado.sum() * ha_px:,.0f} ha — {nombre}\n"
                 f"Sentinel-2 L2A {a.fecha} → {d.fecha}  ·  fondo: NIR posterior", fontsize=11)
    ax.set_xlabel("Este UTM 18S (km)")
    ax.set_ylabel("Norte UTM 18S (km)")
    fig.text(0.01, 0.01, "Fuentes: NASA FIRMS VIIRS, Copernicus Sentinel-2 (Planetary Computer), "
             "ESA WorldCover 2021. No reemplaza reportes oficiales.", fontsize=7, color="#444")
    fig.tight_layout()
    fig.savefig(OUT / f"mapa_{clave}.png")
    plt.close(fig)
    print(f"\nMapa: outputs/mapa_{clave}.png")


if __name__ == "__main__":
    main()
