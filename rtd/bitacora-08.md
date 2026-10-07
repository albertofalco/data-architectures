# Bitácora 8: Entrenamiento inicial de modelos

## Objetivo

Esta bitácora contiene los resultados y conclusiones obtenidos a partir de las ejecuciones de entrenamiento del módulo 04_ml_development, almacenados en el directorio data/ml_outputs/.

## Familias de modelos analizadas

Se entrenaron las siguientes familias de modelos con las configuraciones que se indican a continuación:

- Random Forest: este modelo usa el objeto RandomForestClassifier de la librería scikit-learn. Es el modelo base clásico no intensivo en GPU. Permite tener una referencia robusta, relativamente interpretable y fácil de ejecutar en CPU. Configuración inicial: n_estimators=200; class_weight=balanced; n_jobs=-1. Es especialmente útil como referencia inicial porque analiza relaciones no lineales sin requerir una preparación del conjunto de datos excesivamente sofisticada.

- XGBoost: este modelo usa el objeto XGBClassifier. Representa un ejemplo fuerte de los modelos de naturaleza de potenciación del gradiente, habitualmente caracterizado como muy competitivo en problemas tabulares como riesgo crediticio. Configuración inicial: n_estimators=300; max_depth=5; learning_rate=0.05; eval_metric=logloss; tree_method=hist. Su diseño permite luego ajustar GPU o CPU según disponibilidad del ambiente.

- Red neuronal: local_neural_net representa el modelo neuronal entrenado localmente. Utiliza una arquitectura configurable con capas ocultas. Configuración inicial: hidden_units=[256, 128]; epochs=20; batch_size=512; learning_rate=0.001.

- Mitra: este modelo se integra mediante AutoGluon, con el argumento fine_tune=true. Es el modelo fundacional tabular inicial para fine tuning. Dado que AutoGluon 1.5.0 requiere una versión de Python inferior a 3.14, se recurre al uso de Docker con una versión de Python 3.13.

- TabPFN-3: este modelo utiliza la librería tabpfn. Es un modelo fundacional tabular pensado para benchmark y evaluación interna. Configuración inicial: max_rows=1000000.

- TabICL: este modelo utiliza la librería tabicl. Se incluye como modelo fundacional alternativo para benchmark experimental. Su rol inicial es comparar desempeño predictivo y operativo frente a Mitra, TabPFN-3 y los modelos baseline locales. Configuración inicial: n_estimators=8; batch_size=4; offload_mode=auto; disk_offload_dir=./data/ml_outputs/foundation_cache/tabicl_offload/.

- TabPFNMix: este modelo se integra mediante AutoGluon 1.5.0 usando el modelo autogluon/tabpfn-mix-1.0-classifier. Se agregó como alternativa fundacional más liviana que Mitra y sin el bloqueo de token/licencia observado en TabPFN-3. Configuración inicial: max_epochs=0; n_ensembles=1; dynamic_stacking=false; num_bag_folds=0; num_stack_levels=0; fit_weighted_ensemble=false; predictor_path=./data/ml_outputs/models/autogluon/tabpfn_mix/.

- PyOD AutoEncoder: este modelo usa la librería pyod y constituye un baseline neural de detección de anomalías. No es un modelo fundacional externo: entrena localmente un autoencoder para reconstruir casos normales y usa el error de reconstrucción como identificador de anomalías. Configuración inicial: train_normals_only=true; contamination=0.081; hidden_neuron_list=[128, 64, 64, 128]; epoch_num=20; batch_size=256; learning_rate=0.001; random_state=42.

## Ejecuciones

A continuación, se expone el historial de las ejecuciones por el entrenamiento inicial de los modelos. Se detallan las configuraciones y resultados obtenidos para cada iteración ejecutada:

<table>
  <tr><th>Ejecución 1: Random Forest</th><th>Fecha y hora de ejecución: 2026-06-01 21:53:31.<br>Estado: Exitosa.</th></tr>
  <tr><td>Configuración<br><table>
  <tr><th>Parámetro</th><th>Valor</th></tr>
  <tr><td>n_estimators</td><td>200</td></tr>
  <tr><td>max_depth</td><td>null</td></tr>
  <tr><td>class_weight</td><td>balanced</td></tr>
  <tr><td>n_jobs</td><td>-1</td></tr>
  <tr><td>random_state</td><td>42</td></tr>
