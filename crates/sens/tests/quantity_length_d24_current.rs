//! Живий SENS-свідок чинної української кількісної бібліотеки.
//! Не Python-eval, не історичний blob і не удавана фізична T5M-сертифікація.
use sens::{
    eval_parsed_expressions, load_core_library, parse,
    source_projection::project_ukr_decimal_integer_literals, Session,
};
const LIB: &str = include_str!("../../../lib/quantity.lisp");

fn length_definition() -> &'static str {
    let begin = LIB.find("(визначити науковий-список-довжина-дорівнює?")
        .expect("українська функція чинної бібліотеки");
    let end = LIB[begin..].find("\n(визначити науковий-шостий")
        .map(|offset| begin + offset)
        .expect("наступне визначення");
    &LIB[begin..end]
}

fn evaluate(session: &mut Session, expression: &str) -> sens::Value {
    let parsed = parse(expression).expect("чинний український Lisp reader");
    let projected = project_ukr_decimal_integer_literals(&parsed, expression)
        .expect("точні D24+ математичні операнди");
    eval_parsed_expressions(&projected, session)
        .unwrap_or_else(|error| panic!("SENS source={expression} error={error}"))
        .value
}

#[test]
fn quantity_length_d24_uses_real_sens_d1_and_rejects_malformed_tails() {
    let source = length_definition();
    assert!(!source.contains("(тотожне? залишок 0)"), "D3 EQ не є числовою рівністю");
    assert!(!source.contains("(так"), "не можна підміняти D1 голою назвою");
    assert!(!source.contains("(ні"), "не можна підміняти D1 голою назвою");

    let mut session = Session::default();
    load_core_library(&mut session).expect("справжній Core4");
    evaluate(&mut session, source);
    for (items, expected_length, expected) in [
        ("()", "0", true),
        ("()", "1", false),
        ("()", "-1", false),
        ("(a)", "1", true),
        ("(a)", "0", false),
        ("(a)", "2", false),
        ("(a b c)", "3", true),
        ("(a b c)", "2", false),
        ("(a b c)", "4", false),
        ("(a b c)", "-2", false),
        ("(a . tail)", "1", false),
        ("(a b . tail)", "2", false),
        ("tail", "0", false),
    ] {
        let call = format!(
            "(науковий-список-довжина-дорівнює? (як-є {items}) {expected_length})"
        );
        let value = evaluate(&mut session, &call);
        assert_eq!(value.as_predicate_bit(), Some(expected),
            "test_id=quantity-length layer=SENS input={call} expected=D1:{expected} actual={value}");
    }
}

fn unit_definition(name: &str) -> &'static str {
    let marker = format!("(визначити {name}");
    let begin = LIB.find(&marker).expect("визначення одиниці з чинного Lisp");
    let end = LIB[begin..].find("\n(визначити ")
        .map(|offset| begin + offset).unwrap_or(LIB.len());
    &LIB[begin..end]
}

fn prepare_unit_session(source: &str) -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("чинний SENS Core");
    evaluate(&mut session, source);
    session
}

#[test]
fn quantity_unit_constructor_selector_roundtrips_in_real_sens() {
    let current = [
        unit_definition("схема-одиниці-виміру"),
        unit_definition("створити-одиниця"),
        unit_definition("одиниця-розмірності"),
    ].join("\n");

    let old = "(список схема-одиниці-виміру розмірності)";
    let new = "(сполучити схема-одиниці-виміру розмірності)";
    assert!(current.contains(new), "чинний конструктор мусить зберігати плоскі виміри");
    let mutant = current.replacen(new, old, 1);
    assert_ne!(current, mutant);

    let mut correct = prepare_unit_session(&current);
    let mut legacy = prepare_unit_session(&mutant);
    for (dimensions, expected_record) in [
        ("()", "(unit-1)"),
        ("(метр)", "(unit-1 метр)"),
        ("(метр секунда)", "(unit-1 метр секунда)"),
    ] {
        let roundtrip = format!(
            "(однакові? (одиниця-розмірності (створити-одиниця (як-є {dimensions}))) (як-є {dimensions}))"
        );
        let full_record = format!(
            "(однакові? (створити-одиниця (як-є {dimensions})) (як-є {expected_record}))"
        );
        let actual = evaluate(&mut correct, &roundtrip);
        assert_eq!(actual.as_predicate_bit(), Some(true),
            "test_id=quantity-unit-roundtrip input={roundtrip} expected=D1:YES actual={actual}");
        let actual_record = evaluate(&mut correct, &full_record);
        assert_eq!(actual_record.as_predicate_bit(), Some(true),
            "test_id=quantity-unit-record input={full_record} expected=D1:YES actual={actual_record}");
        // Порожній випадок у старого конструктора теж неправильний: (unit-1 ()).
        let wrong = evaluate(&mut legacy, &roundtrip);
        assert_eq!(wrong.as_predicate_bit(), Some(false),
            "test_id=quantity-unit-mutant input={roundtrip} expected=D1:NO actual={wrong}");
    }
}

#[test]
fn quantity_unit_rejects_non_dimensions_in_real_sens() {
    // Перевіряємо власне SENS-eval, а не Python-скан чи форму тексту.
    // Коректна одиниця має складатися тільки з записів dimension-1.
    let current = [
        "схема-розмірності",
        "схема-одиниці-виміру",
        "науковий-внутрішній-символ?",
        "науковий-список-правильний?",
        "науковий-список-довжина-дорівнює?",
        "створити-розмірність",
        "розмірність?",
        "створити-одиниця",
        "науковий-всі-розмірності-коректні?",
        "одиниця-виміру?",
    ].iter().map(|name| unit_definition(name)).collect::<Vec<_>>().join("\n");

    let mut session = prepare_unit_session(&current);
    for (record, admitted) in [
        ("(створити-одиниця (як-є ()))", true),
        ("(створити-одиниця (список (створити-розмірність (як-є метр) 1)))", true),
        ("(створити-одиниця (як-є (невідома)))", false),
        ("(створити-одиниця (як-є ((dimension-1 метр))))", false),
        ("(створити-одиниця (як-є ((dimension-1 метр 1) . недопустимий-хвіст)))", false),
    ] {
        let input = format!("(одиниця-виміру? {record})");
        let actual = evaluate(&mut session, &input);
        if admitted {
            assert_eq!(actual.as_predicate_bit(), Some(true),
                "test_id=quantity-unit-valid layer=SENS input={input} expected=D1:1 actual={actual}");
        } else {
            assert!(matches!(actual, sens::Value::Nil),
                "test_id=quantity-unit-invalid layer=SENS input={input} expected=D3:NIL actual={actual}");
        }
    }

    // Негативний мутант повторює стару помилку: довільні елементи у
    // правильному списку були помилково визнані розмірностями.
    let guarded = "(науковий-всі-розмірності-коректні? (решта значення))";
    let obsolete = "(науковий-список-правильний? (решта значення))";
    assert_eq!(current.matches(guarded).count(), 1);
    let mutant = current.replacen(guarded, obsolete, 1);
    let mut old = prepare_unit_session(&mutant);
    let bad = "(одиниця-виміру? (створити-одиниця (як-є (невідома))))";
    let incorrect = evaluate(&mut old, bad);
    assert_eq!(incorrect.as_predicate_bit(), Some(true),
        "test_id=quantity-unit-old-mutant layer=SENS має виявляти хибний допуск");
}
