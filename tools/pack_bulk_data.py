"""Pack Heimdall's bulk (non-git) data into GitHub-Release-sized tar parts + a SHA-256 manifest.

The parts are uploaded as assets of release `bulk-data-v<N>` and restored by tools/fetch_bulk_data.py.
BULK_PATHS must match the BULK DATA block in .gitignore.

usage: python tools/pack_bulk_data.py [--version 1]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bulk_release"
MANIFEST = ROOT / "tools" / "bulk_manifest.json"
PART_BYTES = 1_900_000_000  # GitHub release assets must be < 2 GiB each
BULK_PATHS = [
    "data/sierra",
    "data/tardis_free",
    "data/hl_tape",
    "data/fx_histdata",
    "workspace/profit_discovery_2026-09-23/logs",
    "workspace/tick_discovery_2026-09-23/nq_event_atlas_events.parquet",
    "workspace/tick_discovery_2026-09-23/nq_event_atlas_events_STALE_MIDPROXY_INVALID.parquet",
]


class SplitWriter:
    """File-like sink that rolls to a new part file every PART_BYTES."""

    def __init__(self, stem: Path):
        self.stem, self.idx, self.fh, self.n, self.parts = stem, -1, None, 0, []
        self._roll()

    def _roll(self):
        if self.fh:
            self.fh.close()
        self.idx += 1
        path = Path(f"{self.stem}.part{self.idx:02d}")
        self.parts.append(path)
        self.fh, self.n = open(path, "wb"), 0

    def write(self, b: bytes) -> int:
        mv, done = memoryview(b), 0
        while done < len(mv):
            if self.n >= PART_BYTES:
                self._roll()
            k = min(len(mv) - done, PART_BYTES - self.n)
            self.fh.write(mv[done:done + k])
            self.n += k
            done += k
        return len(b)

    def close(self):
        self.fh.close()


class HashingReader:
    def __init__(self, fh):
        self.fh, self.h = fh, hashlib.sha256()

    def read(self, n: int = -1) -> bytes:
        b = self.fh.read(n)
        self.h.update(b)
        return b


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", type=int, default=1)
    a = ap.parse_args()
    files = []
    for p in BULK_PATHS:
        base = ROOT / p
        if not base.exists():
            raise SystemExit(f"missing bulk path: {p}")
        files += [base] if base.is_file() else sorted(x for x in base.rglob("*") if x.is_file())
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.part*"):
        old.unlink()
    stem = OUT / f"heimdall_bulk_v{a.version}.tar"
    entries = []
    sink = SplitWriter(stem)
    with tarfile.open(fileobj=sink, mode="w|", format=tarfile.PAX_FORMAT) as tar:
        for f in files:
            rel = f.relative_to(ROOT).as_posix()
            info = tar.gettarinfo(str(f), arcname=rel)
            with open(f, "rb") as src:  # hash exactly the bytes archived (files may still be growing)
                reader = HashingReader(src)
                tar.addfile(info, reader)
            entries.append({"path": rel, "bytes": info.size, "sha256": reader.h.hexdigest()})
    sink.close()
    manifest = {
        "release_tag": f"bulk-data-v{a.version}",
        "bulk_paths": BULK_PATHS,
        "parts": [{"name": p.name, "bytes": p.stat().st_size, "sha256": sha(p)} for p in sink.parts],
        "file_count": len(entries),
        "total_file_bytes": sum(e["bytes"] for e in entries),
        "files": entries,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(f"{len(entries)} files, {manifest['total_file_bytes'] / 1e9:.2f} GB -> {len(sink.parts)} parts in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
