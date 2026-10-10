//! Direct executable .sens code is parsed without an English or text roundtrip.
use sens::{
    decode_ternary_program, encode_ternary_words, eval_t5_program, parse_canonical_binary,
    parse_canonical_packed_words, prepare_t5_program, Bit1, BinarySourceWord, BitPacker, ErrorKind,
    Session, T5ExecutionError, TernaryTransportError, Value,
};

const QUOTE_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");
const MULTIFORM_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-multiform-cohort-main/two-forms.sens");

#[test]
fn physical_quote_executes_directly_in_a_fresh_binary_session() {
    let result = eval_t5_program(QUOTE_T5, &mut Session::default())
        .expect("physical D3 QUOTE must run without Lisp bootstrap");
    assert!(matches!(result.value, Value::Nil));
    assert!(result.output.is_empty());
}

#[test]
fn physical_multi_form_program_executes_as_a_single_exact_domain_stream() {
    let result = eval_t5_program(MULTIFORM_T5, &mut Session::default())
        .expect("physical T5 must execute both D2-framed forms");
    assert!(matches!(
        &result.value,
        Value::Pair(head, tail)
            if matches!(head.as_ref(), Value::Nil) && matches!(tail.as_ref(), Value::Nil)
    ));
}

#[test]
fn physical_domain_words_share_exact_d2_grammar_with_visible_reference() {
    let words = decode_ternary_program(MULTIFORM_T5).expect("canonical physical T5");
    let mut packer = BitPacker::new();
    for word in words.iter().copied() {
        sens::append_binary_source_word(&mut packer, word);
    }
    let widths = words.iter().map(|word| word.width()).collect::<Vec<_>>();
    let physical = parse_canonical_packed_words(&packer.finish(), &widths)
        .expect("typed binary reader");
    let reference = sens::render_ternary_words_spaced(&words);
    let visible = parse_canonical_binary(&reference).expect("reference visualization");
    assert_eq!(physical.len(), visible.len());
    for (from_bytes, from_reference) in physical.iter().zip(visible.iter()) {
        let left = sens::lower_program(&[from_bytes.clone()]);
        let right = sens::lower_program(&[from_reference.clone()]);
        assert_eq!(
            sens::expr_to_exact_program_data(&left[0]).unwrap(),
            sens::expr_to_exact_program_data(&right[0]).unwrap(),
            "physical and visible views must preserve identical exact domain identities"
        );
    }
}

#[test]
fn physical_d1_value_is_exact_predicate_not_legacy_t() {
    let physical = encode_ternary_words(&[BinarySourceWord::W1(Bit1::new(1).unwrap())])
        .expect("single D1 predicate transports");
    let result = eval_t5_program(&physical, &mut Session::default())
        .expect("D1 predicate executes from physical bytes");
    assert_eq!(result.value.as_predicate_bit(), Some(true));
}

#[test]
fn malformed_transport_and_invalid_d2_are_distinct_fail_closed_errors() {
    assert!(matches!(
        eval_t5_program(&[243], &mut Session::default()),
        Err(T5ExecutionError::Transport(TernaryTransportError::InvalidPhysicalByte))
    ));
    let words = sens::parse_binary_source_words("10 001")
        .unwrap().into_iter().map(|token| token.word).collect::<Vec<_>>();
    let physical = encode_ternary_words(&words).unwrap();
    assert!(matches!(
        eval_t5_program(&physical, &mut Session::default()),
        Err(T5ExecutionError::Language(err)) if err.kind == ErrorKind::Parse
    ));
}

#[test]
fn named_lisp_cannot_enter_canonical_binary_reader() {
    let err = parse_canonical_binary("(quote ())")
        .expect_err("human Lisp names are not physical source");
    assert_eq!(err.kind, ErrorKind::Parse);
}

#[test]
fn prepared_physical_quote_reuses_validated_d2_without_core4_or_text_source() {
    let prepared = prepare_t5_program(QUOTE_T5)
        .expect("physically validated exact D2 QUOTE must prepare");
    assert_eq!(prepared.form_count(), 1);
    // Reuse the same immutable physical program in three independent environments.
    for _ in 0..3 {
        let mut session = Session::bare();
        let reusable = prepared.execute(&mut session)
            .expect("bare prepared D3 QUOTE must execute");
        let full = eval_t5_program(QUOTE_T5, &mut Session::bare())
            .expect("same physical source must execute without prep cache");
        assert_eq!(reusable, full);
        assert!(matches!(reusable.value, Value::Nil));
        assert!(reusable.output.is_empty());
    }
}

#[test]
fn prepared_t5_multiform_and_d1_identity_preserve_semantics() {
    let reusable = prepare_t5_program(MULTIFORM_T5)
        .expect("physically validated D2 multi-form program");
    assert_eq!(reusable.form_count(), 2);
    let value = reusable.execute(&mut Session::bare())
        .expect("bare multi-form evaluation");
    let direct = eval_t5_program(MULTIFORM_T5, &mut Session::bare())
        .expect("bare multi-form direct evaluation");
    assert_eq!(value, direct);

    let yes = encode_ternary_words(&[BinarySourceWord::W1(Bit1::new(1).unwrap())])
        .expect("physical exact D1:YES encoding");
    let prepared = prepare_t5_program(&yes).expect("valid exact D1 data");
    for _ in 0..3 {
        let answer = prepared.execute(&mut Session::bare()).unwrap();
        assert_eq!(answer.value.as_predicate_bit(), Some(true));
        assert_eq!(answer, eval_t5_program(&yes, &mut Session::bare()).unwrap());
    }
}

#[test]
fn preparing_t5_never_bypasses_transport_or_d2_validation() {
    assert!(matches!(
        prepare_t5_program(&[243]),
        Err(T5ExecutionError::Transport(TernaryTransportError::InvalidPhysicalByte))
    ));
    // Physically legal carrier, syntactically incomplete D2 program.
    let unclosed = sens::parse_binary_source_words("10 001")
        .unwrap().into_iter().map(|token| token.word).collect::<Vec<_>>();
    let physical = encode_ternary_words(&unclosed).unwrap();
    assert!(matches!(
        prepare_t5_program(&physical),
        Err(T5ExecutionError::Language(err)) if err.kind == ErrorKind::Parse
    ));
    assert!(matches!(
        prepare_t5_program(&[]),
        Err(T5ExecutionError::Transport(TernaryTransportError::EmptyProgram))
    ));
}