</table></td><td>Resultados<br><table>
  <tr><th>Métrica</th><th>Valor</th></tr>
  <tr><td>preprocess_fit_seconds</td><td>13,7920</td></tr>
  <tr><td>train_seconds</td><td>58,2641</td></tr>
  <tr><td>validation_predict_seconds</td><td>1,9278</td></tr>
  <tr><td>test_predict_seconds</td><td>1,9991</td></tr>
  <tr><td>validation_roc_auc</td><td>0,7352</td></tr>
  <tr><td>validation_pr_auc</td><td>0,2057</td></tr>
  <tr><td>validation_precision</td><td>0,5714</td></tr>
  <tr><td>validation_recall</td><td>0,0009</td></tr>
  <tr><td>validation_f1</td><td>0,0018</td></tr>
  <tr><td>test_roc_auc</td><td>0,7394</td></tr>
  <tr><td>test_pr_auc</td><td>0,2074</td></tr>
  <tr><td>test_precision</td><td>0,6000</td></tr>
  <tr><td>test_recall</td><td>0,0020</td></tr>
  <tr><td>test_f1</td><td>0,0040</td></tr>
</table></td></tr>
</table>

<table>
  <tr><th>Ejecución 2: XGBoost</th><th>Fecha y hora de ejecución: 2026-06-01 22:02:01.<br>Estado: Exitosa.</th></tr>
  <tr><td>Configuración<br><table>
  <tr><th>Parámetro</th><th>Valor</th></tr>
  <tr><td>n_estimators</td><td>300</td></tr>
  <tr><td>max_depth</td><td>5</td></tr>
  <tr><td>learning_rate</td><td>0.05</td></tr>
  <tr><td>eval_metric</td><td>logloss</td></tr>
  <tr><td>tree_method</td><td>hist</td></tr>
  <tr><td>random_state</td><td>42</td></tr>
</table></td><td>Resultados<br><table>
  <tr><th>Métrica</th><th>Valor</th></tr>
  <tr><td>preprocess_fit_seconds</td><td>11,9915</td></tr>
  <tr><td>train_seconds</td><td>40,0696</td></tr>
  <tr><td>validation_predict_seconds</td><td>0,1420</td></tr>
  <tr><td>test_predict_seconds</td><td>0,1373</td></tr>
  <tr><td>validation_roc_auc</td><td>0,7773</td></tr>
  <tr><td>validation_pr_auc</td><td>0,2697</td></tr>
  <tr><td>validation_precision</td><td>0,5542</td></tr>
  <tr><td>validation_recall</td><td>0,0307</td></tr>
  <tr><td>validation_f1</td><td>0,0582</td></tr>
  <tr><td>test_roc_auc</td><td>0,7792</td></tr>
  <tr><td>test_pr_auc</td><td>0,2690</td></tr>
  <tr><td>test_precision</td><td>0,5703</td></tr>
  <tr><td>test_recall</td><td>0,0316</td></tr>
  <tr><td>test_f1</td><td>0,0599</td></tr>
</table></td></tr>
</table>

<table>
  <tr><th>Ejecución 3: Red neuronal</th><th>Fecha y hora de ejecución: 2026-06-01 22:03:20.<br>Estado: Exitosa.</th></tr>
  <tr><td>Configuración<br><table>
  <tr><th>Parámetro</th><th>Valor</th></tr>
  <tr><td>hidden_layer_sizes</td><td>(256, 128)</td></tr>
  <tr><td>max_iter</td><td>20</td></tr>
  <tr><td>batch_size</td><td>512</td></tr>
  <tr><td>learning_rate_init</td><td>0.001</td></tr>
  <tr><td>random_state</td><td>42</td></tr>
