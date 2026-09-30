use sens::{eval_program, load_core_library, Session, Value};

fn eval_after_core(source: &str) -> Value {
    let mut session = Session::default();
    load_core_library(&mut session).expect("strict core must load");
    eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("{source}: {error}"))
        .value
}

const YES: &str = "(00000010 (00000001 ()))";
const NO: &str = "(00000010 (00000001 (00000000)))";

#[test]
fn variadic_or_recurses_through_exact_function8() {
    let source = format!("(10011011 {NO} {NO} {YES})");
    assert!(matches!(eval_after_core(&source), Value::PredicateBit(true)));
}

#[test]
fn variadic_and_recurses_through_exact_function8() {
    let source = format!("(10011010 {YES} {YES} {YES})");
    assert!(matches!(eval_after_core(&source), Value::PredicateBit(true)));
}

#[test]
fn variadic_or_short_circuits_unreachable_tail() {
    let source = format!("(10011011 {YES} definitely-unbound-tail {NO})");
    assert!(matches!(eval_after_core(&source), Value::PredicateBit(true)));
}

#[test]
fn variadic_and_short_circuits_unreachable_tail() {
    let source = format!("(10011010 {NO} definitely-unbound-tail {YES})");
    assert!(matches!(eval_after_core(&source), Value::PredicateBit(false)));
}
