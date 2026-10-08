# Bitácora 11: Inferencia y evaluación productiva

## Objetivo

Esta bitácora registra las sucesivas iteraciones de inferencia ejecutadas en el entorno productivo simulado, con el propósito de evaluar el comportamiento de los modelos seleccionados sobre lotes de distinto tamaño y analizar conjuntamente su desempeño predictivo y operativo. 

## Resumen de las iteraciones ejecutadas

A continuación, se detalla un resumen de las iteraciones de despliegue ejecutadas:

<table>
  <tr><th>Run ID</th><th>Filas</th><th>ID Min</th><th>ID Max</th><th>Observaciones</th></tr>
  <tr><td>prod_20260614_001</td><td>10</td><td>421550</td><td>421563</td><td>Inserción MySQL, refresh DW, inferencia, métricas TARGET y storage completados</td></tr>
  <tr><td>prod_20260615_1000</td><td>1000</td><td>421564</td><td>422693</td><td>Batch representativo desde rank 11; 1000 filas por modelo persistidas en ClickHouse</td></tr>
  <tr><td>prod_20260615_211402</td><td>1000</td><td>422694</td><td>423838</td><td>Tercer batch de 1000 filas nuevas; rank 1011-2010</td></tr>
  <tr><td>prod_20260615_212056</td><td>1000</td><td>423839</td><td>424992</td><td>Cuarto batch de 1000 filas nuevas; rank 2011-3010</td></tr>
  <tr><td>prod_20260625_015311</td><td>5000</td><td>424993</td><td>430680</td><td>Quinto batch de 5000 filas nuevas; rank 3011-8010</td></tr>
  <tr><td>prod_20260625_020027</td><td>10000</td><td>430681</td><td>442381</td><td>Sexto batch de 10000 filas nuevas; rank 8011-18010</td></tr>
</table>

Se detallan las métricas analíticas y operativas para cada iteración:

<table>
  <tr><th>Run ID</th><th>Modelo</th><th>Filas</th><th>Segundos</th><th>Filas/s</th><th>ROC-AUC</th><th>PR-AUC</th><th>F1</th></tr>
  <tr><td>prod_20260614_001</td><td>xgboost</td><td>10</td><td>1,31</td><td>14,18</td><td>0,6875</td><td>0,4167</td><td>0,0000</td></tr>
  <tr><td>prod_20260614_001</td><td>tabpfn_mix</td><td>10</td><td>6,84</td><td>2,44</td><td>0,8125</td><td>0,7000</td><td>0,0000</td></tr>
  <tr><td>prod_20260614_001</td><td>pyod_autoencoder</td><td>10</td><td>6,16</td><td>4,25</td><td>0,4375</td><td>0,2500</td><td>0,0000</td></tr>
  <tr><td>prod_20260615_1000</td><td>xgboost</td><td>1000</td><td>3,84</td><td>326,34</td><td>0,7750</td><td>0,2520</td><td>0,0769</td></tr>
  <tr><td>prod_20260615_1000</td><td>tabpfn_mix</td><td>1000</td><td>9,74</td><td>142,39</td><td>0,7048</td><td>0,1775</td><td>0,0000</td></tr>
  <tr><td>prod_20260615_1000</td><td>pyod_autoencoder</td><td>1000</td><td>8,15</td><td>225,33</td><td>0,4574</td><td>0,0680</td><td>0,0847</td></tr>
  <tr><td>prod_20260615_211402</td><td>xgboost</td><td>1000</td><td>3,63</td><td>360,75</td><td>0,7537</td><td>0,2271</td><td>0,1000</td></tr>
  <tr><td>prod_20260615_211402</td><td>tabpfn_mix</td><td>1000</td><td>9,83</td><td>141,98</td><td>0,6622</td><td>0,1496</td><td>0,0000</td></tr>
  <tr><td>prod_20260615_211402</td><td>pyod_autoencoder</td><td>1000</td><td>8,22</td><td>223,79</td><td>0,4943</td><td>0,0707</td><td>0,0899</td></tr>
  <tr><td>prod_20260615_212056</td><td>xgboost</td><td>1000</td><td>3,38</td><td>366,15</td><td>0,7950</td><td>0,2945</td><td>0,0952</td></tr>
  <tr><td>prod_20260615_212056</td><td>tabpfn_mix</td><td>1000</td><td>9,95</td><td>139,13</td><td>0,6813</td><td>0,1599</td><td>0,0260</td></tr>
  <tr><td>prod_20260615_212056</td><td>pyod_autoencoder</td><td>1000</td><td>8,24</td><td>222,66</td><td>0,4849</td><td>0,0779</td><td>0,0870</td></tr>
  <tr><td>prod_20260625_015311</td><td>xgboost</td><td>5000</td><td>5,42</td><td>1152,58</td><td>0,7718</td><td>0,2750</td><td>0,0486</td></tr>
  <tr><td>prod_20260625_015311</td><td>tabpfn_mix</td><td>5000</td><td>19,21</td><td>305,09</td><td>0,6904</td><td>0,1676</td><td>0,0226</td></tr>
  <tr><td>prod_20260625_015311</td><td>pyod_autoencoder</td><td>5000</td><td>9,87</td><td>818,93</td><td>0,5022</td><td>0,0852</td><td>0,0865</td></tr>
  <tr><td>prod_20260625_020027</td><td>xgboost</td><td>10000</td><td>6,08</td><td>1827,87</td><td>0,7789</td><td>0,2572</td><td>0,0700</td></tr>
  <tr><td>prod_20260625_020027</td><td>tabpfn_mix</td><td>10000</td><td>30,62</td><td>359,56</td><td>0,7010</td><td>0,1720</td><td>0,0246</td></tr>
  <tr><td>prod_20260625_020027</td><td>pyod_autoencoder</td><td>10000</td><td>11,53</td><td>1301,94</td><td>0,5241</td><td>0,0841</td><td>0,0959</td></tr>
