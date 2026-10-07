# Bitácora 9: Optimización de hiperparámetros

## Objetivo

Esta bitácora documenta las ejecuciones destinadas a optimizar los hiperparámetros de los modelos seleccionados, registrando los espacios de búsqueda utilizados, las configuraciones evaluadas, las mejoras obtenidas respecto de los modelos iniciales y las restricciones operativas observadas, con el propósito de seleccionar configuraciones adecuadas para las etapas posteriores de evaluación y despliegue. 

## Configuraciones y restricciones consideradas

Los resultados se almacenaron en data/ml_outputs/metrics/.

Se mantuvieron excluidas de la optimización:

- tabpfn_3: no ejecutado por dependencia de licencia/token TabPFN.

- mitra: no ejecutado por restricciones operativas de CPU/memoria observadas durante entrenamiento.

Configuraciones comunes:

<table>
  <tr><th>Campo</th><th>Valor</th></tr>
  <tr><td>Dataset</td><td>data/ml_outputs/features/application_train_features.parquet</td></tr>
  <tr><td>Filas del dataset</td><td>277.511</td></tr>
  <tr><td>Columnas del dataset</td><td>520</td></tr>
  <tr><td>Entidad principal</td><td>SK_ID_CURR</td></tr>
  <tr><td>Target</td><td>TARGET</td></tr>
  <tr><td>Random state</td><td>42</td></tr>
  <tr><td>Test size</td><td>0.2</td></tr>
  <tr><td>Validation size</td><td>0.2</td></tr>
  <tr><td>Split estratificado</td><td>true</td></tr>
  <tr><td>Trials por modelo</td><td>20</td></tr>
  <tr><td>Timeout</td><td>null</td></tr>
  <tr><td>Optimizador</td><td>Optuna, estudio en memoria</td></tr>
  <tr><td>Metrica objetivo</td><td>validation_pr_auc</td></tr>
  <tr><td>Direccion</td><td>Maximizar</td></tr>
</table>

## Comparación de resultados

<table>
  <tr><th>Modelo</th><th>Estado</th><th>Intentos</th><th>PR-AUC<br>Modelo inicial</th><th>PR-AUC<br>Optimizado</th><th>Delta</th><th>Mejor intento</th><th>Mejores hiperparametros</th><th>Duracion aproximada</th></tr>
  <tr><td>random_forest</td><td>Exitosa</td><td>20</td><td>0,2057</td><td>0,2077</td><td>+0,0020</td><td>15</td><td>n_estimators=399, max_depth=10</td><td>21m 01s</td></tr>
  <tr><td>xgboost</td><td>Exitosa</td><td>20</td><td>0,2697</td><td>0,2708</td><td>+0,0010</td><td>12</td><td>n_estimators=485, max_depth=4, learning_rate=0,0655456399</td><td>17m 30s</td></tr>
  <tr><td>local_neural_net</td><td>Exitosa</td><td>20</td><td>0,1624</td><td>0,2356</td><td>+0,0732</td><td>14</td><td>epochs=5, learning_rate=0,0001670308</td><td>25m 31s</td></tr>
  <tr><td>tabicl</td><td>Exitosa, muestra 2.000</td><td>6</td><td>0,1652</td><td>0,1684</td><td>+0,0032</td><td>0</td><td>n_estimators=2, batch_size=2</td><td>27m 01s</td></tr>
  <tr><td>tabpfn_mix</td><td>Exitosa, muestra 2.000</td><td>6</td><td>0,2824</td><td>0,2824</td><td>+0,0000</td><td>0</td><td>max_epochs=0, n_ensembles=1</td><td>56s</td></tr>
  <tr><td>pyod_autoencoder</td><td>Exitosa, muestra 2.000</td><td>8</td><td>0,1083</td><td>0,1129</td><td>+0,0046</td><td>0</td><td>contamination=0,05, epoch_num=10, hidden_neuron_list=[64, 32, 32, 64]</td><td>9s</td></tr>
</table>

## Ejecuciones

A continuación, se presentan los resultados de cada iteración de optimización:

<table>
  <tr><th>Ejecución 1: Random Forest</th><th></th></tr>
  <tr><td>Espacio de hiperparametros<br><table>
  <tr><th>Parametro</th><th>Rango</th></tr>
  <tr><td>n_estimators</td><td>Entero entre 50 y 400</td></tr>
  <tr><td>max_depth</td><td>Entero entre 3 y 20</td></tr>
