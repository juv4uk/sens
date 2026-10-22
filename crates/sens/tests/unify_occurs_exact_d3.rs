//! Живий oracle: реальний Lisp-owned occurs-check, без симуляції helper.
//! D6 LET вилучений, body перенесений до точної D4 LAMBDA.
use sens::{
    eval_core_library_source, eval_parsed_expressions, parse_mixed_exact_domain,
    parse_mixed_exact_domain_reasoning_source, Session,
};

fn session() -> Session {
    let mut session = Session::default();
    eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("legacy bootstrap must load by pinned path");
    let expressions = parse_mixed_exact_domain_reasoning_source(
        "lib/unify.lisp",
        include_str!("../../../lib/unify.lisp"),
    )
    .expect("real exact D3/D4 unify source must parse");
    eval_parsed_expressions(&expressions, &mut session).expect("real Lisp unifier must load");
    session
}

fn observed(session: &mut Session, source: &str) -> String {
    let expressions = parse_mixed_exact_domain(source).expect("query exact-domain parse");
    eval_parsed_expressions(&expressions, session)
        .unwrap_or_else(|error| panic!("occurs-check failed for {source}: {error:?}"))
        .value
        .to_string()
}

#[test]
fn occurs_check_rejects_self_reference_and_accepts_acyclic_term() {
    let mut session = session();
    for (source, expected) in [
        (
            "(входить-перевірити? (як-є (var x)) (як-є (var x)) (як-є ()))",
            "1",
        ),
        (
            "(входить-перевірити? (як-є (var x)) (як-є (f (var x))) (як-є ()))",
            "1",
        ),
        (
            "(входить-перевірити? (як-є (var x)) (як-є (f y)) (як-є ()))",
            "0",
        ),
        (
            "(входить-перевірити? (як-є (var x)) (як-є y) (як-є ()))",
            "0",
        ),
    ] {
        assert_eq!(observed(&mut session, source), expected, "{source}");
    }
}

#[test]
fn occurs_check_follows_one_existing_substitution_before_testing_reference() {
    let mut session = session();
    for (source, expected) in [
        (
            "(входить-перевірити? (як-є (var x)) (як-є (var y)) (як-є (((var y) (var x)))) )",
            "1",
        ),
        (
            "(входить-перевірити? (як-є (var x)) (як-є (var y)) (як-є (((var y) (var z)))) )",
            "0",
        ),
    ] {
        assert_eq!(observed(&mut session, source), expected, "{source}");
    }
}

#[test]
fn variable_is_exact_proper_two_cell_d3_list() {
    // SENS, не Python: неправильний крапковий хвіст і зайве поле
    // не стають успішною змінною для уніфікації.
    let mut s = session();
    for (literal, expected) in [
        ("(var x)", "1"),
        ("(var)", "0"),
        ("(var . x)", "0"),
        ("(var x . y)", "0"),
        ("(var x y)", "0"),
        ("((var x) y)", "0"),
        ("var", "0"),
        ("(f x)", "0"),
    ] {
        let query = format!("(змінна? (як-є {literal}))");
        assert_eq!(observed(&mut s, &query), expected, "{query}");
    }
}

#[test]
fn unifier_d1_fallback_is_evaluated_by_sens() {
    // Реальне SENS обчислення, не Python/JSON і не статична перевірка тексту.
    // Обидва результати D1 повинні походити з викликаних предикатів.
    let mut s = session();
    for (source, expected) in [
        ("(уніфікація-рівні? (як-є (a b)) (як-є (a c)))", "0"),
        ("(уніфікація-рівні? (як-є (a b)) (як-є (a b)))", "1"),
        ("(підстановка-позначає-невдачу? (як-є ()))", "0"),
        ("(підстановка-позначає-невдачу? (як-є fail))", "1"),
    ] {
        assert_eq!(observed(&mut s, source), expected, "{source}");
    }
}
