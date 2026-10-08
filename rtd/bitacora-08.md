# Bitácora 8: Entrenamiento inicial de modelos

## Objetivo

Esta bitácora registra las ejecuciones iniciales de entrenamiento de las distintas familias de modelos evaluadas en el trabajo.

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

### Ejecución 1: Random Forest

Fecha y hora de ejecución: 2026-06-01 21:53:31.  
Estado: Exitosa.

**Configuración:**

| Parámetro | Valor |
|---|---:|
| n_estimators | 200 |
| max_depth | null |
| class_weight | balanced |
| n_jobs | -1 |
| random_state | 42 |

**Resultados:**

| Métrica | Valor |
|---|---:|
| preprocess_fit_seconds | 13,7920 |
| train_seconds | 58,2641 |
| validation_predict_seconds | 1,9278 |
| test_predict_seconds | 1,9991 |
| validation_roc_auc | 0,7352 |
| validation_pr_auc | 0,2057 |
| validation_precision | 0,5714 |
| validation_recall | 0,0009 |
| validation_f1 | 0,0018 |
| test_roc_auc | 0,7394 |
| test_pr_auc | 0,2074 |
| test_precision | 0,6000 |
| test_recall | 0,0020 |
| test_f1 | 0,0040 |

### Ejecución 2: XGBoost

Fecha y hora de ejecución: 2026-06-01 22:02:01.  
Estado: Exitosa.

**Configuración:**

| Parámetro | Valor |
|---|---:|
| n_estimators | 300 |
| max_depth | 5 |
| learning_rate | 0.05 |
| eval_metric | logloss |
| tree_method | hist |
| random_state | 42 |

**Resultados:**

| Métrica | Valor |
|---|---:|
| preprocess_fit_seconds | 11,9915 |
| train_seconds | 40,0696 |
| validation_predict_seconds | 0,1420 |
| test_predict_seconds | 0,1373 |
| validation_roc_auc | 0,7773 |
| validation_pr_auc | 0,2697 |
| validation_precision | 0,5542 |
| validation_recall | 0,0307 |
| validation_f1 | 0,0582 |
| test_roc_auc | 0,7792 |
| test_pr_auc | 0,2690 |
| test_precision | 0,5703 |
| test_recall | 0,0316 |
| test_f1 | 0,0599 |

### Ejecución 3: Red neuronal

Fecha y hora de ejecución: 2026-06-01 22:03:20.  
Estado: Exitosa.

**Configuración:**

| Parámetro | Valor |
|---|---:|
| hidden_layer_sizes | (256, 128) |
| max_iter | 20 |
| batch_size | 512 |
| learning_rate_init | 0.001 |
| random_state | 42 |

**Resultados:**

| Métrica | Valor |
|---|---:|
| preprocess_fit_seconds | 11,6090 |
| train_seconds | 56,8398 |
| validation_predict_seconds | 0,6203 |
| test_predict_seconds | 0,5850 |
| validation_roc_auc | 0,6662 |
| validation_pr_auc | 0,1624 |
| validation_precision | 0,2227 |
| validation_recall | 0,1746 |
| validation_f1 | 0,1958 |
| test_roc_auc | 0,6770 |
| test_pr_auc | 0,1628 |
| test_precision | 0,2243 |
| test_recall | 0,1737 |
| test_f1 | 0,1958 |

### Ejecución 4: TabICL

Fecha y hora de ejecución: 2026-06-05 23:46:10.  
Estado: Fallida, código 137.

**Configuración:**

| Parámetro | Valor |
|---|---|
| Imagen | data-architectures-foundation:py313 |
| Python de la imagen | 3.13.13 |
| PyTorch de la imagen | 2.9.1+cu128 |
| CUDA visible | False |
| Dataset | data/ml_outputs/features/application_train_features.parquet |
| Filas | 277.511 |
| Columnas | 520 |

**Hallazgos:**

- La ejecución terminó con código 137. El código 137 indica que el proceso fue terminado por el sistema o por Docker, probablemente por un pico de memoria durante carga, preparación o entrenamiento del dataset completo en CPU.
- No se generó modelo ni métricas.

**Comando de entrenamiento:**

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD":/work \
  -w /work \
  data-architectures-foundation:py313 \
  python 04_ml_development/scripts/train.py --model tabicl
