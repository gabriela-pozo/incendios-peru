"""Pipeline de medición reutilizable: el mismo método que Chichas, para cualquier grupo de focos.

Reutiliza las funciones y constantes de paso2_4_medir (lectura, reflectancia, búsqueda de
candidatas, regla de imagen usable) y solo vuelve configurables las decisiones que la
sensibilidad multiparamétrica necesita mover: zona (buffer), máscara SCL, par de imágenes y umbral.
"""
from datetime import date

import numpy as np
import pandas as pd
import geopandas as gpd
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
from shapely.geometry import mapping

from paso2_4_medir import (CRS, RES, NUBES, SIN_DATO, AGUA, SEVERIDAD, WORLDCOVER, MAX_INVALIDO,
                           cat, leer, reflectancia, candidatas, mejor, usable)

HA_PX = RES * RES / 1e4
UMBRALES = [0.05, 0.08, 0.10, 0.15, 0.20, 0.27, 0.35]
MASCARA = NUBES + SIN_DATO + [AGUA]            # la usada en Chichas
GRUPO_WC = {"Bosque": "bosque", "Matorral": "matorral", "Pastizal": "pastizal", "Cultivo": "cultivo"}


def zona_puntos(pts, buffer=1000):
    """Envolvente de los focos + buffer, en rejilla de 20 m (igual que paso2_4_medir.zona)."""
    aoi = pts.to_crs(CRS).union_all().convex_hull.buffer(buffer)
    minx, miny, maxx, maxy = aoi.bounds
    minx, miny = np.floor(minx / RES) * RES, np.floor(miny / RES) * RES
    maxx, maxy = np.ceil(maxx / RES) * RES, np.ceil(maxy / RES) * RES
    w, h = int((maxx - minx) / RES), int((maxy - miny) / RES)
    tr = from_origin(minx, maxy, RES, RES)
    dentro = ~geometry_mask([aoi], (h, w), tr)
    return aoi, (tr, w, h), dentro


def buscar_par(pts, aoi, rejilla, dentro, fin_despues, dias_antes=60, max_nube_escena=80):
    t0, t1 = pts.fecha_utc.min(), pts.fecha_utc.max()
    desde_d = (t1 + pd.Timedelta(days=1)).date()
    antes = candidatas(aoi, (t0 - pd.Timedelta(days=dias_antes)).date(), t0.date(), rejilla, dentro, 10,
                       max_nube_escena)
    despues = (candidatas(aoi, desde_d, fin_despues, rejilla, dentro, 10, max_nube_escena)
               if desde_d <= pd.Timestamp(fin_despues).date() else pd.DataFrame())
    return antes, despues


def motivo(a, d):
    """Por qué no se puede medir (None si se puede)."""
    if d is None:
        return "sin imagen posterior"
    if a is None:
        return "sin imagen previa"
    for nombre, x in [("posterior", d), ("previa", a)]:
        if not usable(x):
            nubes, otro = x.nubes_zona_pct, x.invalido_zona_pct - x.nubes_zona_pct
            causa = "nubes sobre la zona" if nubes >= otro else "tile inválido (zona fuera de cobertura)"
            return f"{causa}: imagen {nombre} con {x.invalido_zona_pct:.1f}% de la zona inválida"
    return None


def nbr(item, rejilla, excluir):
    nir, swir = reflectancia(item, "B8A", rejilla), reflectancia(item, "B12", rejilla)
    scl = leer(item.assets["SCL"].href, rejilla)
    return (nir - swir) / (nir + swir), ~np.isin(scl, excluir)


def worldcover(aoi, rejilla):
    geom = mapping(gpd.GeoSeries([aoi], crs=CRS).to_crs(4326).iloc[0])
    tr, w, h = rejilla
    wc = np.zeros((h, w), dtype="uint8")
    for it in cat.search(collections=["esa-worldcover"], intersects=geom,
                         query={"esa_worldcover:product_version": {"eq": "2.0.0"}}).items():
        x = leer(it.assets["map"].href, rejilla)
        wc = np.where(wc == 0, x, wc)
    return wc


