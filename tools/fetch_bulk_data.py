"""Restore Heimdall's bulk (non-git) data from the GitHub release named in tools/bulk_manifest.json.

Needs the GitHub CLI logged in with access to the repo (`gh auth login`).
Every downloaded part and every extracted file is SHA-256-verified against the manifest.

usage: python tools/fetch_bulk_data.py [--repo aegiszk/heimdall] [--keep-parts]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "bulk_manifest.json"
DL = ROOT / "bulk_release"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class ChainReader:
    """Read the ordered tar parts as one stream."""

    def __init__(self, paths: list[Path]):
        self.paths, self.fh = list(paths), None

    def read(self, n: int = -1) -> bytes:
        out = bytearray()
        while n < 0 or len(out) < n:
            if self.fh is None:
                if not self.paths:
                    break
                self.fh = open(self.paths.pop(0), "rb")
            chunk = self.fh.read(-1 if n < 0 else n - len(out))
            if not chunk:
                self.fh.close()
                self.fh = None
                continue
            out += chunk
        return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="aegiszk/heimdall")
    ap.add_argument("--keep-parts", action="store_true")
    a = ap.parse_args()
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    DL.mkdir(exist_ok=True)
    for part in m["parts"]:
        p = DL / part["name"]
        if p.exists() and sha(p) == part["sha256"]:
            continue
        subprocess.run(["gh", "release", "download", m["release_tag"], "-R", a.repo, "-p", part["name"],
                        "-D", str(DL), "--clobber"], check=True)
        if sha(p) != part["sha256"]:
            raise SystemExit(f"checksum mismatch on {part['name']}")
    print(f"{len(m['parts'])} parts verified; extracting {m['file_count']} files ...")
    with tarfile.open(fileobj=ChainReader([DL / x["name"] for x in m["parts"]]), mode="r|") as tar:
        tar.extractall(ROOT, filter="data")
    bad = [e["path"] for e in m["files"] if not (ROOT / e["path"]).is_file() or sha(ROOT / e["path"]) != e["sha256"]]
    if bad:
        raise SystemExit(f"{len(bad)} extracted files failed verification, e.g. {bad[:5]}")
    if not a.keep_parts:
        shutil.rmtree(DL)
    print(f"OK: {m['file_count']} files ({m['total_file_bytes'] / 1e9:.2f} GB) restored and verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
