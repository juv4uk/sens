//! Compatibility-width regression after the domain migration.
//!
//! Historical exact-eight source remains readable while the canonical Core
//! identity is domain-qualified. The test name is retained for CI continuity;
//! the old "every function is eight bits" ontology is intentionally gone.

use sens::{
    lower_program, parse, parse_binary_source_words, Bija3, Bit3, Bit4, Bit5, Bit6,
    CallableIdentity, CoreD4, CoreD5, CoreD6, CoreDomainIdentity, ExprKind,
};

#[test]
fn bounded_domain_carriers_remain_one_host_byte() {
    assert_eq!(std::mem::size_of::<Bija3>(), 1);
    assert_eq!(std::mem::size_of::<CoreD4>(), 1);
    assert_eq!(std::mem::size_of::<CoreD5>(), 1);
    assert_eq!(std::mem::size_of::<CoreD6>(), 1);
}

#[test]
fn equal_payloads_do_not_collapse_across_domain_widths() {
    let d3 = CallableIdentity::core(CoreDomainIdentity::from(
        Bija3::from_word(Bit3::new(1).unwrap()),
    ));
    let d4 = CallableIdentity::core(CoreDomainIdentity::from(
        CoreD4::from_word(Bit4::new(1).unwrap()),
    ));
    let d5 = CallableIdentity::core(CoreDomainIdentity::from(
        CoreD5::from_word(Bit5::new(1).unwrap()),
    ));
    let d6 = CallableIdentity::core(CoreDomainIdentity::from(
        CoreD6::from_word(Bit6::new(1).unwrap()),
    ));
    let legacy = CallableIdentity::legacy8(1);

    for identity in [d3, d4, d5, d6, legacy] {
        assert_eq!(identity.packed_bits(), 1);
    }
    assert_ne!(d3, d4);
    assert_ne!(d4, d5);
    assert_ne!(d5, d6);
    assert_ne!(d3, legacy);
    assert_ne!(d6, legacy);
}

#[test]
fn canonical_binary_source_preserves_exact_widths() {
    let tokens = parse_binary_source_words("10 001 0101 00101 000001").unwrap();
    assert_eq!(
        tokens.iter().map(|token| token.word.width()).collect::<Vec<_>>(),
        [2, 3, 4, 5, 6],
    );
    assert_eq!(
        tokens.iter().map(|token| token.word.to_string()).collect::<Vec<_>>(),
        ["10", "001", "0101", "00101", "000001"],
    );
}

#[test]
fn historical_exact_eight_reader_path_is_explicit_compatibility() {
    let parsed = parse("(00000010 x)").unwrap();
    let ExprKind::List(items) = &parsed[0].kind else {
        panic!("expected list");
    };
    let ExprKind::Sid(identity) = items[0].kind else {
        panic!("historical exact-eight head must enter identity carrier");
    };
    assert_eq!(identity.legacy8_bits(), Some(0b0000_0010));
    assert_eq!(identity.core_identity(), None);
}

#[test]
fn lowered_legacy_surfaces_remain_explicit_compatibility_not_core_identity() {
    for source in ["(atom? x)", "(атом? x)", "(aṇu x)", "(00000010 x)"] {
        let lowered = lower_program(&parse(source).unwrap());
        let ExprKind::Call(identity, arguments) = &lowered[0].kind else {
            panic!("{source}: expected lowered call");
        };
        assert_eq!(identity.legacy8_bits(), Some(0b0000_0010), "{source}");
        assert_eq!(identity.core_identity(), None, "{source}");
        assert_eq!(arguments.len(), 1, "{source}");
    }
}

#[test]
fn core_identity_and_legacy_eight_bits_have_distinct_serialized_spelling() {
    let core = CallableIdentity::core(CoreDomainIdentity::from(
        CoreD4::from_word(Bit4::new(0b1010).unwrap()),
    ));
    let legacy = CallableIdentity::legacy8(0b0000_1010);

    assert_eq!(core.to_string(), "1010");
    assert_eq!(legacy.to_string(), "00001010");
    assert_ne!(core, legacy);
}
