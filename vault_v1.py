#!/usr/bin/env python3

import argparse
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# === GLOBAL VARS ===

VAULT_DIR = Path.home() / ".vault_storage"
VAULT_LOG = VAULT_DIR / "access.log"

# === UTILITIES ===

def log_access(action, name):
    VAULT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with VAULT_LOG.open("a") as f:
        f.write(f"[{datetime.now().isoformat()}] {action} {name}\n")

# === CORE COMMANDS ===

def save(src_path, name):
    target_dir = VAULT_DIR / name
    src_path = Path(src_path).resolve()

    if not src_path.exists():
        print(f"[!] Source path '{src_path}' does not exist.")
        return

    if target_dir.exists():
        confirm = input(f"[!] Vault '{name}' already exists. Overwrite? [y/N]: ").lower()
        if confirm != 'y':
            log_access("[!] ABORT OVERWRITE:", f"'{name}' to '{src_path}'")
            print("[!] Aborted.")
            return
        shutil.rmtree(target_dir)
        log_access("[+] OVERWRITE:", f"'{name}' to '{src_path}'")
    else:
        target_dir.mkdir(parents=True)

    shutil.copytree(src_path, target_dir)
    log_access("[+] SAVE:", f"'{src_path}' as '{name}'")
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
    
    log_access("[+] LOAD:", f"{name} to {dest_path}")
    print(f"[+] Loaded vault '{name}' into '{dest_path}'.")

def list_vaults():
    if not VAULT_DIR.exists():
        print("[!] No vaults found.")
        return
    print("[*] Vaults:")
    for entry in VAULT_DIR.iterdir():
        print(f" - {entry.name}")

def delete_vault(name):
    entry = VAULT_DIR / name
    if not entry.exists():
        print(f"[!] Vault '{name}' does not exist.")
        return
    confirm = input(f"Are you sure you want to delete the vault '{name}'? [y/N]: ").lower()
    if confirm == 'y':
        shutil.rmtree(entry)
        log_access("[x] DELETE:", f"'{name}'")
        print(f"[x] Vault '{name}' deleted.")
    else:
        log_access("[!] ABORT DELETE:", f"'{name}'")
        print("[!] Aborted.")
        return
    
def vault_log():
    if not VAULT_LOG.exists():
        print("[!] No logs found.")
        return
    for line in VAULT_LOG.read_text().splitlines():
        print(line)

def print_help():
    help_text = """
Vault CLI - Simple Backup & Restore

Usage:
  vault save <source> <name>              Save a project to the vault
  vault load <destination> <name>         Load a project from the vault
  vault log <name>                        Show access logs
  vault list                              List all saved vaults
  vault delete <name>                     Delete a specific vault
  vault --help                            Show this help message
"""
    print(help_text)

# === MAIN FUNCTION ===

def main():
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == "--help"):
        print_help()
        return

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

    log_cmd = subparsers.add_parser("log")

    args = parser.parse_args()

    VAULT_DIR.mkdir(parents=True, exist_ok=True)

    if args.command == 'save':
        save(args.source, args.name)
    elif args.command == 'load':
        load(args.destination, args.name)
    elif args.command == 'list':
        list_vaults()
    elif args.command == 'delete':
        delete_vault(args.name)
    elif args.command == 'log':
        vault_log()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()