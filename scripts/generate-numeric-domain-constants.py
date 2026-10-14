#!/usr/bin/env python3
"""Generate per-language numeric-domain constants from the owner-ratified contract.

SINGLE SOURCE (authority): contracts/numeric-domains-ratification.lisp
  (canonical-domain-names . (D24 D48 D96 D192))
  (initial-width . #d24)  (next-width . double)
  (domain-rule . "D(24 * 2^n), n >= 0")

CONSUMERS (generated, never hand-edited):
  research/zig-codecs/numeric_domains.zig          (Zig = sterile turnstile)
  crates/sens/src/numeric_domains_generated.rs     (Rust = holds bytes)
  scripts/numeric_domains_generated.py             (Python tooling/benches)

Zig is a TURNSTILE, not a REGISTRY: it carries codes, it does not decide them.
Assignment lives here, sourced from the ratified contract.

Usage:  python3 scripts/generate-numeric-domain-constants.py [--check]
        --check  exit 1 if any consumer diverges from the contract (fail-closed).
"""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "numeric-domains-ratification.lisp"
ZIG_OUT = ROOT / "research" / "zig-codecs" / "numeric_domains.zig"
RS_OUT = ROOT / "crates" / "sens" / "src" / "numeric_domains_generated.rs"
PY_OUT = ROOT / "scripts" / "numeric_domains_generated.py"

HEADER = "GENERATED from contracts/numeric-domains-ratification.lisp — DO NOT EDIT BY HAND."


def read_contract() -> dict:
    text = CONTRACT.read_text(encoding="utf-8")
    names = re.search(r"canonical-domain-names\s*\.\s*\(([^)]*)\)", text)
    if not names:
        raise SystemExit("contract: canonical-domain-names not found")
    widths = [int(m.group(1)) for m in re.finditer(r"D(\d+)", names.group(1))]
    rule = re.search(r'domain-rule\s*\.\s*"([^"]*)"', text)
    first = re.search(r"first-domain\s*\.\s*D(\d+)", text)
    if not widths or not rule or not first:
        raise SystemExit("contract: widths/rule/first-domain incomplete")
    # D(24 * 2^n): every rung must match the rule, else the contract is self-inconsistent.
    first_w = int(first.group(1))
    for i, w in enumerate(widths):
        if w != first_w * (2 ** i):
            raise SystemExit(f"contract: D{w} violates rule {rule.group(1)!r}")
    return {"widths": widths, "rule": rule.group(1), "first": first_w}


def zig(c: dict) -> str:
    ws = ", ".join(str(w) for w in c["widths"])
    return f"""//! {HEADER}
//! Authority: contracts/numeric-domains-ratification.lisp ({c['rule']}).
//! Zig is a turnstile: it carries these codes, it does not decide them.

const std = @import("std");

/// Canonical wide numeric-domain widths, in contract order.
pub const WIDE_WIDTHS = [_]u16{{ {ws} }};

/// The first (narrowest) ratified numeric domain width.
pub const FIRST_WIDTH: u16 = {c['first']};

/// Next rung from any ratified width (contract: next-width = double).
pub fn nextWidth(w: u16) u16 {{
    return w * 2;
}}

/// True iff `w` is a ratified wide numeric-domain width.
pub fn isWide(comptime w: u16) bool {{
    inline for (WIDE_WIDTHS) |x| {{
        if (w == x) return true;
    }}
    return false;
}}

test "generated widths obey the ratified rule" {{
    inline for (WIDE_WIDTHS, 0..) |w, i| {{
        try std.testing.expectEqual(FIRST_WIDTH * (@as(u16, 1) << @intCast(i)), w);
    }}
}}
"""


def rust(c: dict) -> str:
    ws = ", ".join(str(w) for w in c["widths"])
    return f"""// {HEADER}
// Authority: contracts/numeric-domains-ratification.lisp ({c['rule']}).
// Rust holds bytes; it does not decide codes.

/// Canonical wide numeric-domain widths, in contract order.
pub const NUMERIC_DOMAIN_WIDTHS: [u16; {len(c['widths'])}] = [ {ws} ];

/// The first (narrowest) ratified numeric domain width.
pub const FIRST_NUMERIC_DOMAIN_WIDTH: u16 = {c['first']};

/// Next rung from any ratified width (contract: next-width = double).
pub const fn next_width(w: u16) -> u16 {{ w * 2 }}
"""


def python(c: dict) -> str:
    ws = ", ".join(str(w) for w in c["widths"])
    return f'''# {HEADER}
# Authority: contracts/numeric-domains-ratification.lisp ({c['rule']}).

WIDE_WIDTHS = [{ws}]
FIRST_WIDTH = {c['first']}


def next_width(w):
    return w * 2


def is_wide(w):
    return w in WIDE_WIDTHS
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    c = read_contract()
    outs = {ZIG_OUT: zig(c), RS_OUT: rust(c), PY_OUT: python(c)}
    if args.check:
        bad = []
        for path, want in outs.items():
            have = path.read_text(encoding="utf-8") if path.exists() else ""
            if have != want:
                bad.append(path.relative_to(ROOT))
        if bad:
            print("DIVERGED from contract (run the generator):")
            for b in bad:
                print("  -", b)
            return 1
        print(f"numeric-domain constants match the contract ({len(c['widths'])} widths: {c['widths']})")
        return 0
    for path, text in outs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print("wrote", path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
