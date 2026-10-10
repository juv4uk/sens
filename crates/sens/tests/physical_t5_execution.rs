//! Direct executable .sens code is parsed without an English or text roundtrip.
use sens::{
    decode_ternary_program, encode_ternary_words, eval_t5_program, parse_canonical_binary,
    parse_canonical_packed_words, Bit1, BinarySourceWord, BitPacker, ErrorKind,
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


/// SENS Zero: a pinned, genuinely physical five-byte program is the oracle.
/// This is (D3:110 COND ((D1:1 D1:1))), not the ASCII text "0"/"1".
#[test]
fn sens_zero_physical_cond_uses_only_exact_d1() {
    let program = "10 110 00 10 1 00 1 01 01";
    const PHYSICAL_T5: &[u8] = &[0x67, 0x38, 0x68, 0x17, 0x2e];
    let words = sens::parse_binary_source_words(program)
        .expect("exact-width binary oracle")
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    assert_eq!(decode_ternary_program(PHYSICAL_T5).unwrap(), words);
    assert_eq!(encode_ternary_words(&words).unwrap().as_slice(), PHYSICAL_T5);

    let selected = eval_t5_program(PHYSICAL_T5, &mut Session::default())
        .expect("D1:1 must select the two-field physical COND clause");
    assert_eq!(selected.value.as_predicate_bit(), Some(true));
    assert!(selected.output.is_empty());

    // D1:0 skips the first clause; D1:1 selects a result of D1:0.
    let no_after_skip = "10 110 00 10 0 00 1 01 00 10 1 00 0 01 01";
    let no_words = sens::parse_binary_source_words(no_after_skip)
        .unwrap().into_iter().map(|token| token.word).collect::<Vec<_>>();
    let no_bytes = encode_ternary_words(&no_words).unwrap();
    let result = eval_t5_program(&no_bytes, &mut Session::default())
        .expect("the selected result remains exact D1:0");
    assert_eq!(result.value.as_predicate_bit(), Some(false));
    assert!(result.output.is_empty());

    // Exhaustion is structural (), never an implicit D1:0 predicate.
    let exhausted = "10 110 00 10 0 00 1 01 01";
    let empty_words = sens::parse_binary_source_words(exhausted)
        .unwrap().into_iter().map(|token| token.word).collect::<Vec<_>>();
    let empty_bytes = encode_ternary_words(&empty_words).unwrap();
    let result = eval_t5_program(&empty_bytes, &mut Session::default())
        .expect("no matching exact D1 clause returns structural empty");
    assert!(matches!(result.value, Value::Nil));
    assert_eq!(result.value.as_predicate_bit(), None);
}

/// Strict negative oracles on actual T5 bytes; failures must come from the
/// SENS language mechanism, not from malformed transport or old truthiness.
#[test]
fn sens_zero_physical_cond_rejects_wrong_domain_and_three_field_clause() {
    for (source, expected_kind) in [
        ("10 110 00 10 000 00 1 01 01", ErrorKind::Type),
        ("10 110 00 10 1 00 0 00 1 01 01", ErrorKind::InvalidForm),
    ] {
        let words = sens::parse_binary_source_words(source)
            .expect("negative witness must be well-formed binary words")
            .into_iter().map(|token| token.word).collect::<Vec<_>>();
        let physical = encode_ternary_words(&words)
            .expect("negative witness must be valid T5 transport");
        assert_eq!(decode_ternary_program(&physical).unwrap(), words);
        assert!(matches!(
            eval_t5_program(&physical, &mut Session::default()),
            Err(T5ExecutionError::Language(err)) if err.kind == expected_kind
        ), "exact D1/COND rejected with wrong error category: {source}");
    }
}