</table></td><td>Mejor resultado<br><table>
  <tr><th>Campo</th><th>Valor</th></tr>
  <tr><td>Mejor trial</td><td>15</td></tr>
  <tr><td>validation_pr_auc</td><td>0,2077</td></tr>
  <tr><td>n_estimators</td><td>399</td></tr>
  <tr><td>max_depth</td><td>10</td></tr>
  <tr><td>Duracion aproximada</td><td>21m 01s</td></tr>
</table></td></tr>
  <tr><td>Hallazgos<br>El mejor resultado obtenido mejora levemente el baseline de entrenamiento inicial (0,205659 -&gt; 0,207706).<br>Las profundidades bajas (max_depth 4-7) rindieron peor.<br>Las profundidades altas observadas (max_depth 16-20) tampoco mejoraron el mejor resultado.<br>La zona mas competitiva estuvo alrededor de max_depth 9-10.<br>No hubo fallos de ejecución.<br>El tuning fue costoso para la pequeña mejora obtenida, especialmente porque el modelo usa n_jobs=-1 y cada búsqueda reentrena sobre el dataset completo.<br>No se observaron fallos de memoria durante esta ejecución.</td><td></td></tr>
</table>

<table>
  <tr><th>Ejecución 2: XGBoost</th><th></th></tr>
  <tr><td>Espacio de hiperparametros<br><table>
  <tr><th>Parametro</th><th>Rango</th></tr>
  <tr><td>n_estimators</td><td>Entero entre 50 y 500</td></tr>
  <tr><td>max_depth</td><td>Entero entre 2 y 10</td></tr>
  <tr><td>learning_rate</td><td>Float logaritmico entre 0,01 y 0,2</td></tr>
</table></td><td>Mejor resultado<br><table>
  <tr><th>Campo</th><th>Valor</th></tr>
  <tr><td>Mejor trial</td><td>12</td></tr>
  <tr><td>validation_pr_auc</td><td>0,2708</td></tr>
  <tr><td>n_estimators</td><td>485</td></tr>
  <tr><td>max_depth</td><td>4</td></tr>
  <tr><td>learning_rate</td><td>0,0655</td></tr>
  <tr><td>Duracion aproximada</td><td>17m 30s</td></tr>
</table></td></tr>
  <tr><td>Hallazgos<br>El mejor resultado supera el baseline inicial de xgboost (0,269677 -&gt; 0,270760).<br>La mejora obtenida no es significativa, pero mantiene a xgboost como el mejor modelo local de la ronda.<br>Las tasas de aprendizaje muy bajas (alrededor de 0,01-0,02) tendieron a subentrenar en el presupuesto de estimadores analizado.<br>Profundidades altas de árboles no generaron incrementos en las métricas obtenidas.<br>No hubo fallos de ejecución.<br>No se observaron fallos de memoria durante esta ejecución.</td><td></td></tr>
</table>

<table>
  <tr><th>Ejecución 3: Red neuronal</th><th></th></tr>
  <tr><td>Espacio de hiperparámetros<br><table>
  <tr><th>Parametro</th><th>Rango</th></tr>
  <tr><td>epochs</td><td>Entero entre 5 y 50</td></tr>
  <tr><td>learning_rate</td><td>Float logaritmico entre 0,0001 y 0,01</td></tr>
</table><br>La arquitectura base se mantuvo igual que en config.yml: hidden_units=[256, 128] y batch_size=512.</td><td>Mejor resultado<br><table>
  <tr><th>Campo</th><th>Valor</th></tr>
  <tr><td>Mejor trial</td><td>14</td></tr>
  <tr><td>validation_pr_auc</td><td>0,2356</td></tr>
  <tr><td>epochs</td><td>5</td></tr>
  <tr><td>learning_rate</td><td>0,0002</td></tr>
  <tr><td>Duracion aproximada</td><td>25m 31s</td></tr>
</table></td></tr>
  <tr><td>Hallazgos<br>La optimización mejoró claramente el baseline de la red neuronal (0,162387 -&gt; 0,235624).<br>Las mejores combinaciones se concentraron en pocas epocas, especialmente epochs=5.<br>Ejecuciones con muchas epocas tendieron a empeorar PR-AUC y consumir mas tiempo.<br>Aunque la mejora relativa fue grande, el modelo sigue por debajo de xgboost optimizado en validation_pr_auc.<br>La ejecucion completó con éxito los 20 intentos previstos, pero MLPClassifier emitió ConvergenceWarning en las pruebas observadas porque alcanzó el maximo de iteraciones sin converger.<br>No se observaron fallos de memoria durante esta ejecucion.</td><td></td></tr>
