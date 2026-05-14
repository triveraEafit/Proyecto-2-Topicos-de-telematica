import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F

args = getResolvedOptions(sys.argv, ["JOB_NAME", "S3_BUCKET"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

BUCKET = args["S3_BUCKET"]
RAW_BASE = f"s3://{BUCKET}/raw"
TRUSTED_BASE = f"s3://{BUCKET}/trusted"

# Table definitions: (zone, filename, key_columns, date_columns)
TABLES = [
    ("rds",  "orders",               ["order_id", "customer_id"],  ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"]),
    ("rds",  "customers",            ["customer_id"],               []),
    ("rds",  "order_items",          ["order_id", "product_id"],    []),
    ("rds",  "order_payments",       ["order_id"],                  []),
    ("rds",  "order_reviews",        ["review_id", "order_id"],     ["review_creation_date", "review_answer_timestamp"]),
    ("rds",  "products",             ["product_id"],                []),
    ("rds",  "sellers",              ["seller_id"],                 []),
    ("ec2",  "geolocation",          ["geolocation_zip_code_prefix"], []),
    ("url",  "category_translation", ["product_category_name"],    []),
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
    input_path = f"{RAW_BASE}/{zone}/{table}.csv"
    output_path = f"{TRUSTED_BASE}/{table}"

    print(f"\n[{table}] Reading from {input_path}")

    df = spark.read.option("header", "true").option("inferSchema", "true").csv(input_path)

    df = normalize_columns(df)

    # Key columns may have been renamed during normalization — normalize key_cols too
    key_cols_norm = [c.strip().lower().replace(" ", "_") for c in key_cols]
    date_cols_norm = [c.strip().lower().replace(" ", "_") for c in date_cols]

    count_before = df.count()
    print(f"[{table}] Rows before cleaning: {count_before}")

    df = drop_null_rows(df, key_cols_norm)
    df = cast_date_columns(df, date_cols_norm)
    df = df.withColumn("ingested_at", F.current_timestamp())

    count_after = df.count()
    print(f"[{table}] Rows after cleaning:  {count_after} (dropped {count_before - count_after})")

    df.write.mode("overwrite").option("compression", "snappy").parquet(output_path)
    print(f"[{table}] Written to {output_path}")

job.commit()
print("\nJob completed successfully.")
