# GENERATED from contracts/numeric-domains-ratification.lisp — DO NOT EDIT BY HAND.
# Чинний D12+ закон: D(12 * 2^n), n >= 0.
# Механічний опис ширин; не виконання семантики SENS.

WIDE_WIDTHS = [12, 24, 48, 96, 192]
FIRST_WIDTH = 12
PHYSICAL_WIDE_WIDTHS = [24, 48, 96, 192]
FIRST_PHYSICAL_WIDTH = 24


def next_width(w):
    return w * 2


def is_wide(w):
    return w in WIDE_WIDTHS


def is_physically_supported(w):
    return w in PHYSICAL_WIDE_WIDTHS