</table>

El siguiente detalle muestra las métricas de consumo de memoria de cada iteración:

<table>
  <tr><th>Run ID</th><th>Predicciones locales MB</th><th>Métricas MB</th><th>Modelos MB</th><th>MySQL total MB</th><th>ClickHouse total MB</th></tr>
  <tr><td>prod_20260614_001</td><td>0,008430</td><td>0,066400</td><td>1786</td><td>232</td><td>2299</td></tr>
  <tr><td>prod_20260615_1000</td><td>0,052609</td><td>0,077134</td><td>1786</td><td>232</td><td>2299</td></tr>
  <tr><td>prod_20260615_211402</td><td>0,096805</td><td>0,087860</td><td>1786</td><td>232</td><td>2300</td></tr>
  <tr><td>prod_20260615_212056</td><td>0,141024</td><td>0,098654</td><td>1786</td><td>232</td><td>2300</td></tr>
  <tr><td>prod_20260625_015311</td><td>0,339553</td><td>0,109465</td><td>1786</td><td>232</td><td>2303</td></tr>
  <tr><td>prod_20260625_020027</td><td>0,735240</td><td>0,120291</td><td>1786</td><td>232</td><td>2307</td></tr>
</table>

## Detalle de iteraciones

A continuación, se describe el objetivo, resumen operativo y resumen por modelo de cada iteración:

### Iteración 1: prod_20260614_001

**Objetivo:**

Realizar una primera prueba de funcionamiento del pipeline del módulo 05, sobre un lote de 10 registros.

**Resumen operativo:**

- Filas insertadas en MySQL application_train: 10
- Filas refrescadas en data_arch_dw.application_train: 10
- Filas refrescadas en data_arch_dw.rep_application_train: 10
- Filas persistidas en data_arch_dw.ml_predictions: 30
- Storage ClickHouse data_arch_dw.ml_predictions: 4.474 bytes

**Resumen por modelo:**

| Modelo | Pred. 0 | Pred. 1 | Segundos | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|
| xgboost | 10 | 0 | 1,3195 | 0,6875 | 0,4167 |
| tabpfn_mix | 10 | 0 | 6,8484 | 0,8125 | 0,7000 |
| pyod_autoencoder | 9 | 1 | 6,1614 | 0,4375 | 0,2500 |

