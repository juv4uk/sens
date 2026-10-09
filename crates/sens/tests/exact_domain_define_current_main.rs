//! Mechanical exact-width domain ladder; executable D2 grammar is separate.
//! A bare D2 close word (01) is structural, not a standalone SENS program.
use sens::{parse_binary_source_words, parse_canonical_binary, DomainIdentity};

fn word_identity(source: &str) -> DomainIdentity {
    let tokens = parse_binary_source_words(source).expect("exact bit word lexes");
    assert_eq!(tokens.len(), 1, "one physical word must remain one token");
    DomainIdentity::from_source_word(tokens[0].word)
}

#[test]
fn rust_observes_exact_width_domain_words_only() {
    for width in 1usize..=9 {
        let payload = (1usize << width) - 1;
        let source = format!("{payload:0width$b}");
        let identity = word_identity(&source);
        assert_eq!(identity.width(), width);
        assert_eq!(identity.packed_bits() as usize, payload);
    }
}

#[test]
fn leading_zeroes_keep_the_word_on_its_original_rung() {
    for width in 1usize..=9 {
        let source = format!("{value:0width$b}", value = 1usize);
        let identity = word_identity(&source);
        assert_eq!(identity.width(), width);
        assert_eq!(identity.packed_bits(), 1);
    }
}

#[test]
fn d2_closer_is_lexically_exact_but_not_an_executable_root() {
    let closing = word_identity("01");
    assert_eq!(closing.width(), 2);
    assert_eq!(closing.packed_bits(), 1);
    assert!(parse_canonical_binary("01").is_err(),
        "D2 close 01 must never be admitted as a standalone program");
}
