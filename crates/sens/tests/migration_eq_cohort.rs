//! #4455 — historical and uppercase sources retain canonical physical T5M.
//! Rust checks transport bytes only; EQ's result law is owned by Lisp.

use sens_cli::zig_transport;

const HISTORICAL: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-eq-cohort/eq-legacy-sid.sens");
const LISP15: &[u8] = include_bytes!("../../../tests/fixtures/migration-eq-cohort/eq-lisp15.sens");
const VISIBLE: &str = "10 101 00 000 00 000 01";
const PHYSICAL: &[u8] = &[0x66, 0x89, 0x06, 0x36, 0xb3];

fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
    zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
}

fn open_ternary_via_zig(bytes: &[u8]) -> String {
    let words = decode_t5m_via_zig(bytes);
    sens::render_binary_words_spaced(&words)
}

#[test]
fn both_migrated_equality_programs_preserve_canonical_transport() {
    for physical in [HISTORICAL, LISP15] {
        assert_eq!(physical, PHYSICAL);
        let words = decode_t5m_via_zig(physical);
        let visible = open_ternary_via_zig(physical);
        assert_eq!(visible, VISIBLE);
        let words_spaced = words
            .iter()
            .map(ToString::to_string)
            .collect::<Vec<_>>()
            .join(" ");
        assert_eq!(words_spaced, VISIBLE);
        // Re-encode via Zig and compare
        let re_encoded = zig_transport::encode_t5m_direct(&words).expect("re-encode via Zig T5M");
        assert_eq!(re_encoded, physical);
    }
}

#[test]
fn malformed_physical_eq_bytes_never_fall_back_to_text() {
    for physical in [HISTORICAL, LISP15] {
        let mut overpadded = physical.to_vec();
        overpadded.push(0xf2);
        assert!(zig_transport::decode_t5m_words(&overpadded).is_err());
    }
    assert!(zig_transport::decode_t5m_words(&[243]).is_err());
}
