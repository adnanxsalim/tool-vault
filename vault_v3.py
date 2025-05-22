#!/usr/bin/env python3

import argparse
import os
import shutil
import sys
import hashlib
import json
import getpass
import tempfile
import difflib
from pathlib import Path
from datetime import datetime
from zipfile import ZipFile
import tarfile
#from cryptography.fernet import Fernet
import base64

VAULT_DIR = Path.home() / ".vault_storage"
VAULT_LOG = VAULT_DIR / "access.log"
VAULT_GIT_DIR = VAULT_DIR / ".git"

# === UTILS ===

def hash_passphrase(passphrase):
    return hashlib.sha256(passphrase.encode()).hexdigest()

def get_vault_path(name, version):
    return VAULT_DIR / name / version

def load_ignore_patterns(source):
    ignore_file = Path(source) / ".vaultignore"
    if ignore_file.exists():
        return set(ignore_file.read_text().splitlines())
    return set()

def is_ignored(path, ignore_patterns):
    for pattern in ignore_patterns:
        if Path(pattern) in path.parents or path.match(pattern):
            return True
    return False

def save_metadata(name, version, source, tags, readonly):
    meta = {
        "name": name,
        "version": version,
        "source": str(source),
        "timestamp": datetime.now().isoformat(),
        "tags": tags,
        "readonly": readonly
    }
    meta_file = get_vault_path(name, version) / "meta.json"
    meta_file.write_text(json.dumps(meta, indent=2))

def log_access(action, name):
    VAULT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with VAULT_LOG.open("a") as f:
        f.write(f"[{datetime.now().isoformat()}] {action} {name}\n")

def encrypt_directory(path, passphrase):
    key = hashlib.sha256(passphrase.encode()).digest()
    fkey = Fernet(base64.urlsafe_b64encode(key[:32]))
    for file in path.rglob("*"):
        if file.is_file():
            data = file.read_bytes()
            enc = fkey.encrypt(data)
            file.write_bytes(enc)

def decrypt_directory(path, passphrase):
    key = hashlib.sha256(passphrase.encode()).digest()
    fkey = Fernet(base64.urlsafe_b64encode(key[:32]))
    for file in path.rglob("*"):
        if file.is_file():
            data = file.read_bytes()
            dec = fkey.decrypt(data)
            file.write_bytes(dec)

def tree(path, prefix=""):
    lines = []
    for child in sorted(Path(path).iterdir()):
        lines.append(f"{prefix}{child.name}/" if child.is_dir() else f"{prefix}{child.name}")
        if child.is_dir():
            lines.extend(tree(child, prefix + "    "))
    return lines

def diff_versions(path1, path2):
    d1 = sorted([str(p.relative_to(path1)) for p in Path(path1).rglob("*") if p.is_file()])
    d2 = sorted([str(p.relative_to(path2)) for p in Path(path2).rglob("*") if p.is_file()])
    return list(difflib.unified_diff(d1, d2, fromfile="v1", tofile="v2"))

# === CORE COMMANDS ===

def save(source, name, version, compress=None, encrypt=False, interactive=False, dry_run=False, tags=None, readonly=False):
    source = Path(source).resolve()
    target = get_vault_path(name, version)
    if target.exists():
        print(f"[!] Vault {name}@{version} already exists. Overwriting...")
        shutil.rmtree(target)

    if dry_run:
        print("[Dry Run] Files to be saved:")
        print("\n".join(tree(source)))
        return

    ignore_patterns = load_ignore_patterns(source)
    if interactive:
        include_parent = input("Include parent directory? [y/N]: ").lower() == 'y'
        if include_parent:
            temp = tempfile.mkdtemp()
            shutil.copytree(source, Path(temp) / source.name, ignore=shutil.ignore_patterns(*ignore_patterns))
            source = Path(temp)

    shutil.copytree(source, target, ignore=shutil.ignore_patterns(*ignore_patterns))

    if compress == "zip":
        shutil.make_archive(str(target), 'zip', target)
        shutil.rmtree(target)
    elif compress == "tar.gz":
        with tarfile.open(f"{target}.tar.gz", "w:gz") as tar:
            tar.add(target, arcname=name)
        shutil.rmtree(target)

    if encrypt:
        passphrase = getpass.getpass("Enter encryption passphrase: ")
        encrypt_directory(target, passphrase)

    save_metadata(name, version, source, tags or [], readonly)
    log_access("SAVED", f"{name}@{version}")
    if not VAULT_GIT_DIR.exists():
        os.system(f"cd {VAULT_DIR} && git init --bare")
    os.system(f"cd {VAULT_DIR} && git add . && git commit -m 'vault save {name}@{version}'")
    print(f"[+] Vault {name}@{version} saved.")

def load(destination, name, version, decrypt=False):
    dest = Path(destination).resolve()
    src = get_vault_path(name, version)
    if not src.exists():
        print(f"[!] Vault {name}@{version} does not exist.")
        return
    if decrypt:
        passphrase = getpass.getpass("Enter decryption passphrase: ")
        decrypt_directory(src, passphrase)
    shutil.copytree(src, dest, dirs_exist_ok=True)
    log_access("LOADED", f"{name}@{version}")
    print(f"[+] Vault {name}@{version} loaded into {dest}.")

