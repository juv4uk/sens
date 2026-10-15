#!/usr/bin/env python3
"""Guard: the sterile Zig corridor is the ONLY path to a published .sens (#5777/#5779).

Owner rule (2026-10-15): the Rust/Python<->SENS link crosses ONLY the sterile Zig
corridor. There are no other paths. If there were, contamination would reach the
SENS machine. So a physical .sens may be published ONLY after the pinned Zig
transport has certified the bytes; there is no silent Python fallback.

This is a STRUCTURAL, fail-closed checker (it does not run Zig):
M1  scripts/migrate-t5-batch.py imports the corridor bridge `zig_codec_bridge`.
M2  it builds the pinned transport (`zig_codec_bridge.build_transport`).
M3  it certifies the candidate bytes through Zig (`zig_codec_bridge.verify_t5`).
M4  publishing (`--write`) REQUIRES `--zig-codec` and fails closed without it --
    the gate `if args.write and not args.zig_codec` must be present.
M5  the Zig certification precedes the publish staging: `verify_t5(` appears
    before the first `staged.append(` in the source.
M6  scripts/zig_codec_bridge.py fails closed: it pins the compiler (0.16.0),
    raises ZigCodecError, refuses to overwrite the built binary, and rejects a
    non-attested binary.

M7  scripts/migrate-parallel.sh (if present) delegates to the canonical driver and
    never touches the codec directly (no second path).

Exit 0 = MIGRATION_ZIG_ONLY_PATH_OK; exit 1 = MIGRATION_ZIG_ONLY_PATH_BLOCKED.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

BATCH = "scripts/migrate-t5-batch.py"
BRIDGE = "scripts/zig_codec_bridge.py"


def _live_nodes(root: ast.AST):
    """AST nodes in executable-looking source; comments/strings/if False cannot certify a route."""
    if isinstance(root, ast.If) and isinstance(root.test, ast.Constant) and root.test.value is False:
        return
    yield root
    for child in ast.iter_child_nodes(root):
        yield from _live_nodes(child)


def _bridge_calls(root: ast.AST, operation: str) -> list[ast.Call]:
    return [
        node for node in _live_nodes(root)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == operation
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "zig_codec_bridge"
    ]


def _is_arg(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == name and (
        isinstance(node.value, ast.Name) and node.value.id == "args"
    )


def _real_write_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If):
        return False
    expr = node.test
    if not isinstance(expr, ast.BoolOp) or not isinstance(expr.op, ast.And):
        return False
    positive = any(_is_arg(v, "write") for v in expr.values)
    negative = any(
        isinstance(v, ast.UnaryOp) and isinstance(v.op, ast.Not)
        and _is_arg(v.operand, "zig_codec") for v in expr.values
    )
    if not (positive and negative):
        return False
    return any(
        isinstance(v, ast.Raise) or
        (isinstance(v, ast.Return) and isinstance(v.value, ast.Constant)
         and isinstance(v.value.value, int) and v.value.value != 0)
        for statement in node.body for v in _live_nodes(statement)
    )


def check_migration_driver_ast(source: str) -> list[str]:
    """Verify actual syntax and placement, not inert Zig-looking substrings."""
    problems: list[str] = []
    try:
        tree = ast.parse(source, filename=BATCH)
    except SyntaxError as exc:
        return [f"M1: migration driver is not valid Python: {exc.msg} line={exc.lineno}"]
    if not any(
        isinstance(node, ast.Import)
        and any(alias.name == "zig_codec_bridge" for alias in node.names)
        for node in tree.body
    ):
        problems.append("M1: no live top-level import zig_codec_bridge")
    runs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run"]
    mains = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"]
    if len(runs) != 1 or len(mains) != 1:
        return problems + ["M2-M5: require unique production run() and main()"]
    run, main = runs[0], mains[0]
    if not _bridge_calls(run, "build_transport"):
        problems.append("M2: no live pinned Zig build_transport() call in run()")
    if not _bridge_calls(run, "verify_t5"):
        problems.append("M3: no live Zig verify_t5() call in run()")
    if not any(_real_write_guard(node) for node in main.body):
        problems.append("M4: main() lacks active --write/--zig-codec fail-closed exit")
    # Must verify the candidate before it can enter the very same per-file
    # publish list. A comment or fake call elsewhere is not a witness.
    valid_flow = False
    for node in _live_nodes(run):
        if not isinstance(node, ast.For):
            continue
        verified = _bridge_calls(node, "verify_t5")
        staged = [
            n for n in _live_nodes(node)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "append"
            and isinstance(n.func.value, ast.Name)
            and n.func.value.id == "staged"
        ]
        if verified and staged and max(v.lineno for v in verified) < min(v.lineno for v in staged):
            valid_flow = True
    if not valid_flow:
        problems.append("M5: same-file staged.append() not preceded by live Zig verify_t5()")
    return problems


def check(root: Path) -> list[str]:
    problems: list[str] = []
    batch_path = root / BATCH
    bridge_path = root / BRIDGE
    if not batch_path.is_file():
        return [f"missing {BATCH}"]
    if not bridge_path.is_file():
        return [f"missing {BRIDGE}"]
    batch = batch_path.read_text(encoding="utf-8")
    bridge = bridge_path.read_text(encoding="utf-8")

    problems.extend(check_migration_driver_ast(batch))

    # M7 -- the parallel runner (if present) must go through the canonical driver
    # and add no second path to a published .sens.
    runner_path = root / "scripts/migrate-parallel.sh"
    if runner_path.is_file():
        runner = runner_path.read_text(encoding="utf-8")
        if "scripts/migrate-t5-batch.py" not in runner:
            problems.append("M7: migrate-parallel.sh does not call the canonical driver "
                            "scripts/migrate-t5-batch.py (a second migration path)")
        if "zig_codec_bridge" in runner or "sens_t5_codec" in runner:
            problems.append("M7: migrate-parallel.sh touches the codec directly instead of "
                            "delegating to the canonical driver (a second path to .sens)")

    # M6 -- the bridge itself fails closed.
    if "ZigCodecError" not in bridge:
        problems.append("M6: zig_codec_bridge.py has no fail-closed ZigCodecError")
    if '"0.16.0"' not in bridge or "PIN_DRIFT" not in bridge:
        problems.append("M6: zig_codec_bridge.py does not pin the compiler (0.16.0)")
    if "ZIG_CODEC_OUTPUT_EXISTS" not in bridge:
        problems.append("M6: zig_codec_bridge.py does not refuse to overwrite the binary")
    if "UNATTESTED_BINARY" not in bridge:
        problems.append("M6: zig_codec_bridge.py does not reject a non-attested binary")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except OSError as exc:
        print(f"MIGRATION_ZIG_ONLY_PATH_BLOCKED: {exc}", flush=True)
        return 1
    if problems:
        print("MIGRATION_ZIG_ONLY_PATH_BLOCKED:", flush=True)
        for problem in problems:
            print(" -", problem, flush=True)
        return 1
    print("MIGRATION_ZIG_ONLY_PATH_OK the sterile Zig corridor is the only path to "
          "a published .sens (build + certify + --write gate + fail-closed bridge)",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
