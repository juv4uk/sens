//! Direct executable .sens code is parsed without an English or text roundtrip.

use sens::{
    parse_canonical_packed_words, BinarySourceWord, BitPacker, Session, Value,
};
use sens_cli::zig_transport;

/// Спільне джерело для двох тестів: раніше було локальним `const` усередині
/// `multiform_ukr_...`, через що другий тест (`physical_domain_words_...`)
/// не бачив `SOURCE` → error[E0425]. Винесено на рівень модуля.
const SOURCE: &str =
    include_str!("../../../tests/fixtures/migration-multiform-cohort-main/two-forms.lisp");


const QUOTE_T5M: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");
const MULTIFORM_T5M: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-multiform-cohort-main/two-forms.sens");

fn decode_t5m_via_zig(bytes: &[u8]) -> Result<Vec<sens::BinarySourceWord>, String> {
    zig_transport::decode_t5m_words(bytes)
}

fn eval_reference_t5m(bytes: &[u8], session: &mut Session) -> Result<sens::EvalResult, String> {
    let words = decode_t5m_via_zig(bytes)?;
    let program = sens::PhysicalT5Program::from_exact_words(&words)
        .map_err(|e| format!("SENS exact-word admission: {e:?}"))?;
    program.execute(session).map_err(|e| format!("SENS execution: {e:?}"))
}

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

#[test]
fn multiform_ukr_and_physical_t5m_execute_to_the_same_sens_value() {
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
    let words = decode_t5m_via_zig(MULTIFORM_T5M).expect("canonical physical T5M");
    let mut packer = BitPacker::new();
    for word in words.iter().copied() {
        sens::append_binary_source_word(&mut packer, word);
    }
    let widths = words.iter().map(|word| word.width()).collect::<Vec<_>>();
    let physical =
        parse_canonical_packed_words(&packer.finish(), &widths).expect("typed binary reader");
    let visible = sens::parse_mixed_exact_domain(SOURCE)
        .expect("canonical Ukrainian source parsed directly by SENS");
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
    let words = vec![BinarySourceWord::W1(sens::Bit1::new(1).unwrap())];
    let physical = zig_transport::encode_t5m_direct(&words).expect("single D1 predicate transports");
    let result = eval_reference_t5m(&physical, &mut Session::default())
        .expect("D1 predicate executes from physical bytes");
    assert_eq!(result.value.as_predicate_bit(), Some(true));
}

#[test]
fn malformed_transport_and_invalid_d2_are_distinct_fail_closed_errors() {
    // Malformed transport byte rejected at Zig transport level
    assert!(matches!(
        zig_transport::decode_t5m_words(&[243]),
        Err(_)
    ));
    
    // Invalid D2 structure rejected at SENS execution level
    let words = sens::parse_binary_source_words("10 001")
        .unwrap()
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    let physical = zig_transport::encode_t5m_direct(&words).unwrap();
    assert!(matches!(
        eval_reference_t5m(&physical, &mut Session::default()),
        Err(_)
    ));
}

#[test]
fn named_lisp_cannot_enter_canonical_binary_reader() {
    let err =
        sens::parse_canonical_binary("(quote ())").expect_err("human Lisp names are not physical source");
    assert_eq!(err.kind, sens::ErrorKind::Parse);
}

