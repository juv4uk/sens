//! #216 observer for the Lisp-owned exact-Q binary contract.
//! Rust transports contract bytes and runtime actuals only. Expected semantic
//! outcomes stay in tests/fixtures/exact-q-binary-v1.lisp.

use std::fs;
use std::path::PathBuf;

use sens::{eval_program, load_core_library, parse, Expr, ExprKind, Session};

#[derive(Clone)]
struct Row {
    source: String,
    expr: String,
    expected: String,
}

fn repo_file(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(relative)
}

fn alist_str<'a>(entries: &'a [Expr], key: &str) -> Option<&'a str> {
    entries.iter().find_map(|entry| {
        let ExprKind::Pair(k, v) = &entry.kind else {
            return None;
        };
        let ExprKind::Symbol(name) = &k.kind else {
            return None;
        };
        if &**name != key {
            return None;
        }
        match &v.kind {
            ExprKind::String(value) => Some(value.as_ref()),
            _ => None,
        }
    })
}

fn rows() -> Vec<Row> {
    let source = include_str!("../../../tests/fixtures/exact-q-binary-v1.lisp");
    parse(source)
        .expect("exact-q-binary-v1.lisp must parse")
        .into_iter()
        .filter_map(|form| {
            let ExprKind::List(entries) = &form.kind else {
                return None;
            };
            Some(Row {
                source: source[form.span.start..form.span.end].to_string(),
                expr: alist_str(entries, "expr")?.to_string(),
                expected: alist_str(entries, "expected")?.to_string(),
            })
        })
        .collect()
}

fn transport_contract(session: &mut Session) {
    let source = fs::read_to_string(repo_file("contracts/exact-q-binary-contract.lisp"))
        .expect("#216 exact-Q binary contract");
    let forms = parse(&source).expect("exact-Q binary contract must parse");
    assert_eq!(forms.len(), 1, "#216 contract must remain one Lisp data document");
    let form = &forms[0];
    let exact = &source[form.span.start..form.span.end];
    eval_program(
        &format!("(def exact-q-binary-document (quote {exact}))"),
        session,
    )
    .expect("transport exact-Q binary contract");
}

fn load_witness_runner(session: &mut Session) {
    let source = fs::read_to_string(repo_file("tests/fixtures/witness-runner.lisp"))
        .expect("Lisp-owned witness runner");
    eval_program(&source, session).expect("witness-runner.lisp must load");
}

fn escape_lisp_string(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"")
}

fn actual(row: &Row, session: &mut Session) -> String {
    match eval_program(&row.expr, session) {
        Ok(result) => format!("(value \"{}\")", escape_lisp_string(&result.value.to_string())),
        Err(error) => format!("(error \"{:?}\")", error.kind),
    }
}

#[test]
fn lisp_owned_exact_q_binary_contract_is_self_consistent() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    transport_contract(&mut session);
    let witness = fs::read_to_string(repo_file(
        "tests/fixtures/exact-q-binary-contract-witness.lisp",
    ))
    .expect("#216 exact-Q contract witness");
    eval_program(&witness, &mut session).expect("exact-Q contract witness must load");
    let verdict = eval_program("(exact-q-binary-contract-witness)", &mut session)
        .expect("exact-Q contract witness must execute")
        .value
        .to_string();
    assert!(
        verdict.starts_with("(exact-q-binary-contract-witness (status pass)"),
        "Lisp-owned exact-Q contract rejected itself: {verdict}"
    );
}

#[test]
fn runtime_comparisons_match_lisp_owned_exact_q_results() {
    let rows = rows();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    load_witness_runner(&mut session);

    for row in &rows {
        let runtime_actual = actual(row, &mut session);
        let program = format!(
            "(witness-status (witness-verdict (quote {}) (quote {})))",
            row.source, runtime_actual
        );
        let status = eval_program(&program, &mut session)
            .unwrap_or_else(|error| panic!("#216 Lisp verdict failed for {}: {error}", row.expr))
            .value
            .to_string();
        assert_eq!(
            status, "pass",
            "Lisp-owned #216 witness rejected runtime actual for {} (expected={}, actual={runtime_actual})",
            row.expr, row.expected
        );
    }
}
