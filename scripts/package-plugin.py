#!/usr/bin/env python3
import argparse
import hashlib
import os
import subprocess
import sys
import zipfile
from pathlib import Path

EXCLUDED_DIRS = {'.git', '.github', 'dist', '__pycache__'}
EXCLUDED_FILES = {'.DS_Store'}

def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def should_include(path):
    parts = set(path.parts)
    if parts & EXCLUDED_DIRS:
        return False
    return path.name not in EXCLUDED_FILES and path.name != 'package-plugin.py'

def main():
    parser = argparse.ArgumentParser(description='Package a Jottr plugin as a zip and checksum it.')
    parser.add_argument('--name', required=True)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, str(root / "scripts" / "validate-plugin-json.py"), str(root / "plugin.json")], check=True)
    dist = root / 'dist'
    dist.mkdir(exist_ok=True)
    archive = dist / f'{args.name}-{args.version}.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        for item in sorted(root.rglob('*')):
            rel = item.relative_to(root)
            if item.is_file() and should_include(rel):
                zip_file.write(item, rel.as_posix())
    digest = sha256_file(archive)
    checksum = archive.with_suffix(archive.suffix + '.sha256')
    checksum.write_text(f'{digest}  {archive.name}\n', encoding='utf-8')
    print(digest)

if __name__ == '__main__':
    main()
