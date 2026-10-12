"""Regression guards against resurrecting the flat SID8 function space."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_profile_follows_owner_ratified_d3():
    domain = (ROOT / "lib/domains/d3.lisp").read_text(encoding="utf-8")
    profile = (ROOT / "contracts/core-profile-contract.lisp").read_text(encoding="utf-8")
    rows = re.findall(
        r"(?m)^\s*\(([01]{3})\s+.*?\(LISP\s+(ATOM|EQ|COND)\)",
        domain,
    )
    expected = {name.lower(): bits for bits, name in rows}
    assert set(expected) == {"atom", "eq", "cond"}
    for name, bits in expected.items():
        pattern = rf'\({name}-object\s*\.\s*\(Core\.D3\s+"{bits}"\)\)'
        assert re.search(pattern, profile), f"{name}: profile differs from D3 law"


def test_retired_sid8_bootstrap_overlay_does_not_reenter_runtime():
    profile = (ROOT / "contracts/core-profile-contract.lisp").read_text(encoding="utf-8")
    assert "core1-sid8-bootstrap-overlay.lisp" not in profile
    assert not (ROOT / "lib/core1-sid8-bootstrap-overlay.lisp").exists()
