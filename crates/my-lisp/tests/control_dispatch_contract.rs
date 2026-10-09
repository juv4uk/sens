//! #217 observer for the Lisp-owned canonical control-dispatch contract.
//! Rust transports contract bytes and runtime outcomes only.

use std::fs;
use std::path::PathBuf;

use my_lisp::{eval_program, load_core_library, parse, Expr, ExprKind, Session};

#[derive(Clone)]
struct Row {
    source: String,
    expr: String,
    expected: Option<String>,
    error: Option<String>,
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

fn alist_true(entries: &[Expr], key: &str) -> bool {
    entries.iter().any(|entry| {
        let ExprKind::Pair(k, v) = &entry.kind else {
            return false;
        };
        let ExprKind::Symbol(name) = &k.kind else {
            return false;
        };
        &**name == key && matches!(&v.kind, ExprKind::Symbol(value) if &**value == "t")
    })
}

fn rows() -> Vec<Row> {
    let source = include_str!("../../../tests/fixtures/control-dispatch-v1.lisp");
    parse(source)
        .expect("control-dispatch-v1.lisp must parse")
        .into_iter()
        .filter_map(|form| {
            let ExprKind::List(entries) = &form.kind else {
                return None;
            };
            if !alist_true(entries, "active") {
                return None;
            }
            Some(Row {
                source: source[form.span.start..form.span.end].to_string(),
                expr: alist_str(entries, "expr")?.to_string(),
                expected: alist_str(entries, "expected").map(str::to_string),
                error: alist_str(entries, "error").map(str::to_string),
            })
        })
        .collect()
}

fn escape_lisp_string(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"")
}

fn load_witness_runner(session: &mut Session) {
    let source = fs::read_to_string(repo_file("tests/fixtures/witness-runner.lisp"))
        .expect("Lisp-owned witness runner");
    eval_program(&source, session).expect("witness-runner.lisp must load");
}

fn actual(row: &Row, session: &mut Session) -> String {
    match eval_program(&row.expr, session) {
        Ok(result) => format!("(value \"{}\")", escape_lisp_string(&result.value.to_string())),
        Err(error) => format!("(error \"{:?}\")", error.kind),
    }
}

fn assert_lisp_verdict(session: &mut Session, row: &Row, actual: &str) {
    let program = format!(
        "(witness-pass? (witness-verdict (quote {}) (quote {})))",
        row.source, actual
    );
    let verdict = eval_program(&program, session)
        .unwrap_or_else(|error| panic!("Lisp verdict failed for {}: {error}", row.expr))
        .value
        .to_string();
    assert_eq!(
        verdict, "t",
        "Lisp-owned #217 witness rejected runtime actual for {} (expected={:?}, error={:?}, actual={actual})",
        row.expr, row.expected, row.error
    );
}

fn transport_contract(session: &mut Session) {
    let source = fs::read_to_string(repo_file("contracts/control-dispatch-contract.lisp"))
        .expect("#217 requires Lisp-owned contracts/control-dispatch-contract.lisp");
    let forms = parse(&source).expect("control-dispatch-contract.lisp must parse");
    assert_eq!(
        forms.len(),
        1,
        "#217 control contract must remain one self-contained Lisp data document"
    );
    let form = &forms[0];
    let exact = &source[form.span.start..form.span.end];
    eval_program(
        &format!("(def control-dispatch-document (quote {exact}))"),
        session,
    )
    .expect("transport control-dispatch contract");
}

#[test]
fn lisp_owned_control_dispatch_contract_is_self_consistent() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    transport_contract(&mut session);
    let witness = fs::read_to_string(repo_file(
        "tests/fixtures/control-dispatch-contract-witness.lisp",
    ))
    .expect("#217 control contract witness");
    eval_program(&witness, &mut session).expect("control contract witness must load");
    let verdict = eval_program("(control-dispatch-contract-witness)", &mut session)
        .expect("control contract witness must execute")
        .value
        .to_string();
    assert!(
        verdict.starts_with("(control-dispatch-contract-witness (status pass)"),
        "Lisp-owned control-dispatch contract rejected itself: {verdict}"
    );
}

#[test]
fn current_runtime_reds_against_explicit_control_results() {
    let rows = rows();
    assert_eq!(rows.len(), 7, "#217 first control RED slice must retain seven rows");

    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    load_witness_runner(&mut session);

    for row in &rows {
        let runtime_actual = actual(row, &mut session);
        assert_lisp_verdict(&mut session, row, &runtime_actual);
    }
}
