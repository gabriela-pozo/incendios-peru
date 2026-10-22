"""Bloques de mapas de la página. construir_pagina.py los inserta si sus archivos existen en outputs/."""
from pathlib import Path

import pandas as pd

OUT = Path("outputs")
NOMBRES = {"Chichas": "Chichas", "Iparia": "Iparía", "SanCristobal": "San Cristóbal", "Curahuasi": "Curahuasi"}


def num(v, d=0):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", "&nbsp;")


def fecha(f):
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    d = pd.Timestamp(f)
    return f"{d.day} {meses[d.month - 1]}"


def rejilla():
    t = pd.read_csv(OUT / "medicion_top20.csv")
    m = t[t.medible]
    if not all((OUT / f"mapa_caso_{d.lower()}.png").exists() for d in m.distrito):
        return "", ""
    tarjetas = []
    for r in m.itertuples():
        n = NOMBRES.get(r.distrito, r.distrito)
        tarjetas.append(f"""      <figure class="caso">
        <img src="outputs/mapa_caso_{r.distrito.lower()}.png" width="1040" height="975" loading="lazy"
             alt="Mapa de severidad del incendio de {n} ({r.departamento}): {num(r.area_quemada_ha, 1)} hectáreas con dNBR de 0,10 o más sobre el infrarrojo cercano posterior, con {r.focos} focos VIIRS y el contorno de la zona analizada.">
        <figcaption>
          <strong>{n}</strong> · {r.departamento} · {r.region}<br>
          <span class="caso-ha">{num(r.area_quemada_ha, 1)}&nbsp;ha</span> · {r.cobertura_dominante} dominante<br>
          Antes {fecha(r.antes_fecha)} ({num(r.antes_nubes_zona_pct, 1)}&nbsp;% de nubes en la zona) →
          después {fecha(r.despues_fecha)} ({num(r.despues_nubes_zona_pct, 1)}&nbsp;%)
        </figcaption>
      </figure>""")
    html = f"""  <section id="cuatro">
    <h2>Los cuatro que sí se pudieron medir</h2>
    <p>Mismo método, misma escala de colores: severidad (dNBR) sobre el infrarrojo cercano de la imagen posterior, con los focos VIIRS encima y el contorno de la zona analizada.</p>
    <div class="rejilla">
{chr(10).join(tarjetas)}
    </div>
    <p class="note">Leyenda común: amarillo, severidad baja; naranja, moderada-baja; rojo, moderada-alta; granate, alta; celeste, sin dato por nube o agua; puntos cian, focos VIIRS. Cada mapa trae su barra de escala. Las zonas tienen tamaños distintos.</p>
  </section>
"""
    css = """
  .rejilla { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-top: 16px; }
  figure.caso { margin: 0; background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 10px; }
  figure.caso img { border: none; }
  figure.caso figcaption { color: var(--fg); font-size: 0.9rem; line-height: 1.5; margin: 8px 4px 2px; }
  .caso-ha { color: var(--accent); font-weight: 750; font-size: 1.15rem; font-variant-numeric: tabular-nums; }
"""
    return html, css


def completar(e):
    html, css = rejilla()
    e["rejilla"] += html
    e["css"] += css
