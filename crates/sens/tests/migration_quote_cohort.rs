//! #4455 — фізичний T5 round-trip for historical quote cohort; laws remain Lisp-owned.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary, open_ternary_program,
    render_ternary_words_spaced, TernaryTransportError,
};

const SOURCE: &str =
    include_str!("../../../tests/fixtures/migration-quote-cohort/quote-legacy.lisp");
const T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort/quote-legacy.sens");
const MYLISP_SOURCE: &str =
    include_str!("../../../tests/fixtures/migration-quote-cohort/quote-mylisp.lisp");
const MYLISP_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort/quote-mylisp.sens");
const LISP15_SOURCE: &str =
    include_str!("../../../tests/fixtures/migration-quote-cohort/quote-lisp15.lisp");
const LISP15_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort/quote-lisp15.sens");

#[test]
fn physical_quote_legacy_migration_preserves_exact_t5_transport() {
    assert_eq!(SOURCE.trim(), "(00000001 ())");
    assert_eq!(T5, [0x63, 0x89, 0x06, 0xa1]);
    let words = decode_ternary_program(T5).expect("canonical T5 bytes + D2 syntax");
    let visible = render_ternary_words_spaced(&words);
    assert_eq!(visible, "10 001 00 000 01");
    assert_eq!(open_ternary_program(T5).unwrap(), visible);
    assert_eq!(encode_binary_projection_ternary(&visible).unwrap(), T5);
}

#[test]
fn three_physical_quote_sources_share_exact_current_identity() {
    for (source, payload, expected_source) in [
        (MYLISP_SOURCE, MYLISP_T5, "(quote ())"),
        (LISP15_SOURCE, LISP15_T5, "(QUOTE ())"),
    ] {
        assert_eq!(source.trim_end(), expected_source);
        assert_eq!(payload, T5);
        let visible = open_ternary_program(payload).expect("physical T5 opens");
        assert_eq!(visible, "10 001 00 000 01");
    }
}

#[test]
fn invalid_t5_bytes_cannot_be_substituted_for_a_migrated_program() {
    assert_eq!(
        decode_ternary_program(&[243u8]),
        Err(TernaryTransportError::InvalidPhysicalByte)
    );
    let mut bad = T5.to_vec();
    bad.push(242u8);
    assert_eq!(
        decode_ternary_program(&bad),
        Err(TernaryTransportError::InvalidTail)
    );
    assert!(encode_binary_projection_ternary("(00000001 ())").is_err());
}
