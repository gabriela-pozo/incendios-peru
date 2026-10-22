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


def comparador():
    a, d = OUT / "chichas_rgb_antes.jpg", OUT / "chichas_rgb_despues.jpg"
    if not (a.exists() and d.exists()):
        return "", ""
    from PIL import Image
    w, h = Image.open(a).size
    img = pd.read_csv(OUT / "imagenes_chichas.csv")
    fa = img[(img.momento == "antes") & img.elegida].iloc[0].fecha
    fd = img[(img.momento == "despues") & img.elegida].iloc[0].fecha
    html = f"""<figure>
      <div class="comparador" style="--pos: 50%">
        <img src="outputs/chichas_rgb_antes.jpg" width="{w}" height="{h}" alt="Imagen Sentinel-2 en color real del {fecha(fa)} de 2026: laderas pardas y quebradas de la puna de Chichas, sin cicatriz.">
        <img class="despues" src="outputs/chichas_rgb_despues.jpg" width="{w}" height="{h}" alt="Imagen Sentinel-2 en color real del {fecha(fd)} de 2026 del mismo terreno: una gran mancha negra de quemado ocupa el centro; abajo a la derecha hay nubes blancas y sus sombras.">
        <span class="etq etq-a">{fecha(fa)}</span><span class="etq etq-d">{fecha(fd)}</span>
        <input type="range" min="0" max="100" value="50" aria-label="Desliza para pasar de la imagen del {fecha(fa)} a la del {fecha(fd)}"
               oninput="this.parentNode.style.setProperty('--pos', this.value + '%')">
      </div>
      <figcaption>Chichas antes y después, Sentinel-2 en color real (10&nbsp;m), mismo recorte y mismo ajuste de color en las dos fechas. A la izquierda de la línea, el {fecha(fa)}; a la derecha, el {fecha(fd)}. Desliza para mover la línea. El recorte es el rectángulo que contiene la zona analizada; las manchas blancas y oscuras de la esquina inferior derecha del {fecha(fd)} son nubes y sus sombras, no quemado.</figcaption>
    </figure>"""
    css = """
  .comparador { position: relative; border-radius: 8px; overflow: hidden; border: 1px solid var(--line); line-height: 0; touch-action: pan-y; }
  .comparador img { width: 100%; height: auto; display: block; border: none; border-radius: 0; }
  .comparador img.despues { position: absolute; inset: 0; clip-path: inset(0 0 0 var(--pos)); }
  .comparador::after { content: ""; position: absolute; top: 0; bottom: 0; left: var(--pos); width: 2px; margin-left: -1px; background: #ffffff; box-shadow: 0 0 4px rgba(0,0,0,0.6); pointer-events: none; }
  .comparador input[type=range] { position: absolute; inset: 0; width: 100%; height: 100%; margin: 0; opacity: 0; cursor: ew-resize; }
  .comparador .etq { position: absolute; top: 10px; line-height: 1.2; font-size: 0.85rem; font-weight: 700; color: #fff; background: rgba(20,32,29,0.75); padding: 3px 8px; border-radius: 999px; pointer-events: none; }
  .comparador .etq-a { left: 10px; } .comparador .etq-d { right: 10px; }
"""
    return html, css


def completar(e):
    html, css = rejilla()
    e["rejilla"] += html
    e["css"] += css
    html, css = comparador()
    e["comparador"] += html
    e["css"] += css
