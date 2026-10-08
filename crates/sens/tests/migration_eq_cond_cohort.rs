//! #4455 — physical T5 migration witness for historical EQ/COND.
//! No local binding, Number payload, Text7, or host I/O is involved.

use sens::{
    decode_ternary_program, encode_binary_projection_ternary, eval_parsed_expressions,
    open_ternary_program, parse_canonical_binary, render_ternary_words_spaced, Session,
    TernaryTransportError, Value,
};

const SELECT_SOURCE: &str =
    include_str!("../../../tests/fixtures/migration-eq-cond-cohort/eq-cond-select.lisp");
const SELECT_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-eq-cond-cohort/eq-cond-select.sens");
const SKIP_SOURCE: &str =
    include_str!("../../../tests/fixtures/migration-eq-cond-cohort/eq-cond-skip.lisp");
const SKIP_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-eq-cond-cohort/eq-cond-skip.sens");

fn eval_physical(data: &[u8]) -> Value {
    let words = decode_ternary_program(data).expect("canonical physical T5");
    let visible = render_ternary_words_spaced(&words);
    assert_eq!(open_ternary_program(data).unwrap(), visible);
    assert_eq!(encode_binary_projection_ternary(&visible).unwrap(), data);
    let expressions = parse_canonical_binary(&visible).expect("exact D1/D2/D3 source parses");
    eval_parsed_expressions(&expressions, &mut Session::default())
        .expect("current exact-domain oracle executes migrated EQ/COND")
        .value
}

#[test]
fn eq_yes_selects_first_cond_clause_through_exact_d1() {
    assert!(SELECT_SOURCE.contains("(00000001 1)"));
    assert!(SELECT_SOURCE.contains("00000011"));
    assert!(SELECT_SOURCE.contains("00000111"));
    assert_eq!(SELECT_T5.len(), 33);

    let observed = eval_physical(SELECT_T5);
    match observed {
        Value::Pair(head, tail) => {
            assert!(matches!(&*head, Value::Nil));
            assert!(matches!(&*tail, Value::Nil));
        }
        other => panic!("EQ=YES must select quoted singleton EMPTY, got {other:?}"),
    }
}

#[test]
fn eq_no_skips_first_cond_clause_instead_of_host_truthiness() {
    assert!(SKIP_SOURCE.contains("(00000001 0)"));
    assert_eq!(SKIP_T5.len(), 33);
    let observed = eval_physical(SKIP_T5);
    assert!(
        matches!(observed, Value::Nil),
        "EQ=NO must skip first clause and select structural EMPTY in second"
    );
}

#[test]
fn corrupted_t5_or_historical_text_is_not_current_binary_source() {
    assert_eq!(
        decode_ternary_program(&[243]),
        Err(TernaryTransportError::InvalidPhysicalByte)
    );
    let mut bad = SELECT_T5.to_vec();
    bad.push(242);
    assert_eq!(
        decode_ternary_program(&bad),
        Err(TernaryTransportError::InvalidTail)
    );
    assert!(encode_binary_projection_ternary(SELECT_SOURCE).is_err());
}
