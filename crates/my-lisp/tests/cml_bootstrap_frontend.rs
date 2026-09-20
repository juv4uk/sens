use my_lisp::{eval_program, load_core_library, Session};
use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn witness_source() -> String {
    let path = repo_root().join("tests/fixtures/cml-bootstrap-frontend-witness.lisp");
    fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()))
}

fn witness_field(name: &str) -> String {
    let source = witness_source();
    let prefix = format!("({name} . \"");
    let start = source
        .find(&prefix)
        .unwrap_or_else(|| panic!("witness field {name} must exist"))
        + prefix.len();
    let tail = &source[start..];
    let end = tail
        .find("\")")
        .unwrap_or_else(|| panic!("witness field {name} must be a quoted string"));
    tail[..end].to_string()
}

fn load_frontend(session: &mut Session) {
    load_core_library(session).expect("core must bootstrap before compiler frontend");
    let path = repo_root().join("lib/compiler/cml-bootstrap.lisp");
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));
    eval_program(&source, session)
        .unwrap_or_else(|error| panic!("{} must load as ordinary my-lisp: {error}", path.display()));
}

fn lower_quoted(form: &str, session: &mut Session) -> String {
    let call = format!("(cml-bootstrap-lower-add (quote {form}))");
    eval_program(&call, session)
        .unwrap_or_else(|error| panic!("frontend witness failed for {form}: {error}"))
        .value
        .to_string()
}

#[test]
fn lisp_authored_frontend_emits_bounded_add_envelope() {
    let mut session = Session::default();
    load_frontend(&mut session);

    let actual = lower_quoted(&witness_field("source"), &mut session);
    assert_eq!(actual, witness_field("expected-envelope"));
}

#[test]
fn lisp_authored_frontend_fails_closed_outside_bounded_shape() {
    let mut session = Session::default();
    load_frontend(&mut session);

    for (source_field, expected_field) in [
        ("unsupported-form-source", "unsupported-form-envelope"),
        ("arity-source", "arity-envelope"),
    ] {
        let actual = lower_quoted(&witness_field(source_field), &mut session);
        assert_eq!(
            actual,
            witness_field(expected_field),
            "unexpected frontend verdict for {source_field}"
        );
    }
}

#[test]
fn frontend_source_contains_no_semantic_id_table_or_machine_encoding() {
    let path = repo_root().join("lib/compiler/cml-bootstrap.lisp");
    let source = fs::read_to_string(path).expect("frontend source");
    assert!(!source.contains("semantic-id"));
    assert!(!source.contains("x86-encode"));
    assert!(!source.contains("machine-op"));

    let witness = witness_source();
    assert!(witness.contains("(authority . \"lib/compiler/cml-bootstrap.lisp\")"));
    assert!(witness.contains("(consumer . \"juv4uk/cml#153\")"));
}
