#!/usr/bin/env python3
"""#2181 — current macro substrate decomposition witness.

Research-only. This checker records where current macro behavior already relies
on ordinary language mechanisms and where host-only transformer mechanics
remain. It does not ratify D5 code 00101.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MACRO_LISP = ROOT / "lib" / "macro.lisp"
SUBSTRATE_RS = ROOT / "crates" / "sens" / "src" / "eval" / "macro_substrate.rs"
EVAL_RS = ROOT / "crates" / "sens" / "src" / "eval" / "mod.rs"
CLOSURES_RS = ROOT / "crates" / "sens" / "src" / "eval" / "closures.rs"
TESTS_RS = ROOT / "crates" / "sens" / "tests" / "macro_derivation.rs"


def require(text: str, needle: str, label: str) -> None:
    assert needle in text, f"missing {label}: {needle!r}"


def main() -> None:
    macro_lisp = MACRO_LISP.read_text(encoding="utf-8")
    substrate = SUBSTRATE_RS.read_text(encoding="utf-8")
    evaluator = EVAL_RS.read_text(encoding="utf-8")
    closures = CLOSURES_RS.read_text(encoding="utf-8")
    tests = TESTS_RS.read_text(encoding="utf-8")

    # Lisp-owned derivation uses existing DEFINE/LAMBDA/form construction and
    # names make-macro as the explicit temporary host substrate.
    require(macro_lisp, "(001 0011)", "canonical D4 DEFINE mechanism reference")
    require(macro_lisp, "(001 0010)", "canonical D4 LAMBDA mechanism reference")
    require(macro_lisp, "make-macro", "temporary transformer materializer")
    require(
        macro_lisp,
        "temporary host substrate with no SID",
        "documented non-language make-macro boundary",
    )

    # First host locus: closure -> macro/transformer materialization.
    require(substrate, "Value::Closure(closure)", "closure input")
    require(substrate, "Ok(Value::Macro(closure.clone()))", "macro value output")

    # Second host locus: call mode dispatch happens before ordinary argument eval.
    macro_dispatch = evaluator.index("Some(Value::Macro(closure))")
    first_argument_eval = evaluator.index(
        "values.push(evaluate(argument, environment)?)", macro_dispatch
    )
    assert macro_dispatch < first_argument_eval

    require(evaluator, "closures::apply_macro", "macro dispatch")

    # Raw arguments are quoted instead of evaluated, expansion is converted
    # back into code, then evaluated in the original calling environment.
    require(closures, "slots.push(quoted(argument)?); // Do NOT evaluate arguments", "raw operand capture")
    require(closures, "let expanded_value = evaluate(last, &local_environment)?;", "transformer-body evaluation")
    require(closures, "let expanded_expr = value_to_expr(expanded_value, span)?;", "data-to-code conversion")
    require(closures, "environment: calling_environment.clone()", "post-expansion caller environment")

    # Observable conformance already proves the raw-operand distinction.
    require(
        tests,
        "language_owned_defmacro_preserves_unevaluated_arguments",
        "unused/raw operand conformance",
    )
    require(tests, "never-defined", "non-evaluated operand witness")

    print("D5 transformer boundary witness: PASS")
    print("existing-language-capabilities=DEFINE,LAMBDA,form-construction,EVAL")
    print("host-mechanism-locus-1=Closure->Macro materialization")
    print("host-mechanism-locus-2=raw-form call mode")
    print("post-expansion-path=data->Expr->caller-environment-eval")
    print("observable-raw-operand-witness=present")
    print("candidate-semantic-compression=one-transformer-call-mode-capability")
    print("candidate-address=00101")
    print("NON-CONCLUSION: one capability vs two remains under falsification")
    print("NON-CONCLUSION: 00101 is not ratified")


if __name__ == "__main__":
    main()
