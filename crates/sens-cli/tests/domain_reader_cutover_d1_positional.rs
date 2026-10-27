//! #5605: bounded D1 canonical reader / historical compatibility evidence.
//! This is a reader-and-physical-roundtrip test, NOT a SENS COND execution oracle.
//! No new law, no D8/SID8 projection, no Zig semantic registry.

use sens::{
    parse_binary_source_words,
    parse_canonical_binary, parse_canonical_word_sequence, parse_exact_domain_source,
    DomainIdentity, ExprKind,
};

const BARE_D1_D2_FRAME: &str = "10 110 00 1 00 0 01";

fn assert_d1(expression: &sens::Expr, expected_bit: u16) {
    let ExprKind::DomainIdentity(DomainIdentity::D1(word)) = &expression.kind else {
        panic!("D1 bit must not turn into numeric, D2 structural, or D3 EMPTY");
    };
    assert_eq!(word.word().packed_bits() as u16, expected_bit);
}

fn encode_t5m_via_zig(words: &[sens::BinarySourceWord]) -> Vec<u8> {
    sens_cli::zig_transport::encode_t5m_direct(words)
        .expect("Zig T5M encoder must produce physical bytes")
}


#[test]
fn bare_d1_bits_inside_d2_structure_are_canonical_without_width_tags() {
    let expressions = parse_canonical_binary(BARE_D1_D2_FRAME)
        .expect("canonical binary D2 with two bare exact D1 source words");
    assert_eq!(expressions.len(), 1);
    let ExprKind::List(items) = &expressions[0].kind else {
        panic!("D2 open/close must frame the program");
    };
    assert_eq!(items.len(), 3, "D2 spaces cannot become values");
    let ExprKind::DomainIdentity(DomainIdentity::D3(_)) = items[0].kind else {
        panic!("110 remains a D3 head, without constructing semantics in reader");
    };
    assert_d1(&items[1], 1);
    assert_d1(&items[2], 0);
}

#[test]
fn tagged_d1_is_not_canonical_binary_source() {
    for source in ["10 110 00 #d1:1 00 0 01", "10 110 00 1 00 #d1:0 01"] {
        assert!(
            parse_canonical_binary(source).is_err(),
            "canonical reader must reject redundant carrier notation"
        );
        assert!(
            parse_exact_domain_source(source).is_err(),
            "exact-domain reader must not silently accept a legacy tag"
        );
    }
}

#[test]
fn original_d1_identity_survives_t5m_word_roundtrip_without_tags() {
    let words: Vec<_> = parse_binary_source_words(BARE_D1_D2_FRAME)
        .expect("canonical width-bearing words")
        .into_iter()
        .map(|t| t.word)
        .collect();
    assert_eq!(
        words.iter().map(|w| w.width()).collect::<Vec<_>>(),
        vec![2, 3, 2, 1, 2, 1, 2]
    );
    let physical = encode_t5m_via_zig(&words);
    let decoded = sens_cli::zig_transport::decode_t5m_words(&physical)
        .expect("mechanical T5M decode");
    assert_eq!(
        decoded, words,
        "T5M must preserve full exact widths and bits"
    );
    let parsed = parse_canonical_word_sequence(&decoded)
        .expect("SENS D2 structure reader after T5 physical words");
    let ExprKind::List(items) = &parsed[0].kind else {
        panic!("D2 list");
    };
    assert_d1(&items[1], 1);
    assert_d1(&items[2], 0);
}

