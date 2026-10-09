//! Domain-ladder-only guard. Native-first language laws belong to SENS witnesses.
use sens::{parse_canonical_binary, syntax::ExprKind};

#[test]
fn exact_domain_ladder_preserves_leading_zeroes_and_widths_d1_through_d9() {
    for width in 1usize..=9 {
        let source = format!("{value:0width$b}", value = 1u16);
        let forms = parse_canonical_binary(&source).expect("exact-width domain word parses");
        assert_eq!(forms.len(), 1);
        let ExprKind::DomainIdentity(identity) = &forms[0].kind else {
            panic!("exact-width source word must remain a domain identity");
        };
        assert_eq!(identity.width(), width);
        assert_eq!(identity.packed_bits(), 1);
    }
}

#[test]
fn same_payload_in_different_rungs_remains_a_different_identity() {
    let d1 = parse_canonical_binary("1").expect("D1 word parses");
    let d3 = parse_canonical_binary("001").expect("D3 word parses");
    let d9 = parse_canonical_binary("000000001").expect("D9 word parses");
    let identity = |forms: &[sens::syntax::Expr]| match &forms[0].kind {
        ExprKind::DomainIdentity(value) => value,
        _ => panic!("expected exact domain identity"),
    };
    assert_eq!(identity(&d1).packed_bits(), 1);
    assert_eq!(identity(&d3).packed_bits(), 1);
    assert_eq!(identity(&d9).packed_bits(), 1);
    assert_ne!(identity(&d1), identity(&d3));
    assert_ne!(identity(&d3), identity(&d9));
}

#[test]
fn nine_bit_payload_is_not_truncated_to_u8() {
    let forms = parse_canonical_binary("100000001").expect("D9 word parses");
    let ExprKind::DomainIdentity(identity) = &forms[0].kind else {
        panic!("D9 word must remain a domain identity");
    };
    assert_eq!(identity.width(), 9);
    assert_eq!(identity.packed_bits(), 257);
}