//! #218 observer: transport public predicate inventory + domain inventory into Lisp.
//! The host owns no semantic classification; PASS/FAIL is decided by Lisp.

use std::fs;
use std::path::PathBuf;

use sens::{eval_program, load_core_library, parse, Session};

fn repo_file(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(relative)
}

fn transport_document(session: &mut Session, path: &str, binding: &str) {
    let source = fs::read_to_string(repo_file(path))
        .unwrap_or_else(|error| panic!("required Lisp authority document {path}: {error}"));
    let forms = parse(&source).unwrap_or_else(|error| panic!("{path} must parse: {error}"));
    assert_eq!(forms.len(), 1, "{path} must remain one self-contained Lisp data document");
    let form = &forms[0];
    let exact = &source[form.span.start..form.span.end];
    eval_program(&format!("(def {binding} (quote {exact}))"), session)
        .unwrap_or_else(|error| panic!("transport {path}: {error}"));
}

#[test]
fn every_public_predicate_has_exactly_one_domain_classification_owned_by_lisp() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");

    transport_document(
        &mut session,
        "lib/surface/uk-inventory.lisp",
        "public-surface-inventory-document",
    );
    transport_document(
        &mut session,
        "contracts/structural-query-inventory.lisp",
        "structural-query-inventory-document",
    );

    let witness = fs::read_to_string(repo_file(
        "tests/fixtures/structural-query-inventory-witness.lisp",
    ))
    .expect("#218 Lisp-owned inventory witness");
    eval_program(&witness, &mut session).expect("structural query inventory witness must load");

    let verdict = eval_program("(structural-query-inventory-witness)", &mut session)
        .expect("structural query inventory witness must execute")
        .value
        .to_string();

    assert!(
        verdict.starts_with("(structural-query-inventory-witness (status pass)"),
        "#218 Lisp-owned inventory rejected predicate classification: {verdict}"
    );
}
