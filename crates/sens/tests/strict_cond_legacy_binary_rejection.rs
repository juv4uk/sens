//! The retired three-field COND is preserved only as physical negative evidence.
//! No English executable identity, Lisp source parser or compatibility switch.
use sens::{
    decode_ternary_program, encode_ternary_words, eval_parsed_expressions,
    parse_canonical_word_sequence, Session,
};

const RETIRED_COND: &[u8] =
    include_bytes!("data/d3-cond-three-field-rejected.t5-negative");

#[test]
fn physical_t5_has_exact_typed_words_and_no_textual_semantic_authority() {
    assert_eq!(RETIRED_COND.len(), 17, "packed T5 is not ASCII pseudo-binary");
    let words = decode_ternary_program(RETIRED_COND)
        .expect("the negative is a *valid D2 program*, not a broken transport file");
    assert_eq!(words.len(), 26);
    assert_eq!(
        encode_ternary_words(&words).unwrap().as_slice(),
        RETIRED_COND,
        "T5 physical bytes must be canonical on this SHA"
    );
    let visible = sens::render_ternary_words_spaced(&words);
    assert_eq!(visible.split_whitespace().count(), 26);
    assert!(visible.split_whitespace().all(|word|
        (1..=9).contains(&word.len())
            && word.bytes().all(|bit| bit == b'0' || bit == b'1')
    ));
    assert_ne!(visible.as_bytes(), RETIRED_COND);
}

#[test]
fn rejected_legacy_three_field_cond_never_reenters_d3_evaluator() {
    let words = decode_ternary_program(RETIRED_COND).unwrap();
    let program = parse_canonical_word_sequence(&words)
        .expect("D2 structural grammar accepts the fixture before strict D3 control");
    assert_eq!(program.len(), 1);
    let error = match eval_parsed_expressions(&program, &mut Session::default()) {
        Ok(_) => panic!("retired three-field COND must never execute"),
        Err(error) => error,
    };
    assert!(
        format!("{error:?}").contains("D3:110 COND requires exactly (test expression)"),
        "negative witness must fail for D3 clause arity, not an unrelated reason: {error:?}"
    );
}
