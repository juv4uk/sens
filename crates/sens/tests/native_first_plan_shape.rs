//! Справжнє виконання SENS для структури native-first-планів.
//! Ці перевірки не симулюють evaluator: джерело Lisp завантажується через SENS.

use sens::{
    eval_parsed_expressions, load_core_library,
    parse_mixed_exact_domain_machine_source, Session,
};

fn execute_current_sens(path: &str, library: &str, source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).expect("базова бібліотека SENS завантажується");
    let definitions = parse_mixed_exact_domain_machine_source(path, library)
        .expect("чинний точнодоменний reader має прочитати бібліотеку");
    eval_parsed_expressions(&definitions, &mut session)
        .expect("чинний SENS evaluator має завантажити Lisp визначення");
    let expression = parse_mixed_exact_domain_machine_source(path, source)
        .expect("чинний точнодоменний reader має прочитати виконувану форму");
    eval_parsed_expressions(&expression, &mut session)
        .unwrap_or_else(|error| panic!("помилка SENS evaluator: {error}; джерело: {source}"))
        .value
        .to_string()
}

fn execute(source: &str) -> String {
    execute_current_sens(
        "lib/machine/dispatch/native-first-execute.lisp",
        include_str!("../../../lib/machine/dispatch/native-first-execute.lisp"),
        source,
    )
}

#[test]
fn compound_plan_tag_does_not_reach_atom_only_d3_eq() {
    assert_eq!(
        execute("(нативний-стан-мітки-плану (як-є ((невідомий-тег) вміст)) (як-є native-plan))"),
        "distinct",
    );
    assert_eq!(
        execute("(нативний-стан-мітки-плану (як-є (native-plan вміст)) (як-є native-plan))"),
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
          ((атом? (як-є ())) (як-є відхилено)))
    "#;
    assert_eq!(execute(overlong), "відхилено");

    let exact = r#"
        (за-умовою
          ((нативний-список-трьох-елементів?
             (як-є (native-plan код дані)))
           (як-є прийнято))
          ((атом? (як-є ())) (як-є помилково-відхилено)))
    "#;
    assert_eq!(execute(exact), "прийнято");
}

#[test]
fn compound_tag_rejects_plan_without_executing_fallback() {
    let actual = execute("(нативне-виконати-план (як-є ((невідомий-тег) вміст)))");
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


/// Окремий завантажуваний SENS модуль точних доменних ключів.
fn execute_domain_key(source: &str) -> String {
    execute_current_sens(
        "lib/machine/dispatch/native-first.lisp",
        include_str!("../../../lib/machine/dispatch/native-first.lisp"),
        source,
    )
}

#[test]
fn three_bit_domain_keys_reject_malformed_lists() {
    let exact = r#"
        (за-умовою
          ((нативні-біти-трибітного-ключа?
             (сполучити (атом? (як-є ())) (сполучити (атом? (сполучити (як-є ()) (як-є ()))) (сполучити (атом? (сполучити (як-є ()) (як-є ()))) (як-є ()))))
             (атом? (як-є ())) (атом? (сполучити (як-є ()) (як-є ()))) (атом? (сполучити (як-є ()) (як-є ()))))
           (як-є прийнято))
          ((атом? (як-є ())) (як-є відхилено)))
    "#;
    assert_eq!(execute_domain_key(exact), "прийнято");

    for malformed in [
        "(сполучити (атом? (як-є ())) (як-є ()))",
        "(сполучити (атом? (як-є ())) (сполучити (атом? (сполучити (як-є ()) (як-є ()))) (сполучити (атом? (сполучити (як-є ()) (як-є ()))) (сполучити (атом? (як-є ())) (як-є ())))))",
        "(сполучити (атом? (як-є ())) (сполучити (атом? (сполучити (як-є ()) (як-є ()))) (сполучити (атом? (сполучити (як-є ()) (як-є ()))) 7)))",
    ] {
        let source = format!(
            "(за-умовою ((нативні-біти-трибітного-ключа? {malformed} (атом? (як-є ())) (атом? (сполучити (як-є ()) (як-є ()))) (атом? (сполучити (як-є ()) (як-є ())))) \
             (як-є помилково-прийнято)) ((атом? (як-є ())) (як-є відхилено)))"
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
    let bits = "(сполучити (атом? (як-є ())) (сполучити (атом? (сполучити (як-є ()) (як-є ()))) (сполучити (атом? (сполучити (як-є ()) (як-є ()))) (як-є ()))))";
    let exact = format!(
        "(за-умовою ((нативна-форма-трибітного-ключа? \
         (сполучити 3 (сполучити {bits} (як-є ()))) (атом? (як-є ())) (атом? (сполучити (як-є ()) (як-є ()))) (атом? (сполучити (як-є ()) (як-є ())))) \
         (як-є прийнято)) ((атом? (як-є ())) (як-є відхилено)))"
    );
    assert_eq!(execute_domain_key(&exact), "прийнято");

    for malformed_shape in [
        "(сполучити 3 (як-є ()))".to_string(),
        format!("(сполучити 4 (сполучити {bits} (як-є ())))"),
        format!("(сполучити 3 (сполучити {bits} (сполучити 9 (як-є ()))))"),
    ] {
        let source = format!(
            "(за-умовою ((нативна-форма-трибітного-ключа? {malformed_shape} (атом? (як-є ())) (атом? (сполучити (як-є ()) (як-є ()))) (атом? (сполучити (як-є ()) (як-є ())))) \
             (як-є помилково-прийнято)) ((атом? (як-є ())) (як-є відхилено)))"
        );
        assert_eq!(
            execute_domain_key(&source),
            "відхилено",
            "неправильна форма доменного ключа має відхилятися: {malformed_shape}"
        );
    }
}
