//! #229 observer for the current Lisp-owned executable Canon laws.
//! Rust transports actual outcomes only; expected semantics live in
//! tests/fixtures/canon-laws-v2-witness.lisp and are judged by witness-runner.lisp.

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
    let source = include_str!("../../../tests/fixtures/canon-laws-v2-witness.lisp");
    parse(source)
        .expect("canon-laws-v2-witness.lisp must parse")
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
            })
        })
        .collect()
}

fn escape_lisp_string(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"")
}

#[test]
fn executable_canon_speaks_layered_answer_semantics() {
    let rows = rows();
    assert_eq!(rows.len(), 13, "#229 slice must keep all 13 Canon V2 rows");

    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");

    let witness = fs::read_to_string(repo_file("tests/fixtures/witness-runner.lisp"))
        .expect("Lisp-owned witness runner");
    eval_program(&witness, &mut session).expect("witness runner must load");

    let canon = fs::read_to_string(repo_file("lib/canon.lisp")).expect("Lisp-owned Canon");
    eval_program(&canon, &mut session).expect("lib/canon.lisp must load as executable semantics");

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
            .unwrap_or_else(|error| {
                let data = "(00000001 ((a . 1) (b . 2)))";
                let caar = format!("(00000101 (00000101 {data}))");
                let eq_miss = format!("(00100010 (00000001 b) {caar})");
                let eq_hit = format!("(00100010 (00000001 a) {caar})");
                let cond_probe = format!("(00000111 ({eq_miss} 0 (00000001 miss)) ({eq_hit} 1 (00000001 hit)))");
                for (label, probe) in [
                    ("atom/nonempty", format!("(00000010 {data})")),
                    ("atom/empty", "(00000010 (00000001 ()))".to_string()),
                    ("car/nonempty", format!("(00000101 {data})")),
                    ("caar/nonempty", caar),
                    ("eq/miss-on-head", eq_miss),
                    ("eq/hit-on-head", eq_hit),
                    ("cond/exact-eq", cond_probe),
                    ("assoc/simple", "(00101101 (00000001 b) (00000001 ((a . 1) (b . 2))))".to_string()),
                    ("assoc/witness", format!("(00101101 (00000001 expected) (quote {}))", row.source)),
                    ("witness-field/expected", format!("(witness-field (00000001 expected) (quote {}))", row.source)),
                ] {
                    eprintln!(
                        "#229 probe {label}: {:?}",
                        eval_program(&probe, &mut session)
                            .map(|value| format!("value={:?}, display={}", value.value, value.value))
                            .map_err(|e| format!("{:?}: {}", e.kind, e))
                    );
                }
                panic!("#229 witness verdict failed for {}: {error}", row.expr)
            })
            .value
            .to_string();
        assert_eq!(
            status, "pass",
            "#229 Lisp-owned Canon witness rejected {} (actual={actual})",
            row.expr
        );
    }
}
