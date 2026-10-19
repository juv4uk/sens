//! Справжня перевірка REPL через SENS reader/evaluator, не Python-оракул.
//! Deutsch: REPL D1 ohne lokale Neudefinitionen.
//! English: REPL D1 without local redefinitions.

use sens::{eval_parsed_expressions, eval_program, parse_mixed_exact_domain, Session};

#[test]
fn repl_core_respects_ratified_d1_and_preserves_initial_state() {
    let mut session = Session::default();
    sens::load_core_library(&mut session).expect("SENS Core evaluator");
    sens::load_meta_evaluator_library(&mut session).expect("SENS meta evaluator");

    let source = std::fs::read_to_string(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../lib/repl-core.lisp"
    )).expect("read current REPL source with Rust I/O");
    let expressions = parse_mixed_exact_domain(&source)
        .expect("SENS reader must parse the entire Ukrainian REPL source");
    eval_parsed_expressions(&expressions, &mut session)
        .expect("SENS evaluator must load real REPL definitions");

    for (expression, expected) in [("так", Some(true)), ("ні", Some(false))] {
        let verdict = eval_program(expression, &mut session)
            .unwrap_or_else(|e| panic!("source {expression}: {e}"));
        assert_eq!(verdict.value.as_predicate_bit(), expected, "{expression}");
    }

    for expression in [
        "(порожній? (перше (репл-почати (як-є ()))))",
        "(порожній? (решта (репл-почати (як-є ()))))",
        "(тотожне? (перше (перше (репл-почати (як-є (маркер))))) (як-є маркер))",
    ] {
        let verdict = eval_program(expression, &mut session)
            .unwrap_or_else(|e| panic!("REPL law {expression}: {e}"));
        assert_eq!(
            verdict.value.as_predicate_bit(),
            Some(true),
            "SENS REPL state law: {expression}"
        );
    }
}
