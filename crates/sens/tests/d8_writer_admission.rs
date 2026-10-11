//! Exact D8 WRITE-TO-STRING admission; no historical-byte reconstitution.
use sens::{parse_mixed_exact_domain_legacy_core_source, eval_parsed_expressions, Session};

#[test]
fn d8_writer_serializes_structural_data_by_ratified_identity() {
    let mut session = Session::default();
    for (source, expected) in [
        ("(11110100 (001 (a b)))", "\"(a b)\""),
        ("(11110100 (001 ()))", "\"()\""),
        ("(11110100 7)", "\"7\""),
    ] {
        let parsed = parse_mixed_exact_domain_legacy_core_source("lib/core.lisp", source)
            .unwrap_or_else(|e| panic!("D8 surface must be an exact call head: {source}: {e:?}"));
        let result = eval_parsed_expressions(&parsed, &mut session)
            .unwrap_or_else(|e| panic!("D8 writer must use a direct mechanism: {source}: {e:?}"));
        assert_eq!(result.value.to_string(), expected, "writer mismatch {source}");
    }
}

#[test]
fn d8_writer_rejects_incorrect_arity() {
    let mut session = Session::default();
    let parsed = parse_mixed_exact_domain_legacy_core_source("lib/core.lisp", "(11110100 1 2)")
        .expect("D8 writer reference parses");
    let error = eval_parsed_expressions(&parsed, &mut session)
        .expect_err("writer accepts exactly one value");
    assert_eq!(error.kind, sens::ErrorKind::Arity);
}