def vault_info(name):
    path = VAULT_DIR / name
    if not path.exists():
        print(f"[!] No vault named {name}.")
        return
    for ver in path.iterdir():
        if ver.is_dir():
            print(f"Version: {ver.name}")
            meta = ver / "meta.json"
            if meta.exists():
                print(meta.read_text())

def vault_diff(name, v1, v2):
    path1 = get_vault_path(name, v1)
    path2 = get_vault_path(name, v2)
    if not path1.exists() or not path2.exists():
        print("[!] One or both versions not found.")
        return
    diff = diff_versions(path1, path2)
    print("\n".join(diff))

def vault_log(name):
    if not VAULT_LOG.exists():
        print("[!] No logs found.")
        return
    for line in VAULT_LOG.read_text().splitlines():
        if name in line:
            print(line)

def vault_search(term):
    for path in VAULT_DIR.glob("**/meta.json"):
        meta = json.loads(path.read_text())
        if term in meta['name'] or term in json.dumps(meta):
            print(f"Found: {meta['name']}@{meta['version']}")

def vault_list():
    if not VAULT_DIR.exists():
        print("[!] No vaults found.")
        return
    for vault in VAULT_DIR.iterdir():
        if vault.is_dir() and not vault.name.startswith('.'):
            print(f"Vault: {vault.name}")
            for version in vault.iterdir():
                if version.is_dir():
                    print(f"  - {version.name}")

def vault_delete(name):
    path = VAULT_DIR / name
    if not path.exists():
        print(f"[!] Vault {name} does not exist.")
        return
    confirm = input(f"Are you sure you want to delete vault '{name}'? [y/N]: ").lower()
    if confirm == 'y':
        shutil.rmtree(path)
        print(f"[+] Vault {name} deleted.")

def print_help():
    help_text = """
Vault CLI - Simple Backup & Restore with Versioning

Usage:
  vault save <source> <name> [--version vX] [--compress zip|tar.gz] [--encrypt] [-i] [--dry-run] [--tags tag1 tag2] [--readonly]
  vault load <destination> <name> [--version vX] [--decrypt]
  vault info <name>                       Show metadata and versions
  vault diff <name> <v1> <v2>             Show file-level diff between versions
  vault log <name>                        Show access logs
  vault search <term>                     Search vaults by name or metadata
  vault list                              List all saved vaults
  vault delete <name>                     Delete a specific vault
  vault --help                            Show this help message

Options:
  --compress     Compress the saved vault (zip or tar.gz)
  --encrypt      Encrypt files with passphrase
  --decrypt      Decrypt files when loading
  -i             Interactive mode, optionally include parent dir
  --dry-run      Show what will be saved in a tree format
  --readonly     Mark vault version as read-only
  --tags         Add custom tags to vault

"""
    print(help_text)

# === MAIN ===

def main():
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == "--help"):
        print_help()
        return

    parser = argparse.ArgumentParser(description="Vault CLI Tool")
    sub = parser.add_subparsers(dest='command')

    save_cmd = sub.add_parser("save")
    save_cmd.add_argument("source")
    save_cmd.add_argument("name")
    save_cmd.add_argument("--version", default="v1")
    save_cmd.add_argument("--compress", choices=["zip", "tar.gz"])
    save_cmd.add_argument("--encrypt", action="store_true")
    save_cmd.add_argument("-i", "--interactive", action="store_true")
    save_cmd.add_argument("--dry-run", action="store_true")
    save_cmd.add_argument("--tags", nargs="*")
    save_cmd.add_argument("--readonly", action="store_true")

    load_cmd = sub.add_parser("load")
    load_cmd.add_argument("destination")
    load_cmd.add_argument("name")
    load_cmd.add_argument("--version", default="v1")
    load_cmd.add_argument("--decrypt", action="store_true")

    info_cmd = sub.add_parser("info")
    info_cmd.add_argument("name")

    diff_cmd = sub.add_parser("diff")
    diff_cmd.add_argument("name")
    diff_cmd.add_argument("v1")
    diff_cmd.add_argument("v2")

    log_cmd = sub.add_parser("log")
    log_cmd.add_argument("name")

    search_cmd = sub.add_parser("search")
    search_cmd.add_argument("term")

    list_cmd = sub.add_parser("list")

    delete_cmd = sub.add_parser("delete")
    delete_cmd.add_argument("name")

    args = parser.parse_args()
    VAULT_DIR.mkdir(parents=True, exist_ok=True)

    if args.command == "save":
        save(args.source, args.name, args.version, args.compress, args.encrypt, args.interactive, args.dry_run, args.tags, args.readonly)
    elif args.command == "load":
        load(args.destination, args.name, args.version, args.decrypt)
    elif args.command == "info":
        vault_info(args.name)
    elif args.command == "diff":
        vault_diff(args.name, args.v1, args.v2)
    elif args.command == "log":
        vault_log(args.name)
    elif args.command == "search":
        vault_search(args.term)
    elif args.command == "list":
        vault_list()
    elif args.command == "delete":
        vault_delete(args.name)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
