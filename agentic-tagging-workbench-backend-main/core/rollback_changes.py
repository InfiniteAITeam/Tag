#!/usr/bin/env python3
"""
Rollback Changes Script
Restores React files from their .taggingai.bak backups and deletes the backups.

Requires .env with:
  REPO_PATH=/mnt/c/Users/sgadal/AppSelector/react-kiosk-billing-js
"""

import os
import shutil
from pathlib import Path
import re

try:
    from cloneRepo import clone_to_fixed_location as clone_repo_url
except Exception:
    clone_repo_url = None

# Load .env (if available)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

CORE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = CORE_DIR / "outputs"
LAST_REPO_ROOT_FILE = OUTPUTS_DIR / ".last_repo_root"


def main():
    print(" ROLLBACK CHANGES (restore + delete backups)")
    print("=" * 20)
    
    # ---- resolve repo root strictly from outputs/.last_repo_root ----
    if not LAST_REPO_ROOT_FILE.exists():
        print(f" Missing {LAST_REPO_ROOT_FILE}")
        print(" Run the tagging step first so it records the repo path there.")
        return

    repo_root_txt = LAST_REPO_ROOT_FILE.read_text(encoding="utf-8").strip()
    if not repo_root_txt:
        print(f" {LAST_REPO_ROOT_FILE} is empty. Re-run the tagging step.")
        return

    repo_root = Path(repo_root_txt).expanduser().resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        print(f" Repo path from {LAST_REPO_ROOT_FILE} does not exist or is not a directory:")
        print(f"   {repo_root}")
        print(" Verify the path or re-run the tagging step to refresh it.")
        return

    # Try common source roots (src/app)
    src_path = None
    for candidate in ("src", "app"):
        p = (repo_root / candidate).resolve()
        if p.exists():
            src_path = p
            break

    if not src_path:
        print(" Could not find your source folder (tried: src, app).")
        print(f"   Repo root: {repo_root}")
        return

    print(f"Using repo src at: {src_path}")

    # Find backups (files only)
    backup_files = [p for p in src_path.rglob("*.taggingai.bak") if p.is_file()]
    if not backup_files:
        print(" No backup files found! Looked for: *.taggingai.bak")
        return

    print(f"Found {len(backup_files)} backup files")

    restored = deleted = 0
    SUFFIX = ".taggingai.bak"

    for backup in backup_files:
        # Compute original path: Foo.js.taggingai.bak -> Foo.js
        backup_str = str(backup)
        if not backup_str.endswith(SUFFIX):
            print(f" Skipping unexpected file: {backup}")
            continue
        original = Path(backup_str[:-len(SUFFIX)])

        try:
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, original)
            print(f" Restored {original.relative_to(repo_root)}")
            restored += 1

            # Delete backup after successful restore
            backup.unlink()
            deleted += 1
            # print(f" Deleted backup {backup.relative_to(repo_root)}")
        except Exception as e:
            try:
                b_rel = backup.relative_to(repo_root)
            except Exception:
                b_rel = backup
            try:
                o_rel = original.relative_to(repo_root)
            except Exception:
                o_rel = original
            print(f"Failed {b_rel} → {o_rel}: {e}")

    print(f"\n Rollback complete! {restored}/{len(backup_files)} restored, {deleted} backups deleted")


if __name__ == "__main__":
    main()
