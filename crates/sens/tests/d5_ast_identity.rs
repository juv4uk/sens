//! #2782 — exact Core.D5 AST identity witness.
//!
//! AST transport is tested independently from source-domain admission.
//! The ordinary parser still does not construct ExprKind::CoreD5.

use sens::{
    fasl_decode_program, fasl_encode_program, wire_decode_program, wire_encode_program,
    Bit5, CoreD5Word, Expr, ExprKind, Span,
};

fn d5_expr(raw: u8) -> Expr {
    Expr {
        kind: ExprKind::CoreD5(CoreD5Word::from_word(Bit5::new(raw).unwrap())),
        span: Span { start: 0, end: 0 },
    }
}

#[test]
fn every_core_d5_word_round_trips_through_ast_identity() {
    for raw in 0u8..32 {
        let expr = d5_expr(raw);
        let ExprKind::CoreD5(identity) = expr.kind.clone() else {
            panic!("Core.D5 AST variant changed");
        };
        assert_eq!(identity.word().packed_bits(), raw);
        assert_eq!(expr.kind, ExprKind::CoreD5(identity));
        assert!(format!("{:?}", expr.kind).contains("CoreD5"));
    }
}

#[test]
fn core_d5_ast_fasl_roundtrip_preserves_exact_five_bit_identity() {
    for raw in 0u8..32 {
        let expr = d5_expr(raw);
        let hash = [raw; 32];
        let encoded = fasl_encode_program(&[expr.clone()], &hash);
        let (decoded, decoded_hash) = fasl_decode_program(&encoded).expect("D5 FASL");
        assert_eq!(decoded_hash, hash);
        assert_eq!(decoded.len(), 1);
        assert_eq!(decoded[0].kind, expr.kind);
        let ExprKind::CoreD5(identity) = decoded[0].kind else {
            panic!("D5 FASL widened identity");
        };
        assert_eq!(identity.word().packed_bits(), raw);
    }
}

#[test]
fn core_d5_ast_wire_roundtrip_preserves_exact_five_bit_identity() {
    for raw in 0u8..32 {
        let expr = d5_expr(raw);
        let encoded = wire_encode_program(&[expr.clone()]);
        let decoded = wire_decode_program(&encoded).expect("D5 wire");
        assert_eq!(decoded.len(), 1);
        assert_eq!(decoded[0].kind, expr.kind);
        let ExprKind::CoreD5(identity) = decoded[0].kind else {
            panic!("D5 wire widened identity");
        };
        assert_eq!(identity.word().packed_bits(), raw);
    }
}