```

### Ejecución 5: TabICL

Fecha y hora de ejecución: 2026-06-06 10:01:00.  
Estado: Fallida, código 137, muestra 10.000.

**Configuración:**

| Parámetro | Valor |
|---|---|
| Imagen | data-architectures-foundation:py313 |
| CUDA visible | False |
| Dataset | data/ml_outputs/features/application_train_features_tabicl_sample_10000.parquet |
| Filas | 10.000 |
| Columnas | 520 |
| Distribución target | {0: 9191, 1: 809} |

**Hallazgos:**

- La ejecución terminó con código 137.
- No se generó objeto de modelo ni métricas.
- La muestra estratificada de 10.000 filas supera la capacidad práctica de esta ejecución con CPU para TabICL con la configuración actual.

**Comando de entrenamiento:**

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD":/work \
  -w /work \
  data-architectures-foundation:py313 \
  python 04_ml_development/scripts/train.py \
    --model tabicl \
    --features-path data/ml_outputs/features/application_train_features_tabicl_sample_10000.parquet
```

### Ejecución 6: TabICL

Fecha y hora de ejecución: 2026-06-06 10:26:51.  
Estado: Exitosa, muestra 1.000.

**Configuración:**

| Parámetro | Valor |
|---|---:|
| Imagen | data-architectures-foundation:py313 |
| Python de la imagen | 3.13.13 |
| PyTorch de la imagen | 2.9.1+cu128 |
| CUDA visible | False |
| Filas de muestra | 1.000 |
| Columnas | 520 |
| Distribución target | {0: 919, 1: 81} |
| Split train | 600 |
| Split validation | 200 |
| Split test | 200 |

**Resultados:**

| Métrica | Valor |
|---|---:|
| preprocess_fit_seconds | 0,0642 |
| train_seconds | 1,5137 |
| validation_predict_seconds | 222,5865 |
| test_predict_seconds | 223,2643 |
| validation_roc_auc | 0,6277 |
| validation_pr_auc | 0,2674 |
| validation_precision | 0,0000 |
| validation_recall | 0,0000 |
| validation_f1 | 0,0000 |
| test_roc_auc | 0,7551 |
| test_pr_auc | 0,2914 |
| test_precision | 0,0000 |
| test_recall | 0,0000 |
| test_f1 | 0,0000 |

**Comando de entrenamiento:**

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD":/work \
  -w /work \
  data-architectures-foundation:py313 \
  python 04_ml_development/scripts/train.py \
    --model tabicl \
    --features-path data/ml_outputs/features/application_train_features_tabicl_sample_1000.parquet
```

**Hallazgos:**

- La ejecución permite validar que el flujo con el modelo TabICL puede completar exitosamente en CPU con una muestra estratificada pequeña.
- Los tiempos de predicción son altos para solo 200 filas de validation/test, por lo que TabICL en CPU no es viable todavía para dataset completo con la configuración actual.
- Las métricas de precision, recall y F1 quedan en cero al umbral de clasificación por defecto; PR-AUC y ROC-AUC deberían revisarse junto con ajuste de umbral antes de descartar el modelo.
- Estas métricas no son comparables directamente contra los baselines entrenados con el dataset completo.

### Ejecución 7: TabICL

Fecha y hora de ejecución: 2026-06-06 12:04:19.  
Estado: Exitosa, muestra 2.000.

**Memoria registrada:**

| Etapa | RSS proc. (MB) | Peak RSS proc. (MB) | Cgroup actual (MB) | Mem. sist. disp. (MB) |
|---|---:|---:|---:|---:|
| Lectura de features | 141 | 140 | 83 | 23.843 |
| Split | 223 | 227 | 142 | 23.793 |
| Preprocessing | 247 | 253 | 164 | 23.769 |
| Fit | 925 | 924 | 626 | 23.291 |
| Validation predict | 977 | 21.143 | 672 | 22.866 |
| Test predict | 977 | 21.143 | 672 | 22.864 |

**Resultados:**

| Métrica | Valor |
|---|---:|
| preprocess_fit_seconds | 0,0995 |
| train_seconds | 1,7537 |
| validation_predict_seconds | 440,9531 |
| test_predict_seconds | 442,5755 |
| validation_roc_auc | 0,6454 |
| validation_pr_auc | 0,1652 |
| validation_precision | 0,3333 |
| validation_recall | 0,0313 |
| validation_f1 | 0,0571 |
| test_roc_auc | 0,8018 |
| test_pr_auc | 0,2348 |
| test_precision | 0,5000 |
| test_recall | 0,0313 |
| test_f1 | 0,0588 |

**Comando de entrenamiento:**

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD":/work \
  -w /work \
  data-architectures-foundation:py313 \
  python 04_ml_development/scripts/train.py \
    --model tabicl \
    --features-path data/ml_outputs/features/application_train_features_tabicl_sample_2000.parquet
```

**Hallazgos:**

