# Bitácora 10: Despliegue productivo

## Objetivo

Esta bitácora describe la implementación del entorno de despliegue productivo simulado utilizado para evaluar la arquitectura y los modelos seleccionados, incluyendo el flujo de incorporación incremental de registros, la inferencia por lotes, la persistencia de predicciones, la implementación de una API y una interfaz web mediante FastAPI, la utilización de Apache Superset para el consumo analítico y la contenerización de los servicios mediante Docker. 

## Arquitectura y flujo productivo

La capa de despliegue diseñada se encuentra separada en tres capas:

- Una capa de servicio de modelos, implementada mediante FastAPI, cuyo fin es exponer las inferencias por lotes y consulta de resultados.

- Una capa de inteligencia de negocios, implementada mediante Apache Superset, cuya finalidad es permitir la creación de tableros a partir de la información almacenada en ClickHouse y obtener una visual de las predicciones obtenidas.

- Una capa web, implementada mediante HTML/Jinja servido por la interfaz FastAPI mencionada anteriormente, cuyo objetivo es mostrar lotes inferidos, predicciones y métricas operativas.

El módulo 05_deployment reutiliza parte de la lógica ya desarrollada y preparada en el módulo 04_ml_development y la construcción de atributos existente. En los modelos que lo requieren, se reutiliza también la imagen Docker data-architectures-foundation:py313.

El flujo de despliegue sigue el siguiente circuito:

- Realizar la lectura de los registros almacenados por diferencia entre data/raw/application_train.csv y data/dw_parquet/rep_application_train.parquet. Los registros separados comprenden aquellos IDs desde 421.550 hasta 456.255.

- De la retención realizada, surgen dos archivos con detalle de IDs y valores reales: holdout_application_train_ids.csv y holdout_application_train_truth.csv.

- A partir de este subconjunto, se inserta un lote de ellos en la base de datos, ordenado por el atributo “SK_ID_CURR”, desde application_train.csv.

- Refrescar el data warehouse para incorporar los nuevos registros almacenados en la base de datos MySQL.

- Ejecutar los scripts de inferencia sobre el lote para los modelos seleccionados en el despliegue.

- Persistir las predicciones obtenidas en archivos locales y en el data warehouse.

- Consumir los resultados desde Apache Superset y desde el servicio web.

Para dejar registro de la incorporación de registros, se utilizan manifiestos almacenados como constancia de avance. Ello evita saltear y solapar registros ya incorporados en el dataset objetivo.

Los modelos seleccionados a efectos del despliegue son los siguientes:

- xgboost

- tabpfn_mix

- pyod_autoencoder

El flujo de inserción, una vez realizada la inferencia y obtenidas las métricas correspondientes, impacta en la tabla data_arch_dw.ml_predictions en el data warehouse. Esta tabla fue creada exclusivamente para recibir las métricas de todas las inferencias realizadas a partir del despliegue por lotes, y sólo admite inserciones, es decir, no se actualizan ni eliminan predicciones históricas.

La tabla usa ORDER BY para favorecer consultas por ejecución y modelo desde Apache Superset y el servicio web.

Cada ejecución genera un manifiesto en data/ml_outputs/inference_runs/<run_id>.json, que registra: los registros consumidos, los IDs incluidos, el recuento de registros, los tiempos de procesamiento, el estado de actualización del data warehouse, y las predicciones y métricas por modelo.

Para la generación de los sucesivos flujos de despliegue e inferencia, se ejecutan los siguientes comandos:

```bash
source venv/bin/activate
python 05_deployment/scripts/generate_holdout_assets.py
python 05_deployment/scripts/insert_holdout_batch.py --rows 1000
python 05_deployment/scripts/refresh_dw_batch.py --manifest <run_id>
python 05_deployment/scripts/run_inference_batch.py --manifest <run_id>
python 05_deployment/scripts/measure_storage.py --run-id <run_id>
```

## API y Servicio WEB

La API diseñada expone endpoints de estado, manifiestos, predicciones locales y resumen por modelo:

