# GENERATED from contracts/numeric-domains-ratification.lisp — DO NOT EDIT BY HAND.
# Authority: contracts/numeric-domains-ratification.lisp (D(24 * 2^n), n >= 0).

WIDE_WIDTHS = [24, 48, 96, 192]
FIRST_WIDTH = 24


def next_width(w):
    return w * 2


def is_wide(w):
    return w in WIDE_WIDTHS
