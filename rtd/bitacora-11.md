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

<table>
  <tr><th>Iteración 1: prod_20260614_001</th><th></th></tr>
  <tr><td>Objetivo<br>Realizar una primera prueba de funcionamiento del pipeline del módulo 05, sobre un lote de 10 registros.</td><td>Resumen operativo<br>Filas insertadas en MySQL application_train	10<br>Filas refrescadas en data_arch_dw.application_train: 10<br>Filas refrescadas en data_arch_dw.rep_application_train: 10<br>Filas persistidas en data_arch_dw.ml_predictions: 30<br>Storage ClickHouse data_arch_dw.ml_predictions: 4.474 bytes</td></tr>
  <tr><td colspan="2">Resumen por modelo<br><table>
  <tr><th>Modelo</th><th>Pred. 0</th><th>Pred. 1</th><th>Segundos</th><th>ROC-AUC</th><th>PR-AUC</th></tr>
  <tr><td>xgboost</td><td>10</td><td>0</td><td>1,3195</td><td>0,6875</td><td>0,4167</td></tr>
  <tr><td>tabpfn_mix</td><td>10</td><td>0</td><td>6,8484</td><td>0,8125</td><td>0,7000</td></tr>
  <tr><td>pyod_autoencoder</td><td>9</td><td>1</td><td>6,1614</td><td>0,4375</td><td>0,2500</td></tr>
</table></td></tr>
</table>

<table>
  <tr><th>Iteración 2: prod_20260615_1000</th><th></th></tr>
  <tr><td>Objetivo<br>Ejecutar las inferencias del módulo sobre un lote más representativo, de 1.000 registros. Evaluar que el selector de registros desestime los primeros 10 registros ya procesado en la iteración anterior. Evaluar el funcionamiento de los modelos seleccionados para el despliegue. Evaluar el impacto en ClickHouse y Apache Superset.<br>Los tres modelos se aplicaron sobre el mismo conjunto de 1000 SK_ID_CURR, permitiendo comparación directa entre resultados.</td><td>Resumen operativo<br>Filas insertadas en MySQL application_train: 1000<br>Rango holdout_rank: 11-1010<br>Filas refrescadas en data_arch_dw.application_train: 1000<br>Filas refrescadas en data_arch_dw.rep_application_train: 1000<br>Filas persistidas en data_arch_dw.ml_predictions: 3000<br>Tiempo inserción MySQL: 0,582203 s<br>Tiempo refresh DW: 0,188220 s</td></tr>
  <tr><td colspan="2">Resumen por modelo<br><table>
  <tr><th>Modelo</th><th>Filas</th><th>Segundos</th><th>Filas/s</th><th>ms/fila</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th><th>PR-AUC</th></tr>
  <tr><td>xgboost</td><td>1000</td><td>3,84</td><td>326,34</td><td>3,06</td><td>0,7500</td><td>0,0405</td><td>0,0769</td><td>0,7750</td><td>0,2520</td></tr>
  <tr><td>tabpfn_mix</td><td>1000</td><td>9,74</td><td>142,39</td><td>7,02</td><td>0,0000</td><td>0,0000</td><td>0,0000</td><td>0,7048</td><td>0,1775</td></tr>
  <tr><td>pyod_autoencoder</td><td>1000</td><td>8,15</td><td>225,33</td><td>4,43</td><td>0,0696</td><td>0,1081</td><td>0,0847</td><td>0,4574</td><td>0,0680</td></tr>
</table></td></tr>
  <tr><td colspan="2">Distribución de predicciones<br><table>
  <tr><th>Modelo</th><th>Pred. 0</th><th>Pred. 1</th><th>Total</th></tr>
  <tr><td>xgboost</td><td>996</td><td>4</td><td>1000</td></tr>
  <tr><td>tabpfn_mix</td><td>999</td><td>1</td><td>1000</td></tr>
  <tr><td>pyod_autoencoder</td><td>885</td><td>115</td><td>1000</td></tr>
</table></td></tr>
</table>