</table></td><td>Resultados<br><table>
  <tr><th>Métrica</th><th>Valor</th></tr>
  <tr><td>preprocess_fit_seconds</td><td>11,6090</td></tr>
  <tr><td>train_seconds</td><td>56,8398</td></tr>
  <tr><td>validation_predict_seconds</td><td>0,6203</td></tr>
  <tr><td>test_predict_seconds</td><td>0,5850</td></tr>
  <tr><td>validation_roc_auc</td><td>0,6662</td></tr>
  <tr><td>validation_pr_auc</td><td>0,1624</td></tr>
  <tr><td>validation_precision</td><td>0,2227</td></tr>
  <tr><td>validation_recall</td><td>0,1746</td></tr>
  <tr><td>validation_f1</td><td>0,1958</td></tr>
  <tr><td>test_roc_auc</td><td>0,6770</td></tr>
  <tr><td>test_pr_auc</td><td>0,1628</td></tr>
  <tr><td>test_precision</td><td>0,2243</td></tr>
  <tr><td>test_recall</td><td>0,1737</td></tr>
  <tr><td>test_f1</td><td>0,1958</td></tr>
</table></td></tr>
</table>

<table>
  <tr><th>Ejecución 4: TabICL</th><th>Fecha y hora de ejecución: 2026-06-05 23:46:10.<br>Estado: Fallida, código 137.</th></tr>
  <tr><td>Configuración<br><table>
  <tr><th>Campo</th><th>Valor</th></tr>
  <tr><td>Imagen</td><td>data-architectures-foundation:py313</td></tr>
  <tr><td>Python de la imagen</td><td>3.13.13</td></tr>
  <tr><td>PyTorch de la imagen</td><td>2.9.1+cu128</td></tr>
  <tr><td>CUDA visible</td><td>False</td></tr>
  <tr><td>Dataset</td><td>data/ml_outputs/features/<br>application_train_features.parquet</td></tr>
  <tr><td>Filas</td><td>277.511</td></tr>
  <tr><td>Columnas</td><td>520</td></tr>
</table></td><td>Hallazgos<br>La ejecución terminó con código 137. El código 137 indica que el proceso fue terminado por el sistema o por Docker, probablemente por un pico de memoria durante carga, preparación o entrenamiento del dataset completo en CPU.<br>No se generó modelo ni métricas.</td></tr>
  <tr><td colspan="2">Comando de entrenamiento<br>docker run --rm \<br>  --user &quot;$(id -u):$(id -g)&quot; \<br>  -v &quot;$PWD&quot;:/work \<br>  -w /work \<br>  data-architectures-foundation:py313 \<br>  python 04_ml_development/scripts/train.py --model tabicl</td></tr>
</table>

<table>
  <tr><th>Ejecución 5: TabICL</th><th>Fecha y hora de ejecución: 2026-06-06 10:01:00.<br>Estado: Fallida, código 137, muestra 10.000.</th></tr>
  <tr><td>Configuración<br><table>
  <tr><th>Campo</th><th>Valor</th></tr>
  <tr><td>Imagen</td><td>data-architectures-foundation:py313</td></tr>
  <tr><td>CUDA visible</td><td>False</td></tr>
  <tr><td>Dataset</td><td>data/ml_outputs/features/<br>application_train_features<br>_tabicl_sample_10000.parquet</td></tr>
  <tr><td>Filas</td><td>10.000</td></tr>
  <tr><td>Columnas</td><td>520</td></tr>
  <tr><td>Distribución target</td><td>{0: 9191, 1: 809}</td></tr>
</table></td><td>Hallazgos<br>La ejecución terminó con código 137.<br>No se generó objeto de modelo ni métricas.<br>La muestra estratificada de 10.000 filas supera la capacidad práctica de esta ejecución con CPU para TabICL con la configuración actual.</td></tr>
  <tr><td colspan="2">Comando de entrenamiento<br>docker run --rm \<br>  --user &quot;$(id -u):$(id -g)&quot; \<br>  -v &quot;$PWD&quot;:/work \<br>  -w /work \<br>  data-architectures-foundation:py313 \<br>  python 04_ml_development/scripts/train.py \<br>    --model tabicl \<br>    --features-path data/ml_outputs/features/application \<br>_train_features_tabicl_sample_10000.parquet</td></tr>
