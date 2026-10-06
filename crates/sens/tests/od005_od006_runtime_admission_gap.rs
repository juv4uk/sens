use sens::{parse, ExprKind};

fn parsed_head(source: &str) -> Vec<sens::Expr> {
    let expressions = parse(source).expect("source must parse");
    assert_eq!(expressions.len(), 1);
    expressions
}

#[test]
fn od005_od006_owner_coordinates_now_reach_exact_domain_identity() {
    for (source, width, bits) in [
        ("(00111)", 5usize, 0b00111u8),
        ("(001111)", 6usize, 0b001111u8),
    ] {
        let expressions = parsed_head(source);
        let ExprKind::List(items) = &expressions[0].kind else {
            panic!("{source}: expected list")
        };
        let ExprKind::DomainIdentity(identity) = items[0].kind else {
            panic!("{source}: exact owner coordinate must be domain-qualified after #2817 migration")
        };
        assert_eq!((identity.width(), identity.packed_bits()), (width, bits));
    }
}

#[test]
fn exact_eight_bit_legacy_control_is_still_sid() {
    let expressions = parsed_head("(00000111)");
    let ExprKind::List(items) = &expressions[0].kind else {
        panic!("expected list")
    };
    assert!(
        matches!(&items[0].kind, ExprKind::Sid(_)),
        "8-bit legacy control remains an explicit compatibility SID"
    );
}
