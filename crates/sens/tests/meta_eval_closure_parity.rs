//! First code step of the evaluator ownership migration.
//! Keep the native evaluator as oracle and verify that the metacircular
//! evaluator preserves closure semantics.

mod common;

use sens::{
    eval_parsed_expressions, eval_program, load_core_library, parse_mixed_exact_domain, Session,
    Value,
};

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
    common::load_meta_evaluator_library(&mut session).expect("meta evaluator should load");

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

#[test]
fn meta_numeric_roots_are_exact_d24_values() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("core should load");
    common::load_meta_evaluator_library(&mut session).expect("meta evaluator should load");

    for (name, expected) in [("мета-число-нуль", "0"), ("мета-число-один", "1")] {
        let value = eval_program(name, &mut session)
            .unwrap_or_else(|error| panic!("{name} should evaluate: {error}"))
            .value;
        let Value::BinaryNumber(number) = &value else {
            panic!("{name} must be an exact D24+ number, got {value:?}");
        };
        assert_eq!(number.numeric_domain_width(), Some(24), "{name}");
        assert_eq!(number.to_decimal_string(), expected, "{name}");
    }
}

#[test]
fn mutual_group_closure_d1_is_computed_by_sens_not_bare_truth_names() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("ядро SENS");
    common::load_meta_evaluator_library(&mut session).expect("живий метаобчислювач");
    let program = include_str!("../../../lib/meta-eval-mutual.lisp");
    let forms = parse_mixed_exact_domain(program).expect("поточна укр проєкція");
    eval_parsed_expressions(&forms, &mut session)
        .expect("завантажити групові Lisp-визначення через SENS");

    for (source, expected) in [
        ("(це-замикання-рекурсивної-групи? (як-є ()))", false),
        (
            "(це-замикання-рекурсивної-групи? (як-є (ordinary-closure a)))",
            false,
        ),
        (
            "(це-замикання-рекурсивної-групи? (як-є (recursive-group-closure a)))",
            true,
        ),
        ("(визначення-лямбди-на-верхньому-рівні? (як-є ()))", false),
        (
            "(визначення-лямбди-на-верхньому-рівні? (як-є (unknown a b)))",
            false,
        ),
    ] {
        let forms = parse_mixed_exact_domain(source).expect("D3/D1 форма");
        let verdict = eval_parsed_expressions(&forms, &mut session)
            .unwrap_or_else(|error| panic!("test_id=meta-mutual-d1 source={source} actual={error}"))
            .value;
        assert_eq!(verdict.as_predicate_bit(), Some(expected), "{source}");
    }
}
