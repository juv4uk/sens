use sens::{
    decode_binary_frame, encode_binary_frame, eval_parsed_expressions, eval_program,
    fasl_decode_program, fasl_encode_program, load_core_library, parse,
    render_value_for_presentation, wire_decode_program, wire_encode_program, BinaryFrame,
    BinaryNumber, Bit1, Bit2, DomainIdentity, Expr, ExprKind, PredicateBit, PresentationLanguage,
    Racana2, Session, Span, Value,
};

fn eval_ukr(source: &str, session: &mut Session) -> Result<sens::EvalResult, sens::LanguageError> {
    let parsed = parse(source)?;
    let projected = sens::source_projection::project_ukr_decimal_integer_literals(&parsed, source)?;
    eval_parsed_expressions(&projected, session)
}

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

fn d24(value: u32) -> Value {
    let mut bits = vec![0u8; 24];
    for i in 0..24 {
        bits[23 - i] = ((value >> i) & 1) as u8;
    }
    Value::BinaryNumber(
        BinaryNumber::from_numeric_domain_bits(24, &bits).expect("explicit D24 test value"),
    )
}

#[test]
fn d5_add_mul_and_order_use_explicit_d24_values_not_literals() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("Core4 loads");
    session.environment.define("left", d24(2));
    session.environment.define("right", d24(3));

    assert_eq!(
        eval_ukr("(додати left right)", &mut session)
            .expect("uk D5 PLUS accepts explicitly qualified D24")
            .value,
        d24(5),
    );
    assert_eq!(
        eval_ukr("(помножити left right)", &mut session)
            .expect("uk D5 TIMES accepts explicitly qualified D24")
            .value,
        d24(6),
    );
    assert_eq!(
        eval_ukr("(менше? left right)", &mut session)
            .expect("uk D5 LESSP returns exact D1")
            .value,
        Value::predicate_bit(true),
    );
    assert_eq!(
        eval_ukr("(більше? left right)", &mut session)
            .expect("uk D5 GREATERP returns exact D1")
            .value,
        Value::predicate_bit(false),
    );
}

