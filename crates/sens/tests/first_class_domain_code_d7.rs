//! Доменний код — першокласна функція: Д7 містить тільки ім'я зв'язування.
//! Реальний SENS-обчислювач, жодної Python/JSON семантики чи SID8-переходу.

use sens::{eval_exact_domain_program, DomainIdentity, ErrorKind, Session, Value};

fn execute(session: &mut Session, source: &str) -> Value {
    eval_exact_domain_program(source, session)
        .unwrap_or_else(|error| panic!(
            "test_id=FIRST_CLASS_DOMAIN_CODE layer=SENS input={source} actual_error={error}"
        ))
        .value
}

#[test]
fn d10_code_passed_through_d7_binding_keeps_its_callable_mechanism() {
    // Установити виконуваний механізм на точній 10-бітній координаті.
    let mut session = Session::bare();
    execute(&mut session, "(0011 0100001100 (0010 () (001 1)))");

    // 1101010 — одне 7-бітне клавіатурне ім'я, не семантичний код.
    // Значенням змінної є саме D10, а не псевдонім функції у Rust.
    let stored = execute(&mut session, "(0011 (1101010) 0100001100)");
    assert!(matches!(stored, Value::DomainIdentity(DomainIdentity::D10(_))),
        "test_id=D10_D7_FIRST_CLASS_STORE expected=D10 actual={stored}");

    // Голова виклику — текстова D7-зв'язка із значенням D10.
    let actual = execute(&mut session, "((1101010))");
    assert!(matches!(actual, Value::DomainIdentity(DomainIdentity::D1(_))),
        "test_id=D10_D7_FIRST_CLASS_CALL expected=D1:1 actual={actual}");
    assert_eq!(actual.to_string(), "1");
}

#[test]
fn an_unbound_mechanism_d7_value_is_not_made_callable() {
    let mut session = Session::bare();
    execute(&mut session, "(0011 (1101010) 1111111)");
    let error = eval_exact_domain_program("((1101010))", &mut session)
        .expect_err("D7 data identity is never a callable function by residency");
    assert_eq!(error.kind, ErrorKind::Type,
        "test_id=FIRST_CLASS_DOMAIN_NEGATIVE expected=Type actual={error}");
}

#[test]
fn ukrainian_d3_codes_are_passed_and_invoked_as_first_class_functions() {
    // Це справжня завантажувана Lisp-програма, не таблиця відповідностей
    // і не хостова симуляція. Д3-перше/решта надходять як значення.
    let source = include_str!("../../../lib/list-domain-first-class-compose.lisp");
    let mut session = Session::default();
    let actual = sens::eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!(
            "test_id=D3-FIRST-CLASS-UKR layer=SENS expected=2 actual_error={error}"
        )).value;
    assert_eq!(actual.to_string(), "2",
        "test_id=D3-FIRST-CLASS-UKR layer=SENS expected=2 actual={actual}");

    // Поміняти порядок застосування двох РІЗНИХ доменних функцій:
    // mutant не може отримати той самий результат.
    let before = "(застосувати-два-коди решта перше (список 1 2 3))";
    let after = "(застосувати-два-коди перше решта (список 1 2 3))";
    assert_eq!(source.matches(before).count(), 1,
        "test_id=D3-FIRST-CLASS-UKR expected=unique_negative_mutation_site");
    let mutant = source.replacen(before, after, 1);
    let mut negative_session = Session::default();
    match sens::eval_program(&mutant, &mut negative_session) {
        Ok(value) => assert_ne!(value.value.to_string(), "2",
            "test_id=D3-FIRST-CLASS-UKR layer=SENS mutant_was_accepted"),
        Err(_) => {} // Передати решта атомові також є коректним негативом Д3.
    }
}
