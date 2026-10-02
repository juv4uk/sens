#!/usr/bin/env python3
"""#2404 — test LIST as a projection of variadic LAMBDA rest binding.

Research only. This does not promote LIST from UNKNOWN.

Evidence layers:
1. live Lisp-owned source shape;
2. independent conformance fixtures for bare-symbol variadic lambda and LIST;
3. bounded adversarial arity model.

The claim under test:
  LIST(a*) == bare-rest-bind(a*) == a*
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "lib" / "core.lisp"
CORE4 = ROOT / "lib" / "core4.lisp"
CONF = ROOT / "tests" / "fixtures" / "conformance.lisp"
CENSUS = ROOT / "knowledge" / "function-status-census.json"


def normalized_source(text: str) -> str:
    return " ".join(
        line.split(";", 1)[0].strip()
        for line in text.splitlines()
        if line.split(";", 1)[0].strip()
    )


def source_shape_gate() -> None:
    expected = "(00001001 list (00001000 args args))"
    for path in (CORE, CORE4):
        text = normalized_source(path.read_text(encoding="utf-8"))
        assert expected in text, f"LIST rest-lambda definition missing in {path}"


def fixture_gate() -> None:
    text = CONF.read_text(encoding="utf-8")

    rest_expr = '((lambda args args) 1 2 3)'
    list_expr = '(list 1 2 3)'
    dotted_expr = '((lambda (a b . rest) rest) 1 2 3 4 5)'
    fixed_error_expr = '((lambda (a b . rest) a) 1)'

    for needle in (rest_expr, list_expr, dotted_expr, fixed_error_expr):
        assert needle in text, f"missing conformance fixture: {needle}"

    # Independent expected observations must remain explicit.
    assert '(expected . "(1 2 3)")' in text
    assert '(expected . "(3 4 5)")' in text
    assert '(error . "Arity")' in text

    # Constitutive status of bare-rest binding is important: LIST should depend
    # on an admitted binder law, not on a helper invented by this research.
    rest_pos = text.find(rest_expr)
    assert rest_pos >= 0
    rest_window = text[rest_pos:rest_pos + 500]
    assert '(role . "constitutive")' in rest_window
    assert '(axioms . (G2))' in rest_window


def bare_rest_bind(args: tuple[object, ...]) -> tuple[object, ...]:
    return args


def list_candidate(args: tuple[object, ...]) -> tuple[object, ...]:
    # Candidate factorization of LIST under the bare-symbol rest-binder law.
    return bare_rest_bind(args)


def dotted_rest_bind(
    fixed_count: int, args: tuple[object, ...]
) -> tuple[tuple[object, ...], tuple[object, ...]]:
    if len(args) < fixed_count:
        raise ValueError("Arity")
    return args[:fixed_count], args[fixed_count:]


def fixed_arity_bind(
    arity: int, args: tuple[object, ...]
) -> tuple[object, ...]:
    if len(args) != arity:
        raise ValueError("Arity")
    return args


def main() -> None:
    source_shape_gate()
    fixture_gate()

    corpus = (
        tuple(),
        (1,),
        (1, 2, 3),
        ("a", ("nested",), 3, None, "z"),
        (0, False, "x", (1, 2), ("tail",)),
    )

    cases = 0
    for args in corpus:
        expected = tuple(args)
        bound = bare_rest_bind(args)
        observed = list_candidate(args)
        assert bound == expected
        assert observed == expected
        assert observed == bound
        cases += 1

    fixed, rest = dotted_rest_bind(2, (1, 2, 3, 4, 5))
    assert fixed == (1, 2)
    assert rest == (3, 4, 5)
    assert rest != (1, 2, 3, 4, 5)

    fixed_arity_rejections = 0
    for args in (tuple(), (1,), (1, 2, 3)):
        try:
            fixed_arity_bind(2, args)
        except ValueError:
            fixed_arity_rejections += 1

    assert fixed_arity_bind(2, (1, 2)) == (1, 2)
    assert fixed_arity_rejections == 3

    # Guard against accidentally treating implementation derivability as
    # already-admitted semantic status.
    import json
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    row = next(
        r for r in census["rows"]
        if r["human_surface_optional"] == "LIST"
    )
    assert row["status"] == "UNKNOWN"

    print("SOURCE-CORE-LIST=REST-LAMBDA")
    print("SOURCE-CORE4-LIST=REST-LAMBDA")
    print("CONSTITUTIVE-G2-BARE-REST-FIXTURE=PASS")
    print("INDEPENDENT-G5-LIST-FIXTURE=PASS")
    print(f"ADVERSARIAL-ARITY-CASES={cases}")
    print("DOTTED-REST-DISTINCT=PASS")
    print(f"FIXED-ARITY-NEGATIVE-CASES={fixed_arity_rejections}")
    print("CANDIDATE-LAW=LIST(args*)=BARE-REST-BIND(args*)")
    print("INSTANCE-MAP-COST=STILL-UNKNOWN")
    print("SEMANTIC-PROMOTION=NONE")
    print("STATUS=PASS-LIST-REST-LAMBDA-CANDIDATE")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
