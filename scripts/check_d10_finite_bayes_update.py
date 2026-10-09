#!/usr/bin/env python3
"""D10 research-only exact finite Bayesian update; no SENS runtime identity."""
from fractions import Fraction
import re

def exact(x):
    if isinstance(x, bool) or isinstance(x, float):
        raise ValueError("inexact input")
    if isinstance(x, (int, Fraction)):
        return Fraction(x)
    if isinstance(x, str) and re.fullmatch(r"[+-]?\d+(?:/[1-9]\d*)?", x):
        return Fraction(x)
    raise ValueError("invalid exact rational")

def update(prior, likelihood):
    if not isinstance(prior, (tuple, list)) or not isinstance(likelihood, (tuple, list)):
        raise ValueError("ordered sequences required")
    if not prior or len(prior) != len(likelihood):
        raise ValueError("nonempty aligned vectors required")
    p = tuple(map(exact, prior))
    l = tuple(map(exact, likelihood))
    if sum(p) != 1 or any(x < 0 or x > 1 for x in p + l):
        raise ValueError("invalid probabilities")
    z = sum((a*b for a,b in zip(p,l)), Fraction(0))
    if not z:
        raise ValueError("undefined zero evidence mass")
    return tuple(a*b/z for a,b in zip(p,l)), z
