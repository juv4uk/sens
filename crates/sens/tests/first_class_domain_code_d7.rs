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
