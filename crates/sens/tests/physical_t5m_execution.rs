//! Direct executable .sens code is parsed without an English or text roundtrip.
mod support;

use sens::{
    decode_ternary_program, encode_ternary_words, parse_canonical_binary,
    parse_canonical_packed_words, BinarySourceWord, Bit1, BitPacker, ErrorKind, Session, Value,
};
use support::{eval_reference_t5m, ReferenceT5mError};

const QUOTE_T5M: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");
const MULTIFORM_T5M: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-multiform-cohort-main/two-forms.sens");

#[test]
fn physical_quote_executes_directly_in_a_fresh_binary_session() {
    let result = eval_reference_t5m(QUOTE_T5M, &mut Session::default())
        .expect("physical D3 QUOTE must run without Lisp bootstrap");
    assert!(matches!(result.value, Value::Nil));
    assert!(result.output.is_empty());
}

#[test]
fn physical_multi_form_program_executes_as_a_single_exact_domain_stream() {
    let result = eval_reference_t5m(MULTIFORM_T5M, &mut Session::default())
        .expect("physical T5M must execute both D2-framed forms");
    assert!(matches!(
        &result.value,
        Value::Pair(node)
            if matches!(node.head, Value::Nil) && matches!(node.tail, Value::Nil)
    ));
}

/// Кілька верхніх D2-форм: живе українське джерело й фізичний Zig/T5M
/// виконуються тим самим SENS, а не інтерпретатором зовнішньої мови.
/// Негатив змінює останню форму і мусить змінити фактичне SENS-значення.
#[test]
fn multiform_ukr_and_physical_t5m_execute_to_the_same_sens_value() {
    const SOURCE: &str =
        include_str!("../../../tests/fixtures/migration-multiform-cohort-main/two-forms.lisp");
    let source_value = sens::eval_program(SOURCE, &mut Session::default())
        .expect("test_id=D2-MULTIFORM-UKR layer=SENS native source execution")
        .value;
    let physical_value = eval_reference_t5m(MULTIFORM_T5M, &mut Session::default())
        .expect("test_id=D2-MULTIFORM-T5M layer=SENS physical execution")
        .value;
    assert_eq!(
        source_value, physical_value,
        "test_id=D2-MULTIFORM-PARITY layer=SENS expected=identical-value for укр/T5M"
    );

    let genuine_last_form = "(сполучити (як-є ()) (як-є ()))";
    assert_eq!(SOURCE.matches(genuine_last_form).count(), 1);
    let mutant = SOURCE.replacen(genuine_last_form, "(як-є ())", 1);
    let wrong_value = sens::eval_program(&mutant, &mut Session::default())
        .expect("test_id=D2-MULTIFORM-MUTANT layer=SENS real negative execution")
        .value;
    assert_ne!(
        wrong_value, physical_value,
        "test_id=D2-MULTIFORM-MUTANT layer=SENS expected=changed-result actual=same"
    );
}

#[test]
fn physical_domain_words_share_exact_d2_grammar_with_visible_reference() {
    let words = decode_ternary_program(MULTIFORM_T5M).expect("canonical physical T5M");
    let mut packer = BitPacker::new();
    for word in words.iter().copied() {
        sens::append_binary_source_word(&mut packer, word);
    }
    let widths = words.iter().map(|word| word.width()).collect::<Vec<_>>();
    let physical =
        parse_canonical_packed_words(&packer.finish(), &widths).expect("typed binary reader");
    let reference = sens::render_binary_words_spaced(&words);
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
    let result = eval_reference_t5m(&physical, &mut Session::default())
        .expect("D1 predicate executes from physical bytes");
    assert_eq!(result.value.as_predicate_bit(), Some(true));
}

