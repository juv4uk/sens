mod common;

use sens::{eval_program, load_core_library, ErrorKind, Session};

fn session_with_meta() -> Session {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("Core bootstrap");
    common::load_meta_evaluator_library(&mut session).expect("MetaEval bootstrap");
    session
}

fn native_session() -> Session {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("Core bootstrap");
    session
}

fn meta_eval(expr: &str) -> String {
    let mut session = session_with_meta();
    eval_program(
        &format!("(обчислити-мета-вираз (quote {expr}) (quote ()))"),
        &mut session,
    )
    .unwrap_or_else(|error| panic!("MetaEval host failure for {expr}: {error}"))
    .value
    .to_string()
}

fn meta_eval_with_hostile_binding(expr: &str, name: &str) -> String {
    let mut session = session_with_meta();
    let source =
        format!("(обчислити-мета-вираз (quote {expr}) (список (сполучити (як-є {name}) 99)))");
    eval_program(&source, &mut session)
        .unwrap_or_else(|error| panic!("hostile MetaEval environment failed for {expr}: {error}"))
        .value
        .to_string()
}

fn meta_program(program: &str) -> String {
    let mut session = session_with_meta();
    let source = format!("(решта (обчислити-послідовність-форм (quote ({program})) (quote ())))");
    eval_program(&source, &mut session)
        .unwrap_or_else(|error| panic!("MetaEval program failed for {program}: {error}"))
        .value
        .to_string()
}

#[test]
fn native_and_meta_reject_canonical_lambda_binders() {
    for name in [
        "атом?",
        "перше",
        "за-умовою",
        "функція",
        "визначити",
        "як-є",
    ] {
        let source = format!("(функція ({name}) {name})");
        let error = eval_program(&source, &mut native_session())
            .expect_err("native evaluator must reject a canonical binder");
        assert_eq!(error.kind, ErrorKind::InvalidForm, "source: {source}");

        let meta = meta_eval(&source);
        assert!(
            meta.contains("error invalid-form"),
            "MetaEval must reject canonical binder {name}, got: {meta}"
        );
    }
}

#[test]
fn meta_top_level_definition_cannot_create_canonical_binding() {
    for name in ["атом?", "перше", "за-умовою"] {
        let result = meta_program(&format!("(визначити {name} 42)"));
        assert_eq!(
            result,
            format!("(error invalid-form (canonical-name-immutable {name}))"),
            "Canonical definition must be rejected: {name}"
        );
    }
}

#[test]
fn hostile_meta_environment_cannot_retarget_canonical_resolution() {
    assert_eq!(
        meta_eval_with_hostile_binding("(перше (як-є (а б)))", "перше"),
        "а"
    );
}

#[test]
fn ordinary_local_function_binding_remains_shadowable() {
    let expr = "((функція (операція) (операція 2 3)) (функція (перший другий) перший))";
    assert_eq!(meta_eval(expr), "2");
}

const META_CANON_NONATOM_WITNESS: &str =
    include_str!("../../../tests/semantic/meta-quoted-structure-law.lisp");

#[test]
fn quoted_structure_remains_data_in_native_and_meta_evaluation() {
    let mut native = native_session();
    let expected = "(0 1)";
    assert_eq!(
        eval_program(META_CANON_NONATOM_WITNESS, &mut native)
            .expect("Ukrainian structure witness evaluates natively")
            .value
            .to_string(),
        expected
    );
    assert_eq!(meta_eval(META_CANON_NONATOM_WITNESS), expected);
}
