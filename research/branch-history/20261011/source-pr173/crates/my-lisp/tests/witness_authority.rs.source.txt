//! WITNESS-CORPUS-1 (#113): the corpus owns expected truth; Rust only
//! transports actual outcomes and asks Lisp-owned witness logic for a verdict.

use std::fs;
use std::path::PathBuf;

use my_lisp::{
    eval_program, load_core_library, load_meta_evaluator_library, parse, Expr, ExprKind, Session,
};

#[derive(Clone)]
struct WitnessRow {
    source: String,
    expr: String,
    expected: Option<String>,
    error: Option<String>,
    meta_eval: bool,
    compiler_corpus: bool,
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

fn alist_flag(entries: &[Expr], key: &str) -> bool {
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

fn witness_rows() -> Vec<WitnessRow> {
    let source = include_str!("../../../tests/fixtures/conformance.lisp");
    parse(source)
        .expect("conformance.lisp must parse")
        .into_iter()
        .filter_map(|form| {
            let ExprKind::List(entries) = &form.kind else {
                return None;
            };
            let compiler_corpus = alist_flag(entries, "compiler-corpus");
            let meta_eval = alist_flag(entries, "meta-eval");
            if !compiler_corpus && !meta_eval {
                return None;
            }
            Some(WitnessRow {
                source: source[form.span.start..form.span.end].to_string(),
                expr: alist_str(entries, "expr")?.to_string(),
                expected: alist_str(entries, "expected").map(str::to_string),
                error: alist_str(entries, "error").map(str::to_string),
                meta_eval,
                compiler_corpus,
            })
        })
        .collect()
}

fn repo_file(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(relative)
}

fn load_witness_library(session: &mut Session) {
    let source = fs::read_to_string(repo_file("tests/fixtures/witness-runner.lisp"))
        .expect("#113 requires Lisp-owned witness runner/comparator fixture");
    eval_program(&source, session).expect("witness-runner.lisp must load");
}

fn escape_lisp_string(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"")
}

fn actual_form_from_native(row: &WitnessRow, session: &mut Session) -> String {
    match eval_program(&row.expr, session) {
        Ok(result) => format!("(value \"{}\")", escape_lisp_string(&result.value.to_string())),
        Err(error) => format!("(error \"{:?}\")", error.kind),
    }
}

fn assert_lisp_owned_verdict_passes(session: &mut Session, row: &WitnessRow, actual: &str) {
    let program = format!(
        "(witness-pass? (witness-verdict (quote {}) (quote {})))",
        row.source, actual
    );
    let result = eval_program(&program, session)
        .unwrap_or_else(|error| panic!("witness verdict failed for {}: {error}", row.expr));
    assert_eq!(
        result.value.to_string(),
        "t",
        "Lisp-owned witness verdict rejected actual outcome for {}",
        row.expr
    );
}

fn init_meta_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    load_meta_evaluator_library(&mut session).expect("meta evaluator");
    load_witness_library(&mut session);
    eval_program(
        include_str!("../../../lib/generated/meta-semantic-registry.lisp"),
        &mut session,
    )
    .expect("generated semantic registry");
    eval_program("(def --witness-meta-env-- (quote ()))", &mut session)
        .expect("meta environment init");
    session
}

fn meta_verdict(session: &mut Session, row: &WitnessRow) -> String {
    let expr = escape_lisp_string(&row.expr);
    eval_program(
        &format!(
            "(def --witness-meta-step-- (my-eval-program (read-all \"{expr}\") --witness-meta-env--))"
        ),
        session,
    )
    .expect("meta step");
    eval_program(
        "(def --witness-meta-env-- (car --witness-meta-step--))",
        session,
    )
    .expect("thread meta environment");

    let program = format!(
        "(witness-verdict (quote {}) (witness-meta-outcome (cdr --witness-meta-step--)))",
        row.source
    );
    eval_program(&program, session)
        .unwrap_or_else(|error| panic!("meta witness verdict failed for {}: {error}", row.expr))
        .value
        .to_string()
}

