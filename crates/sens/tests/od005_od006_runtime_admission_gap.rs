use sens::{parse_canonical_binary, DomainIdentity, ExprKind};

fn parsed_identity(source: &str) -> DomainIdentity {
    let expressions = parse_canonical_binary(source).expect("canonical source must parse");
    assert_eq!(expressions.len(), 1);
    let ExprKind::DomainIdentity(identity) = &expressions[0].kind else {
        panic!("{source}: expected an exact domain identity")
    };
    *identity
}

#[test]
fn od005_od006_owner_coordinates_have_exact_domain_identity() {
    assert!(matches!(parsed_identity("00111"), DomainIdentity::D5(_)));
    assert!(matches!(parsed_identity("001111"), DomainIdentity::D6(_)));
}

#[test]
fn exact_eight_bit_word_is_current_d8_identity_not_legacy_sid() {
    let identity = parsed_identity("00000111");
    assert!(
        matches!(identity, DomainIdentity::D8(_)),
        "an exact-width word is identified by its current D8 domain, not SID8"
    );
}
