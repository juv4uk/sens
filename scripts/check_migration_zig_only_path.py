#!/usr/bin/env python3
"""Guard: the sterile Zig corridor is the ONLY path to a published .sens (#5777/#5779).

Owner rule (2026-10-15): the Rust/Python<->SENS link crosses ONLY the sterile Zig
corridor. There are no other paths. If there were, contamination would reach the
SENS machine. So a physical .sens may be published ONLY after the pinned Zig
transport has certified the bytes; there is no silent Python fallback.

This is a STRUCTURAL, fail-closed checker (it does not run Zig):
M1  scripts/migrate-t5m-batch.py imports the corridor bridge `zig_codec_bridge`.
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
M8  the candidate staged for --write MUST originate in Zig carry_t5() in
    the same per-file loop; Python reference bytes must never be published.
M9  direct run(args) callers MUST reject --write without --zig-codec.

Exit 0 = MIGRATION_ZIG_ONLY_PATH_OK; exit 1 = MIGRATION_ZIG_ONLY_PATH_BLOCKED.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

BATCH = "scripts/migrate-t5m-batch.py"
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


def _write_time_truth(node: ast.AST) -> bool | None:
    """Evaluate only conditions established for --write with mandatory Zig.

    Unknown conditions cannot certify a required physical call. This is a
    conservative AST source gate, not a full Python control-flow proof.
    """
    if _is_arg(node, "write") or _is_arg(node, "zig_codec"):
        return True
    if isinstance(node, ast.Name) and node.id == "zig_binary":
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        inner = _write_time_truth(node.operand)
        return None if inner is None else not inner
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and len(node.comparators) == 1:
        if (isinstance(node.left, ast.Name) and node.left.id == "zig_binary"
                and isinstance(node.comparators[0], ast.Constant)
                and node.comparators[0].value is None):
            if isinstance(node.ops[0], ast.IsNot):
                return True  # --write requires --zig-codec; build must succeed
            if isinstance(node.ops[0], ast.Is):
                return False
    if isinstance(node, ast.BoolOp):
        values = [_write_time_truth(value) for value in node.values]
        if isinstance(node.op, ast.And):
            if False in values:
                return False
            return True if all(value is True for value in values) else None
        if isinstance(node.op, ast.Or):
            if True in values:
                return True
            return False if all(value is False for value in values) else None
    return None


def _write_reachable_nodes(root: ast.AST):
    """Only statement paths guaranteed live on the admitted --write route."""
    yield root
    if isinstance(root, ast.If):
        condition = _write_time_truth(root.test)
        if condition is None:
            return  # Unknown branch may skip the verifier: not evidence
        chosen = root.body if condition else root.orelse
        for statement in chosen:
            yield from _write_reachable_nodes(statement)
        return
    for child in ast.iter_child_nodes(root):
        yield from _write_reachable_nodes(child)



def _is_named(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _uses_t5m_by_default(node: ast.Call) -> bool:
    """An explicit codec may not route the current migration through legacy T5."""
    codec = next((kw.value for kw in node.keywords if kw.arg == "codec"), None)
    return codec is None or (
        isinstance(codec, ast.Constant) and codec.value == "t5m"
    )


def _is_zig_carry(node: ast.AST) -> bool:
    """Only canonical Zig T5M carry of the exact staged projection is evidence."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "carry_t5"
        and _is_named(node.func.value, "zig_codec_bridge")
        and len(node.args) == 2
        and _uses_t5m_by_default(node)
        and all(keyword.arg in ("codec", "trusted_source_sha256")
                for keyword in node.keywords)
        and _is_named(node.args[0], "zig_binary")
        and _is_named(node.args[1], "projection")
    )