#[test]
fn malformed_transport_and_invalid_d2_are_distinct_fail_closed_errors() {
    assert!(matches!(
        eval_reference_t5m(&[243], &mut Session::default()),
        Err(ReferenceT5mError::Transport(
            sens::TernaryTransportError::InvalidPhysicalByte
        ))
    ));
    let words = sens::parse_binary_source_words("10 001")
        .unwrap()
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    let physical = encode_ternary_words(&words).unwrap();
    assert!(matches!(
        eval_reference_t5m(&physical, &mut Session::default()),
        Err(ReferenceT5mError::Language(err)) if err.kind == ErrorKind::Parse
    ));
}

#[test]
fn named_lisp_cannot_enter_canonical_binary_reader() {
    let err =
        parse_canonical_binary("(quote ())").expect_err("human Lisp names are not physical source");
    assert_eq!(err.kind, ErrorKind::Parse);
}

/// SENS Zero: a pinned, genuinely physical five-byte program is the oracle.
/// This is (D3:110 COND ((D1:1 D1:1))), not the ASCII text "0"/"1".
#[test]
fn sens_zero_physical_cond_uses_only_exact_d1() {
    let program = "10 110 00 10 1 00 1 01 01";
    const PHYSICAL_T5M: &[u8] = &[0x67, 0x38, 0x68, 0x17, 0x2e];
    let words = sens::parse_binary_source_words(program)
        .expect("exact-width binary oracle")
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    assert_eq!(decode_ternary_program(PHYSICAL_T5M).unwrap(), words);
    assert_eq!(
        encode_ternary_words(&words).unwrap().as_slice(),
        PHYSICAL_T5M
    );

    let selected = eval_reference_t5m(PHYSICAL_T5M, &mut Session::default())
        .expect("D1:1 must select the two-field physical COND clause");
    assert_eq!(selected.value.as_predicate_bit(), Some(true));
    assert!(selected.output.is_empty());

    // D1:0 skips the first clause; D1:1 selects a result of D1:0.
    let no_after_skip = "10 110 00 10 0 00 1 01 00 10 1 00 0 01 01";
    let no_words = sens::parse_binary_source_words(no_after_skip)
        .unwrap()
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    let no_bytes = encode_ternary_words(&no_words).unwrap();
    let result = eval_reference_t5m(&no_bytes, &mut Session::default())
        .expect("the selected result remains exact D1:0");
    assert_eq!(result.value.as_predicate_bit(), Some(false));
    assert!(result.output.is_empty());

    // Exhaustion is structural (), never an implicit D1:0 predicate.
    let exhausted = "10 110 00 10 0 00 1 01 01";
    let empty_words = sens::parse_binary_source_words(exhausted)
        .unwrap()
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    let empty_bytes = encode_ternary_words(&empty_words).unwrap();
    let result = eval_reference_t5m(&empty_bytes, &mut Session::default())
        .expect("no matching exact D1 clause returns structural empty");
    assert!(matches!(result.value, Value::Nil));
    assert_eq!(result.value.as_predicate_bit(), None);
}

/// #3161 CURRENT FOUNDATION SUPERSESSION / Contract 11.8:
/// фізичний D3:000 у позиції COND test відхиляється помилкою Type,
/// а структурне () при вичерпанні зберігається окремим позитивом вище.
/// Немає прихованого перетворення () на D1:NO під час T5M кодування.
#[test]
fn sens_zero_physical_cond_rejects_structural_empty_as_test() {
    for source in [
        "10 110 00 10 000 00 1 01 01",
        "10 110 00 10 000 00 1 01 00 10 1 00 0 01 01",
    ] {
        let words = sens::parse_binary_source_words(source)
            .expect("точний D2/D3 негативний свідок має читатися")
            .into_iter()
            .map(|token| token.word)
            .collect::<Vec<_>>();
        let physical = encode_ternary_words(&words).expect("чинний Zig/T5M");
        assert_eq!(decode_ternary_program(&physical).unwrap(), words);
        match eval_reference_t5m(&physical, &mut Session::default()) {
            Err(ReferenceT5mError::Language(error)) => {
                assert_eq!(
                    error.kind, ErrorKind::Type,
                    "test_id=3161-PHYSICAL-COND layer=SENS source={source} expected=Type actual={error}"
                );
            }
            other => panic!(
                "test_id=3161-PHYSICAL-COND layer=SENS source={source} expected=Type actual={other:?}"
            ),
        }
    }
}

