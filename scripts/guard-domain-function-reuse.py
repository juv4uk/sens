#!/usr/bin/env python3
"""Guard: програма мусить спиратися на драбини D1–D10 (мінімальне відновлення після placeholder).

Повний файл: python3 knowledge/d11/restore/apply-guard-restore.py (після push part*.b64).
"""
from __future__ import annotations
import argparse, importlib.util, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCOVER = ROOT / "scripts" / "discover_domain_function_candidates.py"
MINIMUM_RATIFIED_SURFACES = 1001
DEF = re.compile(r"\(" + "визначити" + r"\s+([^\s()]+)")
EXCLUDED_PREFIXES = ("lib/generated/", "lib/surface/", "lib/domains/", "lib/machine/", "vendor/", "benchmarks/", "lib/core4-parts/")
SEMANTIC_PREFIX = "tests/semantic/"

def _load_discover():
    spec = importlib.util.spec_from_file_location("discover_domain_function_candidates", DISCOVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def ladder_names(root: Path) -> set[str]:
    discover = _load_discover()
    names: set[str] = set()
    for domain, rows in discover.load_domain_tables(root).items():
        if domain > 10:
            continue
        for row in rows:
            names.update(discover.aliases(row))
    return names

def hook_installed() -> tuple[bool, str]:
    hp = subprocess.run(["git", "config", "--get", "core.hooksPath"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if hp != "githooks":
        return False, f"core.hooksPath={hp or '(порожньо)'} — увімкни: bash scripts/install-hooks.sh"
    hook = ROOT / "githooks" / "pre-commit"
    if not hook.is_file():
        return False, "немає githooks/pre-commit"
    if not os.access(hook, os.X_OK):
        return False, "githooks/pre-commit не виконуваний"
    return True, "увімкнено (githooks/pre-commit виконуваний)"

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--file", action="append")
    ap.add_argument("--paths-from")
    ap.add_argument("--base")
    ap.add_argument("--register", action="store_true")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--when", action="store_true")
    args = ap.parse_args(argv)
    ladder = ladder_names(ROOT)
    if len(ladder) < MINIMUM_RATIFIED_SURFACES:
        print(f"GUARD-DOMAIN-REUSE: НЕ ПЕРЕВІРЕНО — виявлено лише {len(ladder)}", file=sys.stderr)
        return 2
    if args.self_test:
        ok = len(ladder) >= MINIMUM_RATIFIED_SURFACES
        print(f"GUARD-DOMAIN-REUSE self-test: {'OK' if ok else 'FAIL'} (поверхонь у драбинах: {len(ladder)}, джерело: discover_domain_function_candidates)")
        hok, hmsg = hook_installed()
        print(f"GUARD-DOMAIN-REUSE self-test: гачок {'OK' if hok else 'НЕ УВІМКНЕНО'} — {hmsg}")
        if os.environ.get("GITHUB_ACTIONS") == "true":
            if not hok:
                print("GUARD-DOMAIN-REUSE self-test: гачок у CI — попередження (локально: bash scripts/install-hooks.sh)")
            return 0 if ok else 1
        return 0 if (ok and hok) else 1
    print("GUARD-DOMAIN-REUSE: мінімальна збірка — повний сканер: python3 knowledge/d11/restore/apply-guard-restore.py", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
