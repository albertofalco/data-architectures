# Tests de Normalización de Base de Datos

Este directorio contiene los scripts de prueba para validar la integridad de los datasets normalizados.

## Contenido

### `test_content_control.py`
Script principal que verifica que los datasets normalizados mantienen la integridad de los datos comparándolos con los originales.

**Tablas testeadas:**
- `application_train`
- `bureau`
- `previous_application`

**Validaciones realizadas:**
1. **Estructura**: Verifica que el número de filas se mantiene
2. **Columnas**: Valida que todas las columnas esperadas estén presentes
3. **Contenido**: Compara valores entre datasets original y normalizado

## Ejecución

### Desde la carpeta del proyecto
```bash
cd 01_data_normalization
python tests/test_content_control.py
```

### Desde la carpeta tests
```bash
cd tests
python test_content_control.py
```

### Como módulo Python
```python
from test_content_control import run_tests

# Ejecutar todas las pruebas
results = run_tests()

# Ejecutar pruebas específicas
results = run_tests(['application_train', 'bureau'])
```

## Requisitos

- pandas
- numpy
- pandasql

Instalar con:
```bash
pip install pandas numpy pandasql
```

## Estructura de directorios esperada

```
01_data_normalization/
├── data/
│   └── raw/
│       ├── application_train.csv
│       ├── bureau.csv
│       └── previous_application.csv
├── output/
│   ├── application_train/
│   ├── bureau/
│   └── previous_application/
└── tests/
    ├── __init__.py
    ├── test_content_control.py
    └── README.md
```

## Notas sobre las validaciones

- Las columnas `ORGANIZATION_TYPE` y `ORGANIZATION_TYPE_2` se excluyen de la comparación ya que se transforman durante la normalización
- Se tolera una diferencia máxima de `1e-5` en valores numéricos para permitir errores de redondeo en cálculos de punto flotante
- El script genera un resumen detallado de diferencias encontradas para facilitar el debugging
