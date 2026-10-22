"""Paso 6: recurrencia interanual de focos S-NPP (2012-2025) en el polígono quemado de Chichas 2026."""
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from rasterio.features import shapes
from shapely.geometry import shape
from shapely.ops import unary_union
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from paso1_focos import descargar
from paso2_4_medir import OUT, CRS, elegir_par, nbr

ARCHIVO = Path("data/raw/firms_archivo"); ARCHIVO.mkdir(parents=True, exist_ok=True)
URL = "https://firms.modaps.eosdis.nasa.gov/data/country/viirs-snpp/{y}/viirs-snpp_{y}_Peru.csv"
ANIOS = range(2012, 2026)
# 2026 no está en el archivo anual: solo el CSV de 7 días (14-21 oct) que usó el paso 1
NRT_2026 = Path("data/raw/firms_SNPP_SA_7d.csv")


def poligono_quemado():
    _, _, _, _, rejilla, dentro, a, d, _, _ = elegir_par("chichas")
    nbr_a, val_a, _ = nbr(a["item"], rejilla)
    nbr_d, val_d, _ = nbr(d["item"], rejilla)
    dnbr = nbr_a - nbr_d
    quemado = dentro & val_a & val_d & np.isfinite(dnbr) & (dnbr >= 0.10)
    partes = [shape(g) for g, v in shapes(quemado.astype("uint8"), mask=quemado, transform=rejilla[0]) if v == 1]
    return unary_union(partes)


def focos(df):
    df = df.copy()
    df["confidence"] = df["confidence"].astype(str).str.lower().str[0]
    df = df[df["confidence"].isin(["n", "h"])]
    df["acq_date"] = pd.to_datetime(df["acq_date"])
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs=4326).to_crs(CRS)


def main():
    pol = poligono_quemado()
    buf = pol.buffer(1000)
    print(f"Polígono quemado: {pol.area / 1e4:.1f} ha  |  con buffer 1 km: {buf.area / 1e4:.1f} ha")
    gpd.GeoDataFrame({"zona": ["quemado_dnbr010", "quemado_mas_1km"]}, geometry=[pol, buf], crs=CRS) \
        .to_crs(4326).to_file(OUT / "poligono_quemado_chichas.geojson", driver="GeoJSON")

    fuentes = [(y, URL.format(y=y), ARCHIVO / f"viirs-snpp_{y}_Peru.csv") for y in ANIOS]
    filas, cerca = [], []
    for y, url, ruta in fuentes + [(2026, None, NRT_2026)]:
        raw = pd.read_csv(descargar(url, ruta) if url else ruta)
        f = focos(raw)
        if y == 2026:
            f = f[f.geometry.intersects(buf.envelope)]  # el CSV de 7 días es de toda Sudamérica
        en_buf = f[f.geometry.within(buf)]
        en_pol = en_buf[en_buf.geometry.within(pol)]
        cerca.append(en_buf.drop(columns="geometry").assign(anio=y, en_poligono=en_buf.index.isin(en_pol.index)))
        filas.append({"anio": y,
                      "focos_poligono": len(en_pol),
                      "focos_poligono_mas_1km": len(en_buf),
                      "dias_con_focos_1km": en_buf.acq_date.dt.date.nunique(),
                      "meses_con_focos_1km": " ".join(sorted({f"{m:02d}" for m in en_buf.acq_date.dt.month})),
                      "dias_con_datos": raw["acq_date"].nunique(),
                      "fuente": "FIRMS archivo anual S-NPP (Perú)" if url else
                                "FIRMS NRT 7 días S-NPP (14-21 oct 2026)"})
    t = pd.DataFrame(filas)
    t.to_csv(OUT / "recurrencia_chichas.csv", index=False)
    pd.concat(cerca).to_csv(OUT / "focos_historicos_chichas.csv", index=False)
    print(t.to_string(index=False))

    hist = t[t.anio < 2026]
    con = (hist.focos_poligono_mas_1km > 0).sum()
    print(f"\nAños 2012-2025 con al menos un foco a <=1 km: {con} de {len(hist)}"
          f"  |  dentro del polígono: {(hist.focos_poligono > 0).sum()} de {len(hist)}")

    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    col = ["#a85c32" if y == 2026 else "#0d6e5d" for y in t.anio]
    ax.bar(t.anio, t.focos_poligono_mas_1km, color=col, width=0.7, zorder=3)
    for y, v in zip(t.anio, t.focos_poligono_mas_1km):
        ax.text(y, v, f"{v}", ha="center", va="bottom", fontsize=8, color="#14201d")
    ax.set_xticks(list(t.anio))
    ax.set_xticklabels([str(y) if y < 2026 else "2026*" for y in t.anio], rotation=45, fontsize=8)
    ax.set_ylabel("Focos S-NPP (confianza nominal/alta)")
    ax.grid(axis="y", color="#d9e0dc", lw=0.8, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("Focos S-NPP por año en el área quemada de Chichas en 2026 (polígono + 1 km)", fontsize=11)
    fig.text(0.01, 0.01, "* 2026: solo 14-21 de octubre (CSV de 7 días). 2012-2025: año completo, "
             "archivo anual de NASA FIRMS. Solo Suomi-NPP.", fontsize=7, color="#5c6b66")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / "recurrencia_chichas.png")
    plt.close(fig)
    print("Gráfico: outputs/recurrencia_chichas.png")


if __name__ == "__main__":
    main()
