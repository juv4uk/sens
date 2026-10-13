//! Exhaustive two-state D1 fallback for migrated TCP source; no UTF-8/D24 dependency.
use sens::{
    eval_parsed_expressions, parse_mixed_exact_domain_process_tcp_source, ErrorKind, Session,
};

const PATH: &str = "lib/tcp.lisp";
const SOURCE: &str = include_str!("../../../lib/tcp.lisp");

fn eval_exact(source: &str) -> Result<sens::Value, sens::LanguageError> {
    let parsed = parse_mixed_exact_domain_process_tcp_source(PATH, source)?;
    Ok(eval_parsed_expressions(&parsed, &mut Session::default())?.value)
}

#[test]
fn fallback_value_is_strict_d1_yes_and_not_number_one() {
    let yes = eval_exact("(010 (001 ()))").expect("D3 ATOM of quoted empty");
    assert_eq!(yes.as_predicate_bit(), Some(true));
    let error = eval_exact("(0100 (001 ()))")
        .expect_err("D4 NOT must reject structural EMPTY, not coerce it to D1 NO");
    assert_eq!(error.kind, ErrorKind::Type);
    assert!(error.message.contains("D1"));
}

#[test]
fn both_d1_cond_outcomes_preserve_tcp_tag_dispatch() {
    for (source, expected) in [
        ("(110 ((101 (001 decoded) (001 decoded)) (001 text)) ((010 (001 ())) (001 fallback)))", "text"),
        ("(110 ((101 (001 rejected) (001 decoded)) (001 text)) ((010 (001 ())) (001 fallback)))", "fallback"),
    ] {
        let actual = eval_exact(source).expect("D3 COND with strict D1 equality and fallback");
        assert_eq!(actual.to_string(), expected);
    }
}

#[test]
fn numeric_one_cannot_substitute_for_d1_truth_in_cond() {
    let error = eval_exact(
        "(110 ((101 (001 rejected) (001 decoded)) (001 text)) (1 (001 fallback)))"
    ).expect_err("unqualified number 1 is not a D1 predicate");
    assert!(matches!(error.kind, ErrorKind::Type | ErrorKind::InvalidForm));
}

#[test]
fn real_tcp_file_reads_with_current_domain_widths() {
    let parsed = parse_mixed_exact_domain_process_tcp_source(PATH, SOURCE)
        .expect("pinned real TCP module must parse");
    assert_eq!(parsed.len(), 7);
    let code_only = SOURCE.lines()
        .filter(|line| !line.trim_start().starts_with(';'))
        .collect::<Vec<_>>().join("\n");
    assert_eq!(code_only.matches("(010 (001 ()))").count(), 1);
    assert!(!SOURCE.contains("(0100 (101 (100 decoded) (001 decoded)))"));
    assert!(parse_mixed_exact_domain_process_tcp_source("lib/untrusted.lisp", SOURCE).is_err());
}
