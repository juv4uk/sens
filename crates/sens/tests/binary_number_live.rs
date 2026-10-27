//! Тільки фізичне двійкове кодування, збереження доменів та відхилення пошкодженого носія.
//! Арифметичні закони SENS тут НЕ перевіряються засобами Rust.
use sens::{
    decode_binary_frame, encode_binary_frame, fasl_decode_program, fasl_encode_program,
    parse, wire_decode_program, wire_encode_program, BinaryFrame, BinaryNumber,
    Bit1, Bit2, DomainIdentity, Expr, ExprKind, PredicateBit, Racana2, Span, Value,
};

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