</table>

<table>
  <tr><th>Ejecución 6: TabICL</th><th>Fecha y hora de ejecución: 2026-06-06 10:26:51.<br>Estado: Exitosa, muestra 1.000.</th></tr>
  <tr><td>Configuración<br><table>
  <tr><th>Campo</th><th>Valor</th></tr>
  <tr><td>Imagen</td><td>data-architectures-foundation:py313</td></tr>
  <tr><td>Python de la imagen</td><td>3.13.13</td></tr>
  <tr><td>PyTorch de la imagen</td><td>2.9.1+cu128</td></tr>
  <tr><td>CUDA visible</td><td>False</td></tr>
  <tr><td>Filas de muestra</td><td>1.000</td></tr>
  <tr><td>Columnas</td><td>520</td></tr>
  <tr><td>Distribución target</td><td>{0: 919, 1: 81}</td></tr>
  <tr><td>Split train</td><td>600</td></tr>
  <tr><td>Split validation</td><td>200</td></tr>
  <tr><td>Split test</td><td>200</td></tr>
</table></td><td>Resultados<br><table>
  <tr><th>Métrica</th><th>Valor</th></tr>
  <tr><td>preprocess_fit_seconds</td><td>0,0642</td></tr>
  <tr><td>train_seconds</td><td>1,5137</td></tr>
  <tr><td>validation_predict_seconds</td><td>222,5865</td></tr>
  <tr><td>test_predict_seconds</td><td>223,2643</td></tr>
  <tr><td>validation_roc_auc</td><td>0,6277</td></tr>
  <tr><td>validation_pr_auc</td><td>0,2674</td></tr>
  <tr><td>validation_precision</td><td>0,0000</td></tr>
  <tr><td>validation_recall</td><td>0,0000</td></tr>
  <tr><td>validation_f1</td><td>0,0000</td></tr>
  <tr><td>test_roc_auc</td><td>0,7551</td></tr>
  <tr><td>test_pr_auc</td><td>0,2914</td></tr>
  <tr><td>test_precision</td><td>0,0000</td></tr>
  <tr><td>test_recall</td><td>0,0000</td></tr>
  <tr><td>test_f1</td><td>0,0000</td></tr>
</table></td></tr>
  <tr><td>Comando de entrenamiento<br>docker run --rm \<br>  --user &quot;$(id -u):$(id -g)&quot; \<br>  -v &quot;$PWD&quot;:/work \<br>  -w /work \<br>  data-architectures-foundation:py313 \<br>  python 04_ml_development/scripts/train.py \<br>    --model tabicl \<br>    --features-path data/ml_outputs/features/<br>application_train_features_tabicl_sample_1000.parquet</td><td>Hallazgos<br>La ejecución permite validar que el flujo con el modelo TabICL puede completar exitosamente en CPU con una muestra estratificada pequeña.<br>Los tiempos de predicción son altos para solo 200 filas de validation/test, por lo que TabICL en CPU no es viable todavía para dataset completo con la configuración actual.<br>Las métricas de precision, recall y F1 quedan en cero al umbral de clasificación por defecto; PR-AUC y ROC-AUC deberían revisarse junto con ajuste de umbral antes de descartar el modelo.<br>Estas métricas no son comparables directamente contra los baselines entrenados con el dataset completo.</td></tr>
</table>