</table>

<table>
  <tr><th>Ejecución 4: TabICL</th><th>Esta ronda no es comparable directamente contra los modelos anteriores porque se ejecutó sobre una muestra de 2.000 registros, debido a las limitaciones observadas con algunos modelos. El split fue entonces de 1.200 filas para el conjunto de entrenamiento, 400 para el de validación y 400 para el de prueba.</th></tr>
  <tr><td>Espacio de hiperparámetros<br><table>
  <tr><th>Parámetro</th><th>Valores</th></tr>
  <tr><td>n_estimators</td><td>[2, 4, 8]</td></tr>
  <tr><td>batch_size</td><td>[2, 4]</td></tr>
  <tr><td>offload_mode</td><td>auto</td></tr>
  <tr><td>disk_offload_dir</td><td>./data/ml_outputs/<br>foundation_cache/tabicl_offload/</td></tr>
  <tr><td>verbose</td><td>true</td></tr>
</table></td><td>Mejor resultado<br><table>
  <tr><th>Campo</th><th>Valor</th></tr>
  <tr><td>Mejor trial</td><td>0</td></tr>
  <tr><td>validation_pr_auc</td><td>0,1684</td></tr>
  <tr><td>validation_roc_auc</td><td>0,6455</td></tr>
  <tr><td>n_estimators</td><td>2</td></tr>
  <tr><td>batch_size</td><td>2</td></tr>
  <tr><td>Duracion total aproximada</td><td>27m 01s</td></tr>
  <tr><td>Peak RSS maximo observado</td><td>21.261 MB</td></tr>
</table></td></tr>
  <tr><td>Hallazgos<br>El mejor resultado obtenido mejora levemente el baseline sobre la muestra de 2.000 registros (0,165246 -&gt; 0,168424).<br>Reducir n_estimators de 8 a 2 mejoro la métrica de validación PR-AUC y redujo mucho el tiempo de prediccion.<br>batch_size no cambio las metricas para un mismo n_estimators, pero con n_estimators=8 y batch_size=4 se observó el mayor pico de memoria.<br>El costo sigue concentrado en validation_predict_seconds; fit_seconds quedó alrededor de 1,6-1,8 segundos en todos los intentos.<br>Durante el preprocesamiento se generaron mensajes de advertencia por columnas completamente nulas en la muestra: previous__rate_interest_primary__std y previous__rate_interest_privileged__std.<br>No se generaron códigos por fallos de memoria, pero el pico de memoria utilizada se acercó a los 21GB observados en entrenamiento.</td><td></td></tr>
</table>

<table>
  <tr><th>Ejecución 5: TabPFNMix</th><th>Esta ronda también se hizo sobre muestra estratificada de 2.000 filas y con busqueda grid propia dentro de la imagen Docker foundation.</th></tr>
  <tr><td>Espacio de hiperparámetros<br><table>
  <tr><th>Parámetro</th><th>Valores</th></tr>
  <tr><td>max_epochs</td><td>[0, 1]</td></tr>
  <tr><td>n_ensembles</td><td>[1, 2, 4]</td></tr>
  <tr><td>dynamic_stacking</td><td>false</td></tr>
  <tr><td>num_bag_folds</td><td>0</td></tr>
  <tr><td>num_stack_levels</td><td>0</td></tr>
  <tr><td>fit_weighted_ensemble</td><td>false</td></tr>
  <tr><td>predictor_path</td><td>./data/ml_outputs/<br>models/autogluon/<br>tabpfn_mix_tuning/trial_XX/</td></tr>
</table></td><td>Mejor resultado<br><table>
  <tr><th>Campo</th><th>Valor</th></tr>
  <tr><td>Mejor trial</td><td>0</td></tr>
  <tr><td>validation_pr_auc</td><td>0,2824</td></tr>
  <tr><td>validation_roc_auc</td><td>0,6715</td></tr>
  <tr><td>max_epochs</td><td>0</td></tr>
  <tr><td>n_ensembles</td><td>1</td></tr>
  <tr><td>Duracion total aproximada</td><td>56s</td></tr>
  <tr><td>Peak RSS maximo observado</td><td>1.941 MB</td></tr>
