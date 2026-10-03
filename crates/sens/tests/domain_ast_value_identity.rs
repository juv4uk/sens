use sens::{
    fasl_decode_program, fasl_encode_program, wire_decode_program, wire_encode_program, Bija3,
    Bit3, Bit4, Bit7, Bit8, CoreD4, CoreD7, CoreD8, CoreDomainIdentity, Exactness, Expr,
    ExprKind, Span, Value,
};
use std::rc::Rc;

fn d3(raw: u8) -> CoreDomainIdentity {
    Bija3::from_word(Bit3::new(raw).unwrap()).into()
}

fn d4(raw: u8) -> CoreDomainIdentity {
    CoreD4::from_word(Bit4::new(raw).unwrap()).into()
}

fn d7(raw: u8) -> CoreDomainIdentity {
    CoreD7::from_word(Bit7::new(raw).unwrap()).into()
}

fn d8(raw: u8) -> CoreDomainIdentity {
    CoreD8::from_word(Bit8::new(raw).unwrap()).into()
}

fn expr(identity: CoreDomainIdentity) -> Expr {
    Expr {
        kind: ExprKind::DomainIdentity(identity),
        span: Span { start: 0, end: 0 },
    }
}

#[test]
fn same_payload_in_d3_and_d4_remains_distinct_in_ast_and_value() {
    let d3 = d3(1);
    let d4 = d4(1);

    assert_eq!(d3.packed_bits(), d4.packed_bits());
    assert_ne!(d3, d4);
    assert_ne!(expr(d3).kind, expr(d4).kind);

    let v3 = Value::DomainIdentity(d3);
    let v4 = Value::DomainIdentity(d4);
    assert_ne!(v3, v4);
    assert_eq!(v3.to_string(), "001");
    assert_eq!(v4.to_string(), "0001");
    assert_eq!(v3.as_core_domain_identity(), Some(d3));
    assert_eq!(v4.as_core_domain_identity(), Some(d4));
    assert_eq!(v3.as_sens8(), None);
    assert_eq!(v4.as_sens8(), None);
}

#[test]
fn domain_identity_round_trips_through_fasl_and_wire_without_sens8_projection() {
    for identity in [d3(0b101), d4(0b1010), d7(0b1010101), d8(0b10100000)] {
        let original = vec![expr(identity)];

        let fasl = fasl_encode_program(&original, &[7; 32]);
        let (fasl_decoded, hash) = fasl_decode_program(&fasl).expect("domain FASL");
        assert_eq!(hash, [7; 32]);
        assert_eq!(fasl_decoded, original);
        assert!(matches!(
            fasl_decoded[0].kind,
            ExprKind::DomainIdentity(decoded) if decoded == identity
        ));

        let wire = wire_encode_program(&original);
        let wire_decoded = wire_decode_program(&wire).expect("domain wire");
        assert_eq!(wire_decoded, original);
        assert!(matches!(
            wire_decoded[0].kind,
            ExprKind::DomainIdentity(decoded) if decoded == identity
        ));
    }
}

#[test]
fn d7_d8_remain_domain_qualified_and_never_become_legacy_sens8() {
    let sound = d7(0b1010101);
    let core8 = d8(0b00000001);

    assert_eq!(sound.width(), 7);
    assert_eq!(core8.width(), 8);
    assert_ne!(sound, core8);

    let v7 = Value::DomainIdentity(sound);
    let v8 = Value::DomainIdentity(core8);
    assert_eq!(v7.as_core_domain_identity(), Some(sound));
    assert_eq!(v8.as_core_domain_identity(), Some(core8));
    assert_eq!(v7.as_sens8(), None);
    assert_eq!(v8.as_sens8(), None);
    assert_eq!(v7.to_string(), "1010101");
    assert_eq!(v8.to_string(), "00000001");
}

#[test]
fn domain_call_serializes_as_list_with_domain_head_not_legacy_sid() {
    let identity = d4(0b0010);
    let call = Expr {
        kind: ExprKind::DomainCall(
            identity,
            Rc::from([Expr {
                kind: ExprKind::Number(42.0, Exactness::Exact),
                span: Span { start: 0, end: 0 },
            }]),
        ),
        span: Span { start: 0, end: 0 },
    };

    let decoded = wire_decode_program(&wire_encode_program(&[call])).expect("domain call wire");
    let ExprKind::List(items) = &decoded[0].kind else {
        panic!("lowered domain call must serialize as source-shaped list");
    };
    assert!(matches!(
        items[0].kind,
        ExprKind::DomainIdentity(decoded_identity) if decoded_identity == identity
    ));
    assert!(!matches!(items[0].kind, ExprKind::Sid(_)));
}
