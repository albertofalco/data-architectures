# Bitácora 7: Desarrollo de Machine Learning

## Objetivo

Esta bitácora describe el diseño e implementación del módulo de aprendizaje automático, incluyendo su arquitectura modular, los mecanismos de acceso e ingeniería de datos, el preprocesamiento, la construcción de atributos, el entrenamiento y optimización de modelos, la evaluación y el scoring, así como las métricas analíticas y operativas, dependencias, artefactos y pruebas utilizados. 

## Descripción del módulo 04

El módulo 04_ml_development concentra la capa de desarrollo, validación, entrenamiento, evaluación y scoring de modelos de machine learning dentro del flujo general del repositorio. Su objetivo principal es construir un pipeline reproducible para la clasificación binaria de riesgo crediticio usando como variable objetivo “TARGET” y como entidad principal “SK_ID_CURR”.

La entrada para entrenamiento, validación y prueba proviene de los archivos PARQUET generados por el Data Warehouse en data/dw_parquet/. Por lo tanto, en esta etapa, el módulo no modifica el data warehouse ni ejecuta scripts mutantes de base de datos. No obstante, el diseño contempla que los datos se extraigan desde ClickHouse para el uso en producción.

## Arquitectura del módulo 04 y submódulos

Se diseñó una arquitectura modular para que cada capa del pipeline cumpla una sola responsabilidad: análisis exploratorio inicial (EDA), ingeniería de datos, preprocesamiento, entrenamiento, optimización de hiperparámetros, evaluación, scoring productivo sobre lotes y benchmarking productivo.

### src/eda

Se mantiene como bloque separado. Incluye scripts de análisis exploratorio y generación de reportes HTML. No forma parte del pipeline de entrenamiento, optimización ni scoring.

### src/common

Contiene utilidades compartidas que no pertenecen a una etapa específica del pipeline. Incluye carga de configuraciones, resolución de rutas, logging, integración opcional con MLflow y medición de tiempos.

Archivos relevantes:

- config.py: carga config.yml, resuelve rutas relativas a la raiz del repositorio y localiza archivos PARQUET.

- paths.py: centraliza rutas de salida de ML, por ejemplo el archivo PARQUET final de features.

- timing.py: define PerformanceLogger, usado para medir fases como entrenamiento, predicción, transformación y throughput.

- mlflow_tracking.py: configura MLflow local bajo data/ml_outputs/mlruns/ y registra métricas numéricas cuando la dependencia está instalada.

- logging.py: provee logging estándar por módulo.

### src/data_access

Esta capa solo obtiene datos. No genera atributos ni aplica operaciones de preprocesamiento. Contiene los siguientes scripts:

- contracts.py: define un contrato para que el script feature_builder.py no dependa si los datos provienen de una fuente PARQUET o desde ClickHouse.

- parquet_source.py: lee las tablas almacenadas en data/dw_parquet/.

- clickhouse_source.py: lee las tablas desde ClickHouse usando clickhouse-connect y variables de entorno.

### src/data_engineering

Esta capa integra las tablas del data warehouse y genera el dataset final para entrenamiento o evaluación. Su salida esperada es una tabla única con una fila por la entidad “SK_ID_CURR”. Contiene los siguientes scripts:

- feature_builder.py: orquesta la construcción de atributos usando el objeto FeatureSource instanciado en contracts.py.

- aggregations.py: contiene funciones de agregación para tablas uno-a-muchos.

- joins.py: contiene funciones para realizar uniones de atributos contra la tabla base.

- schemas.py: define constantes y nombres estables de atributos.

- build_features.py: caso de uso para construir y persistir el PARQUET final.

Dado que la información a considerar está distribuida en varias tablas del data warehouse, se debe considerar la forma en que se realiza la agregación de datos para el desarrollo de los modelos.

Es por ello que se define como unidad de modelado el atributo “SK_ID_CURR” de la tabla rep_application_train. El pipeline no hace joins fila a fila sobre tablas transaccionales. En su lugar, cada tabla relacionada se reduce previamente a una representación agregada por “SK_ID_CURR”. Para columnas numéricas se calculan estadísticas como: promedio; mínimo; máximo; suma; desviación estándar; cantidad de registros asociados. Para columnas categóricas se calcula, inicialmente, la cantidad de categorías distintas por entidad. Este enfoque evita expandir demasiado el espacio de atributos considerado y mantiene una matriz tabular manejable.

