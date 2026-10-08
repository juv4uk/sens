//! Bounded real migration: historical EQ/COND -> current exact D3 plus D1 atoms.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary, eval_parsed_expressions,
    open_ternary_program, parse_canonical_binary, render_ternary_words_spaced, Session,
    TernaryTransportError, Value,
};

const SELECT_SOURCE: &str = include_str!("../../../tests/fixtures/migration-eq-cond-cohort-main/eq-cond-select.lisp");
const SELECT_T5: &[u8] = include_bytes!("../../../tests/fixtures/migration-eq-cond-cohort-main/eq-cond-select.sens");
const SKIP_SOURCE: &str = include_str!("../../../tests/fixtures/migration-eq-cond-cohort-main/eq-cond-skip.lisp");
const SKIP_T5: &[u8] = include_bytes!("../../../tests/fixtures/migration-eq-cond-cohort-main/eq-cond-skip.sens");

fn eval_physical(data: &[u8]) -> Value {
    let words = decode_ternary_program(data).expect("canonical physical T5");
    let visible = render_ternary_words_spaced(&words);
    assert_eq!(open_ternary_program(data).unwrap(), visible);
    assert_eq!(encode_binary_projection_ternary(&visible).unwrap(), data);
    let expressions = parse_canonical_binary(&visible).expect("exact D1/D2/D3 source parses");
    eval_parsed_expressions(&expressions, &mut Session::default())
        .expect("current exact-domain oracle executes EQ/COND")
        .value
}

#[test]
fn eq_yes_selects_first_cond_clause() {
    assert!(SELECT_SOURCE.contains("(00000001 1)"));
    assert!(SELECT_SOURCE.contains("00000011"));
    assert!(SELECT_SOURCE.contains("00000111"));
    assert_eq!(SELECT_T5.len(), 33);
    // Value implements Drop: borrow it to inspect the pair without moving
    // its owned fields (E0509). The existing exact-domain oracle is unchanged.
    let observed = eval_physical(SELECT_T5);
    match &observed {
        Value::Pair(head, tail) => {
            assert!(matches!(head.as_ref(), Value::Nil));
            assert!(matches!(tail.as_ref(), Value::Nil));
        }
        other => panic!("expected selected pair of empty values, got {other:?}"),
    }
}

#[test]
fn eq_no_skips_first_clause() {
    assert!(SKIP_SOURCE.contains("(00000001 0)"));
    assert_eq!(SKIP_T5.len(), 33);
    assert!(matches!(eval_physical(SKIP_T5), Value::Nil));
}

#[test]
fn corrupt_physical_and_legacy_text_are_rejected() {
    assert_eq!(decode_ternary_program(&[243]), Err(TernaryTransportError::InvalidPhysicalByte));
    let mut bad = SELECT_T5.to_vec();
    bad.push(242);
    assert_eq!(decode_ternary_program(&bad), Err(TernaryTransportError::InvalidTail));
    assert!(encode_binary_projection_ternary(SELECT_SOURCE).is_err());
}
