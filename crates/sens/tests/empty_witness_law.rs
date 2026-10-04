use sens::{
    eval_parsed_expressions, parse_canonical_binary, ErrorKind, LanguageError, Session, Value,
};

fn eval_binary(source: &str) -> Result<Value, LanguageError> {
    let expressions = parse_canonical_binary(source)?;
    let mut session = Session::default();
    Ok(eval_parsed_expressions(&expressions, &mut session)?.value)
}

#[test]
fn canonical_d3_cond_selects_only_exact_d1_one() {
    // (D3:011 (D1:1 D1:0)) => D1:0
    let value = eval_binary("10 011 00 10 1 00 0 01 01").unwrap();
    assert_eq!(value.as_predicate_bit(), Some(false));
}

#[test]
fn canonical_d3_cond_skips_exact_d1_zero() {
    // First D1:0 clause is skipped; second D1:1 clause returns D1:0.
    let value = eval_binary(
        "10 011 00 10 0 00 1 01 00 10 1 00 0 01 01",
    )
    .unwrap();
    assert_eq!(value.as_predicate_bit(), Some(false));
}

#[test]
fn canonical_d3_cond_skips_structural_empty_without_coercing_it_to_zero() {
    // First test is D3:000 structural EMPTY/no-witness; second D1:1 selects.
    let value = eval_binary(
        "10 011 00 10 000 00 1 01 00 10 1 00 0 01 01",
    )
    .unwrap();
    assert_eq!(value.as_predicate_bit(), Some(false));

    let no = eval_binary("0").unwrap();
    let empty = eval_binary("000").unwrap();
    assert_eq!(no.as_predicate_bit(), Some(false));
    assert_eq!(empty.as_predicate_bit(), None);
    assert_ne!(no, empty, "D1:0 NO must remain distinct from D3:000 EMPTY");
}

#[test]
fn canonical_d3_cond_exhaustion_returns_structural_empty() {
    let value = eval_binary("10 011 00 10 0 00 1 01 01").unwrap();
    assert!(matches!(value, Value::Nil));
    assert_eq!(value.as_predicate_bit(), None);
}

#[test]
fn canonical_d3_cond_rejects_any_other_test_value() {
    // D3:001 QUOTE identity as data is neither D1 nor structural EMPTY.
    let error = eval_binary("10 011 00 10 001 00 1 01 01").unwrap_err();
    assert_eq!(error.kind, ErrorKind::Type);
    assert!(error.message.contains("D3:011 COND test must return exact D1"));
}

#[test]
fn canonical_d3_cond_rejects_three_part_migration_clause() {
    let error = eval_binary("10 011 00 10 1 00 0 00 1 01 01").unwrap_err();
    assert_eq!(error.kind, ErrorKind::InvalidForm);
}

#[test]
fn computed_empty_no_witness_can_feed_canonical_cond() {
    // Inner COND exhausts to structural EMPTY. The outer COND observes that
    // exact EMPTY/no-witness result, skips it, then selects on D1:1.
    //
    // (D3:011
    //   ((D3:011 (D1:0 D1:1)) D1:1)
    //   (D1:1 D1:0))
    let value = eval_binary(
        "10 011 00            10 10 011 00 10 0 00 1 01 01 00 1 01 00            10 1 00 0 01          01",
    )
    .unwrap();
    assert_eq!(value.as_predicate_bit(), Some(false));
}
