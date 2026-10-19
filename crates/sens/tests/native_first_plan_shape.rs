//! Справжнє виконання SENS для структури native-first-планів.
//! Ці перевірки не симулюють evaluator: джерело Lisp завантажується через SENS.

use sens::{eval_program, load_core_library, Session};

fn execute(source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).expect("базова бібліотека SENS завантажується");
    eval_program(
        include_str!("../../../lib/machine/dispatch/native-first-execute.lisp"),
        &mut session,
    )
    .expect("native-first execute Lisp завантажується");
    eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("помилка SENS evaluator: {error}; джерело: {source}"))
        .value
        .to_string()
}

#[test]
fn compound_plan_tag_does_not_reach_atom_only_d3_eq() {
    assert_eq!(
        execute("(native-first-plan-tag-state (як-є ((невідомий-тег) вміст)) (як-є native-plan))"),
        "distinct",
    );
    assert_eq!(
        execute("(native-first-plan-tag-state (як-є (native-plan вміст)) (як-є native-plan))"),
        "same",
    );
}

#[test]
fn overlong_plan_is_not_a_three_element_list() {
    let overlong = r#"
        (за-умовою
          ((native-first-proper-list-length-3?
             (як-є (native-plan код дані надлишок)))
           (як-є помилково-прийнято))
          (так (як-є відхилено)))
    "#;
    assert_eq!(execute(overlong), "відхилено");

    let exact = r#"
        (за-умовою
          ((native-first-proper-list-length-3?
             (як-є (native-plan код дані)))
           (як-є прийнято))
          (так (як-є помилково-відхилено)))
    "#;
    assert_eq!(execute(exact), "прийнято");
}

#[test]
fn compound_tag_rejects_plan_without_executing_fallback() {
    let actual = execute("(native-first-execute-plan (як-є ((невідомий-тег) вміст)))");
    assert!(
        actual.starts_with("(execution-route invalid-plan (status rejected)"),
        "некоректний план має відхилятися в SENS, а не падати на D3 EQ: {actual}"
    );
}
