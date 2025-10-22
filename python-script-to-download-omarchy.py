#!/usr/bin/env python3
import os
import requests
from tqdm import tqdm
from threading import Thread

URL = "https://iso.omarchy.org/omarchy-3.1.1.iso"
OUTPUT_PATH = os.path.expanduser("~/Downloads/omarchy-3.1.1.iso")
CONNECTIONS = 10

def get_file_size(url):
    resp = requests.head(url)
    resp.raise_for_status()
    return int(resp.headers.get('content-length', 0))

def download_part(url, start, end, part_num, progress):
    headers = {"Range": f"bytes={start}-{end}"}
    resp = requests.get(url, headers=headers, stream=True)
    resp.raise_for_status()

    part_path = f"{OUTPUT_PATH}.part{part_num}"
    with open(part_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 512):  # 512KB chunks
            if chunk:
                f.write(chunk)
                progress.update(len(chunk))

def merge_parts(total_parts):
    with open(OUTPUT_PATH, "wb") as outfile:
        for i in range(total_parts):
            part_path = f"{OUTPUT_PATH}.part{i}"
            with open(part_path, "rb") as infile:
                outfile.write(infile.read())
            os.remove(part_path)

def main():
    total_size = get_file_size(URL)
    print(f"Total file size: {total_size / (1024*1024):.2f} MB")

    part_size = total_size // CONNECTIONS
    ranges = [
        (i * part_size, (i + 1) * part_size - 1 if i < CONNECTIONS - 1 else total_size - 1)
        for i in range(CONNECTIONS)
    ]

    progress = tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading")

    threads = []
    for i, (start, end) in enumerate(ranges):
        t = Thread(target=download_part, args=(URL, start, end, i, progress))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    progress.close()
    merge_parts(CONNECTIONS)
    print(f"✅ Download complete: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
