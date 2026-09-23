//! Deterministic witness for the Lisp-owned yantraOS bridge contract.
//!
//! No network or yantraOS process is required. The test proves the data
//! boundary: my-lisp creates a typed action envelope and consumes a typed
//! execution observation without granting execution semantics to the model.

use my_lisp::{eval_program, load_core_library, Session};

fn eval_bridge(source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    eval_program(
        include_str!("../../../tests/fixtures/yantraos-bridge-witness.lisp"),
        &mut session,
    )
    .expect("yantraOS bridge witness should load");
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn lisp_builds_typed_yantraos_action_envelope() {
    let source = r#"
        (let ((envelope
                (yo-action-envelope
                  (quote (draft brief))
                  (quote file-management)
                  (quote create)
                  (quote client/brief.txt)
                  (quote ((content "hello") (overwrite 0)))
                  (quote (created-and-verified))
                  (quote ((source my-lisp)
                           (revision 1)))
                  (quote required))))
          (list
            (yo-action-envelope? envelope)
            (yo-field (quote capability) (yo-field (quote action) envelope))
            (yo-field (quote operation) (yo-field (quote action) envelope))
            (yo-field (quote approval) envelope)))
    "#;

    assert_eq!(
        eval_bridge(source),
        "(t file-management create required)"
    );
}

#[test]
fn raw_shell_capability_is_not_a_valid_semantic_action() {
    let source = r#"
        (let ((envelope
                (yo-action-envelope
                  (quote (delete temp))
                  (quote shell)
                  (quote execute)
                  (quote rm)
                  (quote ((command "rm -rf /tmp/x")))
                  (quote (verified))
                  (quote ((source my-lisp)))
                  (quote required))))
          (yo-action-envelope? envelope))
    "#;

    assert_eq!(eval_bridge(source), "()");
}

#[test]
fn execution_result_is_an_observation_with_correlated_provenance() {
    let source = r#"
        (let ((request-provenance
                (quote ((request-id r-42)
                        (state revision-7))))
              (observation
                (yo-execution-observation
                  (quote executed)
                  (quote CLI_FAST_PATH)
                  (quote ((exit-code 0)))
                  (quote ((audit-id a-99)))
                  request-provenance)))
          (list
            (yo-execution-observation? observation)
            (yo-field (quote result) observation)
            (yo-field (quote route) observation)
            (yo-field (quote provenance) observation)))
    "#;

    assert_eq!(
        eval_bridge(source),
        "(t executed CLI_FAST_PATH ((request-id r-42) (state revision-7)))"
    );
}

#[test]
fn execution_observation_does_not_become_truth() {
    let source = r#"
        (let ((observation
                (yo-execution-observation
                  (quote failed)
                  (quote REJECTED)
                  (quote ((reason user-declined)))
                  (quote ((audit-id a-100)))
                  (quote ((request-id r-43)))))
          (list
            (yo-field (quote result) observation)
            (yo-execution-observation? observation)))
    "#;

    assert_eq!(
        eval_bridge(source),
        "(failed t)"
    );
}
