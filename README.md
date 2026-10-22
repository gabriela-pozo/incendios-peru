# Incendios Perú

¿Qué se quemó? De 8 637 focos de calor en el Perú a 1 690 hectáreas medidas en
Chichas, Arequipa. La historia completa está en [index.html](index.html)
(publicada en https://gabriela-pozo.github.io/incendios-peru/ cuando se active GitHub Pages).

## Pregunta

¿Cuántas hectáreas se quemaron en el incendio de Chichas (Condesuyos, Arequipa),
del 16 al 18 de octubre de 2026, y qué tipo de suelo era? Y, como complemento,
¿esa zona arde cada año o 2026 fue excepcional?

## Datos y fechas

- **Focos VIIRS** (Suomi-NPP, NOAA-20, NOAA-21): CSV "South America 7d" de NASA FIRMS,
  descargado el 21-oct-2026 (focos del 14 al 21-oct). Solo confianza nominal/alta:
  8 637 focos en el Perú, agrupados en 2 602 incendios.
- **Archivo anual de focos**, solo Suomi-NPP, Perú, 2012-2025 (NASA FIRMS,
  `viirs-snpp_{año}_Peru.csv`), descargado el 21-oct-2026. El archivo de 2026 aún no existe.
- **Límites distritales**: GADM 4.1, nivel 3.
- **Sentinel-2 L2A** (Microsoft Planetary Computer):

  | Caso | Imagen | Fecha | Tile | Nubes en la zona | Nubes en la escena | Zona inválida |
  |---|---|---|---|---:|---:|---:|
  | Chichas | Antes | 15-oct-2026 | 18LYH | 0,0 % | 0,3 % | 0,0 % |
  | Chichas | Después | 20-oct-2026 | 18LYH | 0,2 % | 11,4 % | 0,2 % |
  | Río Tambo | Antes (la mejor) | 8-oct-2026 | 18LXM | 0,0 % | 38,3 % | 0,0 % |
  | Río Tambo | Después (la mejor) | 20-oct-2026 | 18LXM | 55,4 % | 62,7 % | 55,4 % |

  "Zona inválida" suma nubes, sombras, cirros y píxeles sin dato; el máximo admitido es 30 %.
- **ESA WorldCover 2021** (v2.0.0), vía Microsoft Planetary Computer.
- **Elección del caso**: se eligió primero Callería (Ucayali), pero no había imagen
  Sentinel-2 posterior al fuego (17-21 oct); por regla fija se pasó a Chichas.

## Método

- **Focos**: filtrados a Perú con GADM; dos focos son del mismo incendio si están a
  ≤ 1 km y ≤ 48 h entre sí (las cadenas se unen).
- **Zona analizada**: envolvente de los focos + 1 km (Chichas: 178 focos, 5 399 ha),
  en una rejilla de 20 m (UTM 18S).
- **dNBR**: `NBR = (B8A − B12) / (B8A + B12)`; dNBR = NBR antes − NBR después.
  Píxel quemado si dNBR ≥ 0,10; severidad según Key y Benson (0,10 / 0,27 / 0,44 / 0,66).
- **Máscara SCL**: se excluyen sombra, nube media, nube alta, cirros, agua y sin dato
  en cualquiera de las dos fechas.
- **Cobertura**: ESA WorldCover remuestreado a la rejilla y cruzado con los píxeles quemados.
- **Sensibilidad**: hectáreas quemadas con umbrales de 0,05 a 0,35, mismo par de imágenes.
- **Recurrencia**: focos S-NPP por año dentro del polígono quemado (dNBR ≥ 0,10) y a 1 km de él.

## Tres hallazgos

1. Se quemaron 1 690 ha (dNBR ≥ 0,10), el 31 % de las 5 399 ha analizadas; el 85,7 %
   de lo quemado es de severidad baja.
2. El 72,4 % de lo quemado era pastizal; bosque, 0,1 ha; cultivo, cero.
3. La medición da 43 % menos que lo que sugerían los focos, cuya envolvente apuntaba a 2 957 ha.

| Severidad | Rango dNBR | Hectáreas |
|---|---|---:|
| Baja | 0,10-0,27 | 1 447,6 |
| Moderada-baja | 0,27-0,44 | 240,8 |
| Moderada-alta | 0,44-0,66 | 1,1 |
| Alta | ≥ 0,66 | 0,0 |
| **Total quemado** | ≥ 0,10 | **1 689,5** |

| Cobertura (WorldCover) | Hectáreas | % de lo quemado |
|---|---:|---:|
| Pastizal | 1 223,0 | 72,4 |
| Matorral | 455,6 | 27,0 |
| Suelo desnudo | 10,3 | 0,6 |
| Agua | 0,4 | 0,0 |
| Bosque | 0,1 | 0,0 |
| Cultivo | 0,0 | 0,0 |

Tablas: `outputs/severidad_chichas.csv`, `outputs/cobertura_quemada_chichas.csv`
(y `_detalle.csv`), `outputs/imagenes_chichas.csv`, `outputs/top5_incendios.csv`.

## Mapa

![Área quemada en Chichas](outputs/mapa_chichas.png)

## Sensibilidad al umbral

| Umbral dNBR | Hectáreas quemadas | % de la zona |
|---|---:|---:|
| 0,05 | 2 007,5 | 37,2 |
| 0,08 | 1 842,9 | 34,1 |
| **0,10 (usado)** | **1 689,5** | **31,3** |
| 0,15 | 1 168,9 | 21,6 |
| 0,20 | 686,6 | 12,7 |
| 0,27 | 241,9 | 4,5 |
| 0,35 | 33,9 | 0,6 |

![Hectáreas quemadas según el umbral de dNBR](outputs/sensibilidad_umbral_chichas.png)

- Con el corte estándar de 0,10 el área quemada es de 1 690 ha.
- La cifra es muy elástica: de 2 008 ha a 34 ha entre 0,05 y 0,35, un factor de 59.
- La razón es que el incendio fue de baja severidad y sus píxeles se concentran
  cerca del umbral. Si hubiera sido un incendio forestal intenso, la curva sería plana.
- La escala de Key y Benson se calibró sobre incendios forestales; en pastizal casi
  todo cae en la banda baja y la elección del umbral pesa más que el fuego.
- 34-2 008 ha **no** es "el rango del incendio": con 0,05 se recogen ruido y cambios
  que no son fuego, y con 0,35 solo los núcleos más calientes.

Tabla: `outputs/sensibilidad_umbral_chichas.csv`.

## Recurrencia interanual

¿El área que ardió en 2026 arde cada año o fue excepcional? Se contaron los focos
de Suomi-NPP (confianza nominal/alta) de cada año 2012-2025, del archivo anual de
NASA FIRMS para Perú, dentro del polígono quemado en 2026 (1 689,5 ha, dNBR ≥ 0,10)
y dentro del polígono + 1 km (5 855,2 ha). Solo S-NPP: sumar NOAA-20 (desde 2018)
y NOAA-21 (desde 2023) inflaría los años recientes.

| Año | Focos en el polígono | Focos en polígono + 1 km | Días con datos (Perú) |
|---|---:|---:|---:|
| 2012 | 0 | 0 | 346 |
| 2013 | 0 | 1 | 365 |
| 2014 | 0 | 0 | 363 |
| 2015 | 0 | 0 | 365 |
| 2016 | 0 | 0 | 365 |
| 2017 | 0 | 0 | 364 |
| 2018 | 0 | 4 | 365 |
| 2019 | 0 | 0 | 364 |
| 2020 | 0 | 0 | 366 |
| 2021 | 0 | 0 | 365 |
| 2022 | 0 | 0 | 350 |
| 2023 | 0 | 0 | 363 |
| 2024 | 0 | 0 | 346 |
| 2025 | 0 | 0 | 362 |
| 2026* | 44 | 61 | 8 |

\* 2026: solo 14-21 de octubre (CSV de 7 días); el archivo anual 2026 aún no existe.

![Focos S-NPP por año en el área quemada de Chichas](outputs/recurrencia_chichas.png)

- **Los datos apuntan a un evento excepcional.** En 14 años completos, cero focos
  dentro del polígono. En el anillo de 1 km, focos en solo 2 años: 1 en marzo de 2013
  y 4 en diciembre de 2018. En 2026, en dos días (17 y 18 oct), 44 dentro y 61 con el anillo.
- **Confianza.** Los 14 años tienen datos utilizables (detecciones en el Perú en 346
  a 366 días de cada año). Confianza alta en que entre 2012 y 2025 no hubo ahí un
  incendio del tamaño del de 2026 (que dio 61 focos en dos días). Confianza baja en
  que la zona nunca se queme: S-NPP pasa unas dos veces al día y una quema de pastos
  pequeña y rápida puede ocurrir entre dos pasadas. Incluir los focos de confianza
  baja no cambia el resultado: siguen siendo cero dentro del polígono.
- **Lectura económica.** Una recurrencia alta habría sugerido quema de manejo de
  pastos (práctica productiva con externalidades: humo, emisiones, riesgo de escape).
  La recurrencia nula es más compatible con un evento excepcional, es decir, con un
  daño: forraje perdido sin haberlo planeado. Es evidencia compatible, no prueba:
  las quemas pequeñas pueden escapar al satélite, y un evento excepcional también
  puede ser una quema de manejo que se salió de control.

Tablas: `outputs/recurrencia_chichas.csv`, `outputs/focos_historicos_chichas.csv`;
polígono: `outputs/poligono_quemado_chichas.geojson`.

## Segundo caso, amazónico: Río Tambo (no medible)

Se intentó medir Río Tambo (Satipo, Junín), el incendio con más focos de la semana
(279 focos del 14 al 17 de octubre, el 99,6 % sobre bosque), con exactamente el mismo
método: zona de focos + 1 km (5 530 ha), umbral 0,10, máscara SCL, WorldCover y curva
de sensibilidad. Hay buena imagen anterior (8-oct-2026, tile 18LXM, 0,0 % de la zona
inválida), pero **ninguna posterior utilizable**; la regla exige como máximo el 30 %
de la zona inválida:

| Imagen posterior | Tile | Nubes en la zona | Zona inválida |
|---|---|---:|---:|
| 18-oct-2026 | 18LXM | 85,6 % | 85,6 % |
| 18-oct-2026 | 18LXN | 59,1 % | 96,0 % |
| 20-oct-2026 (la mejor) | 18LXM | 55,4 % | 55,4 % |
| 20-oct-2026 | 18LXN | 44,8 % | 81,7 % |

No se forzó la medición con la mitad sin nubes, porque la cifra no sería comparable
con la de Chichas. Es el mismo problema que dejó fuera a Callería. En la Amazonía,
octubre todavía es temporada de quemas y ya empiezan las lluvias: la
nubosidad impide medir justo cuando más arde, y eso sesga el análisis óptico hacia
los incendios andinos.

**La hipótesis queda sin contrastar.** Se esperaba que en bosque la severidad saliera
alta y la curva plana, y que en pastizal saliera baja y la curva empinada. Chichas es
compatible con la mitad de pastizal (85,7 % de lo quemado en severidad baja, factor de
59 entre umbrales), pero sin un caso de bosque un solo caso no respalda ni refuta la
hipótesis.

Tabla: `outputs/imagenes_riotambo.csv`.

## Literatura

Referencias verificadas (DOI comprobado en Crossref o URL oficial). De cada una se
dice solo lo que se pudo confirmar en su resumen o ficha.

1. Key, C. H. y Benson, N. C. (2006). *Landscape Assessment (LA): Sampling and
   analysis methods*. En FIREMON, USDA Forest Service, Gen. Tech. Rep. RMRS-GTR-164-CD.
   <https://research.fs.usda.gov/treesearch/24066>. Origen del dNBR y de su
   calibración con parcelas de campo CBI, cuyos estratos van del sustrato y las
   hierbas a los árboles grandes.
2. Miller, J. D. y Thode, A. E. (2007). Quantifying burn severity in a heterogeneous
   landscape with a relative version of the delta Normalized Burn Ratio (dNBR).
   *Remote Sensing of Environment*, 109(1), 66-80.
   <https://doi.org/10.1016/j.rse.2006.12.006>. Muestra que el dNBR mide cambio
   absoluto: donde hay poca vegetación previa, un fuego severo produce poco cambio y
   los umbrales fijos lo clasifican mal; proponen el RdNBR.
3. Roy, D. P., Boschetti, L. y Trigg, S. N. (2006). Remote sensing of fire severity:
   assessing the performance of the normalized burn ratio. *IEEE Geoscience and
   Remote Sensing Letters*, 3(1), 112-116. <https://doi.org/10.1109/LGRS.2005.858485>.
   Evalúan si el NBR cumple las condiciones de un índice óptimo de severidad con
   datos de sabanas de Sudáfrica y Australia, bosque boreal y bosque tropical.
4. Picotte, J. J. y Robertson, K. M. (2011). Validation of remote sensing of burn
   severity in south-eastern US ecosystems. *International Journal of Wildland Fire*,
   20(3), 453-464. <https://doi.org/10.1071/WF10013>. Con 731 parcelas CBI, la
   concordancia entre dNBR y severidad de campo varió según el tipo de vegetación.
5. Cansler, C. A. y McKenzie, D. (2012). How robust are burn severity indices when
   applied in a new region? *Remote Sensing*, 4(2), 456-483.
   <https://doi.org/10.3390/rs4020456>. Evalúa cómo se trasladan los índices y
   umbrales calibrados en una región a otra.
6. Lu, B., He, Y. y Tong, A. (2016). Evaluation of spectral indices for estimating
   burn severity in semiarid grasslands. *International Journal of Wildland Fire*,
   25(2), 147-157. <https://doi.org/10.1071/WF15098>. En un pastizal semiárido de
   Canadá, con severidad medida en campo, el índice que mejor funcionó fue el MIRBI,
   no el NBR.

Qué se sigue para Chichas: la escala de Key y Benson se calibró con parcelas
dominadas por estratos leñosos, y la literatura muestra que en pastizal y en
vegetación rala los umbrales fijos del dNBR no se trasladan sin recalibrar. Ninguna
de estas referencias es de pastizal andino: no se encontró un estudio de dNBR con
validación de campo en puna o páramo.

## Limitaciones

- Un foco de calor es un píxel de 375 m donde un satélite detectó fuego, incluidas
  quemas agrícolas. No es un incendio y no es una hectárea.
- La cifra de hectáreas depende de cuatro decisiones: fechas, nubes, umbral y zona.
  Solo el umbral la mueve entre 34 y 2 008 ha (ver "Sensibilidad al umbral").
- La severidad puede estar subestimada: en pastizal el dNBR sale bajo y la imagen
  posterior es de solo dos días después del último foco.
- El encadenamiento de focos puede fusionar incendios distintos cercanos en espacio y tiempo.
- VIIRS no detecta de forma confiable incendios pequeños, bajo dosel cerrado o
  cubiertos por nubes. En la recurrencia, eso limita la conclusión a incendios del
  tamaño del de 2026; la barra de 2026 cubre solo 8 días.
- Un solo caso medido: los dos candidatos amazónicos (Callería y Río Tambo) no
  tenían imagen posterior sin nubes, así que no hay contraste entre bosque y pastizal.
- WorldCover es de 2021, así que la cobertura pudo cambiar antes del incendio.
- Las cifras oficiales no se suman a estas: usan otros métodos y otras definiciones.
- Herramienta independiente con datos públicos; no reemplaza los reportes del
  COEN, INDECI, SERFOR ni SERNANP.

## Cómo reproducir

Requiere Python 3.14 (probado con 3.14.6) y conexión a internet (NASA FIRMS y
Microsoft Planetary Computer, sin clave). Desde la raíz del repositorio:

```bash
python -m venv .venv
.venv/Scripts/activate          # en Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python src/paso1_focos.py        # focos VIIRS → incendios → top 5
python src/paso2_4_medir.py      # par Sentinel-2, dNBR, severidad, WorldCover y mapa
python src/paso5_sensibilidad.py # hectáreas con 7 umbrales de dNBR + gráfico
python src/paso6_recurrencia.py  # archivo S-NPP 2012-2025 + polígono quemado + gráfico
python src/paso7_riotambo.py     # verifica si Río Tambo es medible (no lo es)
```

Los pasos 2 a 7 dependen de `outputs/focos_peru.csv`, que genera el paso 1. Las
descargas se guardan en `data/raw/` (no versionado) y no se repiten si ya existen.

**Ojo:** el CSV de 7 días de FIRMS cambia cada día. Si el paso 1 descarga los archivos
de nuevo, los focos e identificadores de incendio (Chichas = 1052, Río Tambo = 30) ya
no serán los mismos. Para reproducir estas cifras hacen falta los tres
`data/raw/firms_*_SA_7d.csv` descargados el 21-oct-2026; con el `outputs/focos_peru.csv`
versionado se pueden correr los pasos 2 a 7 sin el paso 1.