<table>
  <tr><th>Ejecución 7: TabICL</th><th>Fecha y hora de ejecución: 2026-06-06 12:04:19.<br>Estado: Exitosa, muestra 2.000.</th></tr>
  <tr><td>Memoria registrada<br><table>
  <tr><th>Etapa</th><th>RSS proc. (MB)</th><th>Peak RSS proc. (MB)</th><th>Cgroup actual (MB)</th><th>Mem. sist. disp. (MB)</th></tr>
  <tr><td>Lectura de features</td><td>141</td><td>140</td><td>83</td><td>23.843</td></tr>
  <tr><td>Split</td><td>223</td><td>227</td><td>142</td><td>23.793</td></tr>
  <tr><td>Preprocessing</td><td>247</td><td>253</td><td>164</td><td>23.769</td></tr>
  <tr><td>Fit</td><td>925</td><td>924</td><td>626</td><td>23.291</td></tr>
  <tr><td>Validation predict</td><td>977</td><td>21.143</td><td>672</td><td>22.866</td></tr>
  <tr><td>Test predict</td><td>977</td><td>21.143</td><td>672</td><td>22.864</td></tr>
</table></td><td>Resultados<br><table>
  <tr><th>Métrica</th><th>Valor</th></tr>
  <tr><td>preprocess_fit_seconds</td><td>0,0995</td></tr>
  <tr><td>train_seconds</td><td>1,7537</td></tr>
  <tr><td>validation_predict_seconds</td><td>440,9531</td></tr>
  <tr><td>test_predict_seconds</td><td>442,5755</td></tr>
  <tr><td>validation_roc_auc</td><td>0,6454</td></tr>
  <tr><td>validation_pr_auc</td><td>0,1652</td></tr>
  <tr><td>validation_precision</td><td>0,3333</td></tr>
  <tr><td>validation_recall</td><td>0,0313</td></tr>
  <tr><td>validation_f1</td><td>0,0571</td></tr>
  <tr><td>test_roc_auc</td><td>0,8018</td></tr>
  <tr><td>test_pr_auc</td><td>0,2348</td></tr>
  <tr><td>test_precision</td><td>0,5000</td></tr>
  <tr><td>test_recall</td><td>0,0313</td></tr>
  <tr><td>test_f1</td><td>0,0588</td></tr>
</table></td></tr>
  <tr><td>Comando de entrenamiento<br>docker run --rm \<br>  --user &quot;$(id -u):$(id -g)&quot; \<br>  -v &quot;$PWD&quot;:/work \<br>  -w /work \<br>  data-architectures-foundation:py313 \<br>  python<br>04_ml_development/scripts/train.py \<br>--model tabicl \<br>    --features-path data/ml_outputs/features/application_train_features_tabicl_sample_2000.parquet</td><td>Hallazgos<br>La muestra de 2.000 completa exitosamente en CPU, pero la predicción sigue siendo muy lenta: alrededor de 441-443 segundos por split de 400 filas.<br>La memoria pico del proceso llegó a aproximadamente 21,1 GB durante predicción. Ello explica por qué muestras mayores pueden ocasionar cierres por falta de memoria.</td></tr>
</table>

<table>
  <tr><th>Ejecución 8: TabPFN 3</th><th>Fecha y hora de ejecución: 2026-06-06 14:50:34.<br>Fallida, licencia/token TabPFN faltante, muestra 2.000.</th></tr>
  <tr><td>Configuración<br><table>
  <tr><th>Campo</th><th>Valor</th></tr>
  <tr><td>Imagen</td><td>data-architectures-foundation:py313</td></tr>
  <tr><td>Python de la imagen</td><td>3.13.13</td></tr>
  <tr><td>PyTorch de la imagen</td><td>2.9.1+cu128</td></tr>
  <tr><td>CUDA visible</td><td>False</td></tr>
  <tr><td>Import tabpfn</td><td>Exitoso</td></tr>
  <tr><td>TABPFN_TOKEN presente</td><td>False</td></tr>
  <tr><td>TABPFN_NO_BROWSER</td><td>1</td></tr>
  <tr><td>Filas de muestra</td><td>2.000</td></tr>
  <tr><td>Columnas</td><td>520</td></tr>
  <tr><td>Distribución target</td><td>{0: 1838, 1: 162}</td></tr>
  <tr><td>Split esperado train</td><td>1.200</td></tr>
  <tr><td>Split esperado validation</td><td>400</td></tr>
  <tr><td>Split esperado test</td><td>400</td></tr>