</table></td></tr>
  <tr><td>Hallazgos<br>El baseline de entrenamiento fue la mejor combinación del espacio de búsqueda (0,282406 -&gt; 0,282406).<br>Aumentar n_ensembles con max_epochs=0 no cambió las métricas y aumento el tiempo de inferencia de validation.<br>Usar max_epochs=1 empeoró PR-AUC hasta 0,231300 en esta muestra, aunque mantuvo tiempos y memoria operables.<br>tabpfn_mix sigue siendo mucho mas eficiente que tabicl: el mayor pico de memoria fue de 1.941,055 MB frente a 21.261,246 MB en tabicl, y la ejecución completa duró menos de un minuto.<br>Durante el preprocesamiento se generaron las advertencias señaladas en el modelo anterior.<br>No hubo código 137, errores de memoria ni intentos fallidos.</td><td></td></tr>
</table>

<table>
  <tr><th>Ejecución 6: PyOD AutoEncoder</th><th>Al igual que los casos anteriores, esta ronda se ejecutó sobre una muestra estratificada de 2.000 observaciones, con búsqueda grid propia dentro de la imagen Docker foundation.</th></tr>
  <tr><td>Espacio de hiperparámetros<br><table>
  <tr><th>Parámetro</th><th>Valores</th></tr>
  <tr><td>contamination</td><td>[0,05, 0,081]</td></tr>
  <tr><td>epoch_num</td><td>[10, 20]</td></tr>
  <tr><td>hidden_neuron_list</td><td>[[64, 32, 32, 64], [128, 64, 64, 128]]</td></tr>
  <tr><td>train_normals_only</td><td>true</td></tr>
  <tr><td>batch_size</td><td>256</td></tr>
  <tr><td>learning_rate</td><td>0,001</td></tr>
  <tr><td>random_state</td><td>42</td></tr>
  <tr><td>verbose</td><td>0</td></tr>
</table></td><td>Mejor resultado<br><table>
  <tr><th>Campo</th><th>Valor</th></tr>
  <tr><td>Mejor trial</td><td>0</td></tr>
  <tr><td>validation_pr_auc</td><td>0,1129</td></tr>
  <tr><td>validation_roc_auc</td><td>0,6145</td></tr>
  <tr><td>validation_precision</td><td>0,1379</td></tr>
  <tr><td>validation_recall</td><td>0,1250</td></tr>
  <tr><td>validation_f1</td><td>0,1311</td></tr>
  <tr><td>contamination</td><td>0,05</td></tr>
  <tr><td>epoch_num</td><td>10</td></tr>
  <tr><td>hidden_neuron_list</td><td>[64, 32,<br>32, 64]</td></tr>
  <tr><td>Duracion total aproximada</td><td>9s</td></tr>
  <tr><td>Peak RSS maximo observado</td><td>974 MB</td></tr>
</table></td></tr>
  <tr><td>Hallazgos<br>El mejor resultado obtenido mejoró al obtenido del modelo baseline (0,108287 -&gt; 0,112899).<br>La arquitectura compacta [64, 32, 32, 64] fue consistentemente mejor que la arquitectura base [128, 64, 64, 128] en PR-AUC.<br>epoch_num=10 fue suficiente; aumentar a 20 no mejoró la métrica a maximizar.<br>Cambiar contamination de 0,081 a 0,05 no cambió PR-AUC para la misma arquitectura y epocas, pero si mejoro precision y F1 en el mejor intento.<br>El modelo sigue siendo muy rápido y liviano, aunque el desempeño predictivo quedó bastante por debajo de los modelos supervisados y de tabpfn_mix.<br>Durante el preprocesamiento se generaron los mensajes de advertencia por columnas completamente nulas.<br>No se obtuvo código 137, errores de memoria ni intentos fallidos.<br>El primer intento generó un mayor tiempo de fitting que los siguientes, probablemente por inicializacion/carga de PyTorch/PyOD dentro del proceso.</td><td></td></tr>
</table>

## Conclusiones

- Los modelos locales, TabICL, TabPFNMix y PyOD AutoEncoder generaron resultados válidos.

- Random Forest puede quedar como referencia documentada: la mejora fue marginal y no parece prioritaria frente a XGBoost.

- TabICL también puede quedar como referencia experimental: la mejora en la optimización fue marginal y el costo operativo sigue siendo alto.

- TabPFNMix no requiere reentrenamiento por optimización: su configuración inicial (max_epochs=0, n_ensembles=1) resultó ser el mejor resultado de la grilla y mantiene el menor costo operativo.

- PyOD AutoEncoder puede quedar como modelo base de anomalías liviano. La mejora en la etapa de optimización fue pequeña y no cambia la lectura principal: es eficiente su ejecución, a pesar de su PR-AUC relativamente débil.
