"""
Local PySpark version of raw_to_trusted.py for testing without AWS.
Reads from ../punto2-fuentes-datos/data/raw/ and writes parquet to ./data/trusted/.
"""
import os
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = (
    SparkSession.builder
    .appName("olist-raw-to-trusted-local")
    .master("local[*]")
    .config("spark.sql.ansi.enabled", "false")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

SCRIPT_DIR = Path(__file__).parent
RAW_BASE = SCRIPT_DIR.parent.parent / "punto2-fuentes-datos" / "data" / "raw"
TRUSTED_BASE = SCRIPT_DIR.parent / "data" / "trusted"

TABLES = [
    ("rds",  "orders",               ["order_id", "customer_id"],    ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"]),
    ("rds",  "customers",            ["customer_id"],                 []),
    ("rds",  "order_items",          ["order_id", "product_id"],      []),
    ("rds",  "order_payments",       ["order_id"],                    []),
    ("rds",  "order_reviews",        ["review_id", "order_id"],       ["review_creation_date", "review_answer_timestamp"]),
    ("rds",  "products",             ["product_id"],                  []),
    ("rds",  "sellers",              ["seller_id"],                   []),
    ("ec2",  "geolocation",          ["geolocation_zip_code_prefix"], []),
    ("url",  "category_translation", ["product_category_name"],       []),
]

def normalize_columns(df):
    for col in df.columns:
        normalized = col.strip().lower().replace(" ", "_")
        if normalized != col:
            df = df.withColumnRenamed(col, normalized)
    return df

def drop_null_rows(df, key_columns):
    condition = None
    for col in key_columns:
        col_condition = (F.col(col).isNull()) | (F.trim(F.col(col).cast("string")) == "")
        condition = col_condition if condition is None else condition | col_condition
    return df.filter(~condition)

def cast_date_columns(df, date_columns):
    for col in date_columns:
        if col in df.columns:
            df = df.withColumn(col, F.to_timestamp(F.col(col)))
    return df

for zone, table, key_cols, date_cols in TABLES:
    input_path = str(RAW_BASE / zone / f"{table}.csv")
    output_path = str(TRUSTED_BASE / table)

    if not os.path.exists(input_path):
        print(f"[{table}] SKIP — file not found: {input_path}")
        continue

    print(f"\n[{table}] Reading from {input_path}")
    df = spark.read.option("header", "true").option("inferSchema", "true").csv(input_path)
    df = normalize_columns(df)

    key_cols_norm = [c.strip().lower().replace(" ", "_") for c in key_cols]
    date_cols_norm = [c.strip().lower().replace(" ", "_") for c in date_cols]

    count_before = df.count()
    print(f"[{table}] Rows before cleaning: {count_before}")

    df = drop_null_rows(df, key_cols_norm)
    df = cast_date_columns(df, date_cols_norm)
    df = df.withColumn("ingested_at", F.current_timestamp())

    count_after = df.count()
    print(f"[{table}] Rows after cleaning:  {count_after} (dropped {count_before - count_after})")

    os.makedirs(output_path, exist_ok=True)
    df.write.mode("overwrite").option("compression", "snappy").parquet(output_path)
    print(f"[{table}] Written to {output_path}")

spark.stop()
print("\nLocal test completed.")