Adicionalmente, la tabla bureau_balance requiere un tratamiento especial porque no contiene directamente el atributo “SK_ID_CURR”. Debido a ello, primero se agrega rep_bureau_balance por “SK_ID_BUREAU” y se relacionan las agregaciones con rep_bureau, que si contiene la columna “SK_ID_CURR”. Luego se agrega contra la tabla base.

### src/preprocessing

Esta capa transforma el dataset final para que pueda ser consumido por los modelos. Tiene por objetivo evitar la fuga de la variable objetivo “TARGET”, realiza imputaciones, codifica variables categóricas y genera los subconjuntos de datos estratificados. Contiene los siguientes scripts:

- column_selection.py: separa las variables predictoras y objetivo X e y, excluye “TARGET” de los atributos y remueve columnas técnicas como “_DW_ID”, “SK_ID_PREV” y “SK_ID_BUREAU”.

- imputers.py: define imputación numérica y categórica, como por ejemplo, imputación con mediana o con el valor más frecuente.

- encoders.py: define un encoder categórico con manejo de categorías no vistas.

- pipeline.py: construye un objeto ColumnTransformer de la librería scikit-learn. Realiza el escalado de variables numéricas mediante StandardScaler. Se codifican las variables categóricas con OneHotEncoder y el argumento handle_unknown="ignore", para tolerar categorías nuevas en scoring.

- split.py: genera splits train/validation/test estratificados para preservar proporción de clases. El split configurado es: test_size=0.2; validation_size=0.2 ; stratify=true.

### src/models

Contiene múltiples adaptadores de modelos con una interfaz definida común. Cada adaptador representa un modelo y expone las operaciones fit, predict, predict_proba y save para cada uno de ellos. El script models/base.py permite instanciar un modelo por nombre, por ejemplo random_forest, xgboost, local_neural_net, mitra, tabpfn_3, tabpfn_mix, tabicl o pyod_autoencoder.

### src/training

Esta capa orquesta el entrenamiento, evaluación, persistencia de artefactos y registro de métricas. Contiene los siguientes scripts:

- train_model.py: entrena cada familia de modelo, mide tiempos de ejecución, calcula métricas, guarda el modelo como un “bundle” y registra las ejecuciones en MLflow. El artefacto generado contiene: el adaptador del modelo, los preprocesamientos ajustados, la lista de columnas usadas y las métricas de entrenamiento/evaluación.

- evaluate_model.py: calcula métricas de clasificación y extrae las predicciones de la clase positiva.

- model_registry.py: persiste y carga los modelos almacenados mediante joblib.

- select_model.py: base para priorizar modelos a partir de archivos de métricas.

### src/tuning

Contiene la optimización de hiperparámetros para modelos locales, basada en la librería Optuna. Contempla los siguientes scripts:

- objectives.py: define objetivos para maximizar la métrica PR-AUC de validación.

- tune_model.py: ejecuta la librería Optuna y almacena los resultados.

### src/scoring

Esta capa ejecuta inferencias, obtiene métricas y realiza evaluación de resultados productivos. Contiene los siguientes scripts:

- batch_score.py: carga un modelo, extrae datos desde PARQUET o ClickHouse, aplica las mismas transformaciones del entrenamiento y genera predicciones.

- benchmark_production.py: ejecuta la obtención de métricas para varios tamaños de lotes y registra tiempos.

La salida de scoring se guarda en data/ml_outputs/predictions/ e incluye “SK_ID_CURR”, “score”, “prediction” y “model_name”.

El módulo calcula las siguientes métricas de clasificación binaria: roc_auc (capacidad de ranking global entre clases); pr_auc (curva precisión-recall, especialmente relevante para problemas desbalanceados); precision (proporción de predicciones positivas que fueron correctas); recall (proporción de positivos reales detectados); y f1 (media armónica entre la precisión y la sensibilidad). Cada una de estas métricas se calcula en la etapa de entrenamiento para los subconjuntos de validación y prueba.

Además de calidad predictiva, el módulo registra métricas operativas. Ello es importante ya que el modelo a seleccionar no debe ser únicamente el que mejor performe en términos analíticos, sino también que debe ser eficiente en términos de recursos y latencias aceptables en producción.

Las métricas de tiempo se miden con time.perf_counter() mediante PerformanceLogger. Las métricas planteadas incluyen: feature_build_seconds (duración de la construcción de atributos); preprocess_fit_seconds (tiempo de ajuste y transformación inicial durante entrenamiento); train_seconds (duración del entrenamiento); validation_predict_seconds (duración de predicción en validación); test_predict_seconds (duración de predicción en test); production_extract_transform_seconds (tiempo para extraer y construir features desde la fuente productiva); production_transform_seconds (tiempo de transformación con el preprocessor guardado); production_predict_seconds (tiempo de inferencia del modelo); production_total_seconds (suma de extracción/construcción, transformación e inferencia); batch_size (cantidad de registros procesados); rows_scored (cantidad de filas); rows_per_second (tiempo de procesamiento por fila); avg_latency_ms_per_row (latencia promedio por fila).

