"""Racket CS source adapter for the shared cross-language benchmark (#1548).

The algorithms and parameters intentionally mirror #1546 exactly.  This module
only renders source; phase semantics live in racket_driver.rkt.
"""

from __future__ import annotations


def source(name: str, params: dict[str, int]) -> str:
    n = params["N"]

    if name == "fib":
        body = f"""
  (define (fib n)
    (cond
      [(= n 0) 0]
      [(= n 1) 1]
      [else (+ (fib (- n 1)) (fib (- n 2)))]))
  (define (bench) (fib {n}))
"""

    elif name == "loop":
        body = f"""
  (define (loop n acc)
    (if (= n 0)
        acc
        (loop (- n 1) (+ acc 2))))
  (define (bench) (loop {n} 0))
"""

    elif name == "ackermann":
        body = f"""
  (define (ack m n)
    (cond
      [(= m 0) (+ n 1)]
      [(= n 0) (ack (- m 1) 1)]
      [else (ack (- m 1) (ack m (- n 1)))]))
  (define (bench) (ack 3 {n}))
"""

    elif name == "closures":
        body = f"""
  (define (make-adder k)
    (lambda (x) (+ x k)))
  (define add3 (make-adder 3))
  (define (loop n acc)
    (if (= n 0)
        acc
        (loop (- n 1) (add3 acc))))
  (define (bench) (loop {n} 0))
"""

    elif name == "evenodd":
        body = f"""
  (define (is-even n)
    (if (= n 0)
        1
        (is-odd (- n 1))))
  (define (is-odd n)
    (if (= n 0)
        0
        (is-even (- n 1))))
  (define (bench) (is-even {n}))
"""

    else:
        raise KeyError(name)

    return (
        "(module sens-cross-bench racket/base\n"
        "  (provide bench)\n"
        + body
        + ")\n"
    )