</table></td><td>Hallazgos<br>Estado: fallida antes de completar fit.<br>Código de salida Docker: 1.<br>Error principal: tabpfn.errors.TabPFNLicenseError.<br>Causa: TabPFN requiere aceptación de licencia/token para descargar pesos de inferencia local; como TABPFN_NO_BROWSER=1 está activo y TABPFN_TOKEN no está seteado, el flujo headless queda bloqueado.<br>No se registró OOM ni código 137; esta ejecución no alcanza a evaluar presión de memoria.</td></tr>
  <tr><td colspan="2">Comando de entrenamiento<br>docker run --rm \<br>  --user &quot;$(id -u):$(id -g)&quot; \<br>  -v &quot;$PWD&quot;:/work \<br>  -w /work \<br>  -e TABPFN_TOKEN \<br>  -e TABPFN_NO_BROWSER=1 \<br>  data-architectures-foundation:py313 \<br>  python 04_ml_development/scripts/train.py \<br>    --model tabpfn_3 \<br>    --features-path data/ml_outputs/features/application_train_features_tabpfn_sample_2000.parquet</td></tr>
</table>

<table>
  <tr><th>Ejecución 9: Mitra</th><th>Fecha y hora de ejecución: 2026-06-06.<br>Estado: Parcial/cancelada, diagnósticos CPU/memoria.</th></tr>
  <tr><td>Objetivo<br>Evaluar si Mitra podía reemplazar a TabPFN sin requerir token o autenticación. Probar una ejecución liviana con fine_tune=false en CPU local.</td><td>Hallazgos<br>Mitra no tiene el bloqueo de token/licencia observado en TabPFN.<br>AutoGluon entrenó Mitra con feature_limit=256.<br>Mejor modelo interno: WeightedEnsemble_L2 con peso Mitra: 1.0.<br>Runtime reportado por AutoGluon: entrenamiento: aproximadamente 1.231 segundos; validación interna: aproximadamente 1.221 segundos; total AutoGluon: aproximadamente 2.452 segundos.<br>El pipeline quedó luego ejecutando predict / predict_proba externo sobre validation/test y fue cancelado manualmente.<br>Memoria observada por docker stats: aproximadamente 3,6 a 5,2 GiB sobre 27,81 GiB.<br>Conclusión: En CPU local no resulta práctico para este pipeline: aun con fine_tune=false y reducción a 256 features, el costo de entrenamiento/evaluación fue demasiado alto.</td></tr>
</table>

<table>
  <tr><th>Ejecución 10: TabPFN Mix</th><th>Fecha y hora de ejecución: 2026-06-06 18:18:03.<br>Estado: Exitosa.<br>Objetivo: Evaluar TabPFNMix como alternativa fundacional liviana disponible vía AutoGluon 1.5.0 y pesos públicos en Hugging Face.</th></tr>
  <tr><td>Configuración<br><table>
  <tr><th>Campo</th><th>Valor</th></tr>
  <tr><td>Imagen</td><td>data-architectures-foundation:py313</td></tr>
  <tr><td>Python de la imagen</td><td>3.13.13</td></tr>
  <tr><td>AutoGluon Tabular</td><td>1.5.0</td></tr>
  <tr><td>PyTorch de la imagen</td><td>2.9.1+cu128</td></tr>
  <tr><td>CUDA visible</td><td>False</td></tr>
  <tr><td>Filas de muestra</td><td>2.000</td></tr>
  <tr><td>Columnas</td><td>520</td></tr>
  <tr><td>Distribución target</td><td>{0: 1838, 1: 162}</td></tr>
  <tr><td>Split train</td><td>1.200</td></tr>
  <tr><td>Split validation</td><td>400</td></tr>
  <tr><td>Split test</td><td>400</td></tr>
  <tr><td>Modelo HF</td><td>autogluon/tabpfn-mix-1.0-classifier</td></tr>
  <tr><td>max_epochs</td><td>0</td></tr>
  <tr><td>n_ensembles</td><td>1</td></tr>
  <tr><td>dynamic_stacking</td><td>false</td></tr>
  <tr><td>num_bag_folds</td><td>0</td></tr>
  <tr><td>num_stack_levels</td><td>0</td></tr>
  <tr><td>fit_weighted_ensemble</td><td>false</td></tr>
  <tr><td>Ruta AutoGluon</td><td>data/ml_outputs/models/<br>autogluon/tabpfn_mix/</td></tr>
