//! Domain-ladder-only replacement for the retired Rust compiler-role differential oracle.
//! Semantic roles and compiler law are generated/witnessed by SENS; Rust checks width.
use sens::{parse_canonical_binary, syntax::ExprKind};

#[test]
fn each_supported_domain_width_roundtrips_as_a_distinct_identity() {
    for width in 1usize..=9 {
        let payload = (1usize << width) - 1;
        let source = format!("{payload:0width$b}");
        let forms = parse_canonical_binary(&source).expect("canonical domain word parses");
        assert_eq!(forms.len(), 1);
        let ExprKind::DomainIdentity(identity) = &forms[0].kind else {
            panic!("canonical binary word must remain a domain identity");
        };
        assert_eq!(identity.width(), width);
        assert_eq!(usize::from(identity.packed_bits()), payload);
    }
}

#[test]
fn equal_payloads_do_not_collapse_across_the_domain_ladder() {
    let coordinates = (1usize..=9).map(|width| {
        let source = format!("{value:0width$b}", value = 1usize);
        let parsed = parse_canonical_binary(&source).expect("domain identity parses");
        match &parsed[0].kind {
            ExprKind::DomainIdentity(identity) => (identity.width(), identity.packed_bits()),
            _ => panic!("expected domain identity"),
        }
    }).collect::<Vec<_>>();
    assert_eq!(coordinates.iter().map(|(_, bits)| *bits).collect::<Vec<_>>(), vec![1; 9]);
    assert_eq!(
        coordinates.iter().map(|(width, _)| *width).collect::<Vec<_>>(),
        (1usize..=9).collect::<Vec<_>>()
    );
    for left in 0..coordinates.len() {
        for right in (left + 1)..coordinates.len() {
            assert_ne!(coordinates[left], coordinates[right]);
        }
    }
}