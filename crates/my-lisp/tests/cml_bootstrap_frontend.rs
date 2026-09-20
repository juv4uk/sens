use my_lisp::{eval_program, load_core_library, Session};
use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn load_frontend(session: &mut Session) {
    load_core_library(session).expect("core must bootstrap before compiler frontend");
    let path = repo_root().join("lib/compiler/cml-bootstrap.lisp");
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));
    eval_program(&source, session)
        .unwrap_or_else(|error| panic!("{} must load as ordinary my-lisp: {error}", path.display()));
}

#[test]
fn lisp_authored_frontend_emits_bounded_add_envelope() {
    let mut session = Session::default();
    load_frontend(&mut session);

    let actual = eval_program(
        "(cml-bootstrap-lower-add (quote (+ 1 2)))",
        &mut session,
    )
    .expect("bounded + compiler witness must execute in my-lisp")
    .value
    .to_string();

    assert_eq!(
        actual,
        "(cml-ir-bootstrap-v0 (prim + (literal 1) (literal 2)))"
    );
}

#[test]
fn lisp_authored_frontend_fails_closed_outside_bounded_shape() {
    let mut session = Session::default();
    load_frontend(&mut session);

    for (source, expected) in [
        (
            "(cml-bootstrap-lower-add (quote (- 1 2)))",
            "(compiler-frontend-rejection unsupported-form)",
        ),
        (
            "(cml-bootstrap-lower-add (quote (+ 1)))",
            "(compiler-frontend-rejection arity)",
        ),
    ] {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("frontend rejection witness failed: {error}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "unexpected frontend verdict for {source}");
    }
}

#[test]
fn frontend_source_contains_no_semantic_id_table_or_machine_encoding() {
    let path = repo_root().join("lib/compiler/cml-bootstrap.lisp");
    let source = fs::read_to_string(path).expect("frontend source");
    assert!(!source.contains("semantic-id"));
    assert!(!source.contains("x86-encode"));
    assert!(!source.contains("machine-op"));
}
