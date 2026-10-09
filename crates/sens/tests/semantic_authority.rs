//! LISP-SEMANTIC-WITNESSES-1 (#1709): the Lisp-owned semantic corpus owns the
//! expected meaning. Rust transports the actual outcome and asks the
//! language-owned verdict protocol in `tests/fixtures/semantic/runner.lisp`
//! whether the outcome is the one the corpus declared.
//!
//! The host has no say in what a predicate answer means. It may only:
//!
//! 1. read a corpus row (Lisp data, never a host literal),
//! 2. evaluate the row's `expr` and transport what actually happened,
//! 3. compare the Lisp verdict label with `pass`.
//!
//! It must NOT: normalise the actual into the expected shape, adapt an
//! expectation per profile, or treat "no such function" as a law.

use std::fs;
use std::path::PathBuf;

use sens::{
    eval_program, load_core_library, load_mechanism_lab_library, parse, Exactness, Expr, ExprKind,
    Session, Value,
};

const RUNNER: &str = include_str!("../../../tests/fixtures/semantic/runner.lisp");

const CORPUS: &[(&str, &str)] = &[
    (
        "predicate-1bit-v1.lisp",
        include_str!("../../../tests/fixtures/semantic/predicate-1bit-v1.lisp"),
    ),
    (
        "atom-1bit-v1.lisp",
        include_str!("../../../tests/fixtures/semantic/atom-1bit-v1.lisp"),
    ),
    (
        "eq-1bit-v1.lisp",
        include_str!("../../../tests/fixtures/semantic/eq-1bit-v1.lisp"),
    ),
    (
        "cond-2part-v1.lisp",
        include_str!("../../../tests/fixtures/semantic/cond-2part-v1.lisp"),
    ),
    (
        "core-universal-v1.lisp",
        include_str!("../../../tests/fixtures/semantic/core-universal-v1.lisp"),
    ),
];

/// A corpus row. `expected` is the exact expected envelope as it appears in
/// the Lisp fixture — the host never re-derives it.
#[derive(Clone)]
struct SemanticRow {
    file: &'static str,
    source: String,
    expr: String,
    expect: String,
    expected: String,
    active: bool,
    name: String,
    semantic_id: String,
    governs: String,
    note: String,
}

fn alist_field<'a>(entries: &'a [Expr], key: &str) -> Option<&'a Expr> {
    entries.iter().find_map(|entry| {
        let ExprKind::Pair(k, v) = &entry.kind else {
            return None;
        };
        let ExprKind::Symbol(name) = &k.kind else {
            return None;
        };
        (&**name == key).then_some(v.as_ref())
    })
}

fn alist_str<'a>(entries: &'a [Expr], key: &str) -> Option<&'a str> {
    match &alist_field(entries, key)?.kind {
        ExprKind::String(value) => Some(value.as_ref()),
        other => panic!("{key} must be a string, got {other:?}"),
    }
}

/// An assertion kind may be written as a symbol or as a string; the runner is
/// indifferent, so the harness must be too.
fn alist_word<'a>(entries: &'a [Expr], key: &str) -> Option<&'a str> {
    match &alist_field(entries, key)?.kind {
        ExprKind::String(value) => Some(value.as_ref()),
        ExprKind::Symbol(value) => Some(value.as_ref()),
        other => panic!("{key} must be a symbol or a string, got {other:?}"),
    }
}

/// A semantic id is written as the exact 8-bit literal it names, not as a
/// string or a symbol — the head of the row IS the id.
fn alist_id(entries: &[Expr], key: &str) -> Option<String> {
    match &alist_field(entries, key)?.kind {
        ExprKind::String(value) => Some(value.as_ref().to_string()),
        ExprKind::Sid(sid) => Some(sid.to_string()),
        other => panic!("{key} must be an exact 8-bit literal or a string, got {other:?}"),
    }
}

