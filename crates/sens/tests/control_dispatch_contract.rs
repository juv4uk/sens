//! #217 observer for Lisp-owned explicit control dispatch witnesses.
//! Rust only evaluates expressions and transports actual outcomes to the
//! existing Lisp-owned witness runner.

use std::fs;
use std::path::PathBuf;

use sens::{eval_program, load_core_library, parse, Expr, ExprKind, Session};

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
    let source = include_str!("../../../tests/fixtures/control-dispatch-v1.lisp");
    parse(source)
        .expect("control-dispatch-v1.lisp must parse")
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

#[test]
fn explicit_dispatch_and_bounded_migration_compatibility_follow_lisp_witnesses() {
    let rows = rows();
    assert_eq!(
        rows.len(),
        10,
        "Contract 8.0 slice must keep six canonical and four migration-only active rows"
    );

    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    let witness = fs::read_to_string(repo_file("tests/fixtures/witness-runner.lisp"))
        .expect("Lisp-owned witness runner");
    eval_program(&witness, &mut session).expect("witness runner must load");

    for row in rows {
        let actual = match eval_program(&row.expr, &mut session) {
            Ok(result) => format!("(value \"{}\")", escape_lisp_string(&result.value.to_string())),
            Err(error) => format!("(error \"{:?}\")", error.kind),
        };
        let program = format!(
            "(witness-status (witness-verdict (quote {}) (quote {})))",
            row.source, actual
        );
        let status = eval_program(&program, &mut session)
            .unwrap_or_else(|error| panic!("#217 witness verdict failed for {}: {error}", row.expr))
            .value
            .to_string();
        assert_eq!(
            status, "pass",
            "#217 Lisp-owned control witness rejected {} (actual={actual})",
            row.expr
        );
    }
}
