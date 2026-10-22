"""Paso 5: sensibilidad de las hectáreas quemadas en Chichas al umbral de dNBR."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from paso2_4_medir import OUT, RES, elegir_par, nbr

UMBRALES = [0.05, 0.08, 0.10, 0.15, 0.20, 0.27, 0.35]
USADO = 0.10


def miles(v):
    return f"{v:,.0f}".replace(",", " ")


def main():
    _, nombre, _, _, rejilla, dentro, a, d, _, _ = elegir_par("chichas")
    print(f"\nPar: {a.fecha} → {d.fecha} (tile {a.tile})")
    nbr_a, val_a, _ = nbr(a["item"], rejilla)
    nbr_d, val_d, _ = nbr(d["item"], rejilla)
    dnbr = nbr_a - nbr_d
    valido = dentro & val_a & val_d & np.isfinite(dnbr)
    ha_px = RES * RES / 1e4
    zona_ha = dentro.sum() * ha_px

    tabla = pd.DataFrame({"umbral_dnbr": UMBRALES})
    tabla["hectareas"] = [round((valido & (dnbr >= u)).sum() * ha_px, 1) for u in UMBRALES]
    tabla["pct_zona"] = (100 * tabla.hectareas / zona_ha).round(1)
    tabla["usado"] = tabla.umbral_dnbr == USADO
    tabla.to_csv(OUT / "sensibilidad_umbral_chichas.csv", index=False)
    print(tabla.to_string(index=False))

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    ax.plot(tabla.umbral_dnbr, tabla.hectareas, color="#0d6e5d", lw=2, marker="o", ms=6, zorder=3)
    u = tabla[tabla.usado].iloc[0]
    ax.axvline(USADO, color="#5c6b66", lw=1, ls="--", zorder=1)
    ax.scatter([USADO], [u.hectareas], s=110, facecolor="#0d6e5d", edgecolor="white", lw=2, zorder=4)
    ax.annotate(f"Umbral usado (0,10): {miles(u.hectareas)} ha",
                (USADO, u.hectareas), xytext=(12, 8), textcoords="offset points", fontsize=9, color="#111")
    for x, y in [(tabla.umbral_dnbr.iloc[0], tabla.hectareas.iloc[0]),
                 (tabla.umbral_dnbr.iloc[-1], tabla.hectareas.iloc[-1])]:
        ax.annotate(f"{miles(y)} ha", (x, y), xytext=(0, 9), textcoords="offset points",
                    ha="center", fontsize=8, color="#444")
    ax.set_xticks(UMBRALES)
    ax.set_xticklabels([f"{x:.2f}".replace(".", ",") for x in UMBRALES])
    ax.set_xlabel("Umbral de dNBR (píxel quemado si dNBR ≥ umbral)")
    ax.set_ylabel("Hectáreas quemadas")
    ax.set_ylim(0, tabla.hectareas.max() * 1.12)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: miles(v)))
    ax.grid(axis="y", color="#d9e0dc", lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title(f"Hectáreas quemadas según el umbral de dNBR — {nombre}\n"
                 f"Sentinel-2 L2A {a.fecha} → {d.fecha}  ·  zona analizada {miles(zona_ha)} ha",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "sensibilidad_umbral_chichas.png")
    plt.close(fig)
    print("\nGráfico: outputs/sensibilidad_umbral_chichas.png")


if __name__ == "__main__":
    main()
