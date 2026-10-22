# Incendios Perú

## Pregunta

¿Cuántas hectáreas se quemaron en el incendio de Chichas (Condesuyos, Arequipa), 16-18 de octubre de 2026 y qué tipo de suelo era?

## Datos y fechas

- Focos VIIRS (Suomi-NPP, NOAA-20, NOAA-21), CSV "South America 7d" de NASA FIRMS,
  descargado el 21-oct-2026 (focos del 14 al 21-oct). Solo confianza nominal/alta.
- Límites distritales: GADM 4.1, nivel 3.
- Sentinel-2 L2A, tile 18LYH: ANTES 15-oct-2026 (0.0 % nube en la zona),
  DESPUÉS 20-oct-2026 (0.2 % nube en la zona).
- ESA WorldCover 2021 (v2.0.0), vía Microsoft Planetary Computer.
- Se eligió primero Callería (Ucayali), pero no había imagen Sentinel-2 posterior
  al fuego (17-21 oct); por regla fija se pasó a Chichas.
- Zona analizada: envolvente de los 178 focos + 1 km (5 399 ha), rejilla de 20 m.

## Método

- Focos de calor VIIRS de NASA FIRMS.
- Imágenes Sentinel-2 L2A.
- dNBR (diferencia del índice NBR antes/después) con máscara de nubes SCL.
- Cruce con ESA WorldCover para identificar la cobertura del suelo.

## Tres hallazgos

1. Se quemaron 1 690 ha (dNBR ≥ 0,10), el 31 % de las 5 399 ha analizadas.
2. El 72,4 % de lo quemado era pastizal; bosque, 0,1 ha; cultivo, cero.
3. La medición da 43 % menos que lo que sugerían los focos, cuya envolvente apuntaba a 2 957 ha.

La historia completa está en la página [index.html](index.html)
(publicada en https://gabriela-pozo.github.io/incendios-peru/ cuando se active GitHub Pages).

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

## Limitaciones

- Un foco de calor es un píxel de 375 m donde un satélite detectó fuego, incluidas
  quemas agrícolas. No es un incendio y no es una hectárea.
- La cifra de hectáreas depende de cuatro decisiones: fechas, nubes, umbral y zona.
  Solo el umbral la mueve entre 34 y 2 008 ha (ver "Sensibilidad al umbral").
- VIIRS no detecta de forma confiable incendios pequeños, bajo dosel cerrado o
  cubiertos por nubes.
- WorldCover es de 2021, así que la cobertura pudo cambiar antes del incendio.
- Herramienta independiente con datos públicos; no reemplaza los reportes del
  COEN, INDECI, SERFOR ni SERNANP.
