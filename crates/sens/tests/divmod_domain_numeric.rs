use sens::{
    eval_program, load_core_library, BinaryNumber, Bit9, CoreD9, DomainIdentity, Session, Value,
};

fn d24(value: u32) -> Value {
    let mut bits = vec![0u8; 24];
    for index in 0..24 {
        bits[23 - index] = ((value >> index) & 1) as u8;
    }
    Value::BinaryNumber(
        BinaryNumber::from_numeric_domain_bits(24, &bits).expect("qualified D24 value"),
    )
}

fn d12(value: u16) -> Value {
    let mut bits = vec![0u8; 12];
    for index in 0..12 {
        bits[11 - index] = ((value >> index) & 1) as u8;
    }
    Value::BinaryNumber(
        BinaryNumber::from_numeric_domain_bits(12, &bits).expect("qualified D12 value"),
    )
}

#[test]
fn d9_quotient_remainder_code_is_first_class_for_d24_operands() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("current Core Lisp library");
    session.environment.define("ділене", d24(17));
    session.environment.define("дільник", d24(5));

    // The exact D9 function code is the value passed to the call site.
    // Its Ukrainian spelling is only a projection of these unchanged bits.
    let operation = DomainIdentity::D9(CoreD9::from_word(
        Bit9::new(0b110111111).expect("exact D9 quotient-remainder code"),
    ));
    assert_eq!(operation.width(), 9);
    assert_eq!(operation.packed_bits(), 0b110111111);
    session
        .environment
        .define("операція", Value::DomainIdentity(operation));

    let exact_quotient = eval_program("(частка ділене дільник)", &mut session)
        .expect("D5 exact rational division")
        .value;
    assert_eq!(exact_quotient.to_string(), "17/5");

    let result = eval_program("(операція ділене дільник)", &mut session)
        .expect("first-class exact D9 code call")
        .value;

    assert_eq!(result.to_string(), "(3 2)");
}

#[test]
fn truncate_executes_named_sens_sign_logic_for_d12() {
    // Справжній SENS eval: D8-ціла частка має йти через іменоване
    // мовне замикання, а не через виклик анонімної LAMBDA як значення.
    let mut session = Session::default();
    load_core_library(&mut session).expect("чинний Core4");
    session.environment.define("ділене", d12(7));
    session.environment.define("дільник", d12(3));
    for (program, expected) in [
        ("(округлити-до-нуля ділене дільник)", "2"),
        ("(округлити-до-нуля (змінити-знак ділене) дільник)", "-2"),
        ("(округлити-до-нуля ділене (змінити-знак дільник))", "-2"),
        (
            "(округлити-до-нуля (змінити-знак ділене) (змінити-знак дільник))",
            "2",
        ),
        ("(остача-зі-знаком ділене дільник)", "1"),
    ] {
        let result = eval_program(program, &mut session).unwrap_or_else(|error| {
            panic!("test_id=d8-truncate-named layer=SENS input={program} error={error}")
        });
        assert_eq!(
            result.value.to_string(),
            expected,
            "test_id=d8-truncate-named layer=SENS input={program} expected={expected} actual={}",
            result.value
        );
    }
}
