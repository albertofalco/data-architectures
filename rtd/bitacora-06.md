# Bitácora 6: Configuración del Data Warehouse

## Instalación de Docker para contenerización de aplicaciones

Se instaló Docker en el servidor para la contenerización de ClickHouse OSS y la interfaz gráfica CH-UI.

Instalación de librerías utilizando apt:

```bash
sudo apt-get update
sudo apt install ./docker-desktop-amd64.deb
```

Asimismo, se instaló el repositorio apt de Docker:

```bash
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o    /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
        Types: deb
        URIs: https://download.docker.com/linux/ubuntu
        Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
        Components: stable
        Signed-By: /etc/apt/keyrings/docker.asc
        EOF
```

## Instalación de aplicaciones

Se instaló ClickHouse OSS (https://clickhouse.com/docs/install/docker) y CH-UI (https://ch-ui.com/getting-started.html), mediante el uso de Docker Compose.

```yaml
services:
  clickhouse:
    image: clickhouse/clickhouse-server
    container_name: clickhouse-server
    ports:
      - "8123:8123"
      - "9000:9000"
    environment:
      - CLICKHOUSE_USER=********
      - CLICKHOUSE_PASSWORD=********
    ulimits:
      nofile:
        soft: 262144
        hard: 262144
  ch-ui:
    image: ghcr.io/caioricciuti/ch-ui:latest
    environment:
      VITE_CLICKHOUSE_URL: http://172.17.0.1:8123
      VITE_CLICKHOUSE_USER: ********
      VITE_CLICKHOUSE_PASS: ********
    ports:
      - "5521:5521/tcp"
```

Para acceder a la interfaz simple web de ClickHouse Server, se puede ingresar en el navegador desde el servidor local: http://localhost:8123. Para acceder a la interfaz de CH-UI, se puede ingresar en el navegador: http://localhost:5521.

## Realización de copia de seguridad y prueba de restauración

Se elaboraron dos scripts en bash para la realización de copias de seguridad de la base de datos seleccionada, y para la restauración de los datos almacenados:

- utils/backup_db.sh

- utils/restore_db.sh

## Eliminación de registros y pruebas

Para la incorporación incremental de registros de application_train, se desarrollaron tres scripts con objetivos diferentes:

- El primero de ellos (rows_backup.py) realiza una copia de seguridad de los registros seleccionados, que quedan almacenados en un archivo CSV.

- El segundo (rows_delete.py) lleva a cabo la eliminación de los registros de la base de datos.

- El tercero (rows_insert.py) inserta los registros almacenados nuevamente en la base de datos, en función de la cantidad de registros que se determinen para ingresar.

Este último script será fundamental para simular la inserción de registros en la base de datos y posterior traspaso al data warehouse, para evaluar el rendimiento de los modelos de machine learning en el ambiente de producción.

Se seleccionaron los últimos 30.000 registros de application_train para la realización de evaluaciones posteriores, los cuales comprenden desde el “SK_ID_CURR” 421.550 hasta 456.255. Estos registros fueron eliminados de la base de datos y mantenidos en otro archivo CSV a efectos de ser incorporados de manera progresiva, a medida que se realizan las evaluaciones que se verán más adelante en el trabajo. La tabla modificada queda así en un total de 277.511 observaciones.

## Integración de MySQL y ClickHouse

### Consideraciones iniciales

Para llevar adelante la integración entre la base de datos y el almacén de datos configurados, se debieron tener algunas consideraciones previas:

- No se pudo configurar el motor MaterializedMySQL debido a la versión de ClickHouse configurada. Por lo tanto, tampoco se pudo configurar Binary Log para capturar los cambios en la base de datos.

- Se utilizó directamente el motor disponible que es MySQL.

- Se debieron otorgar permisos de usuario adicionales para el usuario que se conecta desde ClickHouse: SELECT, REPLICATION CLIENT, REPLICATION SLAVE, RELOAD.

- Dado que el servidor ClickHouse se encuentra instalado en un contenedor de Docker, para la conexión entre ambas bases de datos, se debió agregar una línea en el archivo docker_compose.yml, Con esta configuración, el localhost del equipo anfitrión es reconocido dentro de docker como host.docker.internal.

```yaml
services:
  clickhouse:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

- El objetivo es utilizar el motor MySQL de ClickHouse como puente y Materialized Views para la persistencia de datos.

### Conexión a la base de datos

El primer paso dentro de ClickHouse es conectar el DW a la base de datos MySQL. Para ello, se mapea mediante la variable ENGINE.

```sql
CREATE DATABASE staging_mysql
ENGINE = MySQL('host.docker.internal:3306', 'nombre_base_datos', 'usuario', 'contraseña');
```

### Selección de alternativas de almacenamiento y flujo de datos

Ante la cuestión sobre dónde deben permanecer almacenados los datos, surgió la disyuntiva entre: mantener los datos en la base de datos y utilizar JOINs y vistas materializadas para solo almacenar los datos desnormalizados en ClickHouse; y almacenarse en el data warehouse para evitar la sobrecarga de los servidores y luego utilizar vistas normales o materializadas para su consumo. Dado que el objetivo es simular un entorno real, se procura evitar la saturación del servidor de base de datos. Por lo tanto, se adoptó la segunda opción.

En cuanto al uso de vistas normales o materializadas, se optó por el uso de este último grupo, que funcionan como “triggers de inserción”. La vista materializada almacena datos físicamente en una tabla de destino. Cuando se insertan datos en la tabla de origen, la vista materializada intercepta ese bloque de datos, aplica la lógica (joins, cálculos, filtros) y guarda el resultado procesado en una tabla nueva.

Para la implementación de esta alternativa, se debe aplicar una arquitectura de capas útil para la estabilidad y rendimiento del DW:

- Una capa de almacenamiento, que es donde se alojan nativamente los datos. Asegura la persistencia de los datos ante caídas del servidor MySQL.

- Una capa de “staging” o de enlace, que actúa de “tunel” entre la base de datos en MySQL y el DW. EL motor es MySQL.

### Estructuración de la capa de almacenamiento

Se debe crear primero la capa de almacenamiento:

```sql
CREATE DATABASE IF NOT EXISTS data_arch_dw;
```

Las tablas de dimensiones se almacenan mediante diccionarios de ClickHouse dado que mejoran el rendimiento al estar almacenadas automáticamente en memoria. Para la creación de los diccionarios, se utiliza el script dw_dict_creator.py.

Las tablas de transacciones se almacenan en tablas de la base data_arch_dw, utilizando el motor MergeTree.

Se debe realizar una distinción por tabla ya que algunas de ellas no poseen primary keys, necesarias para establecer el argumento ORDER BY en ClickHouse. Se definieron dos grupos:

- Opción A: mantienen la estructura original (sin un campo de ID extra).

- Opción B: se incorpora un ID Autonumerado (“_row_id”). Añade una columna técnica al principio de cada tabla de transacción. Esto garantiza ClickHouse tenga un índice físico al cual acceder para realizar la operación ORDER BY.

Para la creación de las tablas de transacciones, se utilizan los scripts:

- config.yml

- dw_tran_creator.py

- dw_tran_insert.py

### Creación de las vistas materializadas

Las vistas materializadas constituyen no solo vistas almacenadas en el DW, sino también procesos ETL en tiempo real. Para configurar una vista materializada, se debieron crear:

- Las tablas de destino: constituyen tablas comunes y corrientes y allí se almacenan físicamente los datos. Si se borrara la vista materializada por algún motivo, los datos en la tabla de destino no desaparecen.

- Las vistas materializadas: representan un insertador automático (un trigger o desencadenador de inserción). No contienen datos y permiten que la transformación ocurra en el momento exacto en que los datos llegan, aprovechando la memoria RAM antes de que los datos se escriban en el disco.

Se utilizaron los siguientes scripts para la creación de las vistas materializadas y las tablas de destino:

- config.yml

- dw_mv_creator.py

- dw_mv_insert_.py

### Realización de tests de integridad

Se implementaron dos tests para verificar conexión e integridad entre los archivos de origen y las tablas almacenadas en el DW:

- test_connection_dw.py

- test_raw_dw.py

### Exportación de tablas a formato PARQUET

Una vez creadas y pobladas las tablas de reporte en ClickHouse, se exportaron a archivos PARQUET para desacoplar la etapa de machine learning del servidor del data warehouse. De este modo, los scripts de validación, análisis exploratorio inicial, generación de atributos, entrenamiento e inferencia pueden ejecutarse localmente sobre archivos columnares, sin volver a consultar ClickHouse en cada iteración. Los archivos exportados se almacenan en data/dw_parquet/. La exportación se realizó mediante la interfaz HTTP de ClickHouse, solicitando el resultado de una consulta en formato PARQUET:

```sql
mkdir -p data/dw_parquet

curl -u usuario:contrasena \
  -d "SELECT * FROM data_arch_dw.rep_application_train FORMAT Parquet" \
  http://localhost:8123/ \
  --output data/dw_parquet/rep_application_train.parquet
```

Finalmente, la consistencia entre los archivos PARQUET y los archivos CSV crudos se validó con un script inicial del módulo de desarrollo de machine learning (módulo 04):

```bash
python 04_ml_development/tests/test_initial_prep.py
```
