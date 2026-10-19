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
          ((нативний-список-трьох-елементів?
             (як-є (native-plan код дані надлишок)))
           (як-є помилково-прийнято))
          (так (як-є відхилено)))
    "#;
    assert_eq!(execute(overlong), "відхилено");

    let exact = r#"
        (за-умовою
          ((нативний-список-трьох-елементів?
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

#[test]
fn malformed_native_result_tag_rejects_in_native_route() {
    let actual = execute(
        "(нативне-виконання-результат-плану (як-є (native-plan код дані)) (як-є ((пошкоджений-тег) дані)))",
    );
    assert_eq!(
        actual,
        "(execution-route native (status rejected) (detail (malformed-native-result ((пошкоджений-тег) дані))))",
        "Складений native-тег не повинен спричинити D3 EQ помилку або evaluator fallback"
    );

    let rejected = execute(
        "(нативне-виконання-результат-плану (як-є (native-plan код дані)) (як-є (rejected неприпустиме-кодування)))",
    );
    assert_eq!(
        rejected,
        "(execution-route native (status rejected) (detail (rejected неприпустиме-кодування)))",
    );
}


/// Цей SENS-код виконується в evaluator, а не моделюється Rust-логікою.
fn execute_domain_key(source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).expect("базова бібліотека SENS завантажується");
    eval_program(
        include_str!("../../../lib/machine/dispatch/native-first.lisp"),
        &mut session,
    )
    .expect("класифікатор native-first завантажується через SENS");
    eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("помилка SENS ключа D3: {error}; джерело: {source}"))
        .value
        .to_string()
}

#[test]
fn three_bit_domain_keys_reject_malformed_lists() {
    let exact = r#"
        (за-умовою
          ((нативні-біти-трибітного-ключа?
             (сполучити так (сполучити ні (сполучити ні (як-є ()))))
             так ні ні)
           (як-є прийнято))
          (так (як-є відхилено)))
    "#;
    assert_eq!(execute_domain_key(exact), "прийнято");

    for malformed in [
        "(сполучити так (як-є ()))",
        "(сполучити так (сполучити ні (сполучити ні (сполучити так (як-є ())))))",
        "(сполучити так (сполучити ні (сполучити ні 7)))",
    ] {
        let source = format!(
            "(за-умовою ((нативні-біти-трибітного-ключа? {malformed} так ні ні) \
             (як-є помилково-прийнято)) (так (як-є відхилено)))"
        );
        assert_eq!(
            execute_domain_key(&source),
            "відхилено",
            "неточний набір D3 бітів має бути відхилений SENS: {malformed}"
        );
    }
}

#[test]
fn domain_key_shape_requires_exact_width_and_two_fields() {
    let bits = "(сполучити так (сполучити ні (сполучити ні (як-є ()))))";
    let exact = format!(
        "(за-умовою ((нативна-форма-трибітного-ключа? \
         (сполучити 3 (сполучити {bits} (як-є ()))) так ні ні) \
         (як-є прийнято)) (так (як-є відхилено)))"
    );
    assert_eq!(execute_domain_key(&exact), "прийнято");

    for malformed_shape in [
        "(сполучити 3 (як-є ()))".to_string(),
        format!("(сполучити 4 (сполучити {bits} (як-є ())))"),
        format!("(сполучити 3 (сполучити {bits} (сполучити 9 (як-є ()))))"),
    ] {
        let source = format!(
            "(за-умовою ((нативна-форма-трибітного-ключа? {malformed_shape} так ні ні) \
             (як-є помилково-прийнято)) (так (як-є відхилено)))"
        );
        assert_eq!(
            execute_domain_key(&source),
            "відхилено",
            "неправильна форма доменного ключа має відхилятися: {malformed_shape}"
        );
    }
}
