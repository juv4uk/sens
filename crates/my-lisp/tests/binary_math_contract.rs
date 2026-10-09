//! #216 observer: exact-Q binary semantics are owned by Lisp fixture data.
//! Rust transports runtime kind/rendering only.

use std::fs;
use std::path::PathBuf;

use my_lisp::{eval_program, load_core_library, parse, Expr, ExprKind, Session, Value};

#[derive(Clone)]
struct Row {
    source: String,
    expr: String,
}

fn repo_file(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(relative)
}

fn alist_str<'a>(entries: &'a [Expr], key: &str) -> Option<&'a str> {
    entries.iter().find_map(|entry| {
        let ExprKind::Pair(k, v) = &entry.kind else { return None; };
        let ExprKind::Symbol(name) = &k.kind else { return None; };
        if &**name != key { return None; }
        match &v.kind {
            ExprKind::String(value) => Some(value.as_ref()),
            _ => None,
        }
    })
}

fn alist_true(entries: &[Expr], key: &str) -> bool {
    entries.iter().any(|entry| {
        let ExprKind::Pair(k, v) = &entry.kind else { return false; };
        let ExprKind::Symbol(name) = &k.kind else { return false; };
        &**name == key && matches!(&v.kind, ExprKind::Symbol(value) if &**value == "t")
    })
}

fn rows() -> Vec<Row> {
    let source = include_str!("../../../tests/fixtures/binary-math-v1.lisp");
    parse(source)
        .expect("binary-math-v1.lisp must parse")
        .into_iter()
        .filter_map(|form| {
            let ExprKind::List(entries) = &form.kind else { return None; };
            if !alist_true(entries, "active") { return None; }
            Some(Row {
                source: source[form.span.start..form.span.end].to_string(),
                expr: alist_str(entries, "expr")?.to_string(),
            })
        })
        .collect()
}

fn escape_lisp_string(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"")
}

fn kind(value: &Value) -> &'static str {
    match value {
        Value::Rational(_) => "rational",
        Value::Nil => "empty-list",
        Value::Number(_, _) => "number",
        Value::Symbol(_) => "symbol",
        Value::Bool(_) => "host-bool",
        _ => "other",
    }
}

#[test]
fn exact_q_binary_rows_are_judged_by_lisp_owned_witness() {
    let rows = rows();
    assert!(!rows.is_empty(), "#216 exact-Q corpus must remain non-empty");

    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    let witness = fs::read_to_string(repo_file("tests/fixtures/binary-math-witness.lisp"))
        .expect("binary-math witness");
    eval_program(&witness, &mut session).expect("binary-math witness must load");

    for row in rows {
        let value = eval_program(&row.expr, &mut session)
            .unwrap_or_else(|error| panic!("#216 expression {} failed: {error}", row.expr))
            .value;
        let actual_kind = kind(&value);
        let actual_render = escape_lisp_string(&value.to_string());
        let program = format!(
            "(binary-math-verdict (quote {}) (quote {}) \"{}\")",
            row.source, actual_kind, actual_render
        );
        let verdict = eval_program(&program, &mut session)
            .unwrap_or_else(|error| panic!("#216 Lisp verdict failed for {}: {error}", row.expr))
            .value
            .to_string();
        assert!(
            verdict.starts_with("(binary-math-result (status pass)"),
            "#216 Lisp-owned witness rejected {}: {verdict}",
            row.expr
        );
    }
}
