#!/usr/bin/env python3
"""
merge.py — reconstruct files split by split_files.py.

Usage (after cloning the repo):
    python merge.py

Reads .split_manifest.json, concatenates chunks, verifies size + sha256.
"""

import hashlib
import json
import os
import sys

MANIFEST = ".split_manifest.json"


def sha256_of(path: str, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fp:
        for block in iter(lambda: fp.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def merge_one(rel_path: str, info: dict) -> None:
    parts = info["parts"]
    expected_size = info.get("size")
    expected_sha = info.get("sha256")

    # Already there and valid? Skip.
    if os.path.exists(rel_path) and expected_size:
        if os.path.getsize(rel_path) == expected_size:
            if not expected_sha or sha256_of(rel_path) == expected_sha:
                print(f"skip (already present): {rel_path}")
                return

    # Missing chunks?
    missing = [p for p in parts if not os.path.exists(p)]
    if missing:
        print(f"Missing chunks for {rel_path}:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)

    print(f"-> merging: {rel_path}  ({len(parts)} chunks)")
    os.makedirs(os.path.dirname(rel_path) or ".", exist_ok=True)

    with open(rel_path, "wb") as out:
        for p in parts:
            with open(p, "rb") as pf:
                for block in iter(lambda: pf.read(1024 * 1024), b""):
                    out.write(block)

    actual_size = os.path.getsize(rel_path)
    if expected_size and actual_size != expected_size:
        sys.exit(f"Size mismatch for {rel_path}: {actual_size} != {expected_size}")

    if expected_sha:
        actual_sha = sha256_of(rel_path)
        if actual_sha != expected_sha:
            print(f"SHA256 mismatch for {rel_path}")
            print(f"  expected: {expected_sha}")
            print(f"  actual:   {actual_sha}")
            sys.exit(1)

    print(f"OK: {rel_path} ({actual_size / 1024 / 1024:.1f} MB)")


def main():
    if not os.path.exists(MANIFEST):
        sys.exit(f"Manifest not found: {MANIFEST}")

    with open(MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if not manifest:
        print("Manifest is empty.")
        return

    for rel_path, info in manifest.items():
        merge_one(rel_path, info)

    print("\nAll files merged successfully.")


if __name__ == "__main__":
    main()