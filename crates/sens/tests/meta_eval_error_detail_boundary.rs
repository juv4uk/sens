mod common;

use sens::{eval_program, load_core_library, ErrorKind, Session};

fn meta_eval(source: &str) -> String {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("core bootstrap");
    common::load_meta_evaluator_library(&mut session).expect("meta-eval bootstrap");
    eval_program(
        &format!("(обчислити-мета-вираз (quote {source}) (quote ()))"),
        &mut session,
    )
    .expect("host must successfully run the meta-evaluator")
    .value
    .to_string()
}

// s2_explicitly_contracts_category_not_error_wording was a pure
// doc/source-text check, relocated to `cargo xtask verify` per
// TEST-ARCHITECTURE-1 step 4 — see crates/xtask/src/checks.rs.

#[test]
fn equivalent_surface_failures_need_not_have_identical_source_spans() {
    let mut first_session = Session::bare();
    load_core_library(&mut first_session).expect("core bootstrap");
    let first = eval_program("(визначити атом? 42)", &mut first_session)
        .expect_err("Canonical rebinding must fail");

    let mut second_session = Session::bare();
    load_core_library(&mut second_session).expect("core bootstrap");
    let second = eval_program("(визначити тотожне? 42)", &mut second_session)
        .expect_err("Canonical rebinding must fail");

    assert_eq!(first.kind, ErrorKind::InvalidForm);
    assert_eq!(second.kind, ErrorKind::InvalidForm);
    assert_ne!(
        first.span, second.span,
        "source-location metadata is allowed to follow the concrete surface spelling"
    );
}

#[test]
fn meta_structured_diagnostics_remain_available_without_becoming_rust_prose() {
    assert_eq!(
        meta_eval("((функція (аргумент інший) аргумент) 1)"),
        "(error arity (expected (exact 2) received 1))"
    );
    assert_eq!(
        meta_eval("((функція (аргумент інший . хвіст) аргумент) 1)"),
        "(error arity (expected (at-least 2) received 1))"
    );
    assert_eq!(
        meta_eval("(функція (аргумент аргумент) аргумент)"),
        "(error invalid-form (lambda-parameters duplicate-parameter аргумент))"
    );

    // The reference side intentionally proves only the contractual kind here.
    // Its human message/span are not parsed into the Lisp diagnostic shape.
    let mut session = Session::bare();
    load_core_library(&mut session).expect("core bootstrap");
    let native = eval_program("((функція (аргумент інший) аргумент) 1)", &mut session)
        .expect_err("reference arity witness must fail");
    assert_eq!(native.kind, ErrorKind::Arity);
}
