use sens::{eval_program, ErrorKind, Session, Value};
use std::rc::Rc;

fn eval(source: &str) -> Value {
    eval_program(source, &mut Session::default())
        .unwrap_or_else(|error| panic!("evaluation failed: {error}\nsource: {source}"))
        .value
}

#[test]
fn string_append_is_a_first_class_value() {
    assert_eq!(
        eval("(def join string-append) (join \"left\" \"right\")"),
        Value::String(Rc::from("leftright")),
    );
}

#[test]
fn eager_string_builtin_can_be_passed_higher_order() {
    assert_eq!(
        eval("(def apply2 (lambda (f a b) (f a b))) (apply2 string-append \"a\" \"b\")"),
        Value::String(Rc::from("ab")),
    );
}

#[test]
fn all_migrated_string_mechanisms_keep_their_surface_behavior() {
    assert_eq!(eval("(string? \"x\")").as_predicate_bit(), Some(true));
    assert_eq!(eval("(string? 42)").as_predicate_bit(), Some(false));
    assert_eq!(
        eval("(symbol->string (quote hello))"),
        Value::String(Rc::from("hello")),
    );
    assert_eq!(
        eval("(string->symbol \"hello\")"),
        Value::Symbol(Rc::from("hello")),
    );
    assert_eq!(
        eval("(string-first \"λisp\")"),
        Value::String(Rc::from("λ")),
    );
    assert_eq!(
        eval("(string-rest \"λisp\")"),
        Value::String(Rc::from("isp")),
    );
    // string<? визначено мовою в lib/core.lisp (власник, 2026-09-26).
    let mut core = Session::default();
    sens::load_core_library(&mut core).expect("core library should load");
    assert_eq!(
        eval_program("(string<? \"a\" \"b\")", &mut core).unwrap().value,
        Value::Symbol(Rc::from("t"))
    );
}

#[test]
fn codepoint_and_digest_mechanisms_are_first_class_values() {
    assert_eq!(
        eval("(def materialize codepoint->string) (materialize 955)"),
        Value::String(Rc::from("λ")),
    );
    assert_eq!(
        eval("(def scalar string->codepoint) (scalar \"λ\")"),
        Value::Number(955.0, sens::Exactness::Exact),
    );
    assert_eq!(
        eval("(def digest sha256-hex) (digest \"abc\")"),
        Value::String(Rc::from(
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        )),
    );
}

#[test]
fn json_parse_is_a_first_class_value() {
    assert_eq!(
        eval("(def decode json-parse) (decode \"{\\\"a\\\":1}\")").to_string(),
        r#"(("a" . 1))"#,
    );
}

#[test]
fn json_parse_preserves_named_failure_classes() {
    let type_error = eval_program("(json-parse 42)", &mut Session::default())
        .expect_err("non-string JSON input must fail");
    assert_eq!(type_error.kind, ErrorKind::Type);

    let parse_error = eval_program("(json-parse \"{\")", &mut Session::default())
        .expect_err("malformed JSON must fail");
    assert_eq!(parse_error.kind, ErrorKind::Parse);
}

#[test]
fn evaluator_source_does_not_dispatch_migrated_eager_names() {
    let evaluator = include_str!("../src/eval/mod.rs");
    for name in [
        "string-append",
        "string<?",
        "string?",
        "symbol->string",
        "string->symbol",
        "string-first",
        "string-rest",
        "codepoint->string",
        "string->codepoint",
        "sha256-hex",
        "json-parse",
    ] {
        assert!(
            !evaluator.contains(&format!("Some(\"{name}\")")),
            "evaluator regained hard-coded ownership of {name}"
        );
    }
}
