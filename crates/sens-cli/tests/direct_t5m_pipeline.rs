//! Physical T5M and the human bit-view must use the SAME D2 and evaluator
//! laws, but the production path must not construct the bit-view at all.

use sens::{eval_parsed_expressions, parse_canonical_binary, Session};
use sens_cli::zig_transport;

const QUOTE: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");
const ATOM: &[u8] = include_bytes!("../../../tests/fixtures/migration-atom-cohort/atom-empty.sens");
const COND: &[u8] = include_bytes!("../../../tests/fixtures/migration-d1-cond-cohort/branch.sens");
const MULTIFORM: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-multiform-cohort-main/two-forms.sens");

fn decode_t5m_via_zig(bytes: &[u8]) -> Vec<sens::BinarySourceWord> {
    zig_transport::decode_t5m_words(bytes).expect("Zig T5M decoder must recover exact words")
}

fn open_ternary_via_zig(bytes: &[u8]) -> String {
    let words = decode_t5m_via_zig(bytes);
    sens::render_binary_words_spaced(&words)
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
fn physical_execute_matches_reference_visible_path_for_admitted_fixtures() {
    for (label, physical) in [
        ("quote", QUOTE),
        ("atom", ATOM),
        ("cond", COND),
        ("multi", MULTIFORM),
    ] {
        let program =
            sens::PhysicalT5Program::from_exact_words(&decode_t5m_via_zig(physical)).expect(label);
        assert!(program.form_count() > 0, "{label}");
        assert_eq!(program.form_count(), if label == "multi" { 2 } else { 1 });

        // Comparison/reference route only. Production never renders this.
        let visible = open_ternary_via_zig(physical);
        let parsed = parse_canonical_binary(&visible).expect(label);
        let reference = eval_parsed_expressions(&parsed, &mut Session::default()).expect(label);
        let direct = program.execute(&mut Session::default()).expect(label);
        let one_shot = eval_reference_t5m(physical, &mut Session::default()).expect(label);
        assert_eq!(direct.value, reference.value, "{label} result law");
        assert_eq!(direct.output, reference.output, "{label} observable output");
        assert_eq!(one_shot.value, direct.value, "{label} one-shot parity");
        assert_eq!(one_shot.output, direct.output, "{label} one-shot output");
        let again = program.execute(&mut Session::default()).expect(label);
        assert_eq!(again.value, direct.value, "{label} repeat decoded program");
    }
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
