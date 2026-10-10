#!/usr/bin/env python3
"""#2071 bīja3 epistemic-kernel checker.

Research-only. It does not prove global minimality of the eight seeds.

Purpose:
- derive intrinsic word facts from Foundation-0 instead of storing them twice;
- keep semantic capability evidence explicit and epistemically graded;
- ensure remove-one behavior fails closed to UNKNOWN instead of name/geometry fallback;
- guard the special 000/00000000 non-equivalence under current Contract 10.
"""

from __future__ import annotations

# Доказ біджа3 не може друкувати PASS, коли Python прибрав assert.
if not __debug__:
    raise SystemExit("BIJA3-KERNEL: BLOCKED — Python -O вимикає assert")

import csv
from pathlib import Path

MATRIX = Path("docs/research/2071-bija3-kernel.tsv")
EXPECTED = {f"{i:03b}" for i in range(8)}
ALLOWED_ADDRESS_STATUS = {"premise"}
ALLOWED_NECESSITY = {
    "open",
    "bounded-support-open",
    "under-attack",
    "strongest-current-support",
    "capability-supported-packaging-open",
}


def load_rows() -> list[dict[str, str]]:
    with MATRIX.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def intrinsic(word: str) -> dict[str, object]:
    return {
        "width": len(word),
        "bits": tuple(int(b) for b in word),
        "is_binary": all(b in "01" for b in word),
    }


def explain(word: str, rows: list[dict[str, str]]) -> str | None:
    # Deliberately only uses stored semantic evidence keyed by exact word.
    # No human name, numeric rank, Hamming geometry, zero-padding or prefix
    # fallback is allowed.
    for row in rows:
        if row["word"] == word:
            return row["capability"]
    return None


def main() -> None:
    rows = load_rows()
    assert len(rows) == 8, f"expected 8 rows, got {len(rows)}"

    words = [row["word"] for row in rows]
    assert set(words) == EXPECTED, f"wrong seed set: {sorted(words)}"
    assert len(set(words)) == 8

    # Foundation-0 intrinsic facts are derived, not separately authoritative.
    for row in rows:
        facts = intrinsic(row["word"])
        assert facts["is_binary"]
        assert facts["width"] == 3
        assert row["address_status"] in ALLOWED_ADDRESS_STATUS
        assert row["necessity_status"] in ALLOWED_NECESSITY
        assert row["capability"]
        assert row["capability_evidence"]
        assert row["evidence"]

    # Every current explanation is name-erased and exact-word keyed.
    capabilities = {row["word"]: explain(row["word"], rows) for row in rows}
    assert all(capabilities.values())

    # Remove-one discipline: removing the semantic evidence for a seed must
    # make that seed UNKNOWN. No bit-geometry or padded legacy form may fill it.
    for victim in EXPECTED:
        reduced = [row for row in rows if row["word"] != victim]
        assert explain(victim, reduced) is None, victim
        for survivor in EXPECTED - {victim}:
            assert explain(survivor, reduced) == capabilities[survivor]

    # Special ground guard: current Contract 10 says function 00000000 is not ().
    ground = next(row for row in rows if row["word"] == "000")
    assert ground["exact_representative_status"] == "exact-empty-list-premise"
    assert ground["legacy_padded_form"] == "00000000"
    assert ground["legacy_projection_status"] == "forbidden-as-meaning-preserving-projection"

    # The other seven historical zero-padded forms may be compatibility
    # candidates, but remain non-identical exact words.
    for row in rows:
        word = row["word"]
        padded = row["legacy_padded_form"]
        assert padded == word.zfill(8)
        assert padded != word
        if word != "000":
            assert row["legacy_projection_status"] == "compatibility-candidate-not-identity"

    # Width/bit pattern does not itself determine capability.
    # Same width for every row, yet eight distinct semantic evidence records.
    assert {intrinsic(w)["width"] for w in EXPECTED} == {3}
    assert len({row["capability"] for row in rows}) == 8

    print("BIJA3 epistemic-kernel checker: PASS")
    print("rows=8")
    print("intrinsic-width-facts=derived-not-stored-as-semantic-authority")
    print("address-status=premise for all 8")
    print("remove-one unknown-fallback checks=8 PASS")
    print("human-name fallback=0")
    print("geometry/numeric fallback=0")
    print("000->00000000 meaning-preserving projection=FORBIDDEN")
    print("exact-empty-list representative status=PREMISE")
    print("NON-CONCLUSION: bīja3 global minimality is not proven")
    print("NON-CONCLUSION: equal width does not define one homogeneous semantic algebra")


if __name__ == "__main__":
    main()
