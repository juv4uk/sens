use sens::{
    fasl_decode_program, fasl_encode_program, wire_decode_program, wire_encode_program,
    Bija3, Bit3, Bit4, Bit5, Bit6, CoreD4, CoreD5, CoreD6, CoreDomainIdentity,
    Expr, ExprKind, Span, Value,
};

fn expr(identity: CoreDomainIdentity) -> Expr {
    Expr {
        kind: ExprKind::CoreIdentity(identity),
        span: Span { start: 0, end: 0 },
    }
}

fn identities_with_payload(payload: u8) -> [CoreDomainIdentity; 4] {
    [
        CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(payload & 0b111).unwrap())),
        CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(payload & 0b1111).unwrap())),
        CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(payload & 0b1_1111).unwrap())),
        CoreDomainIdentity::D6(CoreD6::from_word(Bit6::new(payload & 0b11_1111).unwrap())),
    ]
}

#[test]
fn equal_payload_in_different_domains_is_distinct_ast_and_value_identity() {
    let [d3, d4, d5, d6] = identities_with_payload(1);

    assert_eq!([d3.packed_bits(), d4.packed_bits(), d5.packed_bits(), d6.packed_bits()], [1, 1, 1, 1]);
    assert_ne!(d3, d4);
    assert_ne!(d4, d5);
    assert_ne!(d5, d6);

    assert_ne!(expr(d3).kind, expr(d4).kind);
    assert_ne!(Value::CoreIdentity(d3), Value::CoreIdentity(d4));
    assert_eq!(Value::CoreIdentity(d5).as_core_identity(), Some(d5));
    assert_eq!(Value::CoreIdentity(d6).as_sens8(), None);
}

#[test]
fn canonical_core_identity_round_trips_through_fasl_and_wire() {
    let cases = [
        CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(0b101).unwrap())),
        CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(0b1010).unwrap())),
        CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(0b10101).unwrap())),
        CoreDomainIdentity::D6(CoreD6::from_word(Bit6::new(0b101010).unwrap())),
    ];

    for (index, identity) in cases.into_iter().enumerate() {
        let original = expr(identity);
        let hash = [index as u8; 32];

        let fasl = fasl_encode_program(&[original.clone()], &hash);
        let (decoded, decoded_hash) = fasl_decode_program(&fasl).expect("Core identity FASL");
        assert_eq!(decoded_hash, hash);
        assert_eq!(decoded.len(), 1);
        assert_eq!(decoded[0].kind, original.kind);

        let wire = wire_encode_program(&[original.clone()]);
        let decoded = wire_decode_program(&wire).expect("Core identity wire");
        assert_eq!(decoded.len(), 1);
        assert_eq!(decoded[0].kind, original.kind);
    }
}

#[test]
fn full_domain_ranges_round_trip_without_sens8_projection() {
    for raw in 0u8..8 {
        let id = CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(raw).unwrap()));
        assert_eq!(Value::CoreIdentity(id).as_sens8(), None);
    }
    for raw in 0u8..16 {
        let id = CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(raw).unwrap()));
        assert_eq!(Value::CoreIdentity(id).as_sens8(), None);
    }
    for raw in 0u8..32 {
        let id = CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(raw).unwrap()));
        assert_eq!(Value::CoreIdentity(id).as_sens8(), None);
    }
    for raw in 0u8..64 {
        let id = CoreDomainIdentity::D6(CoreD6::from_word(Bit6::new(raw).unwrap()));
        assert_eq!(Value::CoreIdentity(id).as_sens8(), None);
    }
}
