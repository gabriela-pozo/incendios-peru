"""Paso 14: mapas de los cuatro incendios medidos (mismo estilo que mapa_chichas.png) y
recortes en color real antes/después de Chichas para el comparador de la página."""
import sys

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch, Rectangle
from matplotlib.lines import Line2D
from rasterio.transform import from_origin
from PIL import Image

from paso2_4_medir import OUT, RES, SEVERIDAD, leer, reflectancia
from medicion import zona_puntos, buscar_par, medir_par
from paso2_4_medir import mejor

COLORES = ["#f2d024", "#f08c3a", "#d93a1f", "#6e1708"]
NOMBRES = {"Chichas": "Chichas", "Iparia": "Iparía", "SanCristobal": "San Cristóbal", "Curahuasi": "Curahuasi"}


def miles(v, d=0):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", " ")


def puntos(focos, incendio):
    g = focos[focos.incendio == incendio]
    return gpd.GeoDataFrame(g, geometry=gpd.points_from_xy(g.longitude, g.latitude), crs=4326)


def par(pts):
    aoi, rejilla, dentro = zona_puntos(pts)
    antes, despues = buscar_par(pts, aoi, rejilla, dentro, "2026-10-21")
    return aoi, rejilla, dentro, mejor(antes), mejor(despues)


def mapa(fila, pts):
    aoi, rejilla, dentro, a, d = par(pts)
    r, dnbr, valido = medir_par(a["item"], d["item"], rejilla, dentro)
    assert abs(r["area_quemada_ha"] - fila.area_quemada_ha) < 0.05, "no coincide con medicion_top20.csv"
    nir = reflectancia(d["item"], "B8A", rejilla)
    clase = np.full(dnbr.shape, -1)
    for k, (lo, hi, _) in enumerate(SEVERIDAD):
        clase[valido & (dnbr >= lo) & (dnbr < hi)] = k
    tr, w, h = rejilla
    ext = [tr.c / 1000, (tr.c + w * RES) / 1000, (tr.f - h * RES) / 1000, tr.f / 1000]
    nom = NOMBRES[fila.distrito]
    fig, ax = plt.subplots(figsize=(8, 7.5), dpi=130)
    fondo = np.where(dentro, nir, np.nan)
    ax.imshow(fondo, cmap="Greys_r", extent=ext, vmin=np.nanpercentile(fondo, 2), vmax=np.nanpercentile(fondo, 98))
    ax.imshow(np.ma.masked_where(clase < 1, clase - 1), cmap=ListedColormap(COLORES), vmin=0, vmax=3, extent=ext,
              interpolation="nearest")
    ax.imshow(np.ma.masked_where(~(dentro & ~valido), np.ones_like(clase)), cmap=ListedColormap(["#6baed6"]),
              alpha=0.6, extent=ext, interpolation="nearest")
    borde = np.array(aoi.exterior.coords) / 1000
    ax.plot(borde[:, 0], borde[:, 1], color="black", lw=1.2)
    p = pts.to_crs(32718)
    ax.scatter(p.geometry.x / 1000, p.geometry.y / 1000, s=12, c="#00e5ff", edgecolor="black", lw=0.5, zorder=5)
    # barra de escala
    ancho_km = ext[1] - ext[0]
    km = 2 if ancho_km > 8 else 1
    x0, y0 = ext[1] - ancho_km * 0.06 - km, ext[2] + (ext[3] - ext[2]) * 0.05
    ax.add_patch(Rectangle((x0, y0), km, (ext[3] - ext[2]) * 0.008, color="black", zorder=6))
    ax.text(x0 + km / 2, y0 + (ext[3] - ext[2]) * 0.02, f"{km} km", ha="center", fontsize=9, zorder=6,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=1.5))
    leyenda = [Patch(color=c, label=f"Severidad {n.lower()}") for c, (_, _, n) in zip(COLORES, SEVERIDAD[1:])]
    leyenda += [Patch(color="#6baed6", alpha=0.6, label="Sin dato (nube/agua)"),
                Line2D([], [], marker="o", ls="", mfc="#00e5ff", mec="black", label=f"Focos VIIRS ({len(p)})"),
                Line2D([], [], color="black", lw=1.2, label="Zona analizada (focos + 1 km)")]
    ax.legend(handles=leyenda, loc="upper left", fontsize=8, framealpha=0.9)
    ax.set_title(f"{nom} ({fila.departamento}): {miles(fila.area_quemada_ha, 1)} ha con dNBR ≥ 0,10\n"
                 f"Sentinel-2 L2A {a.fecha} → {d.fecha}  ·  fondo: NIR posterior", fontsize=10)
    ax.set_xlabel("Este UTM 18S (km)"); ax.set_ylabel("Norte UTM 18S (km)")
    fig.tight_layout()
    fig.savefig(OUT / f"mapa_caso_{fila.distrito.lower()}.png")
    plt.close(fig)
    print(f"mapa_caso_{fila.distrito.lower()}.png  {r['area_quemada_ha']} ha")


def rgb(item, aoi, res=10):
    """Recorte en color real (asset 'visual', 10 m) sobre el rectángulo de la zona analizada."""
    minx, miny, maxx, maxy = aoi.bounds
    w, h = int((maxx - minx) / res), int((maxy - miny) / res)
    rej = (from_origin(minx, maxy, res, res), w, h)
    from rasterio.vrt import WarpedVRT
    import rasterio
    with rasterio.open(item.assets["visual"].href) as src, WarpedVRT(src, crs=32718, transform=rej[0], width=w,
                                                                      height=h) as vrt:
        return np.moveaxis(vrt.read([1, 2, 3]), 0, -1)


def comparador(focos):
    pts = puntos(focos, 1052)
    aoi, rejilla, dentro, a, d = par(pts)
    ims = {"antes": rgb(a["item"], aoi), "despues": rgb(d["item"], aoi)}
    # mismo estiramiento para las dos fechas, para que la diferencia sea real y no de contraste
    todo = np.concatenate([x.reshape(-1, 3) for x in ims.values()])
    lo, hi = np.percentile(todo[todo.sum(1) > 0], [1, 99], axis=0)
    for k, x in ims.items():
        y = np.clip((x.astype(float) - lo) / (hi - lo), 0, 1) ** 0.9
        Image.fromarray((y * 255).astype("uint8")).save(OUT / f"chichas_rgb_{k}.jpg", quality=85)
    print("chichas_rgb_antes.jpg / chichas_rgb_despues.jpg", ims["antes"].shape, a.fecha, d.fecha)


def main():
    focos = pd.read_csv(OUT / "focos_peru.csv", parse_dates=["fecha_utc"])
    if "rgb" not in sys.argv[1:]:
        t = pd.read_csv(OUT / "medicion_top20.csv")
        for fila in t[t.medible].itertuples():
            mapa(fila, puntos(focos, fila.incendio))
    if "mapas" not in sys.argv[1:]:
        comparador(focos)


if __name__ == "__main__":
    main()