<table>
  <tr><th>Endpoint</th><th>Uso</th></tr>
  <tr><td>GET /health</td><td>Healthcheck de la API</td></tr>
  <tr><td>GET /api/runs</td><td>Lista de manifiestos/ejecuciones</td></tr>
  <tr><td>GET /api/runs/{run_id}</td><td>Manifiesto completo de una ejecución</td></tr>
  <tr><td>GET /api/runs/{run_id}/model-summaries</td><td>Resumen por modelo para una ejecución</td></tr>
  <tr><td>GET /api/predictions?run_id=...&amp;model_name=...</td><td>Predicciones locales en parquet</td></tr>
  <tr><td>POST /api/inference/batch</td><td>Ejecuta inferencia batch para un manifiesto</td></tr>
</table>

La vista web que muestra el detalle de cada ejecución:

- identificador de ejecución y estado;

- filas y rango por atributo “SK_ID_CURR”;

- resumen por modelo con filas inferidas;

- cantidad de predicciones 0 y 1;

- tiempo de ejecución por modelo;

- métricas contra “TARGET” real cuando existen datos para la variable objetivo real;

- tabla de predicciones locales por cliente.

La tabla de predicciones muestra como máximo los primeros 50 registros de la ejecución. El endpoint GET /api/predictions conserva el formato largo de los archivos PARQUET locales para consumo programático.

## Apache Superset

El servicio de Apache Superset se configura a partir de una imagen descargada del repositorio oficial de Docker. Se crea un usuario administrador configurado con variables de entorno. El servicio se ejecuta mediante la siguiente URL local: http://localhost:8088.

La conexión a ClickHouse se configura manualmente desde la interfaz de usuario de Superset.

Se replican los siguientes datasets en Apache Superset:

- data_arch_dw.rep_application_train

- data_arch_dw.ml_predictions, con “predicted_at” como columna temporal

### Dashboard de ejecuciones de inferencias

Se genero un dashboard en Apache Superset llamado “Deployment predictions by run”, orientado a monitorear las predicciones persistidas en la tabla ml_predictions en el data warehouse para cada ejecución productiva.

El tablero incorpora un filtro global por id de ejecución, lo que permite analizar una iteración específica del proceso de inferencia.

La consulta base para analizar la distribución de predicciones por modelo es la siguiente:

```sql
SELECT
    run_id,
    model_name,
    prediction,
    count() AS prediction_count,
    avg(score) AS avg_score,
    min(score) AS min_score,
    max(score) AS max_score,
    min(predicted_at) AS first_prediction_at,
    max(predicted_at) AS last_prediction_at
FROM data_arch_dw.ml_predictions
WHERE run_id = '<RUN_ID>'
GROUP BY run_id, model_name, prediction
ORDER BY run_id, model_name, prediction
LIMIT 100
```

A partir de la consulta, se generó un gráfico de barras para distinguir las inferencias según cada modelo desplegado en producción.

Además, se crearon tres tablas adicionales, una para cada clase de modelo, a fines de exponer las predicciones de los primeros 10 registros, según cada iteración. Cada tabla muestra el número de ejecución, el ID y el valor predicho, facilitando la comparación puntual entre modelos sobre los mismos clientes inferidos.

### Dashboard de analisis de aplicaciones

Adicionalmente se generó un dashboard analítico en Apache Superset llamado “Applications Analysis”, orientado a explorar la relación entre la tabla principal data_arch_dw.rep_application_train y la tabla de antecedentes crediticios data_arch_dw.rep_bureau.

Para este tablero se creó un dataset virtual en Superset a partir de una consulta SQL de solo lectura. La consulta agrega previamente rep_bureau a nivel “SK_ID_CURR” y luego une el resultado con rep_application_train. Esta estrategia evita multiplicar filas de la tabla principal, ya que rep_bureau contiene una relación uno-a-muchos por cliente.

## Docker

Para el despliegue de los servicios de consumo por usuarios, se utilizó la herramienta de contenerización Docker, utilizando Docker Compose. Se declararon los siguientes servicios:

<table>
  <tr><th>Servicio</th><th>Puerto</th><th>Uso</th></tr>
  <tr><td>ml-api-web</td><td>8050</td><td>FastAPI + web Jinja de despliegue</td></tr>
  <tr><td>superset-init</td><td>-</td><td>Inicializa DB interna, usuario admin y permisos de Superset</td></tr>
  <tr><td>superset</td><td>8088</td><td>UI de Apache Superset con driver ClickHouse</td></tr>
</table>
