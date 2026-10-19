//! Виконання REPL без SID8/Sens8 і без повторного глобального D1 DEFINE.
//! Deutsch: D1-Werte in SENS-REPL mit echtem Reader/Evaluator.
//! English: Test D1 in real SENS meta-REPL and exact source reader.
use sens::{eval_parsed_expressions, eval_program, parse_mixed_exact_domain, Session};

#[test]
fn repl_core_loads_and_derives_d1_through_sens_meta_environment() {
    // Явний bootstrap: Session::default уже встановлює макрос;
    // load_core_library робить це сам для Session::bare без подвійної реєстрації.
    let mut session = Session::bare();
    sens::load_core_library(&mut session).expect("SENS core");
    sens::load_meta_evaluator_library(&mut session).expect("SENS meta evaluator");
    let source = std::fs::read_to_string(concat!(
        env!("CARGO_MANIFEST_DIR"), "/../../lib/repl-core.lisp"
    )).expect("read live SENS REPL source");
    let forms = parse_mixed_exact_domain(&source).expect("real mixed SENS reader");
    eval_parsed_expressions(&forms, &mut session).expect("load REPL with SENS evaluator");

    for (literal, expected) in [("так", Some(true)), ("ні", Some(false))] {
        let forms = parse_mixed_exact_domain(literal).expect("exact D1 reader");
        let verdict = eval_parsed_expressions(&forms, &mut session)
            .unwrap_or_else(|e| panic!("D1 {literal}: {e}"));
        assert_eq!(verdict.value.as_predicate_bit(), expected, "{literal}");
    }

    let empty_result = eval_program(
        "(порожній? (решта (репл-почати (як-є ()))))", &mut session
    ).expect("SENS REPL initial state");
    assert_eq!(empty_result.value.as_predicate_bit(), Some(true));

    for (word, expected) in [("так", Some(true)), ("ні", Some(false))] {
        let expression = format!(
            "(решта (репл-крок (як-є {word}) (репл-почати (як-є ()))))"
        );
        let verdict = eval_program(&expression, &mut session)
            .unwrap_or_else(|e| panic!("REPL step {word}: {e}"));
        assert_eq!(
            verdict.value.as_predicate_bit(), expected,
            "REPL D1 result after meta evaluation: {word}"
        );
    }
}
