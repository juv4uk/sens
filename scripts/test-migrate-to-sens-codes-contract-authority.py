#!/usr/bin/env python3
"""Focused tests for migrate-to-sens-codes.py Contract 11.8 authority mode."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/migrate-to-sens-codes.py"

spec = importlib.util.spec_from_file_location("migrate_to_sens_codes", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def foundation():
    domains = {}
    for width in range(1, 10):
        count = 1 << width
        residents = {f"{n:0{width}b}": f"D{width}-{n}" for n in range(count)}
        if width == 7:
            residents.pop("0100001")
            residents.pop("0101010")
        domains[f"D{width}"] = {
            "width": width,
            "authority": f"test-D{width}",
            "residents": residents,
        }
    domains["D7"]["reserved_coordinates"] = ["0100001", "0101010"]
    return {
        "status": "owner-ratified",
        "authority": "#4008",
        "domains": domains,
    }


class Resolver:
    def resolve_head(self, token):
        if token.casefold() == "quote":
            identity = SimpleNamespace(
                domain="D3",
                width=3,
                bits="001",
                label="QUOTE",
            )
            return SimpleNamespace(
                resolved=True,
                current=identity,
                ambiguous=(),
                kind="my-lisp-surface",
            )
        return SimpleNamespace(
            resolved=False,
            current=None,
            ambiguous=(),
            kind="dynamic-symbol-head",
        )


def expect_blocked(fn, needle):
    try:
        fn()
    except module.BinaryMigrationError as exc:
        assert needle in str(exc), str(exc)
        return
    raise AssertionError("expected BinaryMigrationError")


def main():
    authority = module.build_exact_authority_index(foundation())

    module.validate_contract_binary_output("10 001 00 1 01 100000000\n", authority)
    expect_blocked(
        lambda: module.validate_contract_binary_output("10 0100001 01\n", authority),
        "unadmitted exact word",
    )
    expect_blocked(
        lambda: module.validate_contract_binary_output("1111111111\n", authority),
        "wider than W9",
    )

    rewritten, hits, _ = module.binary_rewrite(
        "(quote 1)",
        {},
        [],
        resolver=Resolver(),
        contract_authority=True,
        authority_index=authority,
    )
    assert rewritten == "10 001 00 1 01\n", rewritten
    assert hits[0].domain == "D3"
    assert hits[0].bits == "001"

    rewritten, _, _ = module.binary_rewrite(
        "(quote 100000000)",
        {},
        [],
        resolver=Resolver(),
        contract_authority=True,
        authority_index=authority,
    )
    assert "100000000" in rewritten
    module.validate_contract_binary_output(rewritten, authority)

    expect_blocked(
        lambda: module.binary_rewrite(
            "(#b001)",
            {},
            [],
            resolver=Resolver(),
            contract_authority=True,
            authority_index=authority,
        ),
        "binary reader wrapper",
    )

    print("MIGRATE-CONTRACT-AUTHORITY: PASS")


if __name__ == "__main__":
    main()
