//! A real physical .sens stream is executable without a human-name parser,
//! historical SID8 routes, or loading the legacy Lisp bootstrap library.
use sens::{
    decode_ternary_program, encode_ternary_words, eval_t5_program, parse_canonical_binary,
    parse_canonical_words, Bit1, BinarySourceWord, ErrorKind, Session,
    T5ExecutionError, TernaryTransportError, Value,
};

const QUOTE_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");
const MULTIFORM_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-multiform-cohort-main/two-forms.sens");

#[test]
fn physical_quote_executes_directly_in_a_fresh_binary_session() {
    let result = eval_t5_program(QUOTE_T5, &mut Session::default())
        .expect("physical .sens D3 QUOTE must execute without language-library bootstrap");
    assert!(matches!(result.value, Value::Nil));
    assert!(result.output.is_empty());
}

#[test]
fn physical_multi_form_program_executes_as_a_single_exact_domain_stream() {
    let result = eval_t5_program(MULTIFORM_T5, &mut Session::default())
        .expect("a physical T5 stream must execute both D2-framed top-level forms");
    assert!(matches!(
        &result.value,
        Value::Pair(head, tail)
            if matches!(head.as_ref(), Value::Nil) && matches!(tail.as_ref(), Value::Nil)
    ));
}

#[test]
fn typed_word_reader_agrees_with_visible_binary_structure_without_legacy_identity() {
    let words = decode_ternary_program(MULTIFORM_T5).expect("canonical physical T5");
    let binary = sens::render_ternary_words_spaced(&words);
    let from_bytes = parse_canonical_words(&words).expect("parse exact source words");
    let from_text = parse_canonical_binary(&binary).expect("parse visible reference only");
    assert_eq!(from_bytes.len(), from_text.len());
    for (physical, visible) in from_bytes.iter().zip(from_text.iter()) {
        let exact_physical = sens::lower_program(&[physical.clone()]);
        let exact_visible = sens::lower_program(&[visible.clone()]);
        assert_eq!(
            sens::expr_to_exact_program_data(&exact_physical[0]).unwrap(),
            sens::expr_to_exact_program_data(&exact_visible[0]).unwrap(),
            "typed physical word parsing and visible reference have identical domain shapes"
        );
    }
}

#[test]
fn physical_d1_value_is_exact_predicate_not_truthiness_or_legacy_t() {
    let physical = encode_ternary_words(&[BinarySourceWord::W1(Bit1::new(1).unwrap())])
        .expect("single D1 bit has a physical transport");
    let result = eval_t5_program(&physical, &mut Session::default())
        .expect("D1 exact predicate must evaluate directly from T5");
    assert_eq!(result.value.as_predicate_bit(), Some(true));
}

#[test]
fn corrupt_physical_transport_and_invalid_d2_grammar_fail_differently() {
    assert!(matches!(
        eval_t5_program(&[243], &mut Session::default()),
        Err(T5ExecutionError::Transport(TernaryTransportError::InvalidPhysicalByte))
    ));

    let unclosed = sens::parse_binary_source_words("10 001")
        .expect("raw typed binary words are individually width-valid")
        .into_iter().map(|token| token.word).collect::<Vec<_>>();
    let physical = encode_ternary_words(&unclosed)
        .expect("physical transport may encode invalid *program* syntax");
    assert!(matches!(
        eval_t5_program(&physical, &mut Session::default()),
        Err(T5ExecutionError::Language(err)) if err.kind == ErrorKind::Parse
    ));
}

#[test]
fn visible_human_name_cannot_enter_typed_binary_reader() {
    let err = parse_canonical_binary("(quote ())")
        .expect_err("human Lisp spelling is not a canonical binary source word");
    assert_eq!(err.kind, ErrorKind::Parse);
    assert!(sens::parse_binary_source_words("1000000000").is_err());
}
