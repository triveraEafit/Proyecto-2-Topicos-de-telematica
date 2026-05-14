import os
import shutil
import json
from datetime import datetime, timezone
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

EC2_DATA_PATH = os.getenv('EC2_DATA_PATH', '/home/ec2-user/olist-data/')
RAW_DIR = './data/raw'

EC2_FILES = [
    'olist_products_dataset.csv',
    'olist_sellers_dataset.csv',
    'olist_order_items_dataset.csv',
    'olist_geolocation_dataset.csv',
    'product_category_name_translation.csv',
]

os.makedirs(EC2_DATA_PATH, exist_ok=True)

manifest = []
for fname in EC2_FILES:
    src = os.path.join(RAW_DIR, fname)
    dst = os.path.join(EC2_DATA_PATH, fname)
    shutil.copy2(src, dst)
    size = os.path.getsize(dst)
    df = pd.read_csv(dst)
    row_count = len(df)
    manifest.append({
        'filename': fname,
        'size_bytes': size,
        'row_count': row_count,
        'loaded_at': datetime.now(timezone.utc).isoformat(),
    })
    print(f"Copied {fname}  ({size:,} bytes, {row_count:,} rows)")

manifest_path = os.path.join(EC2_DATA_PATH, 'manifest.json')
with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)
print(f"\nManifest written to {manifest_path}")
