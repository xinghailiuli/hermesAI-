#!/usr/bin/env python3
"""Backup ~/api-relay/ to ~/api-relay-backups/ with 30-retention.

Usage:
    python3 backup_api_relay.py

Behavior:
    1. Parse timestamps from existing backup dir names (regex-based), sort oldest first
    2. Delete oldest entries until only MAX_BACKUPS-1 remain
    3. cp -r copy source to backup dir with timestamp name
    4. Exit 0 on success, 1 on failure

Naming convention: api-relay-YYYY.M.D.HH.MM
"""

import os
import shutil
import re
import subprocess
import sys
from datetime import datetime

SRC_DIR = os.path.expanduser("~/api-relay")
BACKUP_DIR = os.path.expanduser("~/api-relay-backups")
MAX_BACKUPS = 30

def parse_ts(name):
    m = re.search(r'(\d{4})\.(\d{1,2})\.(\d{1,2})\.(\d{2})\.(\d{2})', name)
    if m:
        y, mo, d, h, mi = m.groups()
        return datetime(int(y), int(mo), int(d), int(h), int(mi))
    return None

def main():
    if not os.path.isdir(SRC_DIR):
        print(f"Error: Source directory {SRC_DIR} does not exist!", file=sys.stderr)
        return 1

    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Timestamp
    ts = datetime.now().strftime("%Y.%-m.%-d.%H.%M")
    dest_name = f"api-relay-{ts}"
    dest_path = os.path.join(BACKUP_DIR, dest_name)

    # --- Retention: sort existing backups by timestamp, delete oldest ---
    entries = []
    for name in os.listdir(BACKUP_DIR):
        dt = parse_ts(name)
        if dt:
            entries.append((name, dt))
    entries.sort(key=lambda x: x[1])

    # We want to keep MAX_BACKUPS - 1 before adding the new one
    while len(entries) >= MAX_BACKUPS:
        oldest_name, _ = entries.pop(0)
        oldest_path = os.path.join(BACKUP_DIR, oldest_name)
        print(f"Deleting oldest backup: {oldest_name}")
        shutil.rmtree(oldest_path)

    # --- Backup ---
    print(f"Creating backup: {dest_name}")
    shutil.copytree(SRC_DIR, dest_path)

    # --- Summary ---
    remaining = [n for n in os.listdir(BACKUP_DIR) if parse_ts(n)]
    total_size = 0
    for name in remaining:
        p = os.path.join(BACKUP_DIR, name)
        if os.path.isdir(p):
            for dirpath, dirnames, filenames in os.walk(p):
                for f in filenames:
                    try:
                        total_size += os.path.getsize(os.path.join(dirpath, f))
                    except OSError:
                        pass

    print(f"Backup count: {len(remaining)}")
    print(f"Total size: {total_size / 1024:.1f} KB ({total_size} bytes)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
