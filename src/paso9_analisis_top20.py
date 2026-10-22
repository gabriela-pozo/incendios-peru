"""Paso 9: análisis sobre los 20 incendios — éxito por región, severidad por cobertura,
envolvente vs área medida y firma nocturna."""
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, spearmanr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from paso2_4_medir import OUT

SEV = [("pct_sev_baja", "Baja", "#f2d024"), ("pct_sev_moderada_baja", "Moderada-baja", "#f08c3a"),
       ("pct_sev_moderada_alta", "Moderada-alta", "#d93a1f"), ("pct_sev_alta", "Alta", "#6e1708")]


def miles(v):
    return f"{v:,.0f}".replace(",", " ")


def main():
    d = pd.read_csv(OUT / "medicion_top20.csv")
    m = d[d.medible].copy()

    # a) éxito por región
    cats = ["nubes", "sin imagen posterior", "prefiltro de escena", "tile inválido"]
    reg = d.groupby("region").agg(incendios=("medible", "size"), medidos=("medible", "sum"))
    for c in cats:
        reg[f"fallo_{c.replace(' ', '_')}"] = d[d.categoria_motivo == c].groupby("region").size()
    reg = reg.fillna(0).astype(int)
    reg["pct_medidos"] = (100 * reg.medidos / reg.incendios).round(1)
    reg["pct_fallo_nubes"] = (100 * reg.fallo_nubes / reg.incendios).round(1)
    reg = reg.reset_index()
    reg.to_csv(OUT / "top20_exito_region.csv", index=False)
    print(reg.to_string(index=False))
    am, an = reg.set_index("region").loc["Amazonía"], reg.set_index("region").loc["Andes"]
    _, p_med = fisher_exact([[am.medidos, am.incendios - am.medidos], [an.medidos, an.incendios - an.medidos]])
    _, p_nub = fisher_exact([[am.fallo_nubes, am.incendios - am.fallo_nubes],
                             [an.fallo_nubes, an.incendios - an.fallo_nubes]])
    print(f"Fisher (medidos, Amazonía vs Andes): p = {p_med:.2f}  |  Fisher (fallo por nubes): p = {p_nub:.2f}")
    pruebas = [("Fisher: medidos, Amazonía vs Andes", "p", p_med, 19),
               ("Fisher: fallo por nubes, Amazonía vs Andes", "p", p_nub, 19)]

    # b) severidad por cobertura dominante del área quemada
    m["pct_moderada_o_mas"] = (m.pct_sev_moderada_baja + m.pct_sev_moderada_alta + m.pct_sev_alta).round(1)
    m["ratio_035_010"] = (m["ha_umbral_0.35"] / m["ha_umbral_0.10"]).round(3)
    cols = ["distrito", "region", "cobertura_dominante", "area_quemada_ha", "pct_sev_baja", "pct_moderada_o_mas",
            "dnbr_mediana_quemado", "ratio_035_010"]
    print("\n" + m[cols].to_string(index=False))

    # c) envolvente vs área medida
    m["diferencia_pct"] = (100 * (m.area_quemada_ha / m.envolvente_ha - 1)).round(1)
    print("\nÁrea medida vs envolvente (%):", m.set_index("distrito").diferencia_pct.to_dict())

    # d) firma nocturna
    for y in ["area_quemada_ha", "pct_moderada_o_mas", "dnbr_mediana_quemado"]:
        r, p = spearmanr(m.pct_focos_noche, m[y])
        print(f"Spearman % focos nocturnos vs {y}: rho = {r:.2f}, p = {p:.2f} (n = {len(m)})")
        pruebas += [(f"Spearman: % nocturnos vs {y}", "rho", r, len(m)), (f"Spearman: % nocturnos vs {y}", "p", p, len(m))]
    r20, p20 = spearmanr(d.pct_focos_noche, d.envolvente_ha)
    print(f"Spearman % nocturnos vs envolvente, 20 casos: rho = {r20:.2f}, p = {p20:.2f}")
    pruebas += [("Spearman: % nocturnos vs envolvente_ha", "rho", r20, len(d)),
                ("Spearman: % nocturnos vs envolvente_ha", "p", p20, len(d))]
    pd.DataFrame(pruebas, columns=["prueba", "estadistico", "valor", "n"]).round(3)         .to_csv(OUT / "top20_pruebas.csv", index=False)
    resumen = m[["incendio", "distrito", "region", "cobertura_dominante", "pct_focos_noche", "envolvente_ha",
                 "area_quemada_ha", "diferencia_pct", "pct_sev_baja", "pct_moderada_o_mas",
                 "dnbr_mediana_quemado", "ratio_035_010"]]
    resumen.to_csv(OUT / "top20_medidos_resumen.csv", index=False)

    # gráfico: dispersión envolvente vs medida
    fig, ax = plt.subplots(figsize=(6.5, 6), dpi=150)
    lim = max(m.envolvente_ha.max(), m.area_quemada_ha.max()) * 1.15
    ax.plot([0, lim], [0, lim], color="#5c6b66", lw=1, ls="--")
    ax.text(lim * 0.80, lim * 0.74, "medida = envolvente", ha="center", fontsize=8, color="#5c6b66", rotation=45)
    for r in m.itertuples():
        col = "#0d6e5d" if r.cobertura_dominante == "pastizal" else "#a85c32"
        ax.scatter(r.envolvente_ha, r.area_quemada_ha, s=70, color=col, edgecolor="white", lw=1.5, zorder=3)
        ax.annotate(f"{r.distrito} ({r.diferencia_pct:+.0f} %)".replace(".", ","), (r.envolvente_ha, r.area_quemada_ha),
                    xytext=(7, -13 if r.area_quemada_ha < r.envolvente_ha * 0.4 else 3), textcoords="offset points", fontsize=8)
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.set_xlabel("Envolvente de los focos (ha)"); ax.set_ylabel("Área quemada medida, dNBR ≥ 0,10 (ha)")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(color="#d9e0dc", lw=0.6)
    ax.set_title(f"Envolvente de focos vs área medida — {len(m)} incendios medibles de 20", fontsize=10)
    ax.scatter([], [], color="#0d6e5d", label="Pastizal dominante"); ax.scatter([], [], color="#a85c32", label="Bosque dominante")
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout(); fig.savefig(OUT / "top20_envolvente_vs_medida.png"); plt.close(fig)

    # gráfico: distribución de severidad por incendio
    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=150)
    orden = m.sort_values("pct_sev_baja", ascending=False)
    etiquetas = [f"{r.distrito}\n{r.cobertura_dominante}" for r in orden.itertuples()]
    izq = np.zeros(len(orden))
    for c, nom, col in SEV:
        ax.barh(etiquetas, orden[c], left=izq, color=col, label=nom, edgecolor="white", lw=1)
        izq += orden[c].values
    ax.invert_yaxis(); ax.set_xlim(0, 100); ax.set_xlabel("% del área quemada")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(ncol=4, fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.18))
    fig.tight_layout(); fig.savefig(OUT / "top20_severidad.png"); plt.close(fig)


if __name__ == "__main__":
    main()