Las métricas se guardan como un archivo JSON en data/ml_outputs/metrics/. Las ejecuciones de MLflow se escriben bajo data/ml_outputs/mlruns/.

### scripts

Contiene envoltorios para orquestrar los scripts anteriores en base a argumentos de la línea de comandos. Su rol es considerar la ruta de origen, analizar los argumentos, cargar configuración y delegar al caso de uso correspondiente. Contiene los siguientes scripts: build_features.py; train.py; tune.py; evaluate.py; batch_score.py; benchmark_production.py.

## Flujo del pipeline a través de scripts

Para la iniciación del flujo de entrenamiento de modelos, se utiliza el siguiente comando para construir los atributos:

```bash
python 04_ml_development/scripts/build_features.py --source parquet
```

Este script usa data_engineering.build_features.build_features. El flujo carga la configuración dependiendo del origen PARQUET o ClickHouse y construye una matriz analítica consolidada a partir de rep_application_train como tabla base, utilizando “SK_ID_CURR” como identificador principal y manteniendo una única fila por cliente. Si se especifica un límite de registros con --limit, restringe previamente la población de clientes para optimizar el procesamiento.

Posteriormente, genera variables agregadas por cliente a partir de las tablas relacionales, calculando estadísticas para campos numéricos y cantidad de categorías distintas para campos categóricos, incluyendo el tratamiento especial para bureau_balance. Se unen los atributos mediante left joins por “SK_ID_CURR” a la tabla base. Finalmente el resultado se persiste en data/ml_outputs/features/application_train_features.parquet y se registran métricas de construcción de atributos y duración de la etapa en data/ml_outputs/metrics/feature_build_metrics.json.

La salida de build_features.py no es un dataset preprocesado. No se imputan nulos, no se escalan variables, no se codifican categóricas con one-hot encoding, no se separan train/validation/test y no se elimina “TARGET” del archivo PARQUET final. Esas operaciones pertenecen a la capa src/preprocessing y se ejecutan dentro de train.py:

```bash
python 04_ml_development/scripts/train.py --model random_forest
```

Esta ejecución es recomendada como primer entrenamiento para la obtención de modelos base después de la construcción de los atributos. El flujo contiene la lectura de los archivos PARQUET con los atributos construidos, la separación de las variables predictoras y objetivo, la exclusión de la variable objetivo, la división de los subconjuntos de entrenamiento, prueba y validación.

Aquí se realizan las operaciones de preprocesamiento y se instancia el adaptador del modelo según corresponda. Se procede al entrenamiento, se miden tiempos de entrenamiento, validación y prueba, se calculan las métricas predictivas.

Los artefactos se almacenan en data/ml_outputs/models/ y data/ml_outputs/metrics/.

En cuanto a la optimización de hiperparámetros, se utiliza la librería Optuna y está habilitado para modelos base locales:

- random_forest

- xgboost

- local_neural_net

El comando es el siguiente:

```bash
python 04_ml_development/scripts/tune.py --model xgboost
```

El optimizador maximiza la métrica de validación PR-AUC, más adecuada para datasets desbalanceados. La métrica ROC-AUC puede ser informativa pero PR-AUC suele reflejar mejor la capacidad de detectar la clase positiva minoritaria.

La evaluación de los resultados se obtiene mediante el siguiente comando:

```bash
python 04_ml_development/scripts/evaluate.py \
  --model-uri data/ml_outputs/models/random_forest_bundle.joblib
```

La evaluación carga un objeto de modelo persistido, aplica el preprocesamiento guardado y calcula métricas sobre el archivo PARQUET de atributos.

Adicionalmente, el módulo prevé la obtención de métricas en un ambiente productivo. Los scripts relacionados simulan un flujo productivo por lotes. Se leen datos desde ClickHouse, se  construyen atributos con la misma lógica del entrenamiento, se aplica el módulo de preprocesamiento guardado y se genera predicciones. Cuando se usa --limit, primero se limita la tabla base y luego se propagan los IDs hacia las tablas relacionales. Esto evita procesar todo el conjunto histórico del data warehouse para evaluar un lote pequeño.

