"""Paso 13: comportamiento nacional de los focos, mapa nacional estático y curvas de Lorenz (MAUP)."""
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from paso1_focos import cargar_distritos
from paso2_4_medir import OUT
from paso10_robustez import EQUIAREA, grilla

FRP_CLASES = [(0, 5, "< 5 MW", "#f3d9c4"), (5, 20, "5–20 MW", "#dba67f"),
              (20, 100, "20–100 MW", "#a85c32"), (100, np.inf, "> 100 MW", "#5e2f15")]


def comportamiento(f, inc, dist):
    dur = (pd.to_datetime(inc.fin_utc) - pd.to_datetime(inc.inicio_utc)).dt.total_seconds() / 3600
    chichas = dist[dist.distrito == "Chichas"].to_crs(32718).area.sum() / 1e4
    filas = [("focos (confianza nominal/alta, 14-21 oct 2026)", len(f)),
             ("% focos diurnos", round(100 * (f.daynight == "D").mean(), 1)),
             ("% focos nocturnos", round(100 * (f.daynight == "N").mean(), 1)),
             ("FRP mediana por foco (MW)", round(f.frp.median(), 2)),
             ("incendios (grupos de focos)", len(inc)),
             ("incendios con un solo foco", int((inc.focos == 1).sum())),
             ("% incendios de menos de 12 h entre el primer y el último foco", round(100 * (dur < 12).mean(), 1)),
             ("incendios de más de 3 días entre el primer y el último foco", int((dur > 72).sum())),
             ("área del distrito de Chichas según GADM 4.1 (ha)", round(chichas, 1)),
             ("% del distrito de Chichas quemado (1 689,5 ha)", round(100 * 1689.5 / chichas, 1))]
    t = pd.DataFrame(filas, columns=["indicador", "valor"])
    t.to_csv(OUT / "comportamiento_nacional.csv", index=False)
    print(t.to_string(index=False))


def lorenz(f, dist):
    curvas = []
    for unidad, claves in [("distrito", ["departamento", "provincia", "distrito"]),
                           ("provincia", ["departamento", "provincia"])]:
        n = dist.groupby(claves).size().rename("u").to_frame().join(f.groupby(claves).size().rename("n")).fillna(0).n
        curvas.append((unidad, n.values))
    pts = gpd.GeoDataFrame(f, geometry=gpd.points_from_xy(f.longitude, f.latitude), crs=4326).to_crs(EQUIAREA)
    peru = dist.to_crs(EQUIAREA)
    for desfase, nombre in [(0, "grilla 10 x 10 km"), (5000, "grilla 10 x 10 km desplazada 5 km")]:
        g = grilla(peru, desfase)
        n = gpd.sjoin(pts, g, predicate="within").groupby("index_right").size().reindex(g.index, fill_value=0)
        curvas.append((nombre, n.values))
    filas = []
    for nombre, x in curvas:
        x = np.sort(x.astype(float))
        cx = np.r_[0, np.arange(1, len(x) + 1) / len(x)]
        cy = np.r_[0, np.cumsum(x) / x.sum()]
        for q in np.linspace(0, 1, 101):
            filas.append({"unidad": nombre, "pct_unidades": round(100 * q, 1),
                          "pct_focos": round(100 * float(np.interp(q, cx, cy)), 2)})
    lz = pd.DataFrame(filas)
    lz.to_csv(OUT / "lorenz_maup.csv", index=False)
    g = pd.read_csv(OUT / "gini_maup.csv").set_index("unidad").gini_todas_las_unidades
    fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
    ax.plot([0, 100], [0, 100], color="#5c6b66", lw=1, ls="--")
    for (nombre, sub), (col, ls) in zip(lz.groupby("unidad", sort=False),
                                        [("#0d6e5d", "-"), ("#a85c32", "-"), ("#14201d", "-"), ("#14201d", ":")]):
        ax.plot(sub.pct_unidades, sub.pct_focos, color=col, ls=ls, lw=2,
                label=f"{nombre} (Gini {g[nombre]:.3f})".replace(".", ",").replace("10 x 10", "10 × 10"))
    ax.set_xlabel("% de unidades, de menos a más focos"); ax.set_ylabel("% acumulado de focos")
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.grid(color="#d9e0dc", lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    ax.set_title("Curvas de Lorenz de los 8 637 focos con cuatro particiones\n(todas las unidades, también las sin focos)",
                 fontsize=10)
    fig.tight_layout(); fig.savefig(OUT / "lorenz_maup.png"); plt.close(fig)


def mapa(f, dist):
    t20 = pd.read_csv(OUT / "medicion_top20.csv")
    # buffer ida y vuelta para cerrar las astillas entre distritos al disolver
    dep = dist.to_crs(32718).assign(geometry=lambda x: x.buffer(150)).dissolve("departamento")
    dep = dep.assign(geometry=dep.buffer(-150)).to_crs(4326).reset_index()
    fig, ax = plt.subplots(figsize=(8, 10), dpi=150)
    dep.boundary.plot(ax=ax, color="#8a9a94", lw=0.6, zorder=1)
    for lo, hi, etq, col in FRP_CLASES:
        s = f[(f.frp >= lo) & (f.frp < hi)]
        ax.scatter(s.longitude, s.latitude, s=3 + 4 * (lo > 0), color=col, lw=0, zorder=2)
    for medido, col in [(False, "#9aaba5"), (True, "#0d6e5d")]:
        s = t20[t20.medible == medido]
        ax.scatter(s.lon, s.lat, s=260, facecolor="none", edgecolor=col, lw=2.2 if medido else 1.6, zorder=3)
    for r in t20[t20.medible].itertuples():
        ax.annotate(r.distrito.replace("SanCristobal", "San Cristóbal").replace("Iparia", "Iparía"),
                    (r.lon, r.lat), xytext=(10, 6), textcoords="offset points", fontsize=8, color="#0d6e5d",
                    fontweight="bold", zorder=4)
    leyenda = [Line2D([], [], marker="o", ls="", color=c, ms=5, label=f"Foco VIIRS, FRP {e}") for _, _, e, c in FRP_CLASES]
    leyenda += [Line2D([], [], marker="o", ls="", mfc="none", mec="#0d6e5d", mew=2, ms=12, label="Incendio medido (4)"),
                Line2D([], [], marker="o", ls="", mfc="none", mec="#9aaba5", mew=1.6, ms=12, label="No medible (16)")]
    ax.legend(handles=leyenda, loc="lower left", fontsize=8, framealpha=0.95)
    ax.set_aspect("equal"); ax.set_axis_off()
    n = f"{len(f):,}".replace(",", " ")
    ax.set_title(f"{n} focos VIIRS en el Perú, 14-21 de octubre de 2026,\ny los 20 incendios con más focos", fontsize=11)
    fig.text(0.02, 0.01, "Fuentes: NASA FIRMS (Suomi-NPP, NOAA-20, NOAA-21), GADM 4.1. Confianza nominal o alta.",
             fontsize=7, color="#5c6b66")
    fig.tight_layout(); fig.savefig(OUT / "mapa_nacional.png"); plt.close(fig)


def main():
    f = pd.read_csv(OUT / "focos_peru.csv")
    inc = pd.read_csv(OUT / "incendios_peru.csv")
    dist = cargar_distritos()
    comportamiento(f, inc, dist)
    lorenz(f, dist)
    mapa(f, dist)


if __name__ == "__main__":
    main()
