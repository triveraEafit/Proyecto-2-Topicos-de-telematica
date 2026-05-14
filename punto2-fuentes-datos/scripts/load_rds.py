import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ['DB_HOST']
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_NAME = os.environ['DB_NAME']

TABLES = {
    'orders':    './data/raw/olist_orders_dataset.csv',
    'customers': './data/raw/olist_customers_dataset.csv',
    'payments':  './data/raw/olist_order_payments_dataset.csv',
    'reviews':   './data/raw/olist_order_reviews_dataset.csv',
}

engine = create_engine(
    f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
    pool_pre_ping=True,
)

for table_name, csv_path in TABLES.items():
    print(f"Loading {csv_path} → {table_name} ...", end=' ', flush=True)
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, con=engine, if_exists='replace', index=False, chunksize=1000, method='multi')
    with engine.connect() as conn:
        count = conn.execute(text(f'SELECT COUNT(*) FROM `{table_name}`')).scalar()
    print(f"{count:,} rows")

print("Done.")