El comando para obtener el scoring sobre un lote productivo es el siguiente:

```bash
python 04_ml_development/scripts/batch_score.py \
  --source clickhouse \
  --model-uri data/ml_outputs/models/random_forest_bundle.joblib \
  --limit 1000
```

En cuanto al script de benchmarking, ejecuta inferencias para distintos tamaños de lote y registra métricas operativas. Su propósito es comparar modelos no solo por calidad predictiva, sino también por costo de inferencia y viabilidad de uso sobre registros extraídos desde el data warehouse. El comando es el siguiente:

```bash
python 04_ml_development/scripts/benchmark_production.py \
  --model-uri data/ml_outputs/models/random_forest_bundle.joblib \
  --batch-sizes 1,10,100,1000
```

## Dependencias requeridas y uso de Docker

Las dependencias del módulo están fijadas en 04_ml_development/requirements.txt. Dentro de las dependencias principales, se encuentran las siguientes: polars y pyarrow (lectura y procesamiento eficiente de archivos PARQUET); pandas y numpy (manipulación de datos y operaciones numéricas); matplotlib y seaborn (visualización de información); pyyaml y python-dotenv (gestión de configuraciones y variables de entorno); scikit-learn e imbalanced-learn (preprocesamiento, evaluación de modelos y tratamiento del desbalance de clases); xgboost y optuna (entrenamiento y optimización de modelos); mlflow y joblib (seguimiento de experimentos y persistencia de artefactos); torch junto con huggingface-hub (soporte para modelos basados en redes neuronales e integración con repositorios de modelos); y tabpfn y tabicl (modelos fundacionales especializados en datos tabulares). También se debió utilizar la dependencia autogluon para la automatización de modelos fundacionales.

Sin embargo, debido a problemas en las versiones de Python, ciertas librerías debieron ser ejecutadas en contenedores de Docker, con una versión de los binarios de Python diferente. El entorno Docker generado a tales fines utiliza un archivo requirements.txt separado, 04_ml_development/requirements-foundation-py313.txt, donde además se incluye la librería pyod para ejecutar el modelo PyOD AutoEncoder junto con los modelos fundacionales.

Para la construcción de la imagen Docker desde la raíz del repositorio se ejecuta:

```bash
docker build \
  -f 04_ml_development/docker/Dockerfile.foundation \
  -t data-architectures-foundation:py313 \
  .
```

Una vez creada la imagen con las dependencias correspondientes, el entrenamiento se ejecuta de la siguiente forma, utilizando los scripts existentes:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD":/work \
  -w /work \
  -e TABPFN_TOKEN \
  -e TABPFN_NO_BROWSER=1 \
  data-architectures-foundation:py313 \
  python 04_ml_development/scripts/train.py --model tabicl
```

El mismo comando se reutiliza cambiando --model por el modelo fundacional o de autoencoders seleccionado.

## Artefactos generados

El pipeline escribe sus salidas en el directorio data/ml_outputs/. Contiene las siguientes rutas principales:

- data/ml_outputs/features/: archivo PARQUET final luego de las agregaciones.

- data/ml_outputs/models/: objetos que contienen los modelos entrenados.

- data/ml_outputs/models/autogluon/: artefactos internos de AutoGluon.

- data/ml_outputs/metrics/: métricas predictivas y operativas.

- data/ml_outputs/predictions/: predicciones sobre lote productivos.

- data/ml_outputs/mlruns/: tracking local de MLflow.

- data/ml_outputs/foundation_cache/: caches locales de modelos fundacionales.

- data/ml_outputs/eda_reports/: reportes EDA.

- data/ml_outputs/profile_reports/: reportes HTML de la librería fg-data-profiling.

## Validaciones y pruebas

Además de los scripts operativos, se incorporaron algunas pruebas unitarias en 04_ml_development/tests/test_ml_modular_pipeline.py referidas a: la carga de tablas PARQUET; la construcción de atributos por entidad “SK_ID_CURR”; la exclusión de “TARGET” y columnas técnicas; etc. La validación se ejecuta mediante el siguiente comando:

```bash
python -m pytest 04_ml_development/tests/test_ml_modular_pipeline.py -q
```

Por último, como se mencionó anteriormente, el módulo mantiene compatibilidad con la validación entre la información almacenada en el data warehouse y los archivos fuente mediante el script 04_ml_development/tests/test_initial_prep.py. Esta validación es útil para comprobar que los archivos PARQUET obtenidos a partir del data warehouse preservan su estructura y contenido respecto de los archivos CSV de origen.
