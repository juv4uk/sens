//! #4467 / #4472: execute a physical SENS projection specialized from the
//! ALREADY IMPLEMENTED Core1 C1-SECOND = CAR(CDR X). Not a second evaluator.
//!
//! The source witness validates its *own* regeneration from lib/core1.lisp,
//! while this test independently executes the checked-in bytes in the
//! current exact-domain SENS oracle. Historical Core1 T/NIL is not authority.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary,
    eval_parsed_expressions, open_ternary_program, parse_canonical_binary,
    render_ternary_words_spaced, Session, TernaryTransportError, Value,
};

const PROJECTION: &str =
    include_str!("../../../tests/fixtures/core1-domain-canary/second.lisp");
const T5: &[u8] =
    include_bytes!("../../../tests/fixtures/core1-domain-canary/second.sens");

#[test]
fn physical_core1_second_canary_executes_in_current_sens_oracle() {
    assert_eq!(T5.len(), 22, "the committed T5 fixture is exactly 22 bytes");
    // The entrypoint is *physical bytes*, not a handcrafted evaluator value.
    let words = decode_ternary_program(T5)
        .expect("canonical T5 and D2 source structure");
    let visible = render_ternary_words_spaced(&words);
    assert_eq!(visible, PROJECTION.trim(), "same-stem source/bytes differ");
    assert_eq!(open_ternary_program(T5).unwrap(), visible);
    assert_eq!(encode_binary_projection_ternary(&visible).unwrap(), T5);

    let exprs = parse_canonical_binary(&visible)
        .expect("ratified D2/D3 CAR(CDR(CONS...)) source");
    let actual = eval_parsed_expressions(&exprs, &mut Session::default())
        .expect("current SENS oracle executes Core1-specialized program");

    // Applying existing C1-SECOND to a proper two-element list of EMPTYs
    // must yield the second element, namely current D3 EMPTY/NIL.
    assert!(matches!(actual.value, Value::Nil),
            "second-of-two empty values must be D3 EMPTY");
}

#[test]
fn corrupted_or_legacy_transport_cannot_be_admitted_as_the_core1_canary() {
    let mut trailer = T5.to_vec();
    trailer.push(242); // obsolete EOS "22" block, not canonical file EOF
    assert_eq!(
        decode_ternary_program(&trailer),
        Err(TernaryTransportError::InvalidTail)
    );
    assert_eq!(
        decode_ternary_program(&[243u8]),
        Err(TernaryTransportError::InvalidPhysicalByte)
    );
    assert!(encode_binary_projection_ternary("(CAR (CDR X))").is_err());
    assert!(parse_canonical_binary("10 100 00 10 011").is_err());
}
