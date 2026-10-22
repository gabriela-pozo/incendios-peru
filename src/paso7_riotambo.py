"""Paso 7: ¿se puede medir Río Tambo (Satipo, Junín) con el mismo método que Chichas?

Misma zona (focos + 1 km), misma rejilla, misma máscara SCL y misma regla: la imagen
posterior debe tener <= MAX_INVALIDO % de la zona inválida. Aquí no se filtra por nubes
de escena, para que queden registradas todas las imágenes posteriores al fuego.
Si no hay par usable, se documenta y se detiene: no se mide con una imagen nublada.
"""
import numpy as np
import pandas as pd

from paso2_4_medir import OUT, INCENDIOS, MAX_INVALIDO, zona, candidatas, mejor, usable

CLAVE = "riotambo"


def main():
    inc_id, nombre = INCENDIOS[CLAVE]
    pts, aoi, rejilla, dentro = zona(inc_id)
    t0, t1 = pts.fecha_utc.min(), pts.fecha_utc.max()
    ha = dentro.sum() * 0.04
    print(f"{nombre}: {len(pts)} focos, {t0:%d-%b %H:%M} a {t1:%d-%b %H:%M} UTC, zona {ha:,.0f} ha")
    antes = candidatas(aoi, (t0 - pd.Timedelta(days=60)).date(), t0.date(), rejilla, dentro, 10, 101)
    despues = candidatas(aoi, (t1 + pd.Timedelta(days=1)).date(), "2026-10-21", rejilla, dentro, 10, 101)
    a, d = mejor(antes), mejor(despues)
    tabla = pd.concat([antes.assign(momento="antes"), despues.assign(momento="despues")])
    tabla["mejor"] = tabla["item"].map(lambda it: it.id in [x["item"].id for x in (a, d) if x is not None])
    tabla.drop(columns="item").to_csv(OUT / f"imagenes_{CLAVE}.csv", index=False)
    print(tabla.drop(columns="item").to_string(index=False))

    if usable(a) and usable(d):
        print("\nHay par usable: medir con paso2_4_medir y paso5_sensibilidad para esta clave.")
        return
    peor = "posterior" if not usable(d) else "previa"
    x = d if not usable(d) else a
    print(f"\n>>> NO MEDIBLE: la mejor imagen {peor} ({x.fecha}, tile {x.tile}) tiene "
          f"{x.invalido_zona_pct}% de la zona inválida (máximo {MAX_INVALIDO}%). No se fuerza la medición.")


if __name__ == "__main__":
    main()
