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
- **Copernicus DEM GLO-30** (Planetary Computer), para la altitud y la región de cada incendio.
- **MCD64A1 v6.1** (MODIS, área quemada mensual, 500 m; colección `modis-64A1-061` en
  Planetary Computer), para validar el método en incendios de 2024.
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
- **Veinte casos**: el mismo pipeline (`src/medicion.py`) sobre los 20 incendios con más focos.
- **Robustez**: una decisión por vez (umbral, par de imágenes, máscara SCL, zona) y Gini con
  tres unidades espaciales.
- **Validación**: nuestro método frente a MCD64A1 en la misma zona y los mismos píxeles válidos.

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
- **Cruce con la firma nocturna.** Chichas fue muy nocturno: el 56,7 % de sus focos fueron
  de noche (70,5 % solo con S-NPP), frente al 20,1 % del Perú en la misma semana y una
  mediana de 34,3 % en los otros 19 del top 20; es el tercero más nocturno de los 20. La
  lectura "zona de quema habitual donde esta vez el fuego se escapó" exigiría recurrencia
  alta **y** firma nocturna; aquí solo se cumple la segunda. Lo más simple es que un
  incendio grande siga ardiendo de noche.

Tablas: `outputs/recurrencia_chichas.csv`, `outputs/recurrencia_noche_chichas.csv`, `outputs/focos_historicos_chichas.csv`;
polígono: `outputs/poligono_quemado_chichas.geojson`.

## De uno a veinte incendios

El mismo pipeline (búsqueda del par Sentinel-2, máscara SCL, dNBR, severidad y
WorldCover) sobre los 20 incendios con más focos de la semana. **Solo 4 de 20 se
pudieron medir.**

| # | Distrito | Región | Focos | Nocturnos | Envolvente (ha) | Quemado (ha) | Cobertura o motivo |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | Río Tambo | Amazonía | 279 | 56 % | 3 051 | — | nubes (55,4 %) |
| 2 | Curahuasi | Andes | 201 | 34 % | 3 227 | — | sin pasada |
| 3 | Chichas | Andes | 178 | 57 % | 2 957 | **1 689,5** | pastizal |
| 4 | Callería | Amazonía | 116 | 2 % | 1 530 | — | nubes (47,2 %) |
| 5 | Iparía | Amazonía | 108 | 44 % | 724 | **255,4** | bosque |
| 6 | Huanoquite | Andes | 80 | 51 % | 1 220 | — | nubes (100,0 %) |
| 7 | Nueva Requena | Amazonía | 65 | 32 % | 416 | — | nubes (77,7 %) |
| 8 | Cayna | Andes | 63 | 33 % | 724 | — | nubes (100,0 %) |
| 9 | Mazamari | Amazonía | 62 | 32 % | 793 | — | sin pasada |
| 10 | Palca | Andes | 61 | 16 % | 853 | — | nubes (100,0 %) |
| 11 | San Cristóbal | Andes | 59 | 68 % | 587 | **609,9** | pastizal |
| 12 | Santa Cruz | Amazonía | 50 | 22 % | 560 | — | nubes (100,0 %) |
| 13 | Nueva Requena | Amazonía | 49 | 33 % | 315 | — | prefiltro (18,2 %) |
| 14 | Nueva Requena | Amazonía | 48 | 33 % | 308 | — | nubes (100,0 %) |
| 15 | Curahuasi | Andes | 45 | 38 % | 475 | **306,0** | pastizal |
| 16 | Paracas | Costa | 42 | 52 % | 49 | — | sin pasada |
| 17 | San Juan de Jarpa | Andes | 42 | 0 % | 497 | — | nubes (89,4 %) |
| 18 | Caja | Andes | 39 | 56 % | 181 | — | nubes (47,5 %) |
| 19 | Ayahuanco | Andes | 39 | 67 % | 400 | — | nubes (55,1 %) |
| 20 | Ancahuasi | Andes | 36 | 47 % | 259 | — | nubes (65,7 %) |

