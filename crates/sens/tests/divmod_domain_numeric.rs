use sens::{eval_program, load_core_library, BinaryNumber, Session, Value};

fn d24(value: u32) -> Value {
    let mut bits = vec![0u8; 24];
    for index in 0..24 {
        bits[23 - index] = ((value >> index) & 1) as u8;
    }
    Value::BinaryNumber(
        BinaryNumber::from_numeric_domain_bits(24, &bits).expect("qualified D24 value"),
    )
}

#[test]
fn divmod_returns_integer_quotient_and_euclidean_remainder_for_d24_operands() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("current Core Lisp library");
    session.environment.define("dividend", d24(17));
    session.environment.define("divisor", d24(5));

    let exact_quotient = eval_program("(частка dividend divisor)", &mut session)
        .expect("D5 exact rational division")
        .value;
    assert_eq!(exact_quotient.to_string(), "17/5");

    let result = eval_program("(divmod dividend divisor)", &mut session)
        .expect("D24+ divmod call")
        .value;

    assert_eq!(result.to_string(), "(3 2)");
}
