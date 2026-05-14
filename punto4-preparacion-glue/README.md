# Punto 4 — Preparación con AWS Glue

ETL job que mueve los datos del layer **raw** al layer **trusted** en S3, aplicando limpieza y estandarización con PySpark sobre AWS Glue.

## Diagrama de flujo

```
s3://BUCKET_PROYECTO/raw/
  ├── rds/orders.csv
  ├── rds/customers.csv
  ├── rds/order_items.csv
  ├── rds/order_payments.csv
  ├── rds/order_reviews.csv
  ├── rds/products.csv
  ├── rds/sellers.csv
  ├── ec2/geolocation.csv
  └── url/category_translation.csv
          │
          ▼
    [AWS Glue ETL]
    raw_to_trusted.py
          │
          ▼
s3://BUCKET_PROYECTO/trusted/
  ├── orders/        (parquet, snappy)
  ├── customers/     (parquet, snappy)
  ├── order_items/   (parquet, snappy)
  ├── order_payments/(parquet, snappy)
  ├── order_reviews/ (parquet, snappy)
  ├── products/      (parquet, snappy)
  ├── sellers/       (parquet, snappy)
  ├── geolocation/   (parquet, snappy)
  └── category_translation/ (parquet, snappy)
```

## Transformaciones aplicadas

### 1. Eliminación de filas con valores nulos en columnas clave

Cada tabla tiene una o más columnas que actúan como identificador principal. Una fila sin ese valor no puede unirse con otras tablas y contamina los análisis posteriores. Se eliminan filas donde esas columnas sean `NULL` o cadena vacía.

| Tabla                | Columnas clave                          |
|----------------------|-----------------------------------------|
| orders               | order_id, customer_id                   |
| customers            | customer_id                             |
| order_items          | order_id, product_id                    |
| order_payments       | order_id                                |
| order_reviews        | review_id, order_id                     |
| products             | product_id                              |
| sellers              | seller_id                               |
| geolocation          | geolocation_zip_code_prefix             |
| category_translation | product_category_name                   |

### 2. Normalización de nombres de columnas

Todos los nombres de columna se convierten a minúsculas y los espacios se reemplazan por guiones bajos (`_`). Esto garantiza consistencia entre tablas y evita problemas con motores SQL que distinguen mayúsculas.

Ejemplo: `Order ID` → `order_id`

### 3. Casteo de columnas de fecha a timestamp

Las fechas vienen como strings en los CSVs. Se castean a `TimestampType` de Spark para permitir operaciones de tiempo (diferencias, filtros por rango, particionado temporal) en pasos posteriores.

Columnas casteadas:

- **orders**: `order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date`
- **order_reviews**: `review_creation_date`, `review_answer_timestamp`

### 4. Columna de metadatos `ingested_at`

Se agrega `ingested_at = current_timestamp()` a cada tabla. Permite saber cuándo se ejecutó el job que generó cada archivo parquet, útil para auditoría y reingesta incremental futura.

### 5. Formato de salida: Parquet + Snappy

Parquet es columnar, lo que reduce el costo de queries en Athena (solo se leen las columnas necesarias). La compresión Snappy ofrece buen balance entre velocidad y tamaño.

---

## Estructura del directorio

```
punto4-preparacion-glue/
├── glue_jobs/
│   ├── raw_to_trusted.py   # Script para AWS Glue (usa GlueContext)
│   └── local_test.py       # Versión local para pruebas sin AWS
├── glue_config/
│   └── job_config.json     # Configuración de referencia del Glue Job
├── requirements.txt
└── README.md
```

---

## Prueba local con `local_test.py`

### Prerequisitos

```bash
cd punto4-preparacion-glue
pip install -r requirements.txt
```

Asegúrate de que los CSVs estén descargados en `../punto2-fuentes-datos/data/raw/` (ver instrucciones en punto2).

### Ejecutar

```bash
python glue_jobs/local_test.py
```

El script:
1. Lee los CSVs desde `../punto2-fuentes-datos/data/raw/{zone}/{table}.csv`
2. Aplica todas las transformaciones descritas arriba
3. Escribe los parquet resultantes en `./data/trusted/{table}/`
4. Imprime el conteo de filas antes y después de la limpieza para cada tabla

Si un archivo CSV no existe, lo omite con un mensaje `SKIP` y continúa.

---

## Despliegue en AWS

### Paso 1 — Subir el script a S3

Reemplaza `BUCKET_PROYECTO` con el nombre real de tu bucket:

```bash
aws s3 cp glue_jobs/raw_to_trusted.py s3://BUCKET_PROYECTO/scripts/raw_to_trusted.py
```

### Paso 2 — Crear el Glue Job desde la consola AWS

1. Ve a **AWS Glue → ETL Jobs → Create job**
2. Selecciona **Script editor** y elige **Upload script**
3. Sube `glue_jobs/raw_to_trusted.py` o apunta al S3 URI del paso anterior
4. Usa los valores de `glue_config/job_config.json` como referencia:

| Campo           | Valor                                              |
|-----------------|----------------------------------------------------|
| Job name        | `olist-raw-to-trusted`                             |
| IAM Role        | `AWSGlueServiceRole` (debe tener acceso al bucket) |
| Glue version    | `4.0`                                              |
| Worker type     | `G.1X`                                             |
| Number of workers | `2`                                              |
| Python version  | `3`                                                |

5. En **Job parameters**, agrega:

| Key          | Value            |
|--------------|------------------|
| `--S3_BUCKET` | nombre-de-tu-bucket |
| `--enable-metrics` | `true`      |

### Paso 3 — Crear el Glue Job con AWS CLI (alternativa)

```bash
# Reemplaza BUCKET_PROYECTO y el ARN del rol con los valores reales
aws glue create-job \
  --name "olist-raw-to-trusted" \
  --role "arn:aws:iam::ACCOUNT_ID:role/AWSGlueServiceRole" \
  --command '{"Name":"glueetl","ScriptLocation":"s3://BUCKET_PROYECTO/scripts/raw_to_trusted.py","PythonVersion":"3"}' \
  --default-arguments '{"--S3_BUCKET":"BUCKET_PROYECTO","--job-language":"python","--enable-metrics":"true"}' \
  --glue-version "4.0" \
  --number-of-workers 2 \
  --worker-type "G.1X"
```

### Paso 4 — Ejecutar el job

Desde la consola: **Run job**

O desde CLI:

```bash
aws glue start-job-run --job-name olist-raw-to-trusted
```

### Paso 5 — Verificar la salida

```bash
aws s3 ls s3://BUCKET_PROYECTO/trusted/ --recursive | head -30
```

Deberías ver archivos `.parquet` dentro de cada carpeta de tabla.
