//! #4455: exact D1 predicate-only COND, physically packed T5 to current oracle.
//! This is NOT a claim of historical Lisp COND truthiness equivalence.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary, eval_parsed_expressions,
    open_ternary_program, parse_canonical_binary, render_ternary_words_spaced,
    ErrorKind, Session, TernaryTransportError, Value,
};

const SOURCE: &str =
    include_str!("../../../tests/fixtures/migration-d1-cond-cohort/branch.lisp");
const T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-d1-cond-cohort/branch.sens");
const SPACED_VIEW: &str =
    include_str!("../../../tests/fixtures/migration-d1-cond-cohort/branch");
const WORDS: &str =
    "10 110 00 10 0 00 10 100 00 000 01 01 00 10 1 00 1 01 01";

fn run_visible(source: &str) -> Result<Value, sens::LanguageError> {
    let parsed = parse_canonical_binary(source).expect("exact D2 and D1/D3 parse");
    eval_parsed_expressions(&parsed, &mut Session::default()).map(|result| result.value)
}

#[test]
fn physical_t5_d1_cond_executes_in_current_sens_oracle() {
    assert_eq!(SOURCE, "(за-умовою (ні (перше ())) (так так))\n");
    assert_eq!(T5, [0x67, 0x38, 0x65, 0x15, 0xbf, 0x12, 0x3b, 0x2d, 0xc4, 0xa9, 0xb1, 0xa1]);
    let words = decode_ternary_program(T5).expect("committed file must be canonical T5");
    let current = render_ternary_words_spaced(&words);
    assert_eq!(current, WORDS);
    assert_eq!(SPACED_VIEW, format!("{current}\n"));
    assert_eq!(encode_binary_projection_ternary(SPACED_VIEW).unwrap(), T5);
    assert_eq!(open_ternary_program(T5).unwrap(), WORDS);
    assert_eq!(encode_binary_projection_ternary(WORDS).unwrap(), T5);
    // D1:0 skips even though its result expression CAR(EMPTY) would be a Type error.
    // D1:1 selects D1:1; no historical non-NIL truthiness enters this evaluation.
    let value = run_visible(&current).expect("only D1 answers control exact D3 COND");
    assert_eq!(value.as_predicate_bit(), Some(true));
    assert!(!matches!(value, Value::Nil));
}

#[test]
fn empty_is_never_an_implicit_cond_predicate() {
    let wrong_domain = "10 110 00 10 000 00 1 01 01";
    let packed = encode_binary_projection_ternary(wrong_domain)
        .expect("structurally well formed but semantically wrong-domain");
    assert_eq!(open_ternary_program(&packed).unwrap(), wrong_domain);
    let error = run_visible(wrong_domain).expect_err("EMPTY must fail exact COND control");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn d1_zero_skips_and_no_matching_clause_returns_structural_empty() {
    let skipped = "10 110 00 10 0 00 1 01 01";
    let result = run_visible(skipped).expect("exact D1:0 skips without host truthiness");
    assert!(matches!(result, Value::Nil));
    assert_eq!(result.as_predicate_bit(), None);
}

#[test]
fn corrupt_physical_tail_never_falls_back_to_lisp_text() {
    let mut bad = T5.to_vec();
    bad.push(242u8);
    assert_eq!(
        decode_ternary_program(&bad),
        Err(TernaryTransportError::InvalidTail)
    );
    assert_eq!(
        decode_ternary_program(&[243u8]),
        Err(TernaryTransportError::InvalidPhysicalByte)
    );
    assert!(encode_binary_projection_ternary("(110 (1 1))").is_err());
}
