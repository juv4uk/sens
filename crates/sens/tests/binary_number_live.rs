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
fn binary_number_round_trips_fasl_wire_and_binary_frame_as_exact_bits() {
    let parsed = parse("#b101001").expect("parse");
    let hash = [0x30u8; 32];

    let fasl = fasl_encode_program(&parsed, &hash);
    let (fasl_decoded, decoded_hash) = fasl_decode_program(&fasl).expect("FASL");
    assert_eq!(decoded_hash, hash);
    assert_eq!(fasl_decoded, parsed);

    let wire = wire_encode_program(&parsed);
    let wire_decoded = wire_decode_program(&wire).expect("wire");
    assert_eq!(wire_decoded, parsed);

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
