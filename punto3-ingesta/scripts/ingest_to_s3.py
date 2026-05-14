import os
import sys
from pathlib import Path

import boto3
from boto3.s3.transfer import TransferConfig
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('S3_BUCKET', 'BUCKET_PROYECTO')

DATA_DIR = Path(__file__).resolve().parents[2] / 'punto2-fuentes-datos' / 'data'

ZONES = {
    'rds': {
        'prefix': 'raw/rds/',
        'files': [
            DATA_DIR / 'raw' / 'olist_orders_dataset.csv',
            DATA_DIR / 'raw' / 'olist_customers_dataset.csv',
            DATA_DIR / 'raw' / 'olist_order_payments_dataset.csv',
            DATA_DIR / 'raw' / 'olist_order_reviews_dataset.csv',
        ],
    },
    'ec2': {
        'prefix': 'raw/ec2/',
        'files': [
            DATA_DIR / 'raw' / 'olist_products_dataset.csv',
            DATA_DIR / 'raw' / 'olist_sellers_dataset.csv',
            DATA_DIR / 'raw' / 'olist_order_items_dataset.csv',
            DATA_DIR / 'raw' / 'olist_geolocation_dataset.csv',
            DATA_DIR / 'raw' / 'product_category_name_translation.csv',
        ],
    },
    'url': {
        'prefix': 'raw/url/',
        'files': [
            DATA_DIR / 'url_sources' / 'product_category_name_translation.csv',
            DATA_DIR / 'url_sources' / 'brazil-states.geojson',
        ],
    },
}

MULTIPART_THRESHOLD = 10 * 1024 * 1024  # 10 MB

transfer_config = TransferConfig(
    multipart_threshold=MULTIPART_THRESHOLD,
    multipart_chunksize=MULTIPART_THRESHOLD,
)


def make_client():
    kwargs = dict(
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    if AWS_SESSION_TOKEN:
        kwargs['aws_session_token'] = AWS_SESSION_TOKEN
    return boto3.client('s3', **kwargs)


def upload_file(client, local_path: Path, s3_key: str) -> int:
    size = local_path.stat().st_size
    use_multipart = size > MULTIPART_THRESHOLD
    tag = '[multipart]' if use_multipart else '[single]  '
    print(f"  Uploading {local_path.name} {tag} -> s3://{S3_BUCKET}/{s3_key}  ({size / 1024:.1f} KB)")
    client.upload_file(
        str(local_path),
        S3_BUCKET,
        s3_key,
        Config=transfer_config,
    )
    return size


def main():
    client = make_client()
    summary = []

    for zone, config in ZONES.items():
        print(f"\n=== Zone: {zone} ({config['prefix']}) ===")
        for local_path in config['files']:
            if not local_path.exists():
                print(f"  WARNING: {local_path} not found, skipping.")
                continue
            s3_key = config['prefix'] + local_path.name
            size = upload_file(client, local_path, s3_key)
            summary.append({
                'file': local_path.name,
                'source': zone,
                's3_path': f"s3://{S3_BUCKET}/{s3_key}",
                'size_kb': round(size / 1024, 1),
            })

    print("\n" + "=" * 80)
    print(f"{'FILE':<50} {'SOURCE':<6} {'SIZE (KB)':>10}  S3 PATH")
    print("-" * 80)
    for row in summary:
        print(f"{row['file']:<50} {row['source']:<6} {row['size_kb']:>10}  {row['s3_path']}")
    print("=" * 80)
    print(f"Total: {len(summary)} files uploaded to s3://{S3_BUCKET}/raw/")


if __name__ == '__main__':
    main()
