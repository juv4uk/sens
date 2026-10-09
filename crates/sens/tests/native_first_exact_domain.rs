//! Exact-width mechanical word identities belong to the source-word layer.
//! D2 open/close/space/dot are syntax inside executable forms, so parsing a
//! bare D2 CLOSE as a program is *supposed* to fail. Do not relax that guard.
//! Rust checks widths and payloads here, not Lisp semantic laws.
use sens::{parse_binary_source_words, parse_canonical_binary, DomainIdentity};

fn source_identity(source: &str) -> DomainIdentity {
    let tokens = parse_binary_source_words(source).expect("valid exact-width source words");
    assert_eq!(tokens.len(), 1, "one source word at a time");
    tokens[0].word.domain_identity()
}

#[test]
fn exact_domain_ladder_preserves_leading_zeroes_and_widths_d1_through_d9() {
    for width in 1usize..=9 {
        let source = format!("{value:0width$b}", value = 1u16);
        let identity = source_identity(&source);
        assert_eq!(identity.width(), width);
        assert_eq!(identity.packed_bits(), 1);
        assert_eq!(identity.source_word().to_string(), source);
    }
}

#[test]
fn same_payload_in_different_rungs_remains_a_different_identity() {
    let d1 = source_identity("1");
    let d2 = source_identity("01");
    let d3 = source_identity("001");
    let d9 = source_identity("000000001");
    for identity in [d1, d2, d3, d9] {
        assert_eq!(identity.packed_bits(), 1);
    }
    assert_ne!(d1, d2);
    assert_ne!(d2, d3);
    assert_ne!(d3, d9);
    assert_ne!(d1, d9);
}

#[test]
fn d2_close_is_a_word_but_never_an_executable_top_level_form() {
    let close = source_identity("01");
    assert_eq!(close.width(), 2);
    assert_eq!(close.packed_bits(), 1);
    let error = parse_canonical_binary("01").expect_err("D2 CLOSE outside a list must fail closed");
    assert!(error.message.contains("unexpected D2 close word 01"), "{error:?}");
}

#[test]
fn nine_bit_payload_is_not_truncated_to_u8() {
    let identity = source_identity("100000001");
    assert_eq!(identity.width(), 9);
    assert_eq!(identity.packed_bits(), 257);
    assert_eq!(identity.source_word().to_string(), "100000001");
}
