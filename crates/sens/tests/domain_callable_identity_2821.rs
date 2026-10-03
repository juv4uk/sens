use sens::{
    fasl_decode_program, fasl_encode_program, wire_decode_program, wire_encode_program,
    Bija3, Bit3, Bit4, Bit5, Bit6, CallableDomainId, CoreD4, CoreD5, CoreD6, Expr,
    ExprKind, Span,
};

fn sid(identity: CallableDomainId) -> Expr {
    Expr {
        kind: ExprKind::Sid(identity),
        span: Span { start: 0, end: 0 },
    }
}

#[test]
fn equal_payloads_in_different_callable_domains_remain_distinct_in_ast() {
    let d3 = CallableDomainId::D3(Bija3::from_word(Bit3::new(5).unwrap()));
    let d4 = CallableDomainId::D4(CoreD4::from_word(Bit4::new(5).unwrap()));
    let d5 = CallableDomainId::D5(CoreD5::from_word(Bit5::new(5).unwrap()));
    let d6 = CallableDomainId::D6(CoreD6::from_word(Bit6::new(5).unwrap()));

    let values = [d3, d4, d5, d6];
    for left in 0..values.len() {
        for right in 0..values.len() {
            if left == right {
                assert_eq!(values[left], values[right]);
            } else {
                assert_ne!(values[left], values[right]);
            }
        }
    }

    assert_eq!(d3.packed_bits(), 5);
    assert_eq!(d4.packed_bits(), 5);
    assert_eq!(d5.packed_bits(), 5);
    assert_eq!(d6.packed_bits(), 5);
}

#[test]
fn wire_roundtrip_preserves_domain_and_width() {
    let program = vec![
        sid(CallableDomainId::D3(Bija3::from_word(Bit3::new(5).unwrap()))),
        sid(CallableDomainId::D4(CoreD4::from_word(Bit4::new(5).unwrap()))),
        sid(CallableDomainId::D5(CoreD5::from_word(Bit5::new(5).unwrap()))),
        sid(CallableDomainId::D6(CoreD6::from_word(Bit6::new(5).unwrap()))),
    ];

    let encoded = wire_encode_program(&program);
    let decoded = wire_decode_program(&encoded).expect("domain-aware wire roundtrip");
    assert_eq!(decoded, program);
}

#[test]
fn fasl_roundtrip_preserves_domain_and_width() {
    let program = vec![
        sid(CallableDomainId::D3(Bija3::from_word(Bit3::new(5).unwrap()))),
        sid(CallableDomainId::D4(CoreD4::from_word(Bit4::new(5).unwrap()))),
        sid(CallableDomainId::D5(CoreD5::from_word(Bit5::new(5).unwrap()))),
        sid(CallableDomainId::D6(CoreD6::from_word(Bit6::new(5).unwrap()))),
    ];
    let hash = [0x28; 32];

    let encoded = fasl_encode_program(&program, &hash);
    let (decoded, decoded_hash) =
        fasl_decode_program(&encoded).expect("domain-aware FASL roundtrip");
    assert_eq!(decoded_hash, hash);
    assert_eq!(decoded, program);
}

#[test]
fn legacy_sens8_is_an_explicitly_different_ast_variant() {
    let domain = sid(CallableDomainId::D3(Bija3::from_word(Bit3::new(5).unwrap())));
    let legacy = Expr {
        kind: ExprKind::LegacySid(sens::sens!(00000101)),
        span: Span { start: 0, end: 0 },
    };

    assert_ne!(domain, legacy);
}
