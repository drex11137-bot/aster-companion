#!/usr/bin/env python3
import os
import sys
import shutil
import tarfile
import argparse
from datetime import datetime

PROJECT_ROOT = "/workspaces/codespaces-blank"
MEMORY_DIR = os.path.join(PROJECT_ROOT, ".agents", "memory")
BACKUP_DIR = os.path.join(PROJECT_ROOT, ".agents", "backups")

def backup_memory():
    if not os.path.exists(MEMORY_DIR):
        print(f"Error: Memory directory {MEMORY_DIR} does not exist.")
        sys.exit(1)
        
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"memory_backup_{timestamp}.tar.gz")
    
    with tarfile.open(backup_file, "w:gz") as tar:
        tar.add(MEMORY_DIR, arcname=os.path.basename(MEMORY_DIR))
        
    print(f"Memory successfully backed up to: {backup_file}")
    return backup_file

def restore_memory(backup_file):
    if not os.path.exists(backup_file):
        print(f"Error: Backup file {backup_file} does not exist.")
        sys.exit(1)
        
    # Overwrite current state
    if os.path.exists(MEMORY_DIR):
        shutil.rmtree(MEMORY_DIR)
        
    parent_dir = os.path.dirname(MEMORY_DIR)
    
    with tarfile.open(backup_file, "r:gz") as tar:
        tar.extractall(path=parent_dir, filter="data")
        
    print(f"Memory successfully restored from: {backup_file}")

def list_backups():
    if not os.path.exists(BACKUP_DIR):
        print("No backups found.")
        return
        
    backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith("memory_backup_") and f.endswith(".tar.gz")]
    if not backups:
        print("No backups found.")
        return
        
    backups.sort(reverse=True)
    for b in backups:
        print(b)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup and restore memory")
    subparsers = parser.add_subparsers(dest="command")
    
    backup_parser = subparsers.add_parser("backup", help="Backup memory directory")
    
    restore_parser = subparsers.add_parser("restore", help="Restore memory from a backup")
    restore_parser.add_argument("file", help="Path to backup file")
    
    list_parser = subparsers.add_parser("list", help="List available backups")
    
    args = parser.parse_args()
    
    if args.command == "backup":
        backup_memory()
    elif args.command == "restore":
        restore_memory(args.file)
    elif args.command == "list":
        list_backups()
    else:
        parser.print_help()
