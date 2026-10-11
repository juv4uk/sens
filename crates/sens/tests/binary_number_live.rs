use sens::{
    decode_binary_frame, encode_binary_frame, eval_program, fasl_decode_program,
    fasl_encode_program, parse, wire_decode_program, wire_encode_program, BinaryFrame,
    BinaryNumber, Bit1, Bit2, DomainIdentity, Expr, ExprKind, PredicateBit, PresentationLanguage,
    Racana2, Session, Span, Value, render_value_for_presentation,
};

#[test]
fn explicit_binary_source_is_canonical_binary_number_not_rational() {
    let parsed = parse("#b00101").expect("binary Number source parses");
    assert_eq!(parsed.len(), 1);
    match &parsed[0].kind {
        ExprKind::BinaryNumber(number) => assert_eq!(number.bits(), "101"),
        other => panic!("expected BinaryNumber AST, got {other:?}"),
    }

    let value = eval_program("#b00101", &mut Session::default())
        .expect("binary Number evaluates")
        .value;
    match &value {
        Value::BinaryNumber(number) => {
            assert_eq!(number.bits(), "101");
            assert_eq!(number.to_decimal_string(), "5");
        }
        other => panic!("expected BinaryNumber Value, got {other:?}"),
    }

    assert_eq!(value.to_canonical_wire_string(), "#b101");
    assert_eq!(
        render_value_for_presentation(&value, PresentationLanguage::English),
        "5"
    );
}

#[test]
fn d5_add_mul_and_order_use_binary_number_path() {
    let mut session = Session::default();

    let sum = eval_program("(+ #b10 #b11)", &mut session)
        .expect("D5 PLUS accepts canonical binary Number")
        .value;
    assert_eq!(
        sum,
        Value::BinaryNumber(BinaryNumber::parse("101").unwrap())
    );

    let product = eval_program("(* #b11 #b10)", &mut session)
        .expect("D5 TIMES accepts canonical binary Number")
        .value;
    assert_eq!(
        product,
        Value::BinaryNumber(BinaryNumber::parse("110").unwrap())
    );

    let less = eval_program("(< #b10 #b11)", &mut session)
        .expect("D5 LESSP returns D1")
        .value;
    assert_eq!(
        less,
        Value::DomainIdentity(DomainIdentity::D1(PredicateBit::from_word(
            Bit1::new(1).unwrap()
        )))
    );

    let greater = eval_program("(> #b10 #b11)", &mut session)
        .expect("D5 GREATERP returns D1")
        .value;
    assert_eq!(
        greater,
        Value::DomainIdentity(DomainIdentity::D1(PredicateBit::from_word(
            Bit1::new(0).unwrap()
        )))
    );
}

#[test]
fn binary_number_refuses_implicit_legacy_numeric_coercion() {
    let error = eval_program("(+ #b10 3)", &mut Session::default())
        .expect_err("mixed canonical/legacy numerics must fail closed");
    assert_eq!(error.kind, sens::ErrorKind::Type);
}

#[test]
fn equal_rendering_does_not_collapse_binary_and_legacy_number_carriers() {
    let mut session = Session::default();

    let binary = eval_program("#b1001000", &mut session)
        .expect("binary Number")
        .value;
    let legacy = eval_program("#d72", &mut session)
        .expect("legacy/mechanical exact Number")
        .value;

    assert_eq!(
        render_value_for_presentation(&binary, PresentationLanguage::English),
        "72"
    );
    assert_eq!(
        render_value_for_presentation(&legacy, PresentationLanguage::English),
        "72"
    );
    assert_ne!(binary, legacy, "presentation equality must not erase carrier identity");

    // Equality of runtime carriers is not a surface/callability grant.
    // Existing Core does NOT admit the legacy EQUAL? dispatch code here.
    assert_eq!(binary, binary.clone());
    assert_eq!(legacy, legacy.clone());
    for source in [
        "(equal? #b1001000 #d72)",
        "(equal? #d72 #d72)",
    ] {
        let err = eval_program(source, &mut session)
            .expect_err("unadmitted EQUAL? callable must fail closed");
        assert_eq!(err.kind, sens::ErrorKind::Type);
    }
}