</table></td><td>Resultados<br><table>
  <tr><th>Métrica</th><th>Valor</th></tr>
  <tr><td>preprocess_fit_seconds</td><td>0,0977</td></tr>
  <tr><td>train_seconds</td><td>4,4710</td></tr>
  <tr><td>validation_predict_seconds</td><td>1,8789</td></tr>
  <tr><td>test_predict_seconds</td><td>1,8442</td></tr>
  <tr><td>validation_roc_auc</td><td>0,6715</td></tr>
  <tr><td>validation_pr_auc</td><td>0,2824</td></tr>
  <tr><td>validation_precision</td><td>0,5000</td></tr>
  <tr><td>validation_recall</td><td>0,0313</td></tr>
  <tr><td>validation_f1</td><td>0,0588</td></tr>
  <tr><td>test_roc_auc</td><td>0,6688</td></tr>
  <tr><td>test_pr_auc</td><td>0,1818</td></tr>
  <tr><td>test_precision</td><td>0,3333</td></tr>
  <tr><td>test_recall</td><td>0,0313</td></tr>
  <tr><td>test_f1</td><td>0,0571</td></tr>
</table></td></tr>
  <tr><td colspan="2">Comando de entrenamiento<br>docker run --rm \<br>  --user &quot;$(id -u):$(id -g)&quot; \<br>  -v &quot;$PWD&quot;:/work \<br>  -w /work \<br>  data-architectures-foundation:py313 \<br>  python 04_ml_development/scripts/train.py \<br>    --model tabpfn_mix \<br>    --features-path data/ml_outputs/features/application_train_features_tabpfn_mix_sample_2000.parquet</td></tr>
  <tr><td>Memoria registrada<br><table>
  <tr><th>Etapa</th><th>RSS proc. (MB)</th><th>Peak RSS proc. (MB)</th><th>Cgroup actual (MB)</th><th>Mem. Sist. Disp. (MB)</th></tr>
  <tr><td>Lectura de features</td><td>141</td><td>140</td><td>84</td><td>23.535</td></tr>
  <tr><td>Split</td><td>223</td><td>227</td><td>142</td><td>23.469</td></tr>
  <tr><td>Preprocessing</td><td>247</td><td>253</td><td>164</td><td>23.450</td></tr>
  <tr><td>Fit</td><td>1.029</td><td>1.082</td><td>847</td><td>22.800</td></tr>
  <tr><td>Validation predict</td><td>1.091</td><td>1.224</td><td>910</td><td>22.652</td></tr>
  <tr><td>Test predict</td><td>1.152</td><td>1.224</td><td>971</td><td>22.511</td></tr>
</table></td><td>Hallazgos<br>tabpfn_mix es la alternativa fundacional más limpia hasta ahora: no requiere token, entrena rápido en CPU y mantiene memoria controlada.<br>AutoGluon seleccionó internamente 100 features mediante SelectKBest porque TabPFNMix admite como máximo 100 atributos.<br>En validation obtuvo mejor PR-AUC que tabicl con muestra 2.000, aunque en el conjunto de prueba quedó por debajo de TabICL.</td></tr>
</table>

