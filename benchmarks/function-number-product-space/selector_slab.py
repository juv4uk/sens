#!/usr/bin/env python3
"""#3369 / #3321 — D6 selector product-slab witness."""

import json

ROOTS_W3 = (0b011, 0b100)  # numeric roots only
PATHS_W3 = tuple(range(8))

EXPECTED_D6 = {
    0b011000, 0b011001, 0b011010, 0b011011,
    0b011100, 0b011101, 0b011110, 0b011111,
    0b100000, 0b100001, 0b100010, 0b100011,
    0b100100, 0b100101, 0b100110, 0b100111,
}

generated = {(r << 3) | p for r in ROOTS_W3 for p in PATHS_W3}
mask6 = 0b111111
complemented = {x ^ mask6 for x in generated}

rows = [
    {
        "root_w3": format(r, "03b"),
        "path_w3": format(p, "03b"),
        "d6": format((r << 3) | p, "06b"),
        "complement_d6": format(((r << 3) | p) ^ mask6, "06b"),
    }
    for r in ROOTS_W3
    for p in PATHS_W3
]

assert generated == EXPECTED_D6
assert complemented == EXPECTED_D6
assert len(generated) == 16
assert min(generated) == 0b011000
assert max(generated) == 0b100111

report = {
    "issue": "#3369",
    "consumer": "#3321",
    "formula": "d6_selector = concat(root_w3, path_w3)",
    "roots": [format(x, "03b") for x in ROOTS_W3],
    "path_space": "W3 = 000..111",
    "generated_count": len(generated),
    "expected_count": len(EXPECTED_D6),
    "exact_match": generated == EXPECTED_D6,
    "contiguous_interval": {
        "min_bits": format(min(generated), "06b"),
        "max_bits": format(max(generated), "06b"),
        "min_decimal": min(generated),
        "max_decimal": max(generated),
    },
    "closed_under_full_complement": complemented == generated,
    "rows": rows,
    "general_closed_form": (
        "S_w = { concat(r,p) | r in {011,100}, p in W(w-3) }, "
        "|S_w| = 2^(w-2), for w>=3"
    ),
    "predicted_counts": {
        "W3": 2,
        "W4": 4,
        "W5": 8,
        "W6": 16,
        "W7": 32,
        "W8": 64,
    },
}

print(json.dumps(report, indent=2, sort_keys=True))