#[test]
fn three_execution_paths_share_one_lisp_owned_witness() {
    let adapters = fs::read_to_string(repo_file("tests/fixtures/backend-adapters.lisp"))
        .expect("#116 requires Lisp-owned backend adapter declarations");
    assert!(
        adapters.contains("tests/fixtures/conformance.lisp"),
        "#116 adapters must point at the committed Lisp witness corpus"
    );
    for declaration in [
        "(backend native)",
        "(backend meta)",
        "(backend cml)",
        "(adapter cml-execution)",
    ] {
        assert!(
            adapters.contains(declaration),
            "#116 missing transport declaration `{declaration}`"
        );
    }

    let row = witness_rows()
        .into_iter()
        .find(|row| row.compiler_corpus && row.meta_eval)
        .expect("#116 requires one row admitted to native/meta/CML transport");

    let mut native = Session::default();
    load_core_library(&mut native).expect("core library");
    load_witness_library(&mut native);
    let actual = actual_form_from_native(&row, &mut native);
    assert_lisp_owned_verdict_passes(&mut native, &row, &actual);

    let mut meta = init_meta_session();
    let verdict = meta_verdict(&mut meta, &row);
    assert!(
        verdict.starts_with("(witness-result (status pass)"),
        "meta path disagreed with the shared Lisp-owned witness {}: {verdict}",
        row.expr
    );

    // CML independently consumes the same first compiler-corpus row from this
    // committed corpus. my-lisp deliberately does not depend on CML: the
    // adapter declaration is transport metadata, while CML's sibling-repo test
    // is the executable parser -> lowering -> x86 backend consumer and carries
    // no expected semantic answer of its own.
    assert!(
        row.compiler_corpus,
        "shared row must remain admitted to compiler transport"
    );
}

#[test]
fn compiler_corpus_native_actuals_are_judged_only_by_lisp_owned_witness_logic() {
    let rows: Vec<_> = witness_rows()
        .into_iter()
        .filter(|row| row.compiler_corpus)
        .collect();
    assert!(!rows.is_empty(), "compiler-corpus must remain non-empty");

    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    load_witness_library(&mut session);
    let mut named_errors = 0usize;

    for row in &rows {
        let actual = actual_form_from_native(row, &mut session);
        assert_lisp_owned_verdict_passes(&mut session, row, &actual);
        if row.error.is_some() {
            named_errors += 1;
        }
    }

    assert!(
        named_errors > 0,
        "#113 corpus slice must contain at least one Lisp-authored named error witness"
    );
    assert!(
        rows.iter().any(|row| row.expr.contains("lambda")),
        "#113 compiler slice must retain lambda/application or closure evidence"
    );
    assert!(
        rows.iter().any(|row| row.expr.contains("defmacro")),
        "#113 compiler slice must retain macro evidence"
    );
}

#[test]
fn same_committed_corpus_drives_meta_eval_for_rows_admitted_to_that_backend() {
    let rows: Vec<_> = witness_rows()
        .into_iter()
        .filter(|row| row.meta_eval)
        .collect();
    assert!(!rows.is_empty(), "meta-eval witness slice must remain non-empty");

    let mut session = init_meta_session();
    let mut checked_values = 0usize;

    for row in &rows {
        let verdict = meta_verdict(&mut session, row);
        assert!(
            verdict.starts_with("(witness-result (status pass)"),
            "meta-eval disagreed with Lisp-owned witness row {}: {verdict}",
            row.expr
        );
        if row.expected.is_some() {
            checked_values += 1;
        }
    }

    assert!(checked_values > 0, "meta witness slice must contain value witnesses");
    for required_head in ["quote", "atom", "eq", "car", "cdr", "cons", "cond"] {
        let prefix = format!("({required_head}");
        assert!(
            rows.iter().any(|row| row.expr.trim_start().starts_with(&prefix)),
            "meta witness slice lost McCarthy-7/Canon-0 class `{required_head}`"
        );
    }
    assert!(
        rows.iter().any(|row| row.expr.trim_start().starts_with("((lambda")),
        "meta witness slice must contain lambda application"
    );
}

#[test]
fn peer_surface_witness_reads_semantic_registry_instead_of_copying_surface_truth() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    eval_program(
        include_str!("../../../lib/generated/meta-semantic-registry.lisp"),
        &mut session,
    )
    .expect("generated semantic registry");
    load_witness_library(&mut session);

    let verdict = eval_program("(witness-peer-surface-verdict \"0005\")", &mut session)
        .expect("peer surface witness")
        .value
        .to_string();
    assert!(
        verdict.starts_with("(witness-result (status pass)"),
        "CAR peer surfaces must project to one registry-owned semantic identity: {verdict}"
    );
}

#[test]
fn malformed_witness_fails_closed_as_lisp_data() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    load_witness_library(&mut session);

    let verdict = eval_program(
        "(witness-verdict (quote ((expr . \"(+ 1 2)\"))) (quote (value \"3\")))",
        &mut session,
    )
    .expect("malformed witness must return a named data verdict, not crash")
    .value
    .to_string();

    assert!(
        verdict.starts_with("(witness-result (status malformed)"),
        "missing expected/error must fail closed: {verdict}"
    );
}
