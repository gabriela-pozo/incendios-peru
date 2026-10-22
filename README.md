# Incendios Perú

## Pregunta

¿Cuántas hectáreas se quemaron en el incendio de ______ y qué tipo de suelo era?

## Datos y fechas

Pendiente.

## Método

- Focos de calor VIIRS de NASA FIRMS.
- Imágenes Sentinel-2 L2A.
- dNBR (diferencia del índice NBR antes/después) con máscara de nubes SCL.
- Cruce con ESA WorldCover para identificar la cobertura del suelo.

## Tres hallazgos

Pendiente.

## Mapa

Pendiente.

## Limitaciones

- Un foco de calor es un píxel de 375 m donde un satélite detectó fuego, incluidas
  quemas agrícolas. No es un incendio y no es una hectárea.
- La cifra de hectáreas depende de cuatro decisiones: fechas, nubes, umbral y zona.
- VIIRS no detecta de forma confiable incendios pequeños, bajo dosel cerrado o
  cubiertos por nubes.
- WorldCover es de 2021, así que la cobertura pudo cambiar antes del incendio.
- Herramienta independiente con datos públicos; no reemplaza los reportes del
  COEN, INDECI, SERFOR ni SERNANP.
