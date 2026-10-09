//! Exact-width domain-identity mechanics; D2 program structure remains strict.
use sens::{parse_binary_source_words, parse_canonical_binary, DomainIdentity};

fn exact_word(source: &str) -> DomainIdentity {
    let tokens = parse_binary_source_words(source).expect("exact-width word lexes");
    assert_eq!(tokens.len(), 1);
    DomainIdentity::from_source_word(tokens[0].word)
}

#[test]
fn exact_domain_ladder_preserves_leading_zeroes_and_widths_d1_through_d9() {
    for width in 1usize..=9 {
        let source = format!("{value:0width$b}", value = 1u16);
        let identity = exact_word(&source);
        assert_eq!(identity.width(), width);
        assert_eq!(identity.packed_bits(), 1);
    }
}

#[test]
fn same_payload_in_different_rungs_remains_a_different_identity() {
    let d1 = exact_word("1");
    let d3 = exact_word("001");
    let d9 = exact_word("000000001");
    assert_eq!(d1.packed_bits(), 1);
    assert_eq!(d3.packed_bits(), 1);
    assert_eq!(d9.packed_bits(), 1);
    assert_ne!(d1, d3);
    assert_ne!(d3, d9);
}

#[test]
fn nine_bit_payload_is_not_truncated_to_u8() {
    let identity = exact_word("100000001");
    assert_eq!(identity.width(), 9);
    assert_eq!(identity.packed_bits(), 257);
}

#[test]
fn structural_d2_close_is_not_admitted_as_standalone_source() {
    assert_eq!(exact_word("01").width(), 2);
    assert!(parse_canonical_binary("01").is_err(),
        "structural D2 close must be rejected without a matching open");
}
