//! Physical T5M D2/D7 contextual binding witness; no ASCII Lisp fallback.
//! D2 owns structure, D7 owns exact Text7 cells, D4 owns LAMBDA.
//! This proves physical T5M can carry D7 contextual identifiers without
//! treating arbitrary untyped D2/W7 data as executable symbols.

use sens::{parse_canonical_binary, Session, Value};
use sens_cli::zig_transport;

#[test]
fn existing_d2_d7_and_d4_lambda_execute_from_real_t5m_bytes() {
    // ((D4 LAMBDA ((D2-framed D7 'j')) (D2-framed D7 'j')) D3 EMPTY)
    // Structural brackets/separators are D2, not human Lisp punctuation;
    // 1101010 is an exact W7 cell (106), not a host symbol spelling.
    const WORDS: &str = "10 10 0010 10 10 1101010 01 01 10 1101010 01 01 000 01";

    fn encode_via_zig(source: &str) -> Vec<u8> {
        let tokens = sens::parse_binary_source_words(source)
            .expect("binary projection parses to exact-width tokens");
        let words = tokens
            .into_iter()
            .map(|token| token.word)
            .collect::<Vec<_>>();
        zig_transport::encode_t5m_direct(&words)
            .expect("Zig T5M encoder must produce physical bytes")
    }

    fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
        zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
    }

    fn open_ternary_via_zig(bytes: &[u8]) -> String {
        let words = decode_t5m_via_zig(bytes);
        sens::render_binary_words_spaced(&words)
    }

    let t5 = encode_via_zig(WORDS);
    assert!(!t5.is_empty());
    let read = decode_t5m_via_zig(&t5);
    assert!(!read.is_empty());
    assert_eq!(open_ternary_via_zig(&t5), WORDS);
    let parsed = parse_canonical_binary(WORDS).unwrap();
    assert_eq!(parsed.len(), 1);
    let mut session = Session::default();
    let result = eval_reference_t5m(&t5, &mut session)
        .expect("D2 structure + D7 contextual binder + D4 lambda must work");
    assert_eq!(result.value, Value::Nil);
}

#[test]
fn canonical_t5m_d2_d7_has_no_raw_textual_source_backdoor() {
    // D2/W7 data is valid physical data but isn't automatically a function.
    let data = "10 1101010 01";

    fn encode_via_zig(source: &str) -> Vec<u8> {
        let tokens = sens::parse_binary_source_words(source)
            .expect("binary projection parses to exact-width tokens");
        let words = tokens
            .into_iter()
            .map(|token| token.word)
            .collect::<Vec<_>>();
        zig_transport::encode_t5m_direct(&words)
            .expect("Zig T5M encoder must produce physical bytes")
    }

    let physical = encode_via_zig(data);
    assert_eq!(zig_transport::decode_t5m_words(&physical).unwrap().len(), 3);
    assert_eq!(open_ternary_via_zig(&physical), data);
    // The old host Lisp oracle must not be declared canonical by its
    // presence in a D2 structure: nonbinary identifiers stay rejected.
    let tokens = sens::parse_binary_source_words("(00001001 identity (00001000 (value) value))");
    assert!(tokens.is_err());
}

fn eval_reference_t5m(
    bytes: &[u8],
    session: &mut Session,
) -> Result<sens::EvalResult, sens::LanguageError> {
    let words = zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder");
    let visible = sens::render_binary_words_spaced(&words);
    let parsed = sens::parse_canonical_binary(&visible).expect("D2-framed exact SENS");
    sens::eval_parsed_expressions(&parsed, session)
}

fn open_ternary_via_zig(bytes: &[u8]) -> String {
    let words = zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder");
    sens::render_binary_words_spaced(&words)
}