#[test]
fn binary_number_refuses_implicit_legacy_numeric_coercion() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("Core4 loads");
    let error = eval_ukr("(додати #b10 3)", &mut session)
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
    assert_ne!(
        binary, legacy,
        "presentation equality must not erase carrier identity"
    );

    // Equality of runtime carriers is not a surface/callability grant.
    // Existing Core does NOT admit the legacy EQUAL? dispatch code here.
    assert_eq!(binary, binary.clone());
    assert_eq!(legacy, legacy.clone());
    for source in ["(equal? #b1001000 #d72)", "(equal? #d72 #d72)"] {
        let err = eval_program(source, &mut session)
            .expect_err("unadmitted EQUAL? callable must fail closed");
        assert_eq!(err.kind, sens::ErrorKind::UnknownSymbol);
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
    let predicate_one = Value::DomainIdentity(DomainIdentity::D1(PredicateBit::from_word(
        Bit1::new(1).unwrap(),
    )));
    assert_ne!(number_one, predicate_one);

    let number_two = Value::BinaryNumber(BinaryNumber::parse("10").unwrap());
    let structure_open = Value::DomainIdentity(DomainIdentity::D2(Racana2::from_word(
        Bit2::new(0b10).unwrap(),
    )));
    assert_ne!(number_two, structure_open);

    let expressions = vec![
        Expr {
            kind: ExprKind::BinaryNumber(BinaryNumber::parse("10").unwrap()),
            span: Span::default(),
        },
        Expr {
            kind: ExprKind::DomainIdentity(DomainIdentity::D2(Racana2::from_word(
                Bit2::new(0b10).unwrap(),
            ))),
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
    let domain_frame = BinaryFrame::Domain(DomainIdentity::D2(Racana2::from_word(
        Bit2::new(0b10).unwrap(),
    )));
    assert_ne!(
        encode_binary_frame(&number_frame).unwrap(),
        encode_binary_frame(&domain_frame).unwrap(),
        "same payload bits in different domains need different canonical framing"
    );
}

#[test]
fn signed_binary_subtraction_and_exact_division_execute_as_d24_values() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("Core4 loads");
    session.environment.define("six", d24(6));
    session.environment.define("two", d24(2));
    session.environment.define("zero", d24(0));

    assert_eq!(
        eval_ukr("(відняти six two)", &mut session)
            .expect("exact signed D24 subtraction")
            .value,
        d24(4),
    );
    assert_eq!(
        sens::domain_numeric_value("/", &d24(6), &d24(2))
            .expect("exact positive D24 quotient through the admitted numeric API"),
        d24(3),
    );
    assert_eq!(
        eval_ukr("(відняти zero zero)", &mut session)
            .expect("equal D24 subtraction returns exact D24 zero")
            .value,
        d24(0),
    );
    assert_eq!(
        sens::domain_numeric_value("/", &d24(1), &d24(1))
            .expect("unit quotient through the admitted numeric API"),
        d24(1),
    );
}

#[test]
fn unqualified_numeric_literals_fail_closed_d24_negative_and_ratio_execute() {
    // Old #b spelling is still readable as DATA but does not admit Core math.
    let mut rejected_session = Session::default();
    load_core_library(&mut rejected_session).expect("Core4 loads");
    for (source, expected_kind) in [
        ("(відняти #b10 #b11)", sens::ErrorKind::Type),
        ("(відняти #b10)", sens::ErrorKind::Type),
        ("(частка #b111 #b10)", sens::ErrorKind::Type),
        ("(частка #b10)", sens::ErrorKind::Type),
        ("(частка #b1 #b0)", sens::ErrorKind::Type),
        ("(частка #b0)", sens::ErrorKind::Type),
        ("(частка #b110 2)", sens::ErrorKind::Type),
    ] {
        let err = eval_ukr(source, &mut rejected_session)
            .expect_err("unqualified numeric source is not D24 arithmetic");
        assert_eq!(err.kind, expected_kind, "{source}");
    }

    let mut session = Session::default();
    load_core_library(&mut session).expect("Core4 loads");
    session.environment.define("one", d24(1));
    session.environment.define("two", d24(2));
    assert_eq!(
        eval_ukr("(відняти one two)", &mut session)
            .unwrap()
            .value
            .to_string(),
        "-1",
    );
    assert_eq!(
        sens::domain_numeric_value("/", &d24(1), &d24(3))
            .expect("exact ratio through admitted D24+ numeric API")
            .to_string(),
        "1/3",
    );
    assert!(
        sens::domain_numeric_value("/", &d24(1), &d24(0)).is_none(),
        "admitted D24 denominator zero must reject"
    );
}

#[test]
fn numeric_d24_d48_domain_values_survive_actual_fasl_and_wire() {
    // No numeric source literals are used to construct these values.
    let first = BinaryNumber::from_numeric_domain_bits(24, &[0; 24]).expect("D24 exact zero");
    let second = BinaryNumber::from_numeric_domain_bits(48, &[0; 48]).expect("D48 exact zero");
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
    let number = BinaryNumber::from_numeric_domain_bits(24, &[1; 24]).unwrap();
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
    let f_tag = wrong_fasl
        .windows(5)
        .position(|seq| seq == [13, 24, 0, 0, 0])
        .expect("additive numeric FASL domain tag and width");
    wrong_fasl[f_tag + 1] = 25;
    assert!(fasl_decode_program(&wrong_fasl).is_none());

    let mut overlong_wire = original_wire.clone();
    let tag = overlong_wire
        .windows(2)
        .position(|seq| seq == [0x5B, 24])
        .expect("qualified numeric wire header");
    overlong_wire[tag + 1] = 0x80 | 24;
    overlong_wire.insert(tag + 2, 0);
    assert!(
        wire_decode_program(&overlong_wire).is_none(),
        "multiple byte spellings of one D24 domain width must be rejected"
    );

    let mut wrong_wire = original_wire;
    let w_tag = wrong_wire
        .windows(2)
        .position(|seq| seq == [0x5B, 24])
        .expect("additive numeric wire domain tag and width");
    wrong_wire[w_tag + 1] = 25;
    assert!(wire_decode_program(&wrong_wire).is_none());
}
