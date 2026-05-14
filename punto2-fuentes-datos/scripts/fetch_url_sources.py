import os
import requests

OUTPUT_DIR = './data/url_sources'
os.makedirs(OUTPUT_DIR, exist_ok=True)

URLS = [
    'https://raw.githubusercontent.com/olistbr/brazilian-ecommerce/master/product_category_name_translation.csv',
    'https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/brazil-states.geojson',
]

for url in URLS:
    fname = url.split('/')[-1]
    dest = os.path.join(OUTPUT_DIR, fname)
    print(f"Downloading {fname} ...", end=' ', flush=True)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    with open(dest, 'wb') as f:
        f.write(response.content)
    size = os.path.getsize(dest)
    print(f"{size:,} bytes")

print("Done.")