- La muestra de 2.000 completa exitosamente en CPU, pero la predicción sigue siendo muy lenta: alrededor de 441-443 segundos por split de 400 filas.
- La memoria pico del proceso llegó a aproximadamente 21,1 GB durante predicción. Ello explica por qué muestras mayores pueden ocasionar cierres por falta de memoria.

### Ejecución 8: TabPFN 3

Fecha y hora de ejecución: 2026-06-06 14:50:34.  
Estado: Fallida, licencia/token TabPFN faltante, muestra 2.000.

**Configuración:**

| Parámetro | Valor |
|---|---:|
| Imagen | data-architectures-foundation:py313 |
| Python de la imagen | 3.13.13 |
| PyTorch de la imagen | 2.9.1+cu128 |
| CUDA visible | False |
| Import tabpfn | Exitoso |
| TABPFN_TOKEN presente | False |
| TABPFN_NO_BROWSER | 1 |
| Filas de muestra | 2.000 |
| Columnas | 520 |
| Distribución target | {0: 1838, 1: 162} |
| Split esperado train | 1.200 |
| Split esperado validation | 400 |
| Split esperado test | 400 |

**Hallazgos:**

- Estado: fallida antes de completar fit.
- Código de salida Docker: 1.
- Error principal: tabpfn.errors.TabPFNLicenseError.
- Causa: TabPFN requiere aceptación de licencia/token para descargar pesos de inferencia local; como TABPFN_NO_BROWSER=1 está activo y TABPFN_TOKEN no está seteado, el flujo headless queda bloqueado.
- No se registró OOM ni código 137; esta ejecución no alcanza a evaluar presión de memoria.

**Comando de entrenamiento:**

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD":/work \
  -w /work \
  -e TABPFN_TOKEN \
  -e TABPFN_NO_BROWSER=1 \
  data-architectures-foundation:py313 \
  python 04_ml_development/scripts/train.py \
    --model tabpfn_3 \
    --features-path data/ml_outputs/features/application_train_features_tabpfn_sample_2000.parquet
```

### Ejecución 9: Mitra

Fecha y hora de ejecución: 2026-06-06.  
Estado: Parcial/cancelada, diagnósticos CPU/memoria.

**Objetivo:**

Evaluar si Mitra podía reemplazar a TabPFN sin requerir token o autenticación. Probar una ejecución liviana con fine_tune=false en CPU local.

**Hallazgos:**

- Mitra no tiene el bloqueo de token/licencia observado en TabPFN.
- AutoGluon entrenó Mitra con feature_limit=256.
- Mejor modelo interno: WeightedEnsemble_L2 con peso Mitra: 1.0.
- Runtime reportado por AutoGluon: entrenamiento: aproximadamente 1.231 segundos; validación interna: aproximadamente 1.221 segundos; total AutoGluon: aproximadamente 2.452 segundos.
- El pipeline quedó luego ejecutando predict / predict_proba externo sobre validation/test y fue cancelado manualmente.
- Memoria observada por docker stats: aproximadamente 3,6 a 5,2 GiB sobre 27,81 GiB.
- Conclusión: En CPU local no resulta práctico para este pipeline: aun con fine_tune=false y reducción a 256 features, el costo de entrenamiento/evaluación fue demasiado alto.

### Ejecución 10: TabPFN Mix

Fecha y hora de ejecución: 2026-06-06 18:18:03.  
Estado: Exitosa.

**Objetivo:**

Evaluar TabPFNMix como alternativa fundacional liviana disponible vía AutoGluon 1.5.0 y pesos públicos en Hugging Face.

**Configuración:**

| Parámetro | Valor |
|---|---:|
| Imagen | data-architectures-foundation:py313 |
| Python de la imagen | 3.13.13 |
| AutoGluon Tabular | 1.5.0 |
| PyTorch de la imagen | 2.9.1+cu128 |
| CUDA visible | False |
| Filas de muestra | 2.000 |
| Columnas | 520 |
| Distribución target | {0: 1838, 1: 162} |
| Split train | 1.200 |
| Split validation | 400 |
| Split test | 400 |
| Modelo HF | autogluon/tabpfn-mix-1.0-classifier |
| max_epochs | 0 |
| n_ensembles | 1 |
| dynamic_stacking | false |
| num_bag_folds | 0 |
| num_stack_levels | 0 |
| fit_weighted_ensemble | false |
| Ruta AutoGluon | data/ml_outputs/models/autogluon/tabpfn_mix/ |

**Resultados:**

| Métrica | Valor |
|---|---:|
| preprocess_fit_seconds | 0,0977 |
| train_seconds | 4,4710 |
| validation_predict_seconds | 1,8789 |
| test_predict_seconds | 1,8442 |
| validation_roc_auc | 0,6715 |
| validation_pr_auc | 0,2824 |
| validation_precision | 0,5000 |
| validation_recall | 0,0313 |
| validation_f1 | 0,0588 |
| test_roc_auc | 0,6688 |
| test_pr_auc | 0,1818 |
| test_precision | 0,3333 |
| test_recall | 0,0313 |
| test_f1 | 0,0571 |

**Comando de entrenamiento:**

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD":/work \
  -w /work \
  data-architectures-foundation:py313 \
  python 04_ml_development/scripts/train.py \
    --model tabpfn_mix \
    --features-path data/ml_outputs/features/application_train_features_tabpfn_mix_sample_2000.parquet
```

