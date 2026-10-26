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
    // Український Lisp сам перевіряє декілька композицій першокласних Д3;
    // остання форма повертає точний Д1:так, а не старий числовий свідок 2.
    let source = include_str!("../../../lib/list-domain-first-class-compose.lisp");
    let mut session = Session::default();
    let actual = sens::eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!(
            "test_id=D3-FIRST-CLASS-UKR layer=SENS expected=D1:так actual_error={error}"
        )).value;
    assert_eq!(actual.as_predicate_bit(), Some(true),
        "test_id=D3-FIRST-CLASS-UKR layer=SENS expected=D1:так actual={actual}");

    // Псуємо САМ алгоритм композиції, не вигаданий старий виклик із числами.
    // SENS повинен відхилити його або повернути не Д1:так.
    let before = "(зовнішній (внутрішній дані))";
    let after = "(внутрішній (зовнішній дані))";
    assert_eq!(source.matches(before).count(), 1,
        "test_id=D3-FIRST-CLASS-UKR expected=unique_negative_mutation_site");
    let mutant = source.replacen(before, after, 1);
    let mut negative_session = Session::default();
    if let Ok(value) = sens::eval_program(&mutant, &mut negative_session) {
        assert_ne!(
            value.value.as_predicate_bit(),
            Some(true),
            "test_id=D3-FIRST-CLASS-UKR layer=SENS mutant_was_accepted"
        );
    } // Відхилення некоректного хвоста також є допустимим негативним результатом.
}

#[test]
fn last_atomic_run_uses_real_first_class_d3_predicate_without_copying_pairs() {
    // Сам Lisp виконує три незалежні закони для одного проходу за суфіксами.
    // Rust не імітує ATOM, CAR, CDR або семантику D1.
    let source = include_str!("../../../lib/list-last-atomic-run-first-class-zero-copy-general.lisp");
    let mut session = Session::default();
    let actual = sens::eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!(
            "test_id=D3-LAST-ATOMIC-RUN layer=SENS actual_error={error}"
        )).value;
    assert_eq!(actual.as_predicate_bit(), Some(true),
        "test_id=D3-LAST-ATOMIC-RUN layer=D1 expected=так actual={actual}");

    // Зміна лише реального критерію атомарності повинна бути виявлена
    // живими позитивними й негативними Lisp-свідками цього ж файлу.
    let before = "(критерій (перше елементи))";
    let after = "(хибне? (критерій (перше елементи)))";
    assert_eq!(source.matches(before).count(), 1,
        "test_id=D3-LAST-ATOMIC-RUN layer=mutant expected=unique_site");
    let mutant = source.replacen(before, after, 1);
    let mut negative = Session::default();
    if let Ok(value) = sens::eval_program(&mutant, &mut negative) {
        assert_ne!(
            value.value.as_predicate_bit(),
            Some(true),
            "test_id=D3-LAST-ATOMIC-RUN layer=SENS mutant_accepted"
        );
    } // Реальний SENS має право відкинути хибну форму через D3 CAR.
}