Región: Andes si el centro del incendio está a 1 500 m o más; por debajo, Amazonía (o
Costa en departamentos sin selva). Entre paréntesis, el % de la zona inválida en la mejor
imagen posterior. "Sin pasada": ningún Sentinel-2 pasó entre el fin del fuego y el
21-oct. "Prefiltro": la imagen tenía más del 80 % de nubes en la escena completa y el
pipeline la descarta, aunque la zona estaba limpia en un 81,8 %; es un defecto del
pipeline. Río Tambo (el n.º 1) es el caso amazónico que antes se intentó medir aparte:
su mejor imagen posterior (20-oct, tile 18LXM) tiene el 55,4 % de la zona tapada.
Paracas probablemente es una fuente de calor industrial, no un incendio.

![Severidad de los cuatro incendios medibles](outputs/top20_severidad.png)

| Incendio medido | Cobertura dominante | Quemado (ha) | Severidad baja | Moderada o más | dNBR mediano | Medida vs envolvente |
|---|---|---:|---:|---:|---:|---:|
| Chichas | pastizal | 1 689,5 | 85,7 % | 14,4 % | 0,182 | -42,9 % |
| Iparía | bosque | 255,4 | 42,2 % | 57,7 % | 0,304 | -64,7 % |
| San Cristóbal | pastizal | 609,9 | 41,1 % | 58,9 % | 0,293 | 3,9 % |
| Curahuasi | pastizal | 306,0 | 56,0 % | 44,0 % | 0,254 | -35,6 % |

**a) ¿Se mide peor en la Amazonía?**

| Región | Incendios | Medidos | % medidos | Fallo: nubes | Fallo: sin pasada | Fallo: prefiltro |
|---|---:|---:|---:|---:|---:|---:|
| Amazonía | 8 | 1 | 12,5 % | 5 | 1 | 1 |
| Andes | 11 | 3 | 27,3 % | 7 | 1 | 0 |
| Costa | 1 | 0 | 0,0 % | 0 | 1 | 0 |

En la Amazonía se midió 1 de 8 (12,5 %) y en los Andes 3 de 11 (27,3 %), pero la
diferencia no es significativa (Fisher, p = 0,60), y las nubes tumbaron casi la misma
proporción en ambas regiones (62,5 % y 63,6 %). **La hipótesis no se confirma como sesgo
regional.** Lo que sí aparece es un sesgo de calendario: a mediados de octubre empiezan
las lluvias en la selva y en la sierra, y 16 de los 20 incendios más grandes no se pueden
medir. El corte de datos del 21-oct también dejó a varios con muy pocos días para tener
una imagen posterior.

**b) ¿La severidad depende de la cobertura?** La hipótesis (bosque alta, pastizal baja)
**no se respalda**: el único bosque medible, Iparía, tiene 57,7 % de severidad moderada o
más, y San Cristóbal, un pastizal, 58,9 %. Chichas es el caso atípico (14,4 %). Con un
bosque y tres pastizales no se pueden comparar distribuciones. Y aunque la hipótesis se
cumpliera, no probaría que Key y Benson esté mal calibrada para el pastizal andino: para
eso hace falta severidad medida en campo (CBI).

**c) ¿Los focos sobrestiman siempre?**

![Envolvente de focos frente a área medida](outputs/top20_envolvente_vs_medida.png)

En tres de cuatro casos la envolvente sobrestima (Iparía −64,7 %, Chichas −42,9 %,
Curahuasi −35,6 %); en San Cristóbal la medida la supera (+3,9 %). La dirección se repite,
pero el tamaño varía de casi cero a casi dos tercios: no hay un factor sistemático.

**d) ¿Los incendios nocturnos son más grandes o más severos?** No hay evidencia. Con los
cuatro medidos, Spearman entre el % de focos nocturnos y el área quemada da 0,60
(p = 0,40) y con el % de severidad moderada o más, 0,40 (p = 0,60). Con los 20 casos y
la envolvente como tamaño, −0,11 (p = 0,64).

