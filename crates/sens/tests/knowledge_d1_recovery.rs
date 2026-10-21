//! Реальний SENS-виконавець: українські предикати знань із точним D1.
//! Історичний SID8, #d1-текст і старий зріз 6 форм не є доказом.
use sens::{eval_parsed_expressions, eval_program, parse_mixed_exact_domain_reasoning_source,
           Session, Value};

fn session() -> Session {
    let mut s = Session::default();
    sens::load_core_library(&mut s).expect("повний канонічний Core SENS");
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
    for (head, expected) in [
        ("not", true), ("not?", true), ("plain", false),
        // Складена форма — не атомний протокольний маркер not/not?.
        ("(not? (radio))", false),
        ("((not?) radio)", false),
        ("()", false),
    ] {
        let code = format!("(голова-твердження-знань-заперечена? (як-є {head}))");
        let answer = eval(&mut s, &code);
        assert_eq!(answer.as_predicate_bit(), Some(expected), "{code}: {answer}");
    }
}

#[test]
fn knowledge_opposite_head_guards_malformed_negation() {
    // Справжній SENS-eval: CAR/CADR дозволені лише на правильній парі.
    let mut s = session();
    for (head, expected) in [
        ("(not radio)", "radio"),
        ("(not? (signal antenna))", "(signal antenna)"),
        ("(signal antenna)", "(not? (signal antenna))"),
        ("radio", "(not? radio)"),
        ("(not)", "(not? (not))"),
        ("(not radio antenna)", "(not? (not radio antenna))"),
        ("((not?) radio)", "(not? ((not?) radio))"),
        ("((nested) signal)", "(not? ((nested) signal))"),
    ] {
        let query = format!(
            "(отримати-протилежну-голову-твердження-знання (як-є {head}))"
        );
        let actual = eval(&mut s, &query);
        assert_eq!(actual.to_string(), expected, "{query}");
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
fn malformed_package_rows_are_skipped_before_d4_caar() {
    // Справжнє SENS-виконання: атом та складний ключ не є D4 CAAR.
    let mut s = session();
    for rows in [
        "(як-є (пошкоджений (author a)))",
        "(як-є (() (author a)))",
        "(як-є (((nested k) wrong) (author a)))",
    ] {
        let query = format!(
            "(отримати-поле-пакета-знань (як-є author) {rows})"
        );
        let value = eval(&mut s, &query);
        assert_eq!(value.to_string(), "(a)", "{query}: {value}");
    }
    let missing = eval(&mut s,
        "(отримати-поле-пакета-знань (як-є missing) (як-є (пошкоджений ((nested k) wrong))))"
    );
    assert!(matches!(missing, Value::Nil));
}

#[test]
fn opposite_knowledge_head_checks_atom_and_malformed_tail() {
    // Справжнє виконання SENS: D3 CAR/CDR не можна викликати на атомі.
    // Для кожного випадку очікуване значення також обчислює SENS.
    let mut s = session();
    for (source, oracle) in [
        (
            "(отримати-протилежну-голову-твердження-знання (як-є сонце))",
            "(список (як-є not?) (як-є сонце))",
        ),
        (
            "(отримати-протилежну-голову-твердження-знання (як-є (not сонце)))",
            "(як-є сонце)",
        ),
        (
            "(отримати-протилежну-голову-твердження-знання (як-є (not? сонце)))",
            "(як-є сонце)",
        ),
        (
            "(отримати-протилежну-голову-твердження-знання (як-є (not)))",
            "(список (як-є not?) (як-є (not)))",
        ),
        (
            "(отримати-протилежну-голову-твердження-знання (як-є (not сонце зайве)))",
            "(список (як-є not?) (як-є (not сонце зайве)))",
        ),
        (
            "(отримати-протилежну-голову-твердження-знання (як-є ((not?) сонце)))",
            "(список (як-є not?) (як-є ((not?) сонце)))",
        ),
    ] {
        let actual = eval(&mut s, source);
        let expected = eval(&mut s, oracle);
        assert_eq!(actual.to_string(), expected.to_string(), "{source}");
    }
}

#[test]
fn ukrainian_clause_validation_is_exact_d1() {
    let mut s = session();
    for (code, expected) in [
        ("(клаузи-бази-знань-коректні? (як-є ()))", true),
        ("(клаузи-бази-знань-коректні? (як-є malformed))", false),
        // Клауза є списком цілей, а база — списком клауз:
        // ((p x)) — одна клауза з ціллю (p x).
        ("(клаузи-бази-знань-коректні? (як-є (((p x)))))", true),
        ("(клаузи-бази-знань-коректні? (як-є ((p x))))", false),
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
