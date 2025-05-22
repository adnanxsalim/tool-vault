#!/usr/bin/env python3

import argparse
import os
import shutil
from pathlib import Path

VAULT_DIR = Path.home() / ".vault_storage"

def save(src_path, name):
    target_dir = VAULT_DIR / name
    src_path = Path(src_path).resolve()

    if not src_path.exists():
        print(f"[!] Source path {src_path} does not exist.")
        return
    
    if target_dir.exists():
        print(f"[!] A vault entry named '{name}' already exists. Overwriting...")
        shutil.rmtree(target_dir)

    shutil.copytree(src_path, target_dir)
    print(f"[+] Saved '{src_path}' to vault as '{name}'.")

def load(dest_path, name):
    src_dir = VAULT_DIR / name
    dest_path = Path(dest_path).resolve()

    if not src_dir.exists():
        print(f"[!] No vault entry named '{name}' found.")
        return

    if not dest_path.exists():
        dest_path.mkdir(parents=True)

    for item in src_dir.iterdir():
        s = src_dir / item.name
        d = dest_path / item.name
        if s.is_dir():
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)
    
    print(f"[+] Loaded vault '{name}' into '{dest_path}'.")

def list_entries():
    if not VAULT_DIR.exists():
        print("[*] No entries in vault.")
        return
    print("[*] Vault Entries:")
    for entry in VAULT_DIR.iterdir():
        print(f" - {entry.name}")

def delete_entry(name):
    entry = VAULT_DIR / name
    if entry.exists():
        shutil.rmtree(entry)
        print(f"[x] Deleted vault entry '{name}'.")
    else:
        print(f"[!] No entry named '{name}' found.")

def main():
    parser = argparse.ArgumentParser(description="Vault: Save & Load Project Snapshots")
    subparsers = parser.add_subparsers(dest='command')

    save_cmd = subparsers.add_parser('save')
    save_cmd.add_argument('source')
    save_cmd.add_argument('name')

    load_cmd = subparsers.add_parser('load')
    load_cmd.add_argument('destination')
    load_cmd.add_argument('name')

    list_cmd = subparsers.add_parser('list')

    delete_cmd = subparsers.add_parser('delete')
    delete_cmd.add_argument('name')

    args = parser.parse_args()

    VAULT_DIR.mkdir(parents=True, exist_ok=True)

    if args.command == 'save':
        save(args.source, args.name)
    elif args.command == 'load':
        load(args.destination, args.name)
    elif args.command == 'list':
        list_entries()
    elif args.command == 'delete':
        delete_entry(args.name)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()