fn alist_flag(entries: &[Expr], key: &str) -> bool {
    matches!(
        alist_field(entries, key).map(|value| &value.kind),
        Some(ExprKind::Symbol(symbol)) if &**symbol == "t"
    )
}

fn rows() -> Vec<SemanticRow> {
    let mut rows = Vec::new();
    for (file, source) in CORPUS {
        for form in parse(source)
            .unwrap_or_else(|error| panic!("{file} must parse as Lisp data: {error}"))
        {
            let ExprKind::List(entries) = &form.kind else {
                panic!("every {file} row must be a list");
            };
            let expected_expr = alist_field(entries, "expected")
                .unwrap_or_else(|| panic!("every {file} row must declare `expected`"));
            let expect = alist_word(entries, "expect")
                .unwrap_or_else(|| panic!("every {file} row must declare `expect`"))
                .to_string();
            assert!(
                matches!(
                    expect.as_str(),
                    "expect-value" | "expect-error" | "expect-rejected"
                ),
                "{file}: unknown assertion kind {expect}"
            );
            rows.push(SemanticRow {
                file,
                source: source[form.span.start..form.span.end].to_string(),
                expr: alist_str(entries, "expr")
                    .unwrap_or_else(|| panic!("every {file} row must declare `expr`"))
                    .to_string(),
                expect,
                expected: source[expected_expr.span.start..expected_expr.span.end].to_string(),
                active: alist_flag(entries, "active"),
                name: alist_str(entries, "name")
                    .unwrap_or_else(|| panic!("every {file} row must declare `name`"))
                    .to_string(),
                semantic_id: alist_id(entries, "semantic-id")
                    .unwrap_or_else(|| panic!("every {file} row must declare `semantic-id`")),
                governs: alist_str(entries, "governs")
                    .unwrap_or_else(|| panic!("every {file} row must declare `governs`"))
                    .to_string(),
                note: alist_str(entries, "note")
                    .unwrap_or_else(|| panic!("every {file} row must declare `note`"))
                    .to_string(),
            });
        }
    }
    assert!(
        rows.iter().any(|row| row.active),
        "an all-pending corpus would prove nothing"
    );
    assert!(
        rows.iter().any(|row| !row.active),
        "#1709 is a migration: a corpus with no pending rows cannot show the gap"
    );
    rows
}

fn repo_file(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(relative)
}

fn load_runner(session: &mut Session) {
    let source =
        fs::read_to_string(repo_file("tests/fixtures/semantic/runner.lisp")).expect("runner.lisp");
    assert_eq!(source, RUNNER, "runner.lisp must be the inlined protocol");
    eval_program(&source, session).expect("semantic runner must load");
}

fn escape_lisp_string(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"")
}

/// Transport a value as the form `read` turns back into that very datum.
///
/// A value outside this declared transport domain is a hard failure, never a
/// coerced representation: a lossy projection would make a wrong answer look
/// right, which is the one thing this layer exists to prevent.
fn datum_source(value: &Value) -> String {
    match value {
        Value::Nil => "()".to_string(),
        Value::Number(number, exactness) => {
            assert_eq!(
                *exactness,
                Exactness::Exact,
                "exact arithmetic is the only admissible predicate answer"
            );
            assert_eq!(
                number.fract(),
                0.0,
                "only integers are admitted in the semantic corpus"
            );
            format!("{number}")
        }
        Value::String(text) => format!("\"{}\"", escape_lisp_string(text)),
        Value::Symbol(name) => {
            panic!("a symbol is not an admitted predicate answer: {name}")
        }
        Value::Pair(car, cdr) => {
            let mut out = format!("({}", datum_source(car));
            let mut tail: &Value = cdr;
            loop {
                match tail {
                    Value::Nil => break,
                    Value::Pair(next_car, next_cdr) => {
                        out.push(' ');
                        out.push_str(&datum_source(next_car));
                        tail = next_cdr;
                    }
                    other => panic!("improper tail is not an admitted answer: {other:?}"),
                }
            }
            out.push(')');
            out
        }
        other => panic!("value outside the declared answer transport domain: {other:?}"),
    }
}