#[test]
fn sens_zero_physical_cond_uses_only_exact_d1() {
    let program = "10 110 00 10 1 00 1 01 01";
    const PHYSICAL_T5M: &[u8] = &[0x67, 0x38, 0x68, 0x17, 0x2e];
    let words = sens::parse_binary_source_words(program)
        .expect("exact-width binary oracle")
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    let decoded = zig_transport::decode_t5m_words(PHYSICAL_T5M).unwrap();
    assert_eq!(decoded.len(), words.len());
    let re_encoded = zig_transport::encode_t5m_direct(&words).unwrap();
    assert_eq!(re_encoded.as_slice(), [0x67, 0x38, 0x68, 0x17, 0x2e]);

    let selected = eval_reference_t5m(PHYSICAL_T5M, &mut Session::default())
        .expect("D1:1 must select the two-field physical COND clause");
    assert_eq!(selected.value.as_predicate_bit(), Some(true));
    assert!(selected.output.is_empty());

    let no_after_skip = "10 110 00 10 0 00 1 01 00 10 1 00 0 01 01";
    let no_words = sens::parse_binary_source_words(no_after_skip)
        .unwrap()
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    let no_bytes = zig_transport::encode_t5m_direct(&no_words).unwrap();
    let result = eval_reference_t5m(&no_bytes, &mut Session::default())
        .expect("the selected result remains exact D1:0");
    assert_eq!(result.value.as_predicate_bit(), Some(false));
    assert!(result.output.is_empty());

    let exhausted = "10 110 00 10 0 00 1 01 01";
    let empty_words = sens::parse_binary_source_words(exhausted)
        .unwrap()
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    let empty_bytes = zig_transport::encode_t5m_direct(&empty_words).unwrap();
    let result = eval_reference_t5m(&empty_bytes, &mut Session::default())
        .expect("no matching exact D1 clause returns structural empty");
    assert!(matches!(result.value, Value::Nil));
    assert_eq!(result.value.as_predicate_bit(), None);
}

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
        let physical = zig_transport::encode_t5m_direct(&words).expect("чинний Zig/T5M");
        let decoded = zig_transport::decode_t5m_words(&physical).unwrap();
        assert_eq!(decoded, words);
        match eval_reference_t5m(&physical, &mut Session::default()) {
            Err(e) if e.contains("Type") => {}
            other => panic!(
                "test_id=3161-PHYSICAL-COND layer=SENS expected=Type actual={other:?}"
            ),
        }
    }
}

#[test]
fn sens_zero_physical_cond_rejects_three_field_clause() {
    let source = "10 110 00 10 1 00 0 00 1 01 01";
    let words = sens::parse_binary_source_words(source)
        .expect("negative witness must be well-formed binary words")
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    let physical = zig_transport::encode_t5m_direct(&words).expect("negative witness must be valid T5M");
    assert!(
        matches!(
            eval_reference_t5m(&physical, &mut Session::default()),
            Err(e) if e.contains("InvalidForm")
        ),
        "test_id=3161-PHYSICAL-COND-three-fields expected=InvalidForm"
    );
}

#[test]
fn d3_semantics_are_executed_and_decided_by_binary_sens() {
    const PASS_BITS: &str =
        include_str!("../../../tests/fixtures/semantic/d3-selftest.bits");
    const PASS_PHYSICAL: &[u8] =
        include_bytes!("../../../tests/fixtures/semantic/d3-selftest.sens");
    const FAIL_BITS: &str =
        include_str!("../../../tests/fixtures/semantic/d3-selftest-negative.bits");
    const FAIL_PHYSICAL: &[u8] =
        include_bytes!("../../../tests/fixtures/semantic/d3-selftest-negative.sens");

    let pass_words = PASS_BITS.split_whitespace().collect::<Vec<_>>();
    let fail_words = FAIL_BITS.split_whitespace().collect::<Vec<_>>();
    assert_eq!(pass_words.len(), 223, "pinned exact-word count");
    assert_eq!(pass_words.len(), fail_words.len(), "no word added or deleted");
    assert_eq!(pass_words.iter().map(|word| word.len()).sum::<usize>(), 457);
    assert_eq!(PASS_PHYSICAL.len(), 136, "pinned physical T5M size");
    assert_eq!(PASS_PHYSICAL.len(), FAIL_PHYSICAL.len());
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

    for (source, physical, verdict) in [
        (include_str!("../../../tests/fixtures/semantic/d3-selftest.bits"), include_bytes!("../../../tests/fixtures/semantic/d3-selftest.sens"), true),
        (include_str!("../../../tests/fixtures/semantic/d3-selftest-negative.bits"), include_bytes!("../../../tests/fixtures/semantic/d3-selftest-negative.sens"), false),
    ] {
        assert!(source
            .bytes()
            .all(|byte| byte == b'0' || byte == b'1' || byte.is_ascii_whitespace()));
        let re_encoded = zig_transport::encode_t5m_direct(
            &sens::parse_binary_source_words(source)
                .unwrap()
                .into_iter()
                .map(|token| token.word)
                .collect::<Vec<_>>(),
        ).unwrap();
        assert_eq!(
            re_encoded, physical,
            "Zig T5M must preserve the exact domain-code stream"
        );
        let result = eval_reference_t5m(physical, &mut Session::default())
            .expect("SENS self-test must execute directly from packed T5M");
        assert!(result.output.is_empty(), "pure SENS self-test does not print");
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(verdict),
            "SENS, not Rust, must compute its D1 pass/fail verdict"
        );
    }
}
