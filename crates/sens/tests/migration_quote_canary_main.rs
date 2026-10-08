//! Bounded physical T5 migration canary: historical QUOTE -> current exact D3 QUOTE.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary, eval_parsed_expressions,
    open_ternary_program, parse_canonical_binary, render_ternary_words_spaced, Session, Value,
};

const SOURCE: &str =
    include_str!("../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.lisp");
const T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");

#[test]
fn migrated_quote_source_has_exact_t5_and_oracle_parity() {
    assert_eq!(SOURCE, "(00000001 ())\n");
    assert_eq!(T5, [0x63, 0x89, 0x06, 0xa1]);

    let words = decode_ternary_program(T5).expect("canonical T5 bytes");
    let visible = render_ternary_words_spaced(&words);
    assert_eq!(visible, "10 001 00 000 01");
    assert_eq!(open_ternary_program(T5).unwrap(), visible);
    assert_eq!(encode_binary_projection_ternary(&visible).unwrap(), T5);

    let expressions = parse_canonical_binary(&visible).expect("current D3 exact source");
    let result = eval_parsed_expressions(&expressions, &mut Session::default())
        .expect("current oracle executes D3 QUOTE of D3 EMPTY");
    assert!(matches!(result.value, Value::Nil));
}