Tablas: `outputs/medicion_top20.csv`, `outputs/top20_exito_region.csv`,
`outputs/top20_medidos_resumen.csv`, `outputs/top20_pruebas.csv`, `outputs/imagenes_riotambo.csv`.

## Robustez

**Cuánto mueve cada decisión las hectáreas de Chichas** (una por vez, las demás en su
valor base):

![Tornado de decisiones](outputs/tornado_chichas.png)

| Decisión | Opción | Hectáreas | Cambio |
|---|---|---:|---:|
| Base | 0,10 · mejor par · SCL usada · 1 km | 1 689,5 | — |
| Par de imágenes | 2.ª mejor posterior: 2026-10-20 (17,4 % inválido) | 1 276,7 | -24,4 % |
| Par de imágenes | 2.ª mejor previa: 2026-10-13 (0,0 % inválido) | 1 497,6 | -11,4 % |
| Máscara SCL | SCL permisiva | 1 689,5 | 0,0 % |
| Máscara SCL | SCL estricta | 1 473,4 | -12,8 % |
| Zona | focos + 500 m | 1 688,9 | -0,0 % |
| Zona | focos + 2 km | 1 693,1 | 0,2 % |

- **El umbral domina**: de 34 a 2 008 ha.
- **Par de imágenes**: la segunda mejor posterior (Sentinel-2B, otra órbita, el mismo
  20-oct) da 1 276,7 ha, pero tiene el 17,4 % de la zona tapada. En el área válida en
  ambas (4 449,8 ha) la diferencia es de 1 353,9 a 1 276,5 ha, un 5,7 % menos.
- **Máscara**: la permisiva no cambia nada. La estricta quita 216 ha porque Sentinel-2
  marca 178,7 ha de la cicatriz como "zona oscura" (SCL 2) y 37,4 ha como "sin clasificar"
  (SCL 7): borra parte del propio incendio. Es un artefacto, no incertidumbre real.
- **Zona**: casi irrelevante (1 688,9 a 1 693,1 ha); la cicatriz cabe entera en los tres buffers.

**MAUP: la concentración de focos depende de la unidad.**

| Unidad | Con focos | Gini (solo con focos) | Gini (todas) |
|---|---:|---:|---:|
| distrito | 644 de 1 815 | 0,735 | 0,906 |
| provincia | 180 de 195 | 0,737 | 0,758 |
| grilla 10 × 10 km | 1 588 de 13 464 | 0,609 | 0,954 |
| grilla 10 × 10 km desplazada 5 km | 1 595 de 13 453 | 0,607 | 0,953 |

El mismo conjunto de focos da un Gini entre 0,607 y 0,954 según la unidad y el
denominador. **La concentración depende de la unidad elegida**, así que cualquier frase
del tipo "los focos están muy concentrados" debe decir con qué unidad se midió. Desplazar
la grilla 5 km casi no cambia el resultado (0,609 frente a 0,607). Una versión anterior
reportaba 0,733 por distrito; con estos datos y la fórmula estándar sale 0,735 (644
distritos con focos), y no se pudo reproducir el 0,733.

Tablas: `outputs/robustez_chichas.csv`, `outputs/robustez_diagnostico.csv`,
`outputs/tornado_chichas.csv`, `outputs/gini_maup.csv`.

## Validación contra MCD64A1

MCD64A1 de octubre de 2026 aún no existe, así que se validó el **método** en incendios de
2024-2025. Regla fijada antes de ver resultados: grupos de focos S-NPP (confianza
nominal/alta, tipo vegetación) de junio a noviembre, ordenados por número de focos; los
3 primeros medibles. Comparación en la misma zona y los mismos píxeles válidos.

![Validación contra MCD64A1](outputs/validacion_mcd64a1.png)

| Muestra | n | Razón mediana (nuestro / MCD64A1) | Rango | Chichas corregida (ha) |
|---|---:|---:|---:|---:|
| 3 casos (regla fijada) | 3 | 1,048 | 1,016-1,198 | 1 612 |
| 21 candidatos medibles | 21 | 1,171 | 0,678-2,018 | 1 443 |
| solo pastizal dominante | 1 | 1,171 | 1,171-1,171 | 1 443 |

