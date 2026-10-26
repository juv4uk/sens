//! Physical T5M and the human bit-view must use the SAME D2 and evaluator
//! laws, but the production path must not construct the bit-view at all.
mod support;

use sens::{decode_ternary_words, encode_ternary_words, Session, TernaryTransportError};
use support::{admit_reference_t5m, eval_reference_t5m, ReferenceT5mError};

const QUOTE: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");
const ATOM: &[u8] = include_bytes!("../../../tests/fixtures/migration-atom-cohort/atom-empty.sens");
const COND: &[u8] = include_bytes!("../../../tests/fixtures/migration-d1-cond-cohort/branch.sens");
const MULTIFORM: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-multiform-cohort-main/two-forms.sens");

#[test]
fn physical_execute_matches_reference_t5m_runner_for_admitted_fixtures() {
    for (label, physical) in [
        ("quote", QUOTE),
        ("atom", ATOM),
        ("cond", COND),
        ("multi", MULTIFORM),
    ] {
        let program = admit_reference_t5m(physical).expect(label);
        assert!(program.form_count() > 0, "{label}");
        assert_eq!(program.form_count(), if label == "multi" { 2 } else { 1 });

        let direct = program.execute(&mut Session::default()).expect(label);
        let one_shot = eval_reference_t5m(physical, &mut Session::default()).expect(label);
        assert_eq!(one_shot.value, direct.value, "{label} one-shot parity");
        assert_eq!(one_shot.output, direct.output, "{label} one-shot output");
        let again = program.execute(&mut Session::default()).expect(label);
        assert_eq!(again.value, direct.value, "{label} repeat decoded program");
    }
}

#[test]
fn all_invalid_physical_or_d2_inputs_are_rejected_before_interpreter() {
    for invalid in [&[][..], &[243][..], &[242][..], &[100, 242][..]] {
        assert!(matches!(
            admit_reference_t5m(invalid),
            Err(ReferenceT5mError::Transport(_)),
        ));
    }
    // The physical word 01 is a D2 CLOSE, not an executable value.
    let close = decode_ternary_words(
        &encode_ternary_words(&[sens::parse_binary_source_words("01").unwrap()[0].word]).unwrap(),
    )
    .unwrap();
    let bad_structure = encode_ternary_words(&close).unwrap();
    assert!(matches!(
        admit_reference_t5m(&bad_structure),
        Err(ReferenceT5mError::Language(_))
    ));
    assert!(matches!(
        eval_reference_t5m(&bad_structure, &mut Session::default()),
        Err(ReferenceT5mError::Language(_))
    ));
    assert_eq!(
        decode_ternary_words(&[243]),
        Err(TernaryTransportError::InvalidPhysicalByte)
    );
}

#[test]
fn exact_widths_remain_distinct_before_any_surface_lookup() {
    let a = sens::parse_binary_source_words("1").unwrap().into_iter().next().unwrap().word;
    let b = sens::parse_binary_source_words("001").unwrap().into_iter().next().unwrap().word;
    let c = sens::parse_binary_source_words("000000001").unwrap().into_iter().next().unwrap().word;
    assert_eq!(a.width(), 1);
    assert_eq!(b.width(), 3);
    assert_eq!(c.width(), 9);
    assert_ne!(a, b);
    assert_ne!(b, c);
    for word in [&a, &b, &c] {
        sens::parse_canonical_word_sequence(std::slice::from_ref(word))
            .expect("each exact-width D1/D3/D9 coordinate remains a valid SENS word");
    }
}
