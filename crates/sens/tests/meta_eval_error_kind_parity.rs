mod common;

use sens::{eval_program, load_core_library, ErrorKind, Session};

fn meta_session() -> Session {
    let mut session = Session::bare();
    sens::load_core_library(&mut session).expect("core bootstrap");
    common::load_meta_evaluator_library(&mut session).expect("meta-eval bootstrap");
    session
}

fn meta_eval(source: &str) -> String {
    let mut session = meta_session();
    eval_program(
        &format!("(обчислити-мета-вираз (quote {source}) (quote ()))"),
        &mut session,
    )
    .unwrap_or_else(|error| panic!("host failure while meta-evaluating {source}: {error}"))
    .value
    .to_string()
}

fn meta_program_result(program: &str) -> String {
    let mut session = meta_session();
    eval_program(
        &format!("(решта (обчислити-послідовність-форм (quote ({program})) (quote ())))"),
        &mut session,
    )
    .unwrap_or_else(|error| panic!("host failure while meta-evaluating program {program}: {error}"))
    .value
    .to_string()
}

fn native_error_kind(source: &str) -> ErrorKind {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("core bootstrap");
    eval_program(source, &mut session)
        .expect_err("reference program must fail")
        .kind
}

fn meta_error_kind(value: &str) -> Option<&str> {
    let mut tokens = value.trim_start_matches('(').split_whitespace();
    if tokens.next() == Some("error") {
        tokens.next()
    } else {
        None
    }
}

#[test]
fn current_required_meta_error_kinds_have_paired_reference_witnesses() {
    // Parse failures happen before обчислити-мета-вираз receives data. Resource-limit and
    // division-by-zero kinds are not mechanisms owned by the current explicit
    // meta-evaluator. The required evaluator-originated correspondence set in
    // the current evidence scope is exercised below.
    let cases = [
        ("відсутнє", ErrorKind::UnknownSymbol, "unbound-symbol"),
        ("(відсутнє)", ErrorKind::UnknownSymbol, "unbound-symbol"),
        ("(42)", ErrorKind::Type, "not-callable"),
        ("((функція (аргумент) аргумент))", ErrorKind::Arity, "arity"),
        (
            "(функція (аргумент аргумент) аргумент)",
            ErrorKind::InvalidForm,
            "invalid-form",
        ),
        (
            "(функція (атом?) атом?)",
            ErrorKind::InvalidForm,
            "invalid-form",
        ),
    ];

    for (source, reference_kind, meta_kind) in cases {
        assert_eq!(
            native_error_kind(source),
            reference_kind,
            "source: {source}"
        );
        assert_eq!(
            meta_error_kind(&meta_eval(source)),
            Some(meta_kind),
            "source: {source}"
        );
    }
}

#[test]
fn top_level_canon_definition_has_kind_parity_on_every_admitted_definition_surface() {
    // Чинна українська форма визначення має відхилити повторне зв'язування
    // канонічних імен однаково в native та MetaEval.
    for definition in ["визначити"] {
        for name in ["атом?", "тотожне?", "за-умовою"] {
            let source = format!("({definition} {name} 42)");
            assert_eq!(
                native_error_kind(&source),
                ErrorKind::InvalidForm,
                "reference must reject Canon rebinding: {source}"
            );
            assert_eq!(
                meta_error_kind(&meta_program_result(&source)),
                Some("invalid-form"),
                "meta evaluator must reject Canon rebinding: {source}"
            );
        }
    }
}

#[test]
fn top_level_macro_and_recursive_group_failures_keep_their_reference_kinds() {
    let macro_program = "(визначити-макрос один (аргумент) аргумент) (один)";
    assert_eq!(native_error_kind(macro_program), ErrorKind::Arity);
    assert_eq!(
        meta_error_kind(&meta_program_result(macro_program)),
        Some("arity")
    );

    let malformed_group = "(визначити добрий (функція (аргумент) аргумент)) (визначити хибний (функція (аргумент аргумент) аргумент))";
    assert_eq!(native_error_kind(malformed_group), ErrorKind::InvalidForm);
    assert_eq!(
        meta_error_kind(&meta_program_result(malformed_group)),
        Some("invalid-form")
    );
}
