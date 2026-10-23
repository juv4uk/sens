mod common;

use sens::{eval_program, load_core_library, Session};

fn meta_eval(source: &str) -> String {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("core bootstrap");
    common::load_meta_evaluator_library(&mut session).expect("meta-eval bootstrap");
    eval_program(
        &format!("(обчислити-мета-вираз (quote {source}) (quote ()))"),
        &mut session,
    )
    .unwrap_or_else(|error| panic!("host failure while meta-evaluating {source}: {error}"))
    .value
    .to_string()
}

fn native_value(source: &str) -> String {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("core bootstrap");
    eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("reference evaluator failed for {source}: {error}"))
        .value
        .to_string()
}

#[test]
fn error_shaped_user_data_keeps_value_provenance() {
    // native and meta are each checked against the same authored expected
    // value independently, never against each other.
    let source = "((функція (значення) (перше значення)) (як-є (помилка звичайні-дані)))";
    let expected = "помилка";
    assert_eq!(native_value(source), expected);
    assert_eq!(meta_eval(source), expected);
}

#[test]
fn fail_shaped_user_data_is_not_internal_failure() {
    let source = "((функція (значення) (перше значення)) (як-є (невдача звичайні-дані)))";
    let expected = "невдача";
    assert_eq!(native_value(source), expected);
    assert_eq!(meta_eval(source), expected);
}
