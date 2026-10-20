//! Реальний SENS-виконавець: українські предикати знань із точним D1.
//! Історичний SID8, #d1-текст і старий зріз 6 форм не є доказом.
use sens::{eval_core_library_source, eval_parsed_expressions, eval_program,
           parse_mixed_exact_domain_reasoning_source, Session, Value};

fn session() -> Session {
    let mut s = Session::default();
    eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut s)
        .expect("точний SENS bootstrap");
    for (path, text) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
        ("lib/forward.lisp", include_str!("../../../lib/forward.lisp")),
        ("lib/knowledge.lisp", include_str!("../../../lib/knowledge.lisp")),
    ] {
        let forms = parse_mixed_exact_domain_reasoning_source(path, text)
            .unwrap_or_else(|error| panic!("SENS reader {path}: {error:?}"));
        eval_parsed_expressions(&forms, &mut s)
            .unwrap_or_else(|error| panic!("SENS load {path}: {error:?}"));
    }
    s
}

fn eval(s: &mut Session, code: &str) -> Value {
    eval_program(code, s)
        .unwrap_or_else(|error| panic!("SENS evaluation {code}: {error:?}"))
        .value
}

#[test]
fn ukrainian_negation_heads_preserve_exact_d1() {
    let mut s = session();
    for (head, expected) in [("not", true), ("not?", true), ("plain", false)] {
        let code = format!("(голова-твердження-знань-заперечена? (як-є {head}))");
        let answer = eval(&mut s, &code);
        assert_eq!(answer.as_predicate_bit(), Some(expected), "{code}: {answer}");
    }
}

#[test]
fn package_field_returns_data_and_missing_field_is_d3_empty() {
    let mut s = session();
    let found = eval(&mut s,
        "(отримати-поле-пакета-знань (як-є author) (як-є ((author a) (version b))))");
    assert_eq!(found.to_string(), "(a)");
    let missing = eval(&mut s,
        "(отримати-поле-пакета-знань (як-є missing) (як-є ((author a) (version b))))");
    assert!(matches!(missing, Value::Nil));
    assert_eq!(missing.as_predicate_bit(), None);
}

#[test]
fn ukrainian_clause_validation_is_exact_d1() {
    let mut s = session();
    for (code, expected) in [
        ("(клаузи-бази-знань-коректні? (як-є ()))", true),
        ("(клаузи-бази-знань-коректні? (як-є malformed))", false),
        ("(клаузи-бази-знань-коректні? (як-є ((p x))))", true),
    ] {
        let answer = eval(&mut s, code);
        assert_eq!(answer.as_predicate_bit(), Some(expected), "{code}: {answer}");
    }
}

#[test]
fn predicate_false_is_not_d3_empty() {
    let mut s = session();
    let no = eval(&mut s, "(голова-твердження-знань-заперечена? (як-є plain))");
    let empty = eval(&mut s,
        "(отримати-поле-пакета-знань (як-є missing) (як-є ()))");
    assert_eq!(no.as_predicate_bit(), Some(false));
    assert_eq!(empty.as_predicate_bit(), None);
}
