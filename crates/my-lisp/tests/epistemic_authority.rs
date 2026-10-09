//! #287 observer for Lisp-owned epistemic relation and round-trip laws.
//! Rust loads the language-owned witness and checks only its named status
//! envelope; it does not author same/distinct semantic expectations.

use my_lisp::{eval_program, load_core_library, Session};

#[test]
fn epistemic_semantics_are_owned_by_lisp_witness() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    eval_program(include_str!("../../../lib/epistemic.lisp"), &mut session)
        .expect("epistemic library must load");
    eval_program(
        include_str!("../../../tests/fixtures/epistemic-authority-witness.lisp"),
        &mut session,
    )
    .expect("epistemic authority witness must load");

    let verdict = eval_program("(epistemic-authority-witness)", &mut session)
        .expect("epistemic authority witness must execute")
        .value
        .to_string();

    assert!(
        verdict.starts_with("(epistemic-authority-witness (status pass)"),
        "Lisp-owned epistemic witness rejected runtime semantics: {verdict}"
    );
}