def medir_par(a_item, d_item, rejilla, dentro, excluir=MASCARA, umbral=0.10, aoi=None):
    """dNBR, hectáreas por severidad, curva de umbrales y (si se da aoi) cobertura WorldCover."""
    nbr_a, val_a = nbr(a_item, rejilla, excluir)
    nbr_d, val_d = nbr(d_item, rejilla, excluir)
    dnbr = nbr_a - nbr_d
    valido = dentro & val_a & val_d & np.isfinite(dnbr)
    quemado = valido & (dnbr >= umbral)
    q_ha = quemado.sum() * HA_PX
    r = {"zona_ha": round(dentro.sum() * HA_PX, 1),
         "sin_dato_ha": round((dentro & ~valido).sum() * HA_PX, 1),
         "area_quemada_ha": round(q_ha, 1),
         "dnbr_mediana_quemado": round(float(np.median(dnbr[quemado])), 3) if q_ha else np.nan}
    for lo, hi, nom in SEVERIDAD[1:]:
        m = valido & (dnbr >= max(lo, umbral)) & (dnbr < hi)
        clave = "sev_" + nom.lower().replace("-", "_")
        r[f"{clave}_ha"] = round(m.sum() * HA_PX, 1)
        r[f"pct_{clave}"] = round(100 * m.sum() * HA_PX / q_ha, 1) if q_ha else np.nan
    for u in UMBRALES:
        r[f"ha_umbral_{u:.2f}"] = round((valido & (dnbr >= u)).sum() * HA_PX, 1)
    if aoi is not None:
        wc = pd.Series(worldcover(aoi, rejilla)[quemado]).map(WORLDCOVER).fillna("Sin dato")
        grupos = wc.map(GRUPO_WC).fillna("otras").value_counts()
        for g in ["bosque", "matorral", "pastizal", "cultivo", "otras"]:
            r[f"pct_cob_{g}"] = round(100 * grupos.get(g, 0) / len(wc), 1) if len(wc) else np.nan
        r["cobertura_dominante"] = grupos.idxmax() if len(wc) else ""
    return r, dnbr, valido


def fila_imagen(prefijo, x):
    if x is None:
        return {f"{prefijo}_{k}": None for k in ["fecha", "tile", "nubes_zona_pct", "nubes_escena_pct",
                                                  "invalido_zona_pct"]}
    return {f"{prefijo}_fecha": x.fecha, f"{prefijo}_tile": x.tile,
            f"{prefijo}_nubes_zona_pct": x.nubes_zona_pct, f"{prefijo}_nubes_escena_pct": x.nubes_escena_pct,
            f"{prefijo}_invalido_zona_pct": x.invalido_zona_pct}


def medir_incendio(pts, fin_despues, buffer=1000, dias_antes=60):
    """Corre el pipeline completo sobre un grupo de focos. Devuelve una fila (dict)."""
    aoi, rejilla, dentro = zona_puntos(pts, buffer)
    antes, despues = buscar_par(pts, aoi, rejilla, dentro, fin_despues, dias_antes)
    a, d = mejor(antes), mejor(despues)
    fila = {"inicio_utc": pts.fecha_utc.min(), "fin_utc": pts.fecha_utc.max(),
            "n_candidatas_antes": len(antes), "n_candidatas_despues": len(despues)}
    fila |= fila_imagen("antes", a) | fila_imagen("despues", d)
    m = motivo(a, d)
    if m == "sin imagen posterior":
        # Diagnóstico (no cambia la medición): ¿no hubo pasada o todas tenían >80 % de nubes en la escena?
        _, todas = buscar_par(pts, aoi, rejilla, dentro, fin_despues, dias_antes, max_nube_escena=101)
        if len(todas):
            x = mejor(todas)
            fila |= fila_imagen("despues", x)
            if usable(x) and usable(a):
                m = (f"prefiltro de escena: la imagen posterior ({x.fecha}) tiene >80% de nubes en la escena "
                     f"pero solo {x.invalido_zona_pct:.1f}% de la zona inválida; el pipeline la descarta")
                r, _, _ = medir_par(a["item"], x["item"], rejilla, dentro, aoi=aoi)
                fila["area_quemada_ha_sin_prefiltro"] = r["area_quemada_ha"]
            else:
                m = (f"nubes sobre la zona: {len(todas)} imagen(es) posterior(es), todas con >80% de nubes en la "
                     f"escena; la mejor con {x.invalido_zona_pct:.1f}% de la zona inválida")
        else:
            m = "sin imagen posterior (ninguna pasada de Sentinel-2 hasta el " + str(fin_despues) + ")"
    fila["medible"] = m is None
    fila["categoria_motivo"] = ("" if m is None else "sin imagen posterior" if m.startswith("sin imagen posterior")
                                else "nubes" if m.startswith("nubes") else "tile inválido"
                                if m.startswith("tile") else "prefiltro de escena"
                                if m.startswith("prefiltro") else "otro")
    fila["motivo"] = m or ""
    if m is None:
        r, _, _ = medir_par(a["item"], d["item"], rejilla, dentro, aoi=aoi)
        fila |= r
    else:
        fila["zona_ha"] = round(dentro.sum() * HA_PX, 1)
    return fila