### Iteración 2: prod_20260615_1000

**Objetivo:**

Ejecutar las inferencias del módulo sobre un lote más representativo, de 1.000 registros. Evaluar que el selector de registros desestime los primeros 10 registros ya procesado en la iteración anterior. Evaluar el funcionamiento de los modelos seleccionados para el despliegue. Evaluar el impacto en ClickHouse y Apache Superset.

Los tres modelos se aplicaron sobre el mismo conjunto de 1000 SK_ID_CURR, permitiendo comparación directa entre resultados.

**Resumen operativo:**

- Filas insertadas en MySQL application_train: 1000
- Rango holdout_rank: 11-1010
- Filas refrescadas en data_arch_dw.application_train: 1000
- Filas refrescadas en data_arch_dw.rep_application_train: 1000
- Filas persistidas en data_arch_dw.ml_predictions: 3000
- Tiempo inserción MySQL: 0,582203 s
- Tiempo refresh DW: 0,188220 s

**Resumen por modelo:**

| Modelo | Filas | Segundos | Filas/s | ms/fila | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| xgboost | 1000 | 3,84 | 326,34 | 3,06 | 0,7500 | 0,0405 | 0,0769 | 0,7750 | 0,2520 |
| tabpfn_mix | 1000 | 9,74 | 142,39 | 7,02 | 0,0000 | 0,0000 | 0,0000 | 0,7048 | 0,1775 |
| pyod_autoencoder | 1000 | 8,15 | 225,33 | 4,43 | 0,0696 | 0,1081 | 0,0847 | 0,4574 | 0,0680 |

**Distribución de predicciones:**

| Modelo | Pred. 0 | Pred. 1 | Total |
|---|---:|---:|---:|
| xgboost | 996 | 4 | 1000 |
| tabpfn_mix | 999 | 1 | 1000 |
| pyod_autoencoder | 885 | 115 | 1000 |

### Iteración 3: prod_20260615_211402

**Objetivo:**

Ejecutar un segundo lote representativo de 1.000 registros.

**Resumen operativo:**

- Filas insertadas en MySQL application_train: 1000
- Rango holdout_rank: 1011-2010
- Filas refrescadas en data_arch_dw.application_train: 1000
- Filas refrescadas en data_arch_dw.rep_application_train: 1000
- Filas persistidas en data_arch_dw.ml_predictions: 3000
- Tiempo inserción MySQL: 0,660997 s
- Tiempo refresh DW: 0,182532 s

**Resumen por modelo:**

| Modelo | Filas | Segundos | Filas/s | ms/fila | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| xgboost | 1000 | 3,63 | 360,75 | 2,77 | 0,5000 | 0,0556 | 0,1000 | 0,7537 | 0,2271 |
| tabpfn_mix | 1000 | 9,83 | 141,98 | 7,04 | 0,0000 | 0,0000 | 0,0000 | 0,6622 | 0,1496 |
| pyod_autoencoder | 1000 | 8,22 | 223,79 | 4,46 | 0,0755 | 0,1111 | 0,0899 | 0,4943 | 0,0707 |

**Distribución de predicciones persistidas:**

| Modelo | Pred. 0 | Pred. 1 | Total |
|---|---:|---:|---:|
| xgboost | 992 | 8 | 1000 |
| tabpfn_mix | 996 | 4 | 1000 |
| pyod_autoencoder | 894 | 106 | 1000 |

### Iteración 4: prod_20260615_212056

**Objetivo:**

Ejecutar un tercer lote representativo de 1.000 registros.

**Resumen operativo:**

- Filas insertadas en MySQL application_train: 1000
- Rango holdout_rank: 2011-3010
- Filas refrescadas en data_arch_dw.application_train: 1000
- Filas refrescadas en data_arch_dw.rep_application_train: 1000
- Filas persistidas en data_arch_dw.ml_predictions: 3000
- Tiempo inserción MySQL: 0,567967 s
- Tiempo refresh DW: 0,223786 s

**Resumen por modelo:**

