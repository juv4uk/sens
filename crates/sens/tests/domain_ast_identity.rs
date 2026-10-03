//! Domain-qualified AST identity witness for #2782/#2791.
//!
//! The tree and its transport formats preserve Core.D5/Core.D6 as exact-width
//! typed identities. No path in this witness widens either domain to Sens8.

use sens::{
    fasl_decode_program, fasl_encode_program, wire_decode_program, wire_encode_program,
    Bit5, Bit6, CoreD5, CoreD6, Expr, ExprKind, Span,
};

fn expr(kind: ExprKind) -> Expr {
    Expr {
        kind,
        span: Span { start: 0, end: 0 },
    }
}

#[test]
fn all_d5_words_round_trip_without_sens8_widening() {
    for raw in 0u8..32 {
        let original = expr(ExprKind::CoreD5(CoreD5::from_word(Bit5::new(raw).unwrap())));
        let ExprKind::CoreD5(word) = original.kind.clone() else {
            panic!("Core.D5 AST identity changed");
        };
        assert_eq!(word.word().packed_bits(), raw);

        let hash = [raw; 32];
        let fasl = fasl_encode_program(&[original.clone()], &hash);
        let (decoded, decoded_hash) = fasl_decode_program(&fasl).expect("D5 FASL");
        assert_eq!(decoded_hash, hash);
        assert_eq!(decoded[0].kind, original.kind);

        let wire = wire_encode_program(&[original.clone()]);
        let decoded = wire_decode_program(&wire).expect("D5 wire");
        assert_eq!(decoded[0].kind, original.kind);
    }
}

#[test]
fn all_d6_words_round_trip_without_sens8_widening() {
    for raw in 0u8..64 {
        let original = expr(ExprKind::CoreD6(CoreD6::from_word(Bit6::new(raw).unwrap())));
        let ExprKind::CoreD6(word) = original.kind.clone() else {
            panic!("Core.D6 AST identity changed");
        };
        assert_eq!(word.word().packed_bits(), raw);

        let hash = [raw; 32];
        let fasl = fasl_encode_program(&[original.clone()], &hash);
        let (decoded, decoded_hash) = fasl_decode_program(&fasl).expect("D6 FASL");
        assert_eq!(decoded_hash, hash);
        assert_eq!(decoded[0].kind, original.kind);

        let wire = wire_encode_program(&[original.clone()]);
        let decoded = wire_decode_program(&wire).expect("D6 wire");
        assert_eq!(decoded[0].kind, original.kind);
    }
}

#[test]
fn equal_packed_payloads_remain_domain_distinct() {
    let d5 = expr(ExprKind::CoreD5(CoreD5::from_word(Bit5::new(0b00001).unwrap())));
    let d6 = expr(ExprKind::CoreD6(CoreD6::from_word(Bit6::new(0b000001).unwrap())));

    assert_ne!(d5.kind, d6.kind);
    assert!(matches!(d5.kind, ExprKind::CoreD5(_)));
    assert!(matches!(d6.kind, ExprKind::CoreD6(_)));
}
