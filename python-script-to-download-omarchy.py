#!/usr/bin/env python3
import os
import requests
from tqdm import tqdm
from threading import Thread

URL = "https://iso.omarchy.org/omarchy-3.1.3.iso"
OUTPUT_PATH = os.path.expanduser("~/Downloads/omarchy-3.1.3.iso")
CONNECTIONS = 40

def get_file_size(url):
    resp = requests.head(url)
    resp.raise_for_status()
    return int(resp.headers.get('content-length', 0))

def download_part(url, start, end, part_num, progress):
    part_path = f"{OUTPUT_PATH}.part{part_num}"
    
    # Check if part file already exists
    if os.path.exists(part_path):
        current_size = os.path.getsize(part_path)
        # If part is already complete, just update progress and return
        if current_size >= (end - start + 1):
            progress.update(end - start + 1)
            return
        # Otherwise, resume from current position
        start += current_size
        # Update progress for already downloaded portion
        progress.update(current_size)
    
    # If the entire part is already downloaded, return
    if start > end:
        return
        
    headers = {"Range": f"bytes={start}-{end}"}
    resp = requests.get(url, headers=headers, stream=True)
    resp.raise_for_status()

    # Open file in append mode if resuming, otherwise write mode
    mode = "ab" if os.path.exists(part_path) else "wb"
    with open(part_path, mode) as f:
        for chunk in resp.iter_content(chunk_size=1024 * 512):  # 512KB chunks
            if chunk:
                f.write(chunk)
                progress.update(len(chunk))

def merge_parts(total_parts):
    with open(OUTPUT_PATH, "wb") as outfile:
        for i in range(total_parts):
            part_path = f"{OUTPUT_PATH}.part{i}"
            if os.path.exists(part_path):
                with open(part_path, "rb") as infile:
                    outfile.write(infile.read())
                os.remove(part_path)

def get_downloaded_size(total_parts):
    """Calculate total bytes already downloaded across all parts"""
    total_downloaded = 0
    for i in range(total_parts):
        part_path = f"{OUTPUT_PATH}.part{i}"
        if os.path.exists(part_path):
            total_downloaded += os.path.getsize(part_path)
    return total_downloaded

def cleanup_partial_files(total_parts):
    """Remove all part files (use this if you want to start fresh)"""
    for i in range(total_parts):
        part_path = f"{OUTPUT_PATH}.part{i}"
        if os.path.exists(part_path):
            os.remove(part_path)

def main():
    # Uncomment the next line if you want to start fresh
    # cleanup_partial_files(CONNECTIONS)
    
    total_size = get_file_size(URL)
    print(f"Total file size: {total_size / (1024*1024):.2f} MB")

    part_size = total_size // CONNECTIONS
    ranges = [
        (i * part_size, (i + 1) * part_size - 1 if i < CONNECTIONS - 1 else total_size - 1)
        for i in range(CONNECTIONS)
    ]

    # Calculate already downloaded size for progress bar
    already_downloaded = get_downloaded_size(CONNECTIONS)
    
    print(f"Resuming download: {already_downloaded / (1024*1024):.2f} MB already downloaded")
    
    progress = tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading", initial=already_downloaded)

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