| Modelo | Filas | Segundos | Filas/s | ms/fila | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| xgboost | 1000 | 3,38 | 366,15 | 2,73 | 0,4444 | 0,0533 | 0,0952 | 0,7950 | 0,2945 |
| tabpfn_mix | 1000 | 9,95 | 139,13 | 7,18 | 0,5000 | 0,0133 | 0,0260 | 0,6813 | 0,1599 |
| pyod_autoencoder | 1000 | 8,24 | 222,66 | 4,49 | 0,0734 | 0,1067 | 0,0870 | 0,4849 | 0,0779 |

**Distribución de predicciones persistidas:**

| Modelo | Pred. 0 | Pred. 1 | Total |
|---|---:|---:|---:|
| xgboost | 991 | 9 | 1000 |
| tabpfn_mix | 998 | 2 | 1000 |
| pyod_autoencoder | 891 | 109 | 1000 |

### Iteración 5: prod_20260625_015311

**Objetivo:**

Ejecutar un lote ampliado de 5.000 registros para obtener una referencia adicional de métricas analíticas y operativas sobre una escala mayor a las iteraciones previas.

**Resumen operativo:**

- Filas insertadas en MySQL application_train: 5000
- Rango holdout_rank: 3011-8010
- Filas refrescadas en data_arch_dw.application_train: 5000
- Filas refrescadas en data_arch_dw.rep_application_train: 5000
- Filas persistidas en data_arch_dw.ml_predictions: 15000
- Tiempo inserción MySQL: 2,086178 s
- Tiempo refresh DW: 1,928287 s

**Resumen por modelo:**

| Modelo | Filas | Segundos | Filas/s | ms/fila | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| xgboost | 5000 | 5,42 | 1152,58 | 0,86 | 0,4583 | 0,0256 | 0,0486 | 0,7718 | 0,2750 |
| tabpfn_mix | 5000 | 19,21 | 305,09 | 3,27 | 0,3846 | 0,0117 | 0,0226 | 0,6904 | 0,1676 |
| pyod_autoencoder | 5000 | 9,87 | 818,93 | 1,22 | 0,0790 | 0,0956 | 0,0865 | 0,5022 | 0,0852 |

**Distribución de predicciones persistidas:**

| Modelo | Pred. 0 | Pred. 1 | Total |
|---|---:|---:|---:|
| xgboost | 4976 | 24 | 5000 |
| tabpfn_mix | 4987 | 13 | 5000 |
| pyod_autoencoder | 4481 | 519 | 5000 |

### Iteración 6: prod_20260625_020027

**Objetivo:**

Ejecutar un lote ampliado de 10.000 registros para obtener una segunda referencia adicional de métricas analíticas y operativas sobre una escala mayor a las iteraciones previas.

**Resumen operativo:**

- Filas insertadas en MySQL application_train: 10000
- Rango holdout_rank: 8011-18010
- Filas refrescadas en data_arch_dw.application_train: 10000
- Filas refrescadas en data_arch_dw.rep_application_train: 10000
- Filas persistidas en data_arch_dw.ml_predictions: 30000
- Tiempo inserción MySQL: 3,696276 s
- Tiempo refresh DW: 1,758682 s

**Resumen por modelo:**

| Modelo | Filas | Segundos | Filas/s | ms/fila | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| xgboost | 10000 | 6,08 | 1827,87 | 0,54 | 0,6042 | 0,0372 | 0,0700 | 0,7789 | 0,2572 |
| tabpfn_mix | 10000 | 30,62 | 359,56 | 2,78 | 0,3030 | 0,0128 | 0,0246 | 0,7010 | 0,1720 |
| pyod_autoencoder | 10000 | 11,53 | 1301,94 | 0,76 | 0,0856 | 0,1090 | 0,0959 | 0,5241 | 0,0841 |

**Distribución de predicciones persistidas:**

| Modelo | Pred. 0 | Pred. 1 | Total |
|---|---:|---:|---:|
| xgboost | 9952 | 48 | 10000 |
| tabpfn_mix | 9967 | 33 | 10000 |
| pyod_autoencoder | 9007 | 993 | 10000 |
