# Punto 3 — Ingesta automática a S3

Scripts para cargar los datos generados en punto2 hacia S3, organizados en zonas raw.

## Arquitectura de zonas

```
punto2-fuentes-datos/data/raw/        →  s3://BUCKET_PROYECTO/raw/rds/
  olist_orders_dataset.csv
  olist_customers_dataset.csv
  olist_order_payments_dataset.csv
  olist_order_reviews_dataset.csv

punto2-fuentes-datos/data/raw/        →  s3://BUCKET_PROYECTO/raw/ec2/
  olist_products_dataset.csv
  olist_sellers_dataset.csv
  olist_order_items_dataset.csv
  olist_geolocation_dataset.csv
  product_category_name_translation.csv

punto2-fuentes-datos/data/url_sources/ →  s3://BUCKET_PROYECTO/raw/url/
  product_category_name_translation.csv
  brazil-states.geojson
```

## Requisitos

```bash
pip install -r requirements.txt
```

## Variables de entorno

Copiar `.env.example` (en `punto2-fuentes-datos/`) a `.env` y completar:

```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_SESSION_TOKEN=your_session_token   # solo si usas credenciales temporales
AWS_REGION=us-east-1
S3_BUCKET=BUCKET_PROYECTO              # reemplazar con el nombre real del bucket
```

## Ejecución

1. Descargar el dataset (desde `punto2-fuentes-datos/`):

```bash
cd ../punto2-fuentes-datos
python scripts/download_dataset.py
python scripts/fetch_url_sources.py
```

2. Ingestar a S3:

```bash
cd ../punto3-ingesta
python scripts/ingest_to_s3.py
```

3. Verificar la carga:

```bash
python scripts/verify_s3.py
```

`verify_s3.py` sale con código 1 si alguna zona está vacía.

> **Nota:** El archivo `olist_geolocation_dataset.csv` supera 10 MB; el script usa
> multipart upload automáticamente para ese archivo.
