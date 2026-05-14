# Punto 7 — PySpark: Análisis de Negocio Olist

Análisis de 5 preguntas de negocio sobre el dataset Olist usando PySpark DataFrame API y SparkSQL. Lee tablas parquet desde la zona **trusted** y escribe resultados a la zona **refined**.

---

## Preguntas de Negocio

### Q1 — Top 10 estados con mayor ticket promedio
**Insight:** Identifica qué estados concentran los clientes de mayor poder adquisitivo. Permite focalizar campañas de marketing premium y decidir dónde ampliar inventario de productos de alto valor.

Joins: `orders` + `order_payments` + `customers`
Output: `customer_state`, `avg_ticket`, `total_orders`

---

### Q2 — Categorías con mayor tasa de reviews negativas (score ≤ 2)
**Insight:** Detecta categorías de producto con problemas recurrentes de calidad, logística o expectativas mal gestionadas. Prioriza acciones correctivas con proveedores o ajustes en las descripciones de producto.

Joins: `order_reviews` + `order_items` + `products` + `category_translation`
Output: `category`, `total_reviews`, `negative_reviews`, `negative_rate_pct`

---

### Q3 — Correlación tiempo de entrega vs score de satisfacción
**Insight:** Cuantifica el impacto real del tiempo de entrega en la satisfacción del cliente. Permite definir SLAs de entrega con evidencia y justificar inversión en logística last-mile.

Buckets: 0-3, 4-7, 8-14, 15-30, 30+ días
Output: `delivery_bucket`, `total_orders`, `avg_review_score`

---

### Q4 — Vendedores con mayor volumen de ventas y mejor calificación promedio
**Insight:** Identifica los mejores vendedores de la plataforma (alto revenue + buena calificación). Sirve de base para programas de sellers destacados, mejores comisiones o mayor visibilidad en el marketplace.

Filtro: `total_orders >= 50` (vendedores con volumen suficiente)
Output: `seller_id`, `seller_city`, `seller_state`, `total_revenue`, `total_orders`, `avg_review_score`

---

### Q5 — Volumen de órdenes por mes y categoría
**Insight:** Revela patrones estacionales por categoría. Permite planificar stock, campañas y capacidad logística alineadas con picos históricos de demanda (ej. Black Friday, Navidad).

Output: `year_month`, `category`, `total_orders`

---

## Estructura del directorio

```
punto7-pyspark/
├── notebooks/
│   ├── olist_analysis.py   # Script principal (S3 o local según S3_BUCKET)
│   └── local_test.py       # Versión local sin AWS
├── data/
│   └── refined/            # Output local (creado al ejecutar local_test.py)
├── requirements.txt
└── README.md
```

---

## Ejecutar localmente (sin AWS)

```bash
cd punto7-pyspark
pip install -r requirements.txt

# Requiere que punto4-preparacion-glue/data/trusted/ exista con las tablas parquet
python notebooks/local_test.py
```

Los resultados se guardan en `./data/refined/`.

---

## Ejecutar en AWS EMR

1. Subir el script a S3:
```bash
aws s3 cp notebooks/olist_analysis.py s3://<BUCKET>/scripts/olist_analysis.py
```

2. Lanzar paso en clúster EMR existente:
```bash
aws emr add-steps \
  --cluster-id j-XXXXXXXXXXXX \
  --steps Type=Spark,Name="OlistAnalysis",\
ActionOnFailure=CONTINUE,\
Args=[--deploy-mode,cluster,\
      s3://<BUCKET>/scripts/olist_analysis.py]
```

3. O con `spark-submit` directo desde el master node:
```bash
export S3_BUCKET=mi-bucket-proyecto
spark-submit notebooks/olist_analysis.py
```

---

## Output en zona refined (S3)

```
s3://<BUCKET>/refined/
├── q1_ticket_por_estado/        # Parquet, ~10 filas
├── q2_reviews_negativas/        # Parquet, ~15 filas
├── q3_entrega_vs_score/         # Parquet, 5 filas (un bucket por rango)
├── q4_top_vendedores/           # Parquet, hasta 20 filas
└── q5_ordenes_mes_categoria/    # Parquet, ~N meses × categorías activas
```

Todos los archivos usan compresión Snappy por defecto de PySpark.
Los resultados refined son consumidos por el punto 8 (Streamlit) para visualización.
