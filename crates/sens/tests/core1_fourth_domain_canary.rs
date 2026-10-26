//! #4467: exact physical T5M and D2/D3 word-boundary canary.
//! Selected-value laws are witnessed in SENS/Lisp, not in Rust assertions.

use sens_cli::zig_transport;

const T5: &[u8] = include_bytes!("../../../tests/fixtures/core1-fourth-domain-canary/fourth.sens");
const VISIBLE: &str = "10 100 00 10 011 00 10 011 00 10 011 00 10 111 00 10 001 00 000 01 00 10 111 00 10 001 00 000 01 00 10 111 00 10 001 00 000 01 00 10 111 00 10 111 00 10 001 00 000 01 00 10 001 00 000 01 01 00 10 001 00 000 01 01 01 01 01 01 01 01 01";
const EXPECTED_PHYSICAL: &[u8] = &[
    0x66, 0x38, 0x64, 0x89, 0x64, 0x89, 0x64, 0x89, 0x67, 0x89, 0x63, 0x89, 0x06, 0x89, 0x67, 0x89,
    0x63, 0x89, 0x06, 0x89, 0x67, 0x89, 0x63, 0x89, 0x06, 0x89, 0x67, 0x89, 0x67, 0x89, 0x63, 0x89,
    0x06, 0x89, 0x63, 0x89, 0x06, 0x8c, 0x15, 0xa7, 0x12, 0x3b, 0x2e, 0xb1, 0x8c, 0x2e, 0xb3,
];

fn visible_t5m(bytes: &[u8]) -> Result<String, String> {
    zig_transport::decode_t5m_words(bytes).map(|words| {
        words.iter().map(ToString::to_string).collect::<Vec<_>>().join(" ")
    })
}

#[test]
fn fourth_domain_canary_preserves_exact_physical_t5_words() {
    assert_eq!(T5, EXPECTED_PHYSICAL);
    let words = zig_transport::decode_t5m_words(T5).expect("canonical physical T5M, 0..4 pad trits");
    assert_eq!(visible_t5m(T5).unwrap(), VISIBLE);
    assert_eq!(
        words.iter().map(ToString::to_string).collect::<Vec<_>>().join(" "),
        VISIBLE
    );
    let source_words = sens::parse_binary_source_words(VISIBLE)
        .expect("visible view retains exact-width SENS words")
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    assert_eq!(zig_transport::encode_t5m_direct(&source_words).unwrap(), T5);
}

#[test]
fn corrupt_t5m_tail_is_rejected_not_read_as_another_program() {
    let mut appended = T5.to_vec();
    appended.push(0xf2);
    assert!(zig_transport::decode_t5m_words(&appended).is_err());
    assert!(zig_transport::decode_t5m_words(&[243]).is_err());
}
