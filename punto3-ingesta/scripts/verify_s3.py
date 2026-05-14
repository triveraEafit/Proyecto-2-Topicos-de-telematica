import os
import sys

import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('S3_BUCKET', 'BUCKET_PROYECTO')

ZONES = ['rds', 'ec2', 'url']
PREFIX = 'raw/'


def make_client():
    kwargs = dict(
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    if AWS_SESSION_TOKEN:
        kwargs['aws_session_token'] = AWS_SESSION_TOKEN
    return boto3.client('s3', **kwargs)


def list_objects(client, prefix: str) -> list[dict]:
    paginator = client.get_paginator('list_objects_v2')
    objects = []
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
        objects.extend(page.get('Contents', []))
    return objects


def main():
    client = make_client()
    print(f"Verifying s3://{S3_BUCKET}/{PREFIX}\n")

    zone_stats = {}
    for zone in ZONES:
        prefix = f"{PREFIX}{zone}/"
        objects = list_objects(client, prefix)
        total_size = sum(o['Size'] for o in objects)
        zone_stats[zone] = {'count': len(objects), 'size_kb': total_size / 1024}

    print(f"{'ZONE':<8} {'FILES':>6} {'SIZE (KB)':>12}")
    print("-" * 30)
    for zone, stats in zone_stats.items():
        print(f"{zone:<8} {stats['count']:>6} {stats['size_kb']:>12.1f}")
    print()

    empty_zones = [z for z, s in zone_stats.items() if s['count'] == 0]
    if empty_zones:
        print(f"ERROR: empty zones: {', '.join(empty_zones)}")
        sys.exit(1)

    print("All zones OK.")


if __name__ == '__main__':
    main()