**Memoria registrada:**

| Etapa | RSS proc. (MB) | Peak RSS proc. (MB) | Cgroup actual (MB) | Mem. Sist. Disp. (MB) |
|---|---:|---:|---:|---:|
| Lectura de features | 141 | 140 | 84 | 23.535 |
| Split | 223 | 227 | 142 | 23.469 |
| Preprocessing | 247 | 253 | 164 | 23.450 |
| Fit | 1.029 | 1.082 | 847 | 22.800 |
| Validation predict | 1.091 | 1.224 | 910 | 22.652 |
| Test predict | 1.152 | 1.224 | 971 | 22.511 |

**Hallazgos:**

- tabpfn_mix es la alternativa fundacional más limpia hasta ahora: no requiere token, entrena rápido en CPU y mantiene memoria controlada.
- AutoGluon seleccionó internamente 100 features mediante SelectKBest porque TabPFNMix admite como máximo 100 atributos.
- En validation obtuvo mejor PR-AUC que tabicl con muestra 2.000, aunque en el conjunto de prueba quedó por debajo de TabICL.

### Ejecución 11: PyOD AutoEncoder

Fecha y hora de ejecución: 2026-06-06 19:02.  
Estado: Exitosa.

**Objetivo:**

Evaluar un baseline neural de detección de anomalías basado en autoencoder. Entrena de forma semisupervisada usando solo casos normales (TARGET=0) y evalúa TARGET=1 como evento anómalo/riesgoso.

**Configuración:**

| Parámetro | Valor |
|---|---:|
| Imagen | data-architectures-foundation:py313 |
| Python de la imagen | 3.13.13 |
| PyOD | 2.0.5 |
| PyTorch de la imagen | 2.9.1+cu128 |
| CUDA visible | False |
| Filas de muestra | 2.000 |
| Columnas | 520 |
| Distribución target | {0: 1838, 1: 162} |
| Split train | 1.200 |
| Split validation | 400 |
| Split test | 400 |
| Entrenamiento | Solo filas normales TARGET=0 |
| Contamination | 0.081 |
| Hidden neurons | [128, 64, 64, 128] |
| Epochs | 20 |
| Batch size | 256 |
| Learning rate | 0.001 |

**Resultados:**

| Métrica | Valor |
|---|---:|
| preprocess_fit_seconds | 0,0988 |
| train_seconds | 2,8671 |
| validation_predict_seconds | 0,0214 |
| test_predict_seconds | 0,0217 |
| validation_roc_auc | 0,6077 |
| validation_pr_auc | 0,1083 |
| validation_precision | 0,1053 |
| validation_recall | 0,1250 |
| validation_f1 | 0,1143 |
| test_roc_auc | 0,5078 |
| test_pr_auc | 0,0952 |
| test_precision | 0,1087 |
| test_recall | 0,1563 |
| test_f1 | 0,1282 |

**Comando de entrenamiento:**

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD":/work \
  -w /work \
  data-architectures-foundation:py313 \
  python 04_ml_development/scripts/train.py \
    --model pyod_autoencoder \
    --features-path data/ml_outputs/features/application_train_features_pyod_autoencoder_sample_2000.parquet
```

**Memoria registrada:**

| Etapa | RSS proc. (MB) | Peak RSS proc. (MB) | Cgroup actual (MB) | Mem. Sist. Disp. (MB) |
|---|---:|---:|---:|---:|
| Lectura de features | 144 | 143 | 86 | 23.535 |
| Split | 228 | 232 | 147 | 23.454 |
| Preprocessing | 252 | 258 | 169 | 23.430 |
| Fit | 982 | 981 | 539 | 23.068 |
| Validation predict | 982 | 981 | 539 | 23.067 |
| Test predict | 982 | 981 | 539 | 23.067 |

**Hallazgos:**

- pyod_autoencoder es muy liviano y rápido para inferencia en CPU.
- La señal inicial fue débil en test (test_roc_auc cercano a 0,5), por lo que no supera a tabicl, tabpfn_mix ni a los baselines supervisados.
