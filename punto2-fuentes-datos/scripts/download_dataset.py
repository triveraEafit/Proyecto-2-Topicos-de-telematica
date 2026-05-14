import os
import kagglehub

path = kagglehub.dataset_download('olistbr/brazilian-ecommerce', output_dir='./data/raw')

print(f"Dataset downloaded to: {path}")
print("\nDownloaded files:")
for root, _, files in os.walk(path):
    for fname in sorted(files):
        fpath = os.path.join(root, fname)
        size = os.path.getsize(fpath)
        print(f"  {fname}  ({size:,} bytes)")
