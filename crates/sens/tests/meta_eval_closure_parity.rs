//! First code step of the evaluator ownership migration.
//! Keep the native evaluator as oracle and verify that the metacircular
//! evaluator preserves closure semantics.

use sens::{eval_parsed_expressions, eval_program, load_core_library, parse_mixed_exact_domain, Session};

fn native(expr: &str) -> String {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("core should load");
    let forms = parse_mixed_exact_domain(expr).expect("SENS source should parse");
    eval_parsed_expressions(&forms, &mut session)
        .expect("native evaluator should succeed")
        .value
        .to_string()
}

fn meta(expr: &str) -> String {
    let mut session = Session::bare();
    sens::load_core_library(&mut session).expect("core should load");
    sens::load_meta_evaluator_library(&mut session)
        .expect("meta evaluator should load");

    let source = format!("(обчислити-мета-вираз (quote {}) (quote ()))", expr);
    eval_program(&source, &mut session)
        .expect("обчислити-мета-вираз should succeed")
        .value
        .to_string()
}

#[test]
fn closure_capture_has_native_parity() {
    // Both sides are checked independently against an authored expected
    // value, never against each other — a bug shared by both evaluators
    // must not hide behind a native-vs-meta parity check that stays green.
    let expr = "((функція (x) ((функція (y) x) 2)) 40)";
    let expected = "40";
    assert_eq!(native(expr), expected);
    assert_eq!(meta(expr), expected);
}