<table>
  <tr><th>Ejecución 11: PyOD AutoEncoder</th><th>Fecha y hora de ejecución: 2026-06-06 19:02.<br>Estado: Exitosa.<br>Objetivo: Evaluar un baseline neural de detección de anomalías basado en autoencoder. Entrena de forma semisupervisada usando solo casos normales (TARGET=0) y evalúa TARGET=1 como evento anómalo/riesgoso.</th></tr>
  <tr><td>Configuración<br><table>
  <tr><th>Campo</th><th>Valor</th></tr>
  <tr><td>Imagen</td><td>data-architectures-foundation:py313</td></tr>
  <tr><td>Python de la imagen</td><td>3.13.13</td></tr>
  <tr><td>PyOD</td><td>2.0.5</td></tr>
  <tr><td>PyTorch de la imagen</td><td>2.9.1+cu128</td></tr>
  <tr><td>CUDA visible</td><td>False</td></tr>
  <tr><td>Filas de muestra</td><td>2.000</td></tr>
  <tr><td>Columnas</td><td>520</td></tr>
  <tr><td>Distribución target</td><td>{0: 1838, 1: 162}</td></tr>
  <tr><td>Split train</td><td>1.200</td></tr>
  <tr><td>Split validation</td><td>400</td></tr>
  <tr><td>Split test</td><td>400</td></tr>
  <tr><td>Entrenamiento</td><td>Solo filas normales TARGET=0</td></tr>
  <tr><td>Contamination</td><td>0.081</td></tr>
  <tr><td>Hidden neurons</td><td>[128, 64, 64, 128]</td></tr>
  <tr><td>Epochs</td><td>20</td></tr>
  <tr><td>Batch size</td><td>256</td></tr>
  <tr><td>Learning rate</td><td>0.001</td></tr>
</table></td><td>Resultados<br><table>
  <tr><th>Métrica</th><th>Valor</th></tr>
  <tr><td>preprocess_fit_seconds</td><td>0,0988</td></tr>
  <tr><td>train_seconds</td><td>2,8671</td></tr>
  <tr><td>validation_predict_seconds</td><td>0,0214</td></tr>
  <tr><td>test_predict_seconds</td><td>0,0217</td></tr>
  <tr><td>validation_roc_auc</td><td>0,6077</td></tr>
  <tr><td>validation_pr_auc</td><td>0,1083</td></tr>
  <tr><td>validation_precision</td><td>0,1053</td></tr>
  <tr><td>validation_recall</td><td>0,1250</td></tr>
  <tr><td>validation_f1</td><td>0,1143</td></tr>
  <tr><td>test_roc_auc</td><td>0,5078</td></tr>
  <tr><td>test_pr_auc</td><td>0,0952</td></tr>
  <tr><td>test_precision</td><td>0,1087</td></tr>
  <tr><td>test_recall</td><td>0,1563</td></tr>
  <tr><td>test_f1</td><td>0,1282</td></tr>
</table></td></tr>
  <tr><td colspan="2">Comando de entrenamiento<br>docker run --rm \<br>  --user &quot;$(id -u):$(id -g)&quot; \<br>  -v &quot;$PWD&quot;:/work \<br>  -w /work \<br>  data-architectures-foundation:py313 \<br>  python 04_ml_development/scripts/train.py \<br>    --model pyod_autoencoder \<br>    --features-path data/ml_outputs/features/application_train_features_pyod_autoencoder_sample_2000.parquet</td></tr>
  <tr><td>Memoria registrada<br><table>
  <tr><th>Etapa</th><th>RSS proc. (MB)</th><th>Peak RSS proc. (MB)</th><th>Cgroup actual (MB)</th><th>Mem. Sist. Disp. (MB)</th></tr>
  <tr><td>Lectura de features</td><td>144</td><td>143</td><td>86</td><td>23.535</td></tr>
  <tr><td>Split</td><td>228</td><td>232</td><td>147</td><td>23.454</td></tr>
  <tr><td>Preprocessing</td><td>252</td><td>258</td><td>169</td><td>23.430</td></tr>
  <tr><td>Fit</td><td>982</td><td>981</td><td>539</td><td>23.068</td></tr>
  <tr><td>Validation predict</td><td>982</td><td>981</td><td>539</td><td>23.067</td></tr>
  <tr><td>Test predict</td><td>982</td><td>981</td><td>539</td><td>23.067</td></tr>
</table></td><td>Hallazgos<br>pyod_autoencoder es muy liviano y rápido para inferencia en CPU.<br>La señal inicial fue débil en test (test_roc_auc cercano a 0,5), por lo que no supera a tabicl, tabpfn_mix ni a los baselines supervisados.</td></tr>
</table>
