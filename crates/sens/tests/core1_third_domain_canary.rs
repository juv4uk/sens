//! #4467: physical Core1 C1-THIRD specialization on current exact D2/D3.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary, eval_parsed_expressions,
    open_ternary_program, parse_canonical_binary, Session, Value,
};

const SOURCE: &str =
    include_str!("../../../tests/fixtures/core1-third-domain-canary/third.lisp");
const T5: &[u8] =
    include_bytes!("../../../tests/fixtures/core1-third-domain-canary/third.sens");
const VISIBLE: &str = "10 100 00 10 011 00 10 011 00 10 111 00 10 001 00 000 01 00 10 111 00 10 001 00 000 01 00 10 111 00 10 111 00 10 001 00 000 01 00 10 001 00 000 01 01 00 10 001 00 000 01 01 01 01 01 01 01";
const EXPECTED_PHYSICAL: &[u8] = &[0x66, 0x38, 0x64, 0x89, 0x64, 0x89, 0x67, 0x89, 0x63, 0x89, 0x06, 0x89, 0x67, 0x89, 0x63, 0x89, 0x06, 0x89, 0x67, 0x89, 0x67, 0x89, 0x63, 0x89, 0x06, 0x89, 0x63, 0x89, 0x06, 0x8c, 0x15, 0xa7, 0x12, 0x3b, 0x2e, 0xb1, 0x8c, 0x35];

#[test]
fn existing_c1_third_closed_specialization_returns_third_nonempty_pair() {
    assert!(SOURCE.starts_with("(00000101 (00000110 (00000110 "));
    assert_eq!(T5, EXPECTED_PHYSICAL);
    let words = decode_ternary_program(T5).expect("canonical physical T5, 0..4 pad trits");
    let visible = open_ternary_program(T5).expect("typed word view");
    assert_eq!(visible, VISIBLE);
    assert_eq!(
        words.iter().map(ToString::to_string).collect::<Vec<_>>().join(" "),
        VISIBLE
    );
    assert_eq!(encode_binary_projection_ternary(&visible).unwrap(), T5);
    let parsed = parse_canonical_binary(&visible).expect("current exact D2 structure");
    let result = eval_parsed_expressions(&parsed, &mut Session::default())
        .expect("current CAR(CDR(CDR(X))) must execute");
    match &result.value {
        Value::Pair(car, cdr) => {
            assert_eq!(car.as_ref(), &Value::Nil);
            assert_eq!(cdr.as_ref(), &Value::Nil);
        }
        other => panic!("third element must be Pair(Nil,Nil), not first/second Nil: {other:?}"),
    }
}

#[test]
fn corrupt_t5_tail_is_rejected_not_read_as_another_program() {
    let mut appended = T5.to_vec();
    appended.push(0xf2);
    assert!(decode_ternary_program(&appended).is_err());
    assert!(decode_ternary_program(&[243]).is_err());
}
