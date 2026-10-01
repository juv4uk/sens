#!/usr/bin/env python3
"""#1962: quantify selector-path compression against old fixed-8 identities.

Research-only. Uses executable genealogy facts already present in
experiments/function-genealogy.lisp; this script measures representation cost.
"""

ALIASES = {
    "second":  "1011",     # CADR
    "third":   "10111",    # CADDR
    "fourth":  "101111",   # CADDDR
    "fifth":   "1011111",  # CADDDDR
    "caar":    "1010",     # CAAR
    "cadr":    "1011",     # same semantics as second
    "cddr":    "1101",     # CDDR
    "cadddr":  "101111",   # same closure as fourth
}

OLD_IDS = {
    "second": "00101111",
    "third": "00110000",
    "fourth": "00110001",
    "fifth": "00110010",
    "caar": "00110011",
    "cadr": "00110100",
    "cddr": "00110101",
    "cadddr": "00110110",
}


def main() -> None:
    assert set(ALIASES) == set(OLD_IDS)

    print("name\told8\tnew-path\tnew-bits\tsaved-per-use")
    for name in OLD_IDS:
        new = ALIASES[name]
        print(f"{name}\t{OLD_IDS[name]}\t{new}\t{len(new)}\t{8-len(new)}")

    old_identity_count = len(OLD_IDS)
    unique_paths = set(ALIASES.values())
    new_unique_count = len(unique_paths)

    old_once_bits = sum(len(code) for code in OLD_IDS.values())
    new_once_bits = sum(len(code) for code in ALIASES.values())

    # If aliases are normalized to semantic identity, count each unique path once.
    unique_path_bits = sum(len(code) for code in unique_paths)

    assert ALIASES["second"] == ALIASES["cadr"]
    assert ALIASES["fourth"] == ALIASES["cadddr"]
    assert old_identity_count == 8
    assert new_unique_count == 6
    assert old_once_bits == 64
    assert new_once_bits == 40
    assert unique_path_bits == 30

    print()
    print(f"old registered identities: {old_identity_count}")
    print(f"unique selector semantics: {new_unique_count}")
    print(f"duplicate identities eliminated: {old_identity_count-new_unique_count}")
    print(f"one use of each old spelling: {old_once_bits} -> {new_once_bits} identifier bits")
    print(f"saving: {old_once_bits-new_once_bits} bits = {(old_once_bits-new_once_bits)/old_once_bits:.1%}")
    print(f"unique semantic dictionary footprint: {old_once_bits} -> {unique_path_bits} bits")
    print(f"semantic-path saving: {old_once_bits-unique_path_bits} bits = {(old_once_bits-unique_path_bits)/old_once_bits:.1%}")
    print()
    print("PASS: selector paths compress both width and duplicate identities.")
    print("Separator/framing cost is intentionally excluded from both sides.")


if __name__ == "__main__":
    main()
