use sens::{
    fasl_decode_program, fasl_encode_program, wire_decode_program, wire_encode_program, Bija3,
    Bit3, Bit4, CallableIdentity, CoreD4, CoreDomainIdentity, Exactness, Expr, ExprKind, Span, Value,
};
use std::rc::Rc;

fn d3(raw: u8) -> CoreDomainIdentity {
    Bija3::from_word(Bit3::new(raw).unwrap()).into()
}

fn d4(raw: u8) -> CoreDomainIdentity {
    CoreD4::from_word(Bit4::new(raw).unwrap()).into()
}

fn expr(identity: CoreDomainIdentity) -> Expr {
    Expr {
        kind: ExprKind::Sid(CallableIdentity::core(identity)),
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

    let v3 = Value::Sid(CallableIdentity::core(d3));
    let v4 = Value::Sid(CallableIdentity::core(d4));
    assert_ne!(v3, v4);
    assert_eq!(v3.to_string(), "001");
    assert_eq!(v4.to_string(), "0001");
    assert_eq!(v3.as_core_domain_identity(), Some(d3));
    assert_eq!(v4.as_core_domain_identity(), Some(d4));
    assert_eq!(v3.as_legacy8_bits(), None);
    assert_eq!(v4.as_legacy8_bits(), None);
}

#[test]
fn domain_identity_round_trips_through_fasl_and_wire_without_sens8_projection() {
    for identity in [d3(0b101), d4(0b1010)] {
        let original = vec![expr(identity)];

        let fasl = fasl_encode_program(&original, &[7; 32]);
        let (fasl_decoded, hash) = fasl_decode_program(&fasl).expect("domain FASL");
        assert_eq!(hash, [7; 32]);
        assert_eq!(fasl_decoded, original);
        assert!(matches!(
            fasl_decoded[0].kind,
            ExprKind::Sid(decoded) if decoded.core_identity() == Some(identity)
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
fn domain_call_serializes_as_list_with_domain_head_not_legacy_sid() {
    let identity = d4(0b0010);
    let call = Expr {
        kind: ExprKind::Call(
            CallableIdentity::core(identity),
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
        ExprKind::Sid(decoded_identity)
            if decoded_identity.core_identity() == Some(identity)
    ));
    assert!(matches!(
        items[0].kind,
        ExprKind::Sid(decoded_identity)
            if decoded_identity.core_identity() == Some(identity)
    ));
}
