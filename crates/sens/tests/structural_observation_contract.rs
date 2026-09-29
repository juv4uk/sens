//! #218 observer for remaining Lisp-owned structural result contracts.
//! ATOM/EQ one-bit laws are witnessed separately under #1709.

use std::fs;
use std::path::PathBuf;

use sens::{eval_program, load_core_library, parse, Session};

fn repo_file(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(relative)
}

fn transport_contract(session: &mut Session) {
    let source = fs::read_to_string(repo_file("contracts/structural-observation-contract.lisp"))
        .expect("#218 structural observation contract");
    let forms = parse(&source).expect("structural observation contract must parse");
    assert_eq!(forms.len(), 1, "#218 contract must remain one Lisp data document");
    let form = &forms[0];
    let exact = &source[form.span.start..form.span.end];
    eval_program(
        &format!("(def structural-observation-document (quote {exact}))"),
        session,
    )
    .expect("transport structural observation contract");
}

#[test]
fn lisp_owned_structural_observation_contract_is_self_consistent() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    transport_contract(&mut session);
    let witness = fs::read_to_string(repo_file(
        "tests/fixtures/structural-observation-contract-witness.lisp",
    ))
    .expect("#218 structural contract witness");
    eval_program(&witness, &mut session).expect("structural contract witness must load");
    let verdict = eval_program("(structural-observation-contract-witness)", &mut session)
        .expect("structural contract witness must execute")
        .value
        .to_string();
    assert!(
        verdict.starts_with("(structural-observation-contract-witness (status pass)"),
        "Lisp-owned structural observation contract rejected itself: {verdict}"
    );
}