#[test]
fn binary_number_round_trips_fasl_wire_and_binary_frame_as_exact_bits() {
    let parsed = parse("#b101001").expect("parse");
    let hash = [0x30u8; 32];

    let fasl = fasl_encode_program(&parsed, &hash);
    let (fasl_decoded, decoded_hash) = fasl_decode_program(&fasl).expect("FASL");
    assert_eq!(decoded_hash, hash);
    assert_eq!(fasl_decoded.len(), parsed.len());
    assert_eq!(fasl_decoded[0].kind, parsed[0].kind);

    let wire = wire_encode_program(&parsed);
    let wire_decoded = wire_decode_program(&wire).expect("wire");
    assert_eq!(wire_decoded.len(), parsed.len());
    assert_eq!(wire_decoded[0].kind, parsed[0].kind);

    let frame = BinaryFrame::BinaryNumber(BinaryNumber::parse("101001").unwrap());
    let bits = encode_binary_frame(&frame).expect("frame encode");
    let (decoded, consumed) = decode_binary_frame(&bits).expect("frame decode");
    assert_eq!(decoded, frame);
    assert_eq!(consumed, bits.len());
}

#[test]
fn binary_number_arithmetic_is_not_host_width_bounded() {
    let wide = BinaryNumber::parse(&"1".repeat(256)).unwrap();
    let widened = wide.add(&BinaryNumber::one());
    assert_eq!(widened.bits(), format!("1{}", "0".repeat(256)));
}

#[test]
fn number_bits_do_not_collapse_equal_payload_core_domains() {
    let number_one = Value::BinaryNumber(BinaryNumber::parse("1").unwrap());
    let predicate_one = Value::DomainIdentity(DomainIdentity::D1(
        PredicateBit::from_word(Bit1::new(1).unwrap()),
    ));
    assert_ne!(number_one, predicate_one);

    let number_two = Value::BinaryNumber(BinaryNumber::parse("10").unwrap());
    let structure_open = Value::DomainIdentity(DomainIdentity::D2(
        Racana2::from_word(Bit2::new(0b10).unwrap()),
    ));
    assert_ne!(number_two, structure_open);

    let expressions = vec![
        Expr {
            kind: ExprKind::BinaryNumber(BinaryNumber::parse("10").unwrap()),
            span: Span::default(),
        },
        Expr {
            kind: ExprKind::DomainIdentity(DomainIdentity::D2(
                Racana2::from_word(Bit2::new(0b10).unwrap()),
            )),
            span: Span::default(),
        },
    ];

    let hash = [0x22u8; 32];
    let fasl = fasl_encode_program(&expressions, &hash);
    let (fasl_decoded, _) = fasl_decode_program(&fasl).expect("FASL domain separation");
    assert_eq!(fasl_decoded, expressions);

    let wire = wire_encode_program(&expressions);
    let wire_decoded = wire_decode_program(&wire).expect("wire domain separation");
    assert_eq!(wire_decoded, expressions);

    let number_frame = BinaryFrame::BinaryNumber(BinaryNumber::parse("10").unwrap());
    let domain_frame = BinaryFrame::Domain(DomainIdentity::D2(
        Racana2::from_word(Bit2::new(0b10).unwrap()),
    ));
    assert_ne!(
        encode_binary_frame(&number_frame).unwrap(),
        encode_binary_frame(&domain_frame).unwrap(),
        "same payload bits in different domains need different canonical framing"
    );
}


#[test]
fn natural_binary_subtraction_and_exact_division_execute_as_bits() {
    let mut session = Session::default();
    let subtract = eval_program("(- #b110 #b10)", &mut session)
        .expect("natural difference").value;
    assert_eq!(subtract, Value::BinaryNumber(BinaryNumber::parse("100").unwrap()));

    let divide = eval_program("(/ #b110 #b10)", &mut session)
        .expect("exact natural quotient").value;
    assert_eq!(divide, Value::BinaryNumber(BinaryNumber::parse("11").unwrap()));

    let unary_zero = eval_program("(- #b0)", &mut session)
        .expect("negative zero is zero").value;
    assert_eq!(unary_zero, Value::BinaryNumber(BinaryNumber::zero()));

    let reciprocal_one = eval_program("(/ #b1)", &mut session)
        .expect("reciprocal of one").value;
    assert_eq!(reciprocal_one, Value::BinaryNumber(BinaryNumber::one()));
}

