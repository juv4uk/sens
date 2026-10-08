//! #4455 — two historical top-level programs through one physical T5 source.
//! This is a bounded exact D2 stream witness, not an arbitrary loader claim.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary, eval_parsed_expressions,
    open_ternary_program, parse_canonical_binary, Session, Value,
};

const SOURCE: &str =
    include_str!("../../../tests/fixtures/migration-multiform-cohort/two-forms.lisp");
const T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-multiform-cohort/two-forms.sens");
const PROJECTION: &str =
    "10 001 00 000 01 00 10 111 00 10 001 00 000 01 00 10 001 00 000 01 01";

#[test]
fn physical_two_form_source_retains_d2_boundary_and_executes_both() {
    assert_eq!(
        SOURCE,
        "(00000001 ())\n(00000100 (00000001 ()) (00000001 ()))\n"
    );
    assert_eq!(
        T5,
        [
            0x63, 0x89, 0x06, 0x89, 0x67, 0x89, 0x63, 0x89, 0x06, 0x89, 0x63, 0x89, 0x06,
            0x8c,
        ]
    );
    let words = decode_ternary_program(T5).expect("one canonical physical T5");
    assert_eq!(words.len(), 21);
    let visible = open_ternary_program(T5).expect("binary program opens");
    assert_eq!(
        visible.split_whitespace().nth(5),
        Some("00"),
        "D2 inter-form separator"
    );
    assert_eq!(visible, PROJECTION);
    assert_eq!(encode_binary_projection_ternary(&visible).unwrap(), T5);

    let forms = parse_canonical_binary(&visible).expect("parse two current-domain forms");
    assert_eq!(forms.len(), 2, "two top-level forms, not one concatenated datum");
    let first = eval_parsed_expressions(&forms[0..1], &mut Session::default())
        .expect("D3 QUOTE executes")
        .value;
    assert!(matches!(first, Value::Nil));

    let second = eval_parsed_expressions(&forms[1..2], &mut Session::default())
        .expect("D3 CONS and QUOTE execute")
        .value;
    match &second {
        Value::Pair(head, tail) => {
            assert!(matches!(head.as_ref(), Value::Nil));
            assert!(matches!(tail.as_ref(), Value::Nil));
        }
        _ => panic!("second program must yield a pair of empty values"),
    }
}

#[test]
fn invalid_t5_tail_never_becomes_a_second_program() {
    assert!(decode_ternary_program(&[243u8]).is_err());
    let mut bad = T5.to_vec();
    bad.push(242u8);
    assert!(decode_ternary_program(&bad).is_err());
}
