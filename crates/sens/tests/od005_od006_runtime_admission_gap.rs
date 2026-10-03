use sens::{parse, ExprKind};

fn parsed_head(source: &str) -> Vec<sens::Expr> {
    let expressions = parse(source).expect("source must parse");
    assert_eq!(expressions.len(), 1);
    expressions
}

#[test]
fn od005_od006_owner_coordinates_are_exact_domain_identities() {
    for (source, width, bits) in [("(00111)", 5, 0b00111), ("(001111)", 6, 0b001111)] {
        let expressions = parsed_head(source);
        let ExprKind::List(items) = &expressions[0].kind else {
            panic!("{source}: expected list")
        };
        let ExprKind::DomainIdentity(identity) = items[0].kind else {
            panic!("{source}: expected exact Core domain identity")
        };
        assert_eq!(identity.width(), width, "{source}");
        assert_eq!(identity.packed_bits(), bits, "{source}");
    }
}

#[test]
fn exact_eight_bit_legacy_control_is_still_explicit_compatibility_sid() {
    let expressions = parsed_head("(00000111)");
    let ExprKind::List(items) = &expressions[0].kind else {
        panic!("expected list")
    };
    assert!(
        matches!(&items[0].kind, ExprKind::Sid(_)),
        "8-bit legacy control must remain isolated in the compatibility lane"
    );
}
