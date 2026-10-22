"""Paso 11: cruce de la recurrencia (paso 6) con la firma nocturna de los focos.

Lectura propuesta: recurrencia alta + firma nocturna = zona de quema habitual donde esta vez
el fuego se escapó. Aquí se mide cada pieza por separado.
"""
import pandas as pd

from paso2_4_medir import OUT


def main():
    f = pd.read_csv(OUT / "focos_peru.csv")
    t20 = pd.read_csv(OUT / "medicion_top20.csv")
    rec = pd.read_csv(OUT / "recurrencia_chichas.csv")
    hist = pd.read_csv(OUT / "focos_historicos_chichas.csv")
    ch = f[f.incendio == 1052]
    noche = lambda s: round(100 * (s == "N").mean(), 1)
    otros = t20[t20.incendio != 1052].pct_focos_noche
    h = rec[rec.anio < 2026]
    filas = [
        ("% focos nocturnos, Chichas 2026 (3 satélites)", noche(ch.daynight)),
        ("% focos nocturnos, Chichas 2026 (solo S-NPP)", noche(ch[ch.sat == "SNPP"].daynight)),
        ("% focos nocturnos, todo el Perú 14-21 oct 2026", noche(f.daynight)),
        ("% focos nocturnos, mediana de los otros 19 del top 20", round(otros.median(), 1)),
        ("lugar de Chichas en % nocturno dentro del top 20 (1 = más nocturno)",
         int(t20.pct_focos_noche.rank(ascending=False, method="min")[t20.incendio == 1052].iloc[0])),
        ("años 2012-2025 con focos dentro del polígono", int((h.focos_poligono > 0).sum())),
        ("años 2012-2025 con focos a <= 1 km", int((h.focos_poligono_mas_1km > 0).sum())),
        ("focos históricos (2012-2025) a <= 1 km", len(hist[hist.anio < 2026])),
        ("de ellos nocturnos", int((hist[hist.anio < 2026].daynight == "N").sum())),
    ]
    t = pd.DataFrame(filas, columns=["indicador", "valor"])
    t.to_csv(OUT / "recurrencia_noche_chichas.csv", index=False)
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
