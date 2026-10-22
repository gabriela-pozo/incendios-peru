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


LEAFLET = "https://unpkg.com/leaflet@1.9.4/dist/leaflet"


def mapa_nacional(estatico):
    if not (OUT / "mapa_nacional_datos.js").exists():
        return None
    t = pd.read_csv(OUT / "medicion_top20.csv")
    regiones = [r for r in ["Andes", "Amazonía", "Costa"] if (t.region == r).any()]
    chk_reg = "".join(f'<label><input type="checkbox" name="reg" value="{r}" checked> {r} ({(t.region == r).sum()})</label>'
                      for r in regiones)
    n_med, n_no = int(t.medible.sum()), int((~t.medible).sum())
    n_focos = len(pd.read_csv(OUT / "focos_peru.csv", usecols=["frp"]))
    head = (f'<link rel="stylesheet" href="{LEAFLET}.css">\n'
            f'<script src="{LEAFLET}.js" defer></script>\n'
            f'<script src="outputs/mapa_nacional_datos.js" defer></script>')
    html = f"""<figure>
      <div id="mapa-nac-caja" hidden>
        <div class="filtros" role="group" aria-label="Filtros del mapa">
          <span class="filtro-tit">Región:</span> {chk_reg}
          <span class="filtro-tit">Resultado:</span>
          <label><input type="checkbox" name="res" value="1" checked> medidos ({n_med})</label>
          <label><input type="checkbox" name="res" value="0" checked> no medidos ({n_no})</label>
        </div>
        <div id="mapa-nac" aria-label="Mapa interactivo de los focos de calor del Perú y los 20 incendios analizados"></div>
        <div class="leyenda-mapa">
          <span><i class="pt" style="background:#f3d9c4"></i>FRP &lt; 5&nbsp;MW</span>
          <span><i class="pt" style="background:#dba67f"></i>5–20</span>
          <span><i class="pt" style="background:#a85c32"></i>20–100</span>
          <span><i class="pt" style="background:#5e2f15"></i>&gt; 100&nbsp;MW</span>
          <span><i class="anillo" style="border-color:#0d6e5d"></i>incendio medido</span>
          <span><i class="anillo" style="border-color:#8a9a94"></i>no medible</span>
        </div>
      </div>
      <div id="mapa-nac-estatico">
      {estatico}
      </div>
      <figcaption id="mapa-nac-pie" hidden>Los {num(n_focos)} focos VIIRS del 14 al 21 de octubre de 2026, coloreados por potencia radiativa (FRP), y los 20 incendios con más focos: anillos verdes, los {n_med} que se pudieron medir; grises, los {n_no} que no. Toca o pasa el cursor sobre un anillo para ver el incendio y su resultado; los filtros ocultan anillos por región o por resultado. Las líneas son los límites departamentales.</figcaption>
    </figure>"""
    css = """
  #mapa-nac { height: 600px; border-radius: 8px; border: 1px solid var(--line); background: var(--card); }
  .filtros { display: flex; flex-wrap: wrap; gap: 6px 14px; align-items: center; font-size: 0.9rem; margin-bottom: 10px; }
  .filtros label { white-space: nowrap; cursor: pointer; }
  .filtro-tit { font-weight: 700; color: var(--muted); }
  .leyenda-mapa { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 0.85rem; color: var(--muted); margin-top: 8px; }
  .leyenda-mapa i { display: inline-block; vertical-align: -2px; margin-right: 5px; }
  .leyenda-mapa i.pt { width: 10px; height: 10px; border-radius: 50%; }
  .leyenda-mapa i.anillo { width: 13px; height: 13px; border-radius: 50%; border: 3px solid; }
  .leaflet-container { font: inherit; }
  @media (max-width: 560px) { #mapa-nac { height: 420px; } }
"""
    script = r"""<script>
window.addEventListener('load', function () {
  if (!window.L || !window.DATOS_MAPA) return;            // sin librería o sin datos: queda el mapa estático
  var D = window.DATOS_MAPA;
  document.getElementById('mapa-nac-caja').hidden = false;
  document.getElementById('mapa-nac-estatico').hidden = true;
  var pie = document.getElementById('mapa-nac-pie');
  pie.hidden = false;
  var oscuro = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  var mapa = L.map('mapa-nac', { preferCanvas: true, scrollWheelZoom: false, minZoom: 4, maxZoom: 11, zoomSnap: 0.25 });
  // sin mapa base de terceros: solo los límites departamentales (GADM 4.1)
  var deps = L.geoJSON(D.departamentos, { style: { color: oscuro ? '#9aaba5' : '#5c6b66', weight: 1,
    fillColor: oscuro ? '#1b2a26' : '#e8eeea', fillOpacity: 1 }, interactive: false }).addTo(mapa);
  mapa.fitBounds(deps.getBounds(), { padding: [10, 10] });
  mapa.attributionControl.setPrefix('').addAttribution('Focos: NASA FIRMS · Límites: GADM 4.1');
  function color(frp) { return frp < 5 ? '#f3d9c4' : frp < 20 ? '#dba67f' : frp < 100 ? '#a85c32' : '#5e2f15'; }
  var focos = L.layerGroup();
  D.focos.forEach(function (f) {
    L.circleMarker([f[0], f[1]], { radius: f[2] < 5 ? 1.8 : 2.6, stroke: false, fillColor: color(f[2]), fillOpacity: 0.85, interactive: false }).addTo(focos);
  });
  focos.addTo(mapa);
  var anillos = D.incendios.map(function (i) {
    var txt = '<strong>' + i.n + '</strong> (' + i.d + ', ' + i.reg + ')<br>' + i.focos + ' focos<br>' +
      (i.med ? 'Medido: ' + i.ha.toFixed(1).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, ' ') + ' ha' : 'No medible: ' + i.mot);
    var m = L.circleMarker([i.lat, i.lon], { radius: 11, weight: i.med ? 3.5 : 2.5, color: i.med ? '#0d6e5d' : '#8a9a94',
      fill: true, fillOpacity: 0, opacity: 1 }).bindTooltip(txt).bindPopup(txt);
    m.datos = i;
    return m;
  });
  var capa = L.layerGroup().addTo(mapa);
  function filtrar() {
    var reg = Array.from(document.querySelectorAll('input[name=reg]:checked')).map(function (x) { return x.value; });
    var res = Array.from(document.querySelectorAll('input[name=res]:checked')).map(function (x) { return x.value === '1'; });
    capa.clearLayers();
    anillos.forEach(function (m) {
      if (reg.indexOf(m.datos.reg) >= 0 && res.indexOf(m.datos.med) >= 0) { capa.addLayer(m); if (m.datos.med) m.bringToFront(); }
    });
  }
  document.querySelectorAll('.filtros input').forEach(function (x) { x.addEventListener('change', filtrar); });
  filtrar();
});
</script>"""
    return head, html, css, script


def completar(e):
    r = mapa_nacional(e["mapa_nacional"])
    if r:
        head, html, css, script = r
        e["head"] += head
        e["mapa_nacional"] = html
        e["css"] += css
        e["scripts"] += script
    html, css = rejilla()
    e["rejilla"] += html
    e["css"] += css
    html, css = comparador()
    e["comparador"] += html
    e["css"] += css
