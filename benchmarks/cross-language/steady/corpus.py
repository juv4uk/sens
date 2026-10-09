"""Shared five-workload corpus — aligned with #3601 / external_controls.py."""

from __future__ import annotations

CASES = ("fib", "loop", "ackermann", "closures", "evenodd")

PARAMS = {
    "fib": 16,
    "loop": 700,
    "ackermann": 3,
    "closures": 700,
    "evenodd": 700,
}

EXPECTED = {
    "fib": "987",
    "loop": "1400",
    "ackermann": "61",
    "closures": "2100",
    "evenodd": "1",
}

# Exact-domain SENS heads (Contract 11.6 lane — documentation only here).
DEFINE = "0011"       # D4
LAMBDA = "0010"       # D4
EQ = "101"            # D3
COND = "110"          # D3
PLUS = "01010"        # D5
DIFFERENCE = "01011"  # D5
TRUE_TEST = f"({EQ} 0 0)"


def python_source(name: str) -> str:
    n = PARAMS[name]
    limit = max(10_000, n * 4 + 100)

    if name == "fib":
        return f"""import sys
sys.setrecursionlimit({limit})

def fib(n):
    if n == 0:
        return 0
    if n == 1:
        return 1
    return fib(n - 1) + fib(n - 2)

def bench():
    return fib({n})
"""

    if name == "loop":
        return f"""import sys
sys.setrecursionlimit({limit})

def loop(n, acc):
    if n == 0:
        return acc
    return loop(n - 1, acc + 2)

def bench():
    return loop({n}, 0)
"""

    if name == "ackermann":
        return f"""import sys
sys.setrecursionlimit({limit})

def ack(m, n):
    if m == 0:
        return n + 1
    if n == 0:
        return ack(m - 1, 1)
    return ack(m - 1, ack(m, n - 1))

def bench():
    return ack(3, {n})
"""

    if name == "closures":
        return f"""import sys
sys.setrecursionlimit({limit})

def make_adder(k):
    def add(x):
        return x + k
    return add

add3 = make_adder(3)

def loop(n, acc):
    if n == 0:
        return acc
    return loop(n - 1, add3(acc))

def bench():
    return loop({n}, 0)
"""

    if name == "evenodd":
        return f"""import sys
sys.setrecursionlimit({limit})

def is_even(n):
    if n == 0:
        return 1
    return is_odd(n - 1)

def is_odd(n):
    if n == 0:
        return 0
    return is_even(n - 1)

def bench():
    return is_even({n})
"""

    raise KeyError(name)


def sens_source(name: str) -> str:
    """Exact D3/D4/D5 heads only — same shape as #3601 current_sens.py."""
    n = PARAMS[name]
    if name == "fib":
        return f"""({DEFINE} fib ({LAMBDA} (n)
  ({COND}
    (({EQ} n 0) 0)
    (({EQ} n 1) 1)
    ({TRUE_TEST} ({PLUS}
      (fib ({DIFFERENCE} n 1))
      (fib ({DIFFERENCE} n 2)))))))
(fib {n})
"""
    if name == "loop":
        return f"""({DEFINE} loop ({LAMBDA} (n acc)
  ({COND}
    (({EQ} n 0) acc)
    ({TRUE_TEST} (loop ({DIFFERENCE} n 1) ({PLUS} acc 2))))))
(loop {n} 0)
"""
    if name == "ackermann":
        return f"""({DEFINE} ack ({LAMBDA} (m n)
  ({COND}
    (({EQ} m 0) ({PLUS} n 1))
    (({EQ} n 0) (ack ({DIFFERENCE} m 1) 1))
    ({TRUE_TEST}
      (ack ({DIFFERENCE} m 1)
           (ack m ({DIFFERENCE} n 1)))))))
(ack 3 {n})
"""
    if name == "closures":
        return f"""({DEFINE} make-adder
  ({LAMBDA} (k) ({LAMBDA} (x) ({PLUS} x k))))
({DEFINE} add3 (make-adder 3))
({DEFINE} loop ({LAMBDA} (n acc)
  ({COND}
    (({EQ} n 0) acc)
    ({TRUE_TEST} (loop ({DIFFERENCE} n 1) (add3 acc))))))
(loop {n} 0)
"""
    if name == "evenodd":
        return f"""({DEFINE} is-even ({LAMBDA} (n)
  ({COND}
    (({EQ} n 0) 1)
    ({TRUE_TEST} (is-odd ({DIFFERENCE} n 1))))))
({DEFINE} is-odd ({LAMBDA} (n)
  ({COND}
    (({EQ} n 0) 0)
    ({TRUE_TEST} (is-even ({DIFFERENCE} n 1))))))
(is-even {n})
"""
    raise KeyError(name)