Los 3 casos de la regla son bosque amazónico de septiembre de 2024: nuestro método da
entre +1,6 % y +19,8 % (mediana +4,8 %). Tres casos subestiman la dispersión: en los 21
candidatos medibles (misma regla, sin elegir) la razón va de 0,678 a 2,018, con mediana
1,171 (+17,1 %). **Nuestro método tiende a dar más que MCD64A1.**

**Factor de corrección declarado:** con el sesgo mediano de los 21 casos, Chichas pasaría
de 1 690 a **1 443 ha** (1 612 ha con los 3 de la regla). Se reporta como cifra alternativa,
no reemplaza a la principal: casi toda la validación es en bosque amazónico (un solo
pastizal, razón 1,171); MCD64A1 tiene píxeles de 500 m y no es verdad de campo; y varios de
los 21 candidatos se solapan en el espacio, así que no son independientes. En septiembre de
2024 fueron medibles 21 de 24 candidatos, frente a 4 de 20 en octubre de 2026, aunque los de
2024 tenían 20 días para conseguir imagen posterior y los de 2026, como mucho 7.

Tablas: `outputs/validacion_mcd64a1.csv`, `outputs/validacion_candidatos.csv`,
`outputs/validacion_resumen.csv`.

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

## Qué no se pudo hacer

- **Medir 16 de los 20 incendios más grandes**: 12 por nubes, 3 porque ningún Sentinel-2
  pasó antes del corte de datos y 1 por el prefiltro de nubes de escena del pipeline.
- **Contrastar bosque contra pastizal**: solo un bosque fue medible (Iparía).
- **Validar en pastizal andino**: 20 de los 21 casos de validación son de bosque
  amazónico, y MCD64A1 de octubre de 2026 aún no existe.
- **Probar mala calibración de Key y Benson**: requiere severidad medida en campo (CBI).
- **Reproducir el Gini de 0,733**: con estos datos sale 0,735.
- **Recurrencia completa de 2026**: el archivo anual no existe y, sin MAP_KEY de FIRMS,
  la barra de 2026 cubre solo 8 días.
- **Literatura andina**: no se halló ningún estudio de dNBR con validación de campo en
  puna o páramo. Tampoco se pudo confirmar la conclusión de Roy et al. (2006), solo qué
  evaluaron.

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
- Cuatro casos medidos de veinte: las nubes de octubre dejaron fuera a la mayoría y solo
  un bosque fue medible.
- La validación es casi toda en bosque y contra un producto de 500 m, no contra datos de campo.
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
python src/paso8_top20.py        # mismo pipeline sobre los 20 incendios con más focos
python src/paso9_analisis_top20.py  # éxito por región, severidad, envolvente, noche
python src/paso10_robustez.py    # Gini con tres unidades + tornado de Chichas
python src/paso11_recurrencia_noche.py  # cruce recurrencia × firma nocturna (tras pasos 6 y 8)
python src/paso12_validacion.py  # validación contra MCD64A1 (usa el archivo del paso 6)
```

Los pasos 2 a 12 dependen de `outputs/focos_peru.csv`, que genera el paso 1. Las
descargas se guardan en `data/raw/` y los resultados por incendio de los pasos 8 y 12 en
`data/cache/` (ninguno versionado); no se repiten si ya existen. Los pasos 8 y 12 corren
en paralelo (6 hilos) y tardan unos 2 y 5 minutos.

**Ojo:** el CSV de 7 días de FIRMS cambia cada día. Si el paso 1 descarga los archivos
de nuevo, los focos e identificadores de incendio (Chichas = 1052, Río Tambo = 30) ya
no serán los mismos. Para reproducir estas cifras hacen falta los tres
`data/raw/firms_*_SA_7d.csv` descargados el 21-oct-2026; con el `outputs/focos_peru.csv`
versionado se pueden correr los pasos 2 a 12 sin el paso 1.
