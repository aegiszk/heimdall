"""Shared read-only .scid reader (Sierra intraday file format: 56-byte header, 40-byte records)."""
import glob, os, struct, numpy as np, pandas as pd
SC_EPOCH_US = 25569 * 86_400_000_000
REC = np.dtype([("dt", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"), ("n", "<u4"), ("v", "<u4"), ("bv", "<u4"), ("av", "<u4")])
def read_scid(path):
    raw = np.fromfile(path, dtype=np.uint8)
    hs = struct.unpack("<I", raw[4:8].tobytes())[0]
    a = np.frombuffer(raw[hs:hs + (len(raw) - hs) // 40 * 40].tobytes(), dtype=REC)
    df = pd.DataFrame({k: (a[k].astype(np.int64) if k in ("v", "bv", "av", "n") else a[k].astype(np.float64)) for k in ("o", "h", "l", "c", "v", "bv", "av", "n")})  # int64: avoid uint32 wraparound on av-bv
    df.index = pd.to_datetime(a["dt"] - SC_EPOCH_US, unit="us", utc=True)
    return df
def front_by_day(pattern):
    """Map each UTC date -> contract file with the largest traded volume that day (per-contract 1m files)."""
    vols = {}
    for f in glob.glob(pattern):
        if os.path.getsize(f) <= 56: continue
        d = read_scid(f); vols[os.path.basename(f)] = d.v.groupby(d.index.date).sum()
    V = pd.DataFrame(vols).fillna(0)
    return V.idxmax(axis=1), V
