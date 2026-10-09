//! #4455: підтвердження виконання фізичних T5-файлів історичних CAR/CDR/CONS.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary, eval_parsed_expressions,
    open_ternary_program, parse_canonical_binary, render_ternary_words_spaced, Session,
    TernaryTransportError, Value,
};

const CAR_SOURCE: &str =
    include_str!("../../../tests/fixtures/migration-pair-cohort/car-head.lisp");
const CDR_SOURCE: &str =
    include_str!("../../../tests/fixtures/migration-pair-cohort/cdr-tail.lisp");
const CAR_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-pair-cohort/car-head.sens");
const CDR_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-pair-cohort/cdr-tail.sens");

fn eval_file(data: &[u8]) -> Value {
    let words = decode_ternary_program(data).expect("canonical physical T5 and D2");
    let display = render_ternary_words_spaced(&words);
    assert_eq!(open_ternary_program(data).unwrap(), display);
    assert_eq!(encode_binary_projection_ternary(&display).unwrap(), data);
    let parsed = parse_canonical_binary(&display).expect("exact D3 parser");
    eval_parsed_expressions(&parsed, &mut Session::default())
        .expect("current SENS evaluator executes D3 selectors")
        .value
}

#[test]
fn physical_car_returns_the_head_of_cons_without_sid_fallback() {
    assert_eq!(CAR_SOURCE.trim(), "(00000101 (00000100 (00000001 ()) (00000001 (()))))");
    assert_eq!(CAR_T5, b"\x66\x38\x67\x89\x63\x89\x06\x89\x63\x89\x63\x3b\x2e\xb3");
    assert!(matches!(eval_file(CAR_T5), Value::Nil));
}

#[test]
fn physical_cdr_returns_the_pair_tail_not_the_car_head() {
    assert_eq!(CDR_SOURCE.trim(), "(00000110 (00000100 (00000001 ()) (00000001 (()))))");
    assert_eq!(CDR_T5, b"\x64\x89\x67\x89\x63\x89\x06\x89\x63\x89\x63\x3b\x2e\xb3");
    let observed = eval_file(CDR_T5);
    match &observed {
        Value::Pair(head, tail) => {
            assert!(matches!(&**head, Value::Nil));
            assert!(matches!(&**tail, Value::Nil));
        }
        other => panic!("CDR should return the quoted singleton, got {other:?}"),
    }
}

#[test]
fn damaged_physical_or_text_masquerade_is_never_executable() {
    assert_eq!(
        decode_ternary_program(&[243]),
        Err(TernaryTransportError::InvalidPhysicalByte),
    );
    let mut corrupt = CAR_T5.to_vec();
    corrupt.push(242);
    assert_eq!(
        decode_ternary_program(&corrupt),
        Err(TernaryTransportError::InvalidTail),
    );
    assert!(encode_binary_projection_ternary(CAR_SOURCE).is_err());
}
