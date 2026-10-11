//! Regression for the legacy Core macro MAP head (D6 101000).
//! Ordinary Lisp parse interprets 101000 as a number; the pinned reader
//! must preserve the callable exact-domain identity without numeric fallback.
use sens::{
    eval_parsed_expressions, eval_program, parse_mixed_exact_domain_legacy_core_source,
    Session,
};
const SOURCE: &str = include_str!("../../../lib/core.lisp");

#[test]
fn legacy_core_reader_is_explicitly_path_bound() {
    assert!(parse_mixed_exact_domain_legacy_core_source("lib/core.lisp", SOURCE).is_ok());
    for path in ["lib/core4.lisp", "lib/forward.lisp", "../core.lisp"] {
        assert!(
            parse_mixed_exact_domain_legacy_core_source(path, SOURCE).is_err(),
            "unapproved core source: {path}"
        );
    }
}

#[test]
fn legacy_core_let_macro_calls_exact_d6_map_not_decimal_101000() {
    let mut session = Session::default();
    let parsed = parse_mixed_exact_domain_legacy_core_source("lib/core.lisp", SOURCE)
        .expect("historical core source should parse with exact D6 call heads");
    eval_parsed_expressions(&parsed, &mut session)
        .expect("legacy core bootstrap with D3-D6 typed calls");
    for (program, expected) in [
        ("(let ((x 7)) x)", "7"),
        ("(let ((x 7) (y 9)) (list x y))", "(7 9)"),
    ] {
        let result = eval_program(program, &mut session)
            .unwrap_or_else(|e| panic!("let macro must execute via D6 MAP in {program}: {e:?}"));
        assert_eq!(result.value.to_string(), expected);
    }
}