<table>
  <tr><th>Iteración 3: prod_20260615_211402</th><th></th></tr>
  <tr><td>Objetivo<br>Ejecutar un segundo lote representativo de 1.000 registros.</td><td>Resumen operativo<br>Filas insertadas en MySQL application_train: 1000<br>Rango holdout_rank: 1011-2010<br>Filas refrescadas en data_arch_dw.application_train: 1000<br>Filas refrescadas en data_arch_dw.rep_application_train: 1000<br>Filas persistidas en data_arch_dw.ml_predictions: 3000<br>Tiempo inserción MySQL: 0,660997 s<br>Tiempo refresh DW: 0,182532 s</td></tr>
  <tr><td colspan="2">Resumen por modelo<br><table>
  <tr><th>Modelo</th><th>Filas</th><th>Segundos</th><th>Filas/s</th><th>ms/fila</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th><th>PR-AUC</th></tr>
  <tr><td>xgboost</td><td>1000</td><td>3,63</td><td>360,75</td><td>2,77</td><td>0,5000</td><td>0,0556</td><td>0,1000</td><td>0,7537</td><td>0,2271</td></tr>
  <tr><td>tabpfn_mix</td><td>1000</td><td>9,83</td><td>141,98</td><td>7,04</td><td>0,0000</td><td>0,0000</td><td>0,0000</td><td>0,6622</td><td>0,1496</td></tr>
  <tr><td>pyod_autoencoder</td><td>1000</td><td>8,22</td><td>223,79</td><td>4,46</td><td>0,0755</td><td>0,1111</td><td>0,0899</td><td>0,4943</td><td>0,0707</td></tr>
</table></td></tr>
  <tr><td colspan="2">Distribución de predicciones persistidas<br><table>
  <tr><th>Modelo</th><th>Pred. 0</th><th>Pred. 1</th><th>Total</th></tr>
  <tr><td>xgboost</td><td>992</td><td>8</td><td>1000</td></tr>
  <tr><td>tabpfn_mix</td><td>996</td><td>4</td><td>1000</td></tr>
  <tr><td>pyod_autoencoder</td><td>894</td><td>106</td><td>1000</td></tr>
</table></td></tr>
</table>

<table>
  <tr><th>Iteración 4: prod_20260615_212056</th><th></th></tr>
  <tr><td>Objetivo<br>Ejecutar un tercer lote representativo de 1.000 registros.</td><td>Resumen operativo<br>Filas insertadas en MySQL application_train: 1000<br>Rango holdout_rank: 2011-3010<br>Filas refrescadas en data_arch_dw.application_train: 1000<br>Filas refrescadas en data_arch_dw.rep_application_train: 1000<br>Filas persistidas en data_arch_dw.ml_predictions: 3000<br>Tiempo inserción MySQL: 0,567967 s<br>Tiempo refresh DW: 0,223786 s</td></tr>
  <tr><td colspan="2">Resumen por modelo<br><table>
  <tr><th>Modelo</th><th>Filas</th><th>Segundos</th><th>Filas/s</th><th>ms/fila</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th><th>PR-AUC</th></tr>
  <tr><td>xgboost</td><td>1000</td><td>3,38</td><td>366,15</td><td>2,73</td><td>0,4444</td><td>0,0533</td><td>0,0952</td><td>0,7950</td><td>0,2945</td></tr>
  <tr><td>tabpfn_mix</td><td>1000</td><td>9,95</td><td>139,13</td><td>7,18</td><td>0,5000</td><td>0,0133</td><td>0,0260</td><td>0,6813</td><td>0,1599</td></tr>
  <tr><td>pyod_autoencoder</td><td>1000</td><td>8,24</td><td>222,66</td><td>4,49</td><td>0,0734</td><td>0,1067</td><td>0,0870</td><td>0,4849</td><td>0,0779</td></tr>
</table></td></tr>
  <tr><td colspan="2">Distribución de predicciones persistidas<br><table>
  <tr><th>Modelo</th><th>Pred. 0</th><th>Pred. 1</th><th>Total</th></tr>
  <tr><td>xgboost</td><td>991</td><td>9</td><td>1000</td></tr>
  <tr><td>tabpfn_mix</td><td>998</td><td>2</td><td>1000</td></tr>
  <tr><td>pyod_autoencoder</td><td>891</td><td>109</td><td>1000</td></tr>
</table></td></tr>
</table>

