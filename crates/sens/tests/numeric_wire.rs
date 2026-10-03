use sens::{eval_program, Exactness, Session, Value};
use std::rc::Rc;

fn eval(source: &str) -> Value {
    eval_program(source, &mut Session::default())
        .unwrap_or_else(|error| panic!("evaluation failed: {error}\nsource: {source}"))
        .value
}

#[test]
fn exact_numbers_use_tagged_binary_canonical_wire() {
    assert_eq!(
        eval("(write-to-string 42)"),
        Value::String(Rc::from("#q2:101010/1")),
    );
    assert_eq!(
        eval("(write-to-string 1/2)"),
        Value::String(Rc::from("#q2:1/10")),
    );
    assert_eq!(
        eval("(write-to-string -5/4)"),
        Value::String(Rc::from("#q2:-101/100")),
    );
}

#[test]
fn tagged_binary_wire_round_trips_exact_numbers() {
    assert_eq!(
        eval("(read (write-to-string 42))"),
        Value::Number(42.0, Exactness::Exact),
    );
    assert_eq!(
        eval("(read (write-to-string 5/4))").to_string(),
        "5/4",
    );
    assert_eq!(
        eval("(read (write-to-string -5/4))").to_string(),
        "-5/4",
    );
}

#[test]
fn numeric_wire_never_aliases_the_exact_function_space() {
    let function = eval("(read \"00000000\")");
    assert!(function.as_legacy8_bits().is_some());

    let number = eval("(read \"#q2:00000000/1\")");
    assert!(number.as_legacy8_bits().is_none());
    assert_eq!(number, Value::Number(0.0, Exactness::Exact));
    assert_eq!(
        eval("(write-to-string (read \"#q2:00000000/1\"))"),
        Value::String(Rc::from("#q2:0/1")),
    );

    let max_function = eval("(read \"11111111\")");
    assert!(max_function.as_legacy8_bits().is_some());

    let numeric_255 = eval("(read \"#q2:11111111/1\")");
    assert!(numeric_255.as_legacy8_bits().is_none());
    assert_eq!(numeric_255, Value::Number(255.0, Exactness::Exact));
    assert_eq!(
        eval("(write-to-string 255)"),
        Value::String(Rc::from("#q2:11111111/1")),
    );
}

#[test]
fn arbitrary_precision_binary_wire_is_exact() {
    let numerator = format!("1{}", "0".repeat(160));
    let wire = format!("#q2:{numerator}/11");
    let program = format!("(write-to-string (read \"{wire}\"))");
    assert_eq!(eval(&program), Value::String(Rc::from(wire)));
}

#[test]
fn canonical_wire_recurses_without_changing_human_value_display() {
    assert_eq!(
        eval("(write-to-string (quote (42 1/2 00000000)))"),
        Value::String(Rc::from("(#q2:101010/1 #q2:1/10 00000000)")),
    );
    assert_eq!(eval("5/4").to_string(), "5/4");
    assert_eq!(eval("42").to_string(), "42");
}
