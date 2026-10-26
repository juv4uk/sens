
use sens_cli::zig_transport;//! Physical T5 transport canary; ATOM's result law remains SENS/Lisp-owned.
use sens::{BinarySourceWord, render_binary_words_spaced,
};

const T5: &[u8] = include_bytes!("../../../tests/fixtures/migration-atom-cohort/atom-empty.sens");



// Обгортки над чинним Zig T5M: staged-out ternary виведено (f5a5b213).
fn decode_ternary_program(bytes: &[u8]) -> Result<Vec<BinarySourceWord>, String> {
    zig_transport::decode_t5m_words(bytes)
}

fn open_ternary_program(bytes: &[u8]) -> Result<String, String> {
    zig_transport::decode_t5m_words(bytes).map(|words| render_binary_words_spaced(&words))
}

fn encode_binary_projection_ternary(source: &str) -> Result<Vec<u8>, String> {
    let words: Vec<BinarySourceWord> = sens::parse_binary_source_words(source)
        .map_err(|error| format!("{error:?}"))?
        .into_iter()
        .map(|token| token.word)
        .collect();
    zig_transport::encode_t5m_direct(&words)
}

#[test]
fn physical_atom_fixture_roundtrips_exact_t5_transport() {
    assert_eq!(T5, [0x64, 0x38, 0x06, 0xa1]);

    let words = decode_ternary_program(T5).expect("canonical T5 bytes decode");
    let visible = render_binary_words_spaced(&words);
    assert_eq!(visible, "10 010 00 000 01");
    assert_eq!(open_ternary_program(T5).unwrap(), visible);
    assert_eq!(encode_binary_projection_ternary(&visible).unwrap(), T5);
}

#[test]
fn malformed_physical_bytes_fail_closed() {
    assert!(decode_ternary_program(&[243]).is_err());
    let mut bad = T5.to_vec();
    bad.push(242);
    assert!(decode_ternary_program(&bad).is_err());
}