def _is_verified_packed(node: ast.AST) -> bool:
    """The pre-publish verifier must check the SAME Zig-minted T5M bytes."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "verify_t5"
        and _is_named(node.func.value, "zig_codec_bridge")
        and len(node.args) == 2
        and _is_named(node.args[0], "zig_binary")
        and _is_named(node.args[1], "packed")
        and _uses_t5m_by_default(node)
        and all(keyword.arg in ("codec", "trusted_source_sha256")
                for keyword in node.keywords)
    )


def _is_staging_packed(node: ast.AST) -> bool:
    """Publisher's 5-field tuple must actually contain the Zig bytes."""
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "append"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "staged"
        and len(node.args) == 1
    ):
        return False
    record = node.args[0]
    return (
        isinstance(record, ast.Tuple)
        and len(record.elts) == 5
        and isinstance(record.elts[3], ast.Name)
        and record.elts[3].id == "packed"
    )


def _has_zig_mint_on_write(run: ast.FunctionDef) -> bool:
    """Conservative source proof of one real Zig byte producer before staging.

    A dead/dry-run call, Python-packed replacement, multiple live writes to
    packed, or staged reference bytes never establishes release evidence.
    This is AST structural evidence, not a Zig runtime or SENS semantic PASS.
    """
    for loop in ast.walk(run):
        if not isinstance(loop, ast.For):
            continue
        live = list(_write_reachable_nodes(loop))
        staged = [node for node in live if _is_staging_packed(node)]
        if not staged:
            continue
        packed_assignments = [
            node for node in live
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            and any(
                isinstance(target, ast.Name) and target.id == "packed"
                for target in (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
            )
        ]
        if len(packed_assignments) != 1:
            continue
        mint = packed_assignments[0]
        if (_is_zig_carry(mint.value)
                and mint.lineno < min(s.lineno for s in staged)):
            return True
    return False


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
    if not any(_real_write_guard(node) for node in run.body):
        problems.append("M9: direct run() lacks active --write/--zig-codec fail-closed exit")
    if not _has_zig_mint_on_write(run):
        problems.append(
            "M8: --write staged bytes are not exclusively minted by live "
            "zig_codec_bridge.carry_t5() using T5M in the same per-file loop "
            "(Python reference and unproven staging forbidden)"
        )
    # Prove that the physical Zig call is reachable ON THE WRITE PATH,
    # before the same file is staged. A dry-run-only call is no receipt.
    valid_flow = False
    for node in _live_nodes(run):
        if not isinstance(node, ast.For):
            continue
        write_nodes = list(_write_reachable_nodes(node))
        verified = [
            n for n in write_nodes if _is_verified_packed(n)
        ]
        staged = [
            n for n in write_nodes
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "append"
            and isinstance(n.func.value, ast.Name)
            and n.func.value.id == "staged"
        ]
        if verified and staged and max(v.lineno for v in verified) < min(v.lineno for v in staged):
            valid_flow = True
    if not valid_flow:
        problems.append(
            "M5: layer=transport test_id=migration-zig-verified-packed "
            "--write staged.append() requires a preceding write-reachable "
            "zig_codec_bridge.verify_t5(zig_binary, packed) using T5M in the same "
            "per-file loop; repro=python3 -m unittest discover -s tests "
            "-p test_check_migration_zig_only_path.py -v"
        )
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
        if "scripts/migrate-t5m-batch.py" not in runner:
            problems.append("M7: migrate-parallel.sh does not call the canonical driver "
                            "scripts/migrate-t5m-batch.py (a second migration path)")
        if "zig_codec_bridge" in runner or "sens_t5_t5m_codec" in runner:
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
    if not all(re.search(pattern, bridge) for pattern in (
        r"def carry_t5\([\s\S]*?codec:\s*str\s*=\s*\"t5m\"",
        r"def verify_t5\([\s\S]*?codec:\s*str\s*=\s*\"t5m\"",
    )):
        problems.append("M10: physical bridge does not default both carry and verify to T5M")

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
    print("MIGRATION_ZIG_ONLY_PATH_OK Zig MINTS published .sens: "
          "build + live carry + certify + run/write guards + fail-closed bridge",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
