# Punto 2 — Fuentes de Datos

## Distribución de archivos por destino

### RDS (MariaDB) — 4 tablas
| Tabla | Archivo CSV |
|-------|-------------|
| `orders` | `olist_orders_dataset.csv` |
| `customers` | `olist_customers_dataset.csv` |
| `payments` | `olist_order_payments_dataset.csv` |
| `reviews` | `olist_order_reviews_dataset.csv` |

### EC2 (archivos locales) — 5 archivos
| Archivo |
|---------|
| `olist_products_dataset.csv` |
| `olist_sellers_dataset.csv` |
| `olist_order_items_dataset.csv` |
| `olist_geolocation_dataset.csv` |
| `product_category_name_translation.csv` |

### URL sources (descarga directa) — 2 archivos
| Archivo | URL |
|---------|-----|
| `product_category_name_translation.csv` | GitHub – olistbr/brazilian-ecommerce |
| `brazil-states.geojson` | GitHub – codeforgermany/click_that_hood |

---

## Configuración inicial

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Copiar el archivo de variables de entorno y completarlo:
   ```bash
   cp .env.example .env
   # Editar .env con los valores reales
   ```

### Cómo obtener el token de Kaggle
1. Ir a [kaggle.com/settings](https://www.kaggle.com/settings) → sección **API**.
2. Hacer clic en **Generate New Token** — descarga `kaggle.json`.
3. Copiar el valor de `"key"` del archivo y pegarlo en `.env`:
   ```
   KAGGLE_API_TOKEN=<valor de "key">
   ```

---

## Ejecución paso a paso

### Paso 1 — Descargar el dataset desde Kaggle
```bash
cd punto2-fuentes-datos
python scripts/download_dataset.py
```
Descarga los 9 CSVs del dataset Olist en `./data/raw/`.

### Paso 2 — Descargar fuentes desde URL
```bash
python scripts/fetch_url_sources.py
```
Descarga `product_category_name_translation.csv` y `brazil-states.geojson` en `./data/url_sources/`.

### Paso 3 — Cargar tablas en RDS (MariaDB)
```bash
python scripts/load_rds.py
```
Requiere las variables `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` en `.env`.  
Crea (o reemplaza) las 4 tablas en la instancia RDS e imprime el conteo de filas por tabla.

### Paso 4 — Preparar archivos para EC2
```bash
# Opción A: ejecutar localmente y luego hacer SCP
python scripts/setup_ec2_files.py   # usa EC2_DATA_PATH del .env o /home/ec2-user/olist-data/ por defecto

# Opción B: copiar el script a la instancia EC2 y ejecutarlo allí
scp scripts/setup_ec2_files.py ec2-user@<IP>:~
scp -r data/raw/ ec2-user@<IP>:~/data/raw/
ssh ec2-user@<IP> "pip install pandas python-dotenv && python setup_ec2_files.py"
```
Copia los 5 CSVs al directorio configurado y genera `manifest.json` con metadatos de cada archivo.
