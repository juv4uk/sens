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