#[test]
fn signed_rational_and_division_by_zero_remain_fail_closed() {
    for source in ["(- #b10 #b11)", "(- #b10)", "(/ #b111 #b10)", "(/ #b10)"] {
        let err = eval_program(source, &mut Session::default())
            .expect_err("no unratified signed or rational encoding");
        assert_eq!(err.kind, sens::ErrorKind::Type, "{source}");
    }
    for source in ["(/ #b1 #b0)", "(/ #b0)"] {
        let err = eval_program(source, &mut Session::default())
            .expect_err("cannot divide by zero");
        assert_eq!(err.kind, sens::ErrorKind::DivisionByZero, "{source}");
    }
    let err = eval_program("(/ #b110 2)", &mut Session::default())
        .expect_err("no implicit legacy number bridge");
    assert_eq!(err.kind, sens::ErrorKind::Type);
}

#[test]
fn numeric_d24_d48_domain_values_survive_actual_fasl_and_wire() {
    // No numeric source literals are used to construct these values.
    let first = BinaryNumber::from_numeric_domain_bits(24, &vec![0; 24])
        .expect("D24 exact zero");
    let second = BinaryNumber::from_numeric_domain_bits(48, &vec![0; 48])
        .expect("D48 exact zero");
    assert_ne!(first, second);
    let forms = [first.clone(), second.clone()]
        .into_iter()
        .map(|number| Expr {
            kind: ExprKind::BinaryNumber(number),
            span: Span::default(),
        })
        .collect::<Vec<_>>();
    let hash = [0x55u8; 32];
    let fasl = fasl_encode_program(&forms, &hash);
    let (from_fasl, decoded_hash) = fasl_decode_program(&fasl).expect("qualified FASL");
    assert_eq!(decoded_hash, hash);
    assert_eq!(from_fasl, forms);

    let wire = wire_encode_program(&forms);
    let from_wire = wire_decode_program(&wire).expect("qualified wire");
    assert_eq!(from_wire, forms);
    // Both retain their explicit numeric domain after the round-trip.
    for (number, width) in [(first, 24), (second, 48)] {
        assert_eq!(number.numeric_domain_width(), Some(width));
        assert_eq!(number.exact_numeric_domain_bits(), Some(vec![0; width]));
    }
}

#[test]
fn numeric_domain_ast_formats_reject_invalid_width_and_truncation() {
    let number = BinaryNumber::from_numeric_domain_bits(24, &vec![1; 24]).unwrap();
    let forms = vec![Expr {
        kind: ExprKind::BinaryNumber(number),
        span: Span::default(),
    }];
    let hash = [0x23u8; 32];

    let original_fasl = fasl_encode_program(&forms, &hash);
    let original_wire = wire_encode_program(&forms);

    let mut short_fasl = original_fasl.clone();
    short_fasl.pop();
    assert!(fasl_decode_program(&short_fasl).is_none());

    let mut short_wire = original_wire.clone();
    short_wire.pop();
    assert!(wire_decode_program(&short_wire).is_none());

    // Explicit width is semantic framing metadata. Invalid D25 must fail
    // rather than being auto-coerced to a nearby D24 or D48.
    let mut wrong_fasl = original_fasl;
    let f_tag = wrong_fasl.windows(5).position(|seq| seq == [13, 24, 0, 0, 0])
        .expect("additive numeric FASL domain tag and width");
    wrong_fasl[f_tag + 1] = 25;
    assert!(fasl_decode_program(&wrong_fasl).is_none());

    let mut overlong_wire = original_wire.clone();
    let tag = overlong_wire.windows(2).position(|seq| seq == [0x5B, 24])
        .expect("qualified numeric wire header");
    overlong_wire[tag + 1] = 0x80 | 24;
    overlong_wire.insert(tag + 2, 0);
    assert!(wire_decode_program(&overlong_wire).is_none(),
        "multiple byte spellings of one D24 domain width must be rejected");

    let mut wrong_wire = original_wire;
    let w_tag = wrong_wire.windows(2).position(|seq| seq == [0x5B, 24])
        .expect("additive numeric wire domain tag and width");
    wrong_wire[w_tag + 1] = 25;
    assert!(wire_decode_program(&wrong_wire).is_none());
}
