//! #1131 — host-side transport/observer for the Lisp-owned four-core profile contract.
//!
//! Rust must not duplicate the profile semantics. It transports the exact Lisp
//! document, loads the Lisp witness, and checks only the witness verdict.

use std::fs;
use std::path::PathBuf;

use my_lisp::{eval_program, load_core_library, parse, Session};

fn repo_file(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(relative)
}

#[test]
fn four_core_profiles_share_one_lisp_owned_semantic_authority() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("current Core 4 bootstrap must load");

    let contract = fs::read_to_string(repo_file("contracts/core-profile-contract.lisp"))
        .expect("#1131 requires the Lisp-owned core profile contract");
    let forms = parse(&contract).expect("core-profile-contract.lisp must parse");
    assert_eq!(
        forms.len(),
        1,
        "#1131 core profile contract must remain one self-contained Lisp data document"
    );

    let form = &forms[0];
    let exact_form_source = &contract[form.span.start..form.span.end];
    let transport = format!("(def core-profile-document (quote {exact_form_source}))");
    eval_program(&transport, &mut session)
        .expect("host observer must transport the profile contract unchanged");

    let witness = fs::read_to_string(repo_file("tests/fixtures/core-profile-witness.lisp"))
        .expect("#1131 requires its Lisp-owned witness");
    eval_program(&witness, &mut session).expect("core-profile-witness.lisp must load");

    let verdict = eval_program("(core-profile-witness)", &mut session)
        .expect("Lisp-owned core profile witness must execute");

    assert_eq!(
        verdict.value.to_string(),
        "(core-profile-witness (status pass) (detail one-authority-four-profiles))"
    );
}
