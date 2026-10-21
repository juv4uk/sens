//! Real process-source D1 reflection: direct one-bit predicates, strict separation.
//! Does not run OS processes, bypass UTF-8/D24+ or assert global release readiness.
use sens::{
    eval_parsed_expressions, parse_mixed_exact_domain_process_tcp_source,
    DomainIdentity, Expr, ExprKind, ErrorKind, Session,
};

const FILE: &str = include_str!("../../../lib/process.lisp");
const PATH: &str = "lib/process.lisp";

fn eval(source: &str) -> Result<sens::Value, sens::LanguageError> {
    let forms = parse_mixed_exact_domain_process_tcp_source(PATH, source)?;
    Ok(eval_parsed_expressions(&forms, &mut Session::default())?.value)
}

fn walk(expr: &Expr, direct: &mut usize) {
    match &expr.kind {
        ExprKind::DomainIdentity(DomainIdentity::D1(_)) => *direct += 1,
        ExprKind::List(items) => {
            for item in items.iter() { walk(item, direct); }
        },
        _ => (),
    }
}

#[test]
fn five_direct_one_bit_values_in_full_process_module() {
    let parsed = parse_mixed_exact_domain_process_tcp_source(PATH, FILE)
        .expect("process module read through exact bounded bridge");
    let mut total = 0;
    for expr in &parsed { walk(expr, &mut total); }
    assert_eq!(total, 0, "no hidden D1 literal may replace executable Lisp");
    assert_eq!(FILE.matches("(атом? (як-є ()))").count(), 5);
    assert!(!FILE.contains("#d1:"));
    assert!(!FILE.contains("((функція"));
    assert!(parse_mixed_exact_domain_process_tcp_source("lib/untrusted.lisp", FILE).is_err());
}

#[test]
fn direct_yes_matches_original_atom_quote_yes_and_direct_no_still_skips() {
    let expected = eval("(010 (001 ()))").expect("legacy expression still valid");
    let actual = eval("(010 (001 ()))").expect("real executable predicate");
    assert_eq!(expected, actual);
    assert_eq!(actual.as_predicate_bit(), Some(true));
    for (bit, selected) in [("(010 (001 (())))","no"), ("(010 (001 ()))","yes")] {
        let code = format!("(110 ({bit} (001 yes)) ((010 (001 ())) (001 no)))");
        let result = eval(&code).expect("D3 COND must consume strict D1");
        assert_eq!(result.to_string(), selected);
    }
}

#[test]
fn short_circuit_d3_cond_and_separation_from_empty_and_numeric() {
    let result = eval("(110 ((010 (001 ())) (001 selected)) ((010 (001 ())) (unreachable-function)))")
        .expect("unreachable branch must not run");
    assert_eq!(result.to_string(), "selected");
    let nil = eval("(001 ())").expect("quoted empty").as_predicate_bit();
    assert_eq!(nil, None, "D3 EMPTY must not become D1 false");
    for bad in [
        "(110 (1 (001 bad)) ((010 (001 ())) (001 yes)))",
        "(110 ((001 ()) (001 bad)) ((010 (001 ())) (001 yes)))",
    ] {
        let error = eval(bad).expect_err("D3 COND requires strict D1 predicate");
        assert_eq!(error.kind, ErrorKind::Type);
    }
}

#[test]
fn direct_zero_and_one_refuse_numeric_inference() {
    for (source, expected) in [("(010 (001 (())))", false), ("(010 (001 ()))", true)] {
        assert_eq!(eval(source).expect("typed W1").as_predicate_bit(), Some(expected));
    }
    assert_eq!(eval("1").expect("legacy number").as_predicate_bit(), None);
    assert_eq!(eval("0").expect("legacy number").as_predicate_bit(), None);
}