<table>
  <tr><th>Iteración 5: prod_20260625_015311</th><th></th></tr>
  <tr><td>Objetivo<br>Ejecutar un lote ampliado de 5.000 registros para obtener una referencia adicional de métricas analíticas y operativas sobre una escala mayor a las iteraciones previas.</td><td>Resumen operativo<br>Filas insertadas en MySQL application_train: 5000<br>Rango holdout_rank: 3011-8010<br>Filas refrescadas en data_arch_dw.application_train: 5000<br>Filas refrescadas en data_arch_dw.rep_application_train: 5000<br>Filas persistidas en data_arch_dw.ml_predictions: 15000<br>Tiempo inserción MySQL: 2,086178 s<br>Tiempo refresh DW: 1,928287 s</td></tr>
  <tr><td colspan="2">Resumen por modelo<br><table>
  <tr><th>Modelo</th><th>Filas</th><th>Segundos</th><th>Filas/s</th><th>ms/fila</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th><th>PR-AUC</th></tr>
  <tr><td>xgboost</td><td>5000</td><td>5,42</td><td>1152,58</td><td>0,86</td><td>0,4583</td><td>0,0256</td><td>0,0486</td><td>0,7718</td><td>0,2750</td></tr>
  <tr><td>tabpfn_mix</td><td>5000</td><td>19,21</td><td>305,09</td><td>3,27</td><td>0,3846</td><td>0,0117</td><td>0,0226</td><td>0,6904</td><td>0,1676</td></tr>
  <tr><td>pyod_autoencoder</td><td>5000</td><td>9,87</td><td>818,93</td><td>1,22</td><td>0,0790</td><td>0,0956</td><td>0,0865</td><td>0,5022</td><td>0,0852</td></tr>
</table></td></tr>
  <tr><td colspan="2">Distribución de predicciones persistidas<br><table>
  <tr><th>Modelo</th><th>Pred. 0</th><th>Pred. 1</th><th>Total</th></tr>
  <tr><td>xgboost</td><td>4976</td><td>24</td><td>5000</td></tr>
  <tr><td>tabpfn_mix</td><td>4987</td><td>13</td><td>5000</td></tr>
  <tr><td>pyod_autoencoder</td><td>4481</td><td>519</td><td>5000</td></tr>
</table></td></tr>
</table>

<table>
  <tr><th>Iteración 6: prod_20260625_020027</th><th></th></tr>
  <tr><td>Objetivo<br>Ejecutar un lote ampliado de 10.000 registros para obtener una segunda referencia adicional de métricas analíticas y operativas sobre una escala mayor a las iteraciones previas.</td><td>Resumen operativo<br>Filas insertadas en MySQL application_train	10000<br>Rango holdout_rank: 8011-18010<br>Filas refrescadas en data_arch_dw.application_train: 10000<br>Filas refrescadas en data_arch_dw.rep_application_train: 10000<br>Filas persistidas en data_arch_dw.ml_predictions: 30000<br>Tiempo inserción MySQL: 3,696276 s<br>Tiempo refresh DW: 1,758682 s</td></tr>
  <tr><td colspan="2">Resumen por modelo<br><table>
  <tr><th>Modelo</th><th>Filas</th><th>Segundos</th><th>Filas/s</th><th>ms/fila</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th><th>PR-AUC</th></tr>
  <tr><td>xgboost</td><td>10000</td><td>6,08</td><td>1827,87</td><td>0,54</td><td>0,6042</td><td>0,0372</td><td>0,0700</td><td>0,7789</td><td>0,2572</td></tr>
  <tr><td>tabpfn_mix</td><td>10000</td><td>30,62</td><td>359,56</td><td>2,78</td><td>0,3030</td><td>0,0128</td><td>0,0246</td><td>0,7010</td><td>0,1720</td></tr>
  <tr><td>pyod_autoencoder</td><td>10000</td><td>11,53</td><td>1301,94</td><td>0,76</td><td>0,0856</td><td>0,1090</td><td>0,0959</td><td>0,5241</td><td>0,0841</td></tr>
</table></td></tr>
  <tr><td colspan="2">Distribución de predicciones persistidas<br><table>
  <tr><th>Modelo</th><th>Pred. 0</th><th>Pred. 1</th><th>Total</th></tr>
  <tr><td>xgboost</td><td>9952</td><td>48</td><td>10000</td></tr>
  <tr><td>tabpfn_mix</td><td>9967</td><td>33</td><td>10000</td></tr>
  <tr><td>pyod_autoencoder</td><td>9007</td><td>993</td><td>10000</td></tr>
</table></td></tr>
</table>
