"""Deterministic-money-path guarantee: /core may not import /meta. AST-based, CI-enforced.
Exit 1 on any violation. This is the enforcement behind SPEC section 8."""
from __future__ import annotations
import ast, pathlib, sys

def violations(root: str = "core") -> list[str]:
    out = []
    for path in pathlib.Path(root).rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""]
            for m in mods:
                if m == "meta" or m.startswith("meta."):
                    out.append(f"{path}:{node.lineno} imports '{m}'")
    return out

if __name__ == "__main__":
    v = violations()
    if v:
        print("CORE PURITY VIOLATION (/core imported /meta):")
        for x in v: print("  " + x)
        sys.exit(1)
    print("core purity OK: /core is free of /meta imports")
