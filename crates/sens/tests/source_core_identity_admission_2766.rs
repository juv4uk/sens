use sens::{
    parse_binary_source_words, BinarySourceWord, CoreDomainIdentity,
};

fn one(source: &str) -> BinarySourceWord {
    let tokens = parse_binary_source_words(source).expect("canonical binary source");
    assert_eq!(tokens.len(), 1);
    tokens[0].word
}

#[test]
fn every_d5_coordinate_enters_canonical_core_identity_without_widening() {
    for raw in 0u8..32 {
        let text = format!("{raw:05b}");
        let word = one(&text);
        assert_eq!(word.width(), 5);
        let identity = word.core_identity().expect("W5 must admit Core.D5 identity");
        assert!(matches!(identity, CoreDomainIdentity::D5(_)));
        assert_eq!(identity.width(), 5);
        assert_eq!(identity.packed_bits(), raw);
    }
}

#[test]
fn every_d6_coordinate_enters_canonical_core_identity_without_widening() {
    for raw in 0u8..64 {
        let text = format!("{raw:06b}");
        let word = one(&text);
        assert_eq!(word.width(), 6);
        let identity = word.core_identity().expect("W6 must admit Core.D6 identity");
        assert!(matches!(identity, CoreDomainIdentity::D6(_)));
        assert_eq!(identity.width(), 6);
        assert_eq!(identity.packed_bits(), raw);
    }
}

#[test]
fn equal_payloads_at_d5_and_d6_remain_distinct_identities() {
    for raw in 0u8..32 {
        let d5 = one(&format!("{raw:05b}")).core_identity().unwrap();
        let d6 = one(&format!("{raw:06b}")).core_identity().unwrap();

        assert_eq!(d5.packed_bits(), d6.packed_bits());
        assert_eq!(d5.packed_bits(), raw);
        assert_ne!(d5, d6);
        assert_eq!(d5.width(), 5);
        assert_eq!(d6.width(), 6);
    }
}

#[test]
fn non_core_widths_do_not_gain_core_identity_by_width_alone() {
    for source in ["0", "01", "0000000", "00000000"] {
        let word = one(source);
        assert!(word.core_identity().is_none(), "{source} must not gain Core identity");
    }
}

#[test]
fn d3_and_d4_source_words_enter_the_same_canonical_identity_family() {
    let d3 = one("101").core_identity().expect("W3");
    let d4 = one("0101").core_identity().expect("W4");

    assert!(matches!(d3, CoreDomainIdentity::D3(_)));
    assert!(matches!(d4, CoreDomainIdentity::D4(_)));
    assert_eq!(d3.packed_bits(), 5);
    assert_eq!(d4.packed_bits(), 5);
    assert_ne!(d3, d4);
}
