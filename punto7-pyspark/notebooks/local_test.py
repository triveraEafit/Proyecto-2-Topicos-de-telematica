"""
Olist PySpark Analysis — Local Test Version
Reads from ../punto4-preparacion-glue/data/trusted/ and saves to ./data/refined/
No AWS credentials required.
"""

import os
import time
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# ---------------------------------------------------------------------------
# Local paths (no S3 needed)
# ---------------------------------------------------------------------------

BASE_DIR     = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TRUSTED_BASE = os.path.abspath(os.path.join(BASE_DIR, "../punto4-preparacion-glue/data/trusted"))
REFINED_BASE = os.path.join(BASE_DIR, "data/refined")

os.makedirs(REFINED_BASE, exist_ok=True)

print(f"[config] TRUSTED_BASE = {TRUSTED_BASE}")
print(f"[config] REFINED_BASE = {REFINED_BASE}")

# ---------------------------------------------------------------------------
# SparkSession (local mode)
# ---------------------------------------------------------------------------

spark = (
    SparkSession.builder
    .appName("OlistAnalysis")
    .master("local[*]")
    .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
    .config("spark.driver.memory", "2g")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# ---------------------------------------------------------------------------
# Load trusted tables
# ---------------------------------------------------------------------------

def read_table(name: str):
    path = f"{TRUSTED_BASE}/{name}"
    return spark.read.parquet(path)

orders               = read_table("orders")
customers            = read_table("customers")
order_items          = read_table("order_items")
order_payments       = read_table("order_payments")
order_reviews        = read_table("order_reviews")
products             = read_table("products")
sellers              = read_table("sellers")
category_translation = read_table("category_translation")

for name, df in [
    ("orders", orders),
    ("customers", customers),
    ("order_items", order_items),
    ("order_payments", order_payments),
    ("order_reviews", order_reviews),
    ("products", products),
    ("sellers", sellers),
    ("category_translation", category_translation),
]:
    df.createOrReplaceTempView(name)

print("[load] All tables registered as SQL views\n")

results_summary = {}

# ---------------------------------------------------------------------------
# Q1: Top 10 estados con mayor ticket promedio
# ---------------------------------------------------------------------------

print("=" * 60)
print("Q1: Top 10 estados con mayor ticket promedio")
print("=" * 60)

t0 = time.time()

q1 = spark.sql("""
    SELECT
        c.customer_state,
        ROUND(AVG(p.payment_value), 2) AS avg_ticket,
        COUNT(DISTINCT o.order_id)     AS total_orders
    FROM orders o
    JOIN customers c        ON o.customer_id    = c.customer_id
    JOIN order_payments p   ON o.order_id       = p.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_state
    ORDER BY avg_ticket DESC
    LIMIT 10
""")

q1.show(10, truncate=False)
q1_count = q1.count()
q1_path = os.path.join(REFINED_BASE, "q1_ticket_por_estado")
q1.write.mode("overwrite").parquet(q1_path)

elapsed = round(time.time() - t0, 2)
print(f"[Q1] Rows: {q1_count} | Time: {elapsed}s | Saved: {q1_path}\n")
results_summary["Q1"] = {"rows": q1_count, "path": q1_path, "time_s": elapsed}

# ---------------------------------------------------------------------------
# Q2: Categorías con mayor tasa de reviews negativas (score <= 2)
# ---------------------------------------------------------------------------

print("=" * 60)
print("Q2: Categorías con mayor tasa de reviews negativas (score <= 2)")
print("=" * 60)

t0 = time.time()

q2 = spark.sql("""
    SELECT
        ct.product_category_name_english                          AS category,
        COUNT(*)                                                   AS total_reviews,
        SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END)      AS negative_reviews,
        ROUND(
            SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END)
            / COUNT(*) * 100, 2
        )                                                          AS negative_rate_pct
    FROM order_reviews r
    JOIN order_items   oi ON r.order_id          = oi.order_id
    JOIN products      p  ON oi.product_id       = p.product_id
    JOIN category_translation ct
                          ON p.product_category_name = ct.product_category_name
    GROUP BY ct.product_category_name_english
    HAVING COUNT(*) >= 30
    ORDER BY negative_rate_pct DESC
    LIMIT 15
""")

q2.show(15, truncate=False)
q2_count = q2.count()
q2_path = os.path.join(REFINED_BASE, "q2_reviews_negativas")
q2.write.mode("overwrite").parquet(q2_path)

elapsed = round(time.time() - t0, 2)
print(f"[Q2] Rows: {q2_count} | Time: {elapsed}s | Saved: {q2_path}\n")
results_summary["Q2"] = {"rows": q2_count, "path": q2_path, "time_s": elapsed}

# ---------------------------------------------------------------------------
# Q3: Correlación tiempo de entrega vs score de satisfacción
# ---------------------------------------------------------------------------

print("=" * 60)
print("Q3: Correlación tiempo de entrega vs score de satisfacción")
print("=" * 60)

t0 = time.time()

orders_with_days = orders.filter(
    F.col("order_delivered_customer_date").isNotNull()
    & F.col("order_purchase_timestamp").isNotNull()
).withColumn(
    "delivery_days",
    F.datediff(
        F.col("order_delivered_customer_date").cast("date"),
        F.col("order_purchase_timestamp").cast("date"),
    ),
).filter(F.col("delivery_days") >= 0)

orders_with_days.createOrReplaceTempView("orders_with_days")

q3 = spark.sql("""
    SELECT
        CASE
            WHEN delivery_days BETWEEN 0  AND 3  THEN '0-3 days'
            WHEN delivery_days BETWEEN 4  AND 7  THEN '4-7 days'
            WHEN delivery_days BETWEEN 8  AND 14 THEN '8-14 days'
            WHEN delivery_days BETWEEN 15 AND 30 THEN '15-30 days'
            ELSE '30+ days'
        END                           AS delivery_bucket,
        COUNT(*)                      AS total_orders,
        ROUND(AVG(r.review_score), 3) AS avg_review_score,
        MIN(delivery_days)            AS min_days,
        MAX(delivery_days)            AS max_days
    FROM orders_with_days o
    JOIN order_reviews r ON o.order_id = r.order_id
    GROUP BY delivery_bucket
    ORDER BY min_days
""")

q3.show(10, truncate=False)
q3_count = q3.count()
q3_path = os.path.join(REFINED_BASE, "q3_entrega_vs_score")
q3.write.mode("overwrite").parquet(q3_path)

elapsed = round(time.time() - t0, 2)
print(f"[Q3] Rows: {q3_count} | Time: {elapsed}s | Saved: {q3_path}\n")
results_summary["Q3"] = {"rows": q3_count, "path": q3_path, "time_s": elapsed}

# ---------------------------------------------------------------------------
# Q4: Vendedores con mayor volumen de ventas y mejor calificación promedio
# ---------------------------------------------------------------------------

print("=" * 60)
print("Q4: Top vendedores por volumen de ventas y calificación")
print("=" * 60)

t0 = time.time()

q4 = spark.sql("""
    SELECT
        oi.seller_id,
        s.seller_city,
        s.seller_state,
        ROUND(SUM(oi.price), 2)          AS total_revenue,
        COUNT(DISTINCT o.order_id)        AS total_orders,
        ROUND(AVG(r.review_score), 3)     AS avg_review_score
    FROM order_items oi
    JOIN orders       o  ON oi.order_id  = o.order_id
    JOIN order_reviews r ON o.order_id   = r.order_id
    JOIN sellers      s  ON oi.seller_id = s.seller_id
    WHERE o.order_status = 'delivered'
    GROUP BY oi.seller_id, s.seller_city, s.seller_state
    HAVING COUNT(DISTINCT o.order_id) >= 50
    ORDER BY total_revenue DESC
    LIMIT 20
""")

q4.show(20, truncate=False)
q4_count = q4.count()
q4_path = os.path.join(REFINED_BASE, "q4_top_vendedores")
q4.write.mode("overwrite").parquet(q4_path)

elapsed = round(time.time() - t0, 2)
print(f"[Q4] Rows: {q4_count} | Time: {elapsed}s | Saved: {q4_path}\n")
results_summary["Q4"] = {"rows": q4_count, "path": q4_path, "time_s": elapsed}

# ---------------------------------------------------------------------------
# Q5: Volumen de órdenes por mes y categoría
# ---------------------------------------------------------------------------

print("=" * 60)
print("Q5: Volumen de órdenes por mes y categoría")
print("=" * 60)

t0 = time.time()

q5 = spark.sql("""
    SELECT
        DATE_FORMAT(o.order_purchase_timestamp, 'yyyy-MM') AS year_month,
        ct.product_category_name_english                   AS category,
        COUNT(DISTINCT o.order_id)                         AS total_orders
    FROM orders o
    JOIN order_items oi ON o.order_id          = oi.order_id
    JOIN products    p  ON oi.product_id       = p.product_id
    JOIN category_translation ct
                        ON p.product_category_name = ct.product_category_name
    WHERE o.order_purchase_timestamp IS NOT NULL
    GROUP BY year_month, ct.product_category_name_english
    ORDER BY year_month, total_orders DESC
""")

q5.show(20, truncate=False)
q5_count = q5.count()
q5_path = os.path.join(REFINED_BASE, "q5_ordenes_mes_categoria")
q5.write.mode("overwrite").parquet(q5_path)

elapsed = round(time.time() - t0, 2)
print(f"[Q5] Rows: {q5_count} | Time: {elapsed}s | Saved: {q5_path}\n")
results_summary["Q5"] = {"rows": q5_count, "path": q5_path, "time_s": elapsed}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print("\n" + "=" * 60)
print("SUMMARY — Olist Analysis Results (LOCAL)")
print("=" * 60)
for q, info in results_summary.items():
    print(f"  {q}: {info['rows']} rows | {info['time_s']}s | {info['path']}")
print("=" * 60)

spark.stop()
