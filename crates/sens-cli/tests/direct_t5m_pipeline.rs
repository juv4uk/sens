//! Rust checks only the physical T5M/D2 boundary. SENS owns execution laws.

use sens::Session;
use sens_cli::zig_transport;

fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
    zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
}

fn eval_reference_t5m(
    bytes: &[u8],
    session: &mut Session,
) -> Result<sens::EvalResult, sens::LanguageError> {
    let words = decode_t5m_via_zig(bytes);
    let program = sens::PhysicalT5Program::from_exact_words(&words)?;
    program.execute(session)
}

#[test]
fn all_invalid_physical_or_d2_inputs_are_rejected_before_interpreter() {
    for invalid in [&[][..], &[243][..], &[242][..], &[100, 242][..]] {
        assert!(zig_transport::decode_t5m_words(invalid).is_err());
    }
    // The physical word 01 is a D2 CLOSE, not an executable value.
    let close_word = sens::parse_binary_source_words("01").unwrap()[0].word;
    let close = vec![close_word];
    let bad_structure = zig_transport::encode_t5m_direct(&close).unwrap();
    assert!(eval_reference_t5m(&bad_structure, &mut Session::default()).is_err());
    assert!(zig_transport::decode_t5m_words(&[243]).is_err());
}

#[test]
fn exact_widths_remain_distinct_before_any_surface_lookup() {
    let word1 = sens::parse_binary_source_words("1").unwrap()[0].word;
    let word2 = sens::parse_binary_source_words("001").unwrap()[0].word;
    let word3 = sens::parse_binary_source_words("000000001").unwrap()[0].word;
    let a = zig_transport::encode_t5m_direct(&[word1]).unwrap();
    let b = zig_transport::encode_t5m_direct(&[word2]).unwrap();
    let c = zig_transport::encode_t5m_direct(&[word3]).unwrap();
    assert_ne!(a, b);
    assert_ne!(b, c);
    for physical in [&a, &b, &c] {
        assert_eq!(
            sens::PhysicalT5Program::from_exact_words(&decode_t5m_via_zig(physical))
                .unwrap()
                .form_count(),
            1
        );
    }
}
