//! Справжні перевірки зв'язування Core через повну українську проєкцію.
//! Немає path-specific reader, історичних байтів чи вбудованих двійкових голів.
use sens::{eval_parsed_expressions, parse_mixed_exact_domain, Session};

const SOURCE: &str = include_str!("../../../lib/core.lisp");

fn eval_ukr(source: &str, session: &mut Session) -> Result<sens::Value, sens::LanguageError> {
    let forms = parse_mixed_exact_domain(source)?;
    Ok(eval_parsed_expressions(&forms, session)?.value)
}

fn load_core(session: &mut Session) {
    let forms =
        parse_mixed_exact_domain(SOURCE).expect("актуальний Core читається загальним SENS reader");
    eval_parsed_expressions(&forms, session)
        .expect("актуальний Core виконується без адаптера SID8/Sens8");
}

#[test]
fn current_core_uses_the_generic_exact_domain_reader() {
    let mut session = Session::default();
    load_core(&mut session);
    assert_eq!(
        eval_ukr("(додати 2 3)", &mut session).unwrap().to_string(),
        "5"
    );
}

#[test]
fn derived_let_macro_preserves_parallel_bindings_and_lexical_scope() {
    let mut session = Session::default();
    load_core(&mut session);
    for (source, expected) in [
        ("(нехай-похідне () 42)", "42"),
        ("(нехай-похідне ((x 7)) x)", "7"),
        (
            "(нехай-похідне ((x 7) (y 9)) (сполучити x (сполучити y (як-є ())))))",
            "(7 9)",
        ),
        ("((функція (x) ((функція (y) (додати x y)) 9)) 7)", "16"),
    ] {
        let actual = eval_ukr(source, &mut session)
            .unwrap_or_else(|error| panic!("українське зв'язування {source}: {error:?}"))
            .to_string();
        assert_eq!(
            actual, expected,
            "лексична область / макророзгортання: {source}"
        );
    }
}

#[test]
fn derived_length_handles_empty_and_nonempty_lists() {
    let mut session = Session::default();
    load_core(&mut session);
    for (source, expected) in [
        ("(довжина (як-є ()))", "0"),
        ("(довжина (як-є (a)))", "1"),
        ("(довжина (як-є (a b)))", "2"),
    ] {
        let actual = eval_ukr(source, &mut session)
            .unwrap_or_else(|error| panic!("довжина списку {source}: {error:?}"))
            .to_string();
        assert_eq!(actual, expected);
    }
}

#[test]
fn d6_map_resident_does_not_gain_callability_without_a_language_mechanism() {
    let mut session = Session::default();
    load_core(&mut session);
    let error = eval_ukr(
        "(відобразити (функція (x) x) (сполучити 1 (як-є ())))",
        &mut session,
    )
    .expect_err("D6 identity residency alone must not invent an evaluator mechanism");
    assert!(
        error.message.contains("domain identity is not callable"),
        "expected an explicit exact-domain callability error: {error:?}"
    );
}