/// Трипольовий COND лишається реальною помилкою форми, а не альтернативою
/// точному двопольовому закону; негатив виконується з фізичних байтів.
#[test]
fn sens_zero_physical_cond_rejects_three_field_clause() {
    let source = "10 110 00 10 1 00 0 00 1 01 01";
    let words = sens::parse_binary_source_words(source)
        .expect("negative witness must be well-formed binary words")
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    let physical = encode_ternary_words(&words).expect("negative witness must be valid T5M");
    assert_eq!(decode_ternary_program(&physical).unwrap(), words);
    assert!(
        matches!(
            eval_reference_t5m(&physical, &mut Session::default()),
            Err(ReferenceT5mError::Language(err)) if err.kind == ErrorKind::InvalidForm
        ),
        "test_id=3161-PHYSICAL-COND-three-fields source={source} expected=InvalidForm"
    );
}

/// SENS owns the entire semantic law matrix in its executable 0/1 program.
/// Rust checks only bit-exact T5 carriage, execution, and the final one-bit
/// verdict protocol; it does not restate D3 behavior in a host-side table.
#[test]
fn d3_semantics_are_executed_and_decided_by_binary_sens() {
    let fixtures: [(&str, &[u8], bool); 2] = [
        (
            include_str!("../../../tests/fixtures/semantic/d3-selftest.bits"),
            include_bytes!("../../../tests/fixtures/semantic/d3-selftest.sens"),
            true,
        ),
        (
            include_str!("../../../tests/fixtures/semantic/d3-selftest-negative.bits"),
            include_bytes!("../../../tests/fixtures/semantic/d3-selftest-negative.sens"),
            false,
        ),
    ];

    // Mechanical mutation control only: both programs have the same domain
    // word positions and exactly ONE D1 source bit is inverted.
    let pass_words = fixtures[0].0.split_whitespace().collect::<Vec<_>>();
    let fail_words = fixtures[1].0.split_whitespace().collect::<Vec<_>>();
    assert_eq!(pass_words.len(), 223, "pinned exact-word count");
    assert_eq!(
        pass_words.len(),
        fail_words.len(),
        "no word added or deleted"
    );
    assert_eq!(pass_words.iter().map(|word| word.len()).sum::<usize>(), 457);
    assert_eq!(fixtures[0].1.len(), 136, "pinned physical T5M size");
    assert_eq!(fixtures[0].1.len(), fixtures[1].1.len());
    let changed = pass_words
        .iter()
        .zip(&fail_words)
        .filter(|(before, after)| before != after)
        .collect::<Vec<_>>();
    assert_eq!(
        changed.as_slice(),
        &[(&"1", &"0")],
        "the negative SENS program must invert exactly one D1 bit"
    );

    for (source, physical, verdict) in fixtures {
        // Only exact binary SENS is admitted: no English/Lisp identifiers.
        assert!(source
            .bytes()
            .all(|byte| byte == b'0' || byte == b'1' || byte.is_ascii_whitespace()));
        let source_words = sens::parse_binary_source_words(source)
            .expect("current exact-width SENS source")
            .into_iter()
            .map(|token| token.word)
            .collect::<Vec<_>>();
        let physical_words = decode_ternary_program(physical)
            .expect("tracked physical T5M decodes to exact-width words");
        assert_eq!(
            physical_words, source_words,
            "the tracked .sens must preserve each source word's exact width and bits"
        );
        let result = eval_reference_t5m(physical, &mut Session::default())
            .expect("SENS self-test must execute directly from packed T5");
        assert!(
            result.output.is_empty(),
            "pure SENS self-test does not print"
        );
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(verdict),
            "SENS, not Rust, must compute its D1 pass/fail verdict"
        );
    }
}
