# Bitácora 4: Refactorización de scripts de normalización y conexión a base de datos

## Contexto

Durante la ejecución de las tareas de normalización (Bitácora 3), se identificaron varios aspectos técnicos que requirieron correcciones y mejoras:

- Dimensiones comunes no normalizadas: Existían columnas compartidas entre múltiples tablas con valores inconsistentes que necesitaban un mapeo centralizado.

- Selección de tipos de datos: Se evaluó el uso de INT versus BIGINT para almacenamiento en MySQL, decidiéndose por el primero por eficiencia.

- Inconsistencias en tipos de datos: Los scripts principales y los tests diseñados presentaban discrepancias en el manejo de tipos (Int64 vs float64).

- Falta de validación end-to-end: No existía un mecanismo que verificara la integridad de los datos desde los archivos CSV fuente hasta su carga en la base de datos.

## Mejoras en el proceso de normalización

Desarrollo de Herramientas de Mapeo y Diagnóstico: Antes de la refactorización principal del módulo 01_data_normalization, se desarrollaron scripts críticos para automatizar la identificación de dimensiones:

- schema_report.py: Script diseñado para analizar la carpeta data/raw/ y generar un reporte de columnas compartidas entre tablas. Este análisis permitió identificar 37 columnas con coincidencias, fundamentando la creación de dimensiones comunes.

- common_dims_mapper.py: Herramienta para la consolidación de valores únicos y generación de mappings.json.

- Se implementó un ordenamiento personalizado para la columna “weekday_appr_process_start”, forzando la secuencia cronológica de lunes (1) a domingo (7) en lugar del orden alfabético.

- Se asignó IDs enteros secuenciales para garantizar la integridad en la fase de remapeo.

Implementación de soporte para mappings.json: Se modificó el script de normalización (01_data_normalization/src/__main__.py) para incorporar el sistema de mapeo centralizado mediante el archivo mappings.json. Este archivo contiene definiciones de dimensiones comunes que se aplican de manera consistente a todos los datasets. El proceso de normalización ahora se ejecuta en dos fases:

- Fase 1 - Remapeo: Aplicación de mappings.json a columnas definidas;

- Fase 2 - Normalización estándar: Procesamiento del resto de columnas categóricas.

Optimización de tipos de datos: Se implementó la función convert_to_nullable_int() que convierte las columnas a float64 cuando todos los valores son enteros. Al implementar la función, se convierten a al formato Int64 permitiendo la coexistencia de valores enteros y nulos y manteniendo la compatibilidad con MySQL.

Mejoras en las pruebas de integridad y estructura: Se realizaron mejoras sobre las pruebas de integridad y estructura de datos para la importación:

- test_content.py: se amplió la cobertura para incluir todos los datasets. Se agregó un límite de filas para mejorar el rendimiento. Durante las pruebas de integridad, se identificó una explosión en el consumo de memoria al procesar varias tablas debido al uso de sqldf para los JOINs de desnormalización. Se planificó la transición hacia técnicas de chunking y la aplicación de límites de carga (head()) en la tabla principal antes de realizar el JOIN, asegurando la estabilidad del sistema sin sacrificar la validación de las dimensiones.

- test_structure.py: se diseñó un script para realizar un análisis global de la estructura después del proceso de normalización.

- test_data_types.py: se desarrolló un script que recorre recursivamente las subcarpetas de data/db_input para validar la interpretación de tipos de pandas.

- test_head_csv.py: se diseñó un script pequeño para mostrar las primeras filas de un archivo CSV seleccionado.

## Mejoras en la conexión a base de datos

Manejo de tipos enteros: Se modificó el script principal del módulo 02_database_connections para manejar correctamente los tipos Int64 de pandas, detectándolos y mapeándolos al tipo entero de SQLAlchemy antes de cargar a MySQL.

Análisis de tamaño de enteros: Se creó el script test_int_size.py que analiza los archivos CSV para identificar columnas que excederían el rango de Int32. Este análisis fundamentó la decisión de utilizar INT en lugar de BIGINT.

Validación end-to-end: Se desarrolló el script test_raw_db.py que realiza una validación completa:

- Lee los datos de la base de datos MySQL;

- Reconstruye las tablas desnormalizadas mediante JOINs con las tablas dimensionales generadas anteriormente;

- Compara los valores hash resultantes con los archivos CSV originales.