/// What the host actually observed, in the language's own convention.
///
/// EVERY payload is a string literal whose text `read` turns back into the very
/// datum `expected` names: a value payload carries the datum's source form, and
/// an error/rejection payload carries a quoted string literal, because `read`
/// would otherwise turn `"Type"` into the symbol `Type`.
fn actual_source(row: &SemanticRow, session: &mut Session) -> String {
    if row.expect == "expect-rejected" {
        let text = escape_lisp_string(&row.expr);
        return match parse(&row.expr) {
            // Parsed after all: the source is legal, so the reader admitted it.
            // Transport the readable source as a value payload and let the Lisp
            // verdict reject it against the corpus expectation.
            Ok(_) => format!("(value \"{text}\")"),
            Err(_) => format!("(rejected \"\\\"{text}\\\"\")"),
        };
    }
    match eval_program(&row.expr, session) {
        Ok(result) => format!(
            "(value \"{}\")",
            escape_lisp_string(&datum_source(&result.value))
        ),
        Err(error) => format!("(error \"\\\"{:?}\\\"\")", error.kind),
    }
}

/// The verdict is the language's. Rust only compares the label symbol.
fn verdict_label(row: &SemanticRow, actual: &str, session: &mut Session) -> String {
    let program = format!(
        "(semantic-verdict-label (quote {}) (quote {}))",
        row.source, actual
    );
    let result = eval_program(&program, session)
        .unwrap_or_else(|error| panic!("verdict failed for {}: {error}", row.expr));
    match &result.value {
        Value::Symbol(name) => name.as_ref().to_string(),
        other => panic!(
            "the verdict label must be a symbol the runner owns, got {other:?}"
        ),
    }
}

fn assert_corpus_holds(session: &mut Session, profile: &str) {
    for row in rows().iter().filter(|row| row.active) {
        let actual = actual_source(row, session);
        assert_eq!(
            verdict_label(row, &actual, session),
            "pass",
            "{profile}: {} — {}\n  expected: {}\n  actual:   {actual}",
            row.file,
            row.name,
            row.expected
        );
    }
}

#[test]
fn native_semantic_witnesses_agree_with_the_lisp_corpus() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    load_runner(&mut session);
    assert_corpus_holds(&mut session, "native");
}

#[test]
fn mechanism_lab_uses_the_same_lisp_semantic_corpus() {
    let mut session = Session::default();
    load_mechanism_lab_library(&mut session).expect("mechanism lab");
    load_runner(&mut session);
    assert_corpus_holds(&mut session, "mechanism-lab");
}

/// The corpus must stay a corpus: every row states a law and names the issue
/// that governs it, so a pending row is a visible gap rather than a silent one.
#[test]
fn every_row_states_a_law() {
    let rows = rows();
    assert!(rows.len() >= 10, "corpus is too small to be a corpus");
    for row in &rows {
        let where_ = format!("{}: {}", row.file, row.name);
        // The declared envelope must be the one the assertion kind promises,
        // so a row cannot claim "expect-error" over a value and read as a law.
        let envelope = match row.expect.as_str() {
            "expect-value" => "(value ",
            "expect-error" => "(error \"",
            "expect-rejected" => "(rejected \"",
            other => panic!("{where_}: unknown assertion kind {other}"),
        };
        assert!(
            row.expected.starts_with(envelope),
            "{where_}: {} does not declare {}",
            row.expected,
            envelope
        );
        // A row is anchored when it says which issue governs it, which exact
        // semantic id it exercises, and why the expectation is what it is.
        assert!(row.governs.starts_with('#'), "{where_}: unanchored `governs`");
        assert!(!row.semantic_id.trim().is_empty(), "{where_}: no `semantic-id`");
        assert!(!row.note.trim().is_empty(), "{where_}: no `note`");
    }
}
