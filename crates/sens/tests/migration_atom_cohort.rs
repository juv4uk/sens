//! Physical T5M transport canary; ATOM's result law remains SENS/Lisp-owned.

use sens_cli::zig_transport;

const T5: &[u8] = include_bytes!("../../../tests/fixtures/migration-atom-cohort/atom-empty.sens");

fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
    zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
}

fn open_ternary_via_zig(bytes: &[u8]) -> String {
    let words = decode_t5m_via_zig(bytes);
    sens::render_binary_words_spaced(&words)
}

#[test]
fn physical_atom_fixture_roundtrips_exact_t5m_transport() {
    assert_eq!(T5, [0x64, 0x38, 0x06, 0xa1]);

    let words = decode_t5m_via_zig(T5);
    let visible = open_ternary_via_zig(T5);
    assert_eq!(visible, "10 010 00 000 01");
    let re_encoded = zig_transport::encode_t5m_direct(&words).expect("re-encode via Zig T5M");
    assert_eq!(re_encoded, T5);
}

#[test]
fn malformed_physical_bytes_fail_closed() {
    assert!(zig_transport::decode_t5m_words(&[243]).is_err());
    let mut bad = T5.to_vec();
    bad.push(242);
    assert!(zig_transport::decode_t5m_words(&bad).is_err());
}
