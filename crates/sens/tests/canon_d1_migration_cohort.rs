//! Регресійна когорта #5029: виконуємо Canon напряму, без історичного
//! witness-runner (він мігрується окремо в #5025).
use sens::{
    eval_parsed_expressions, eval_program, load_core_library, parse_mixed_exact_domain, Session,
};

fn canon_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("current Core library");
    // Existing mixed-domain reader preserves compatibility D1 projections
    // while lifting canonical D3/D4 call heads into exact domain identities.
    let forms = parse_mixed_exact_domain(include_str!("../../../lib/canon.lisp"))
        .expect("Canon current D3/D4 source must parse");
    eval_parsed_expressions(&forms, &mut session).expect("Canon source must load");
    session
}

#[test]
fn canon_constitutive_laws_use_current_predicate_results() {
    let mut session = canon_session();
    let cases: [(&str, &str); 13] = [
        ("канон-порожній-список", "()"),
        (
            "(канон-закон-порожній-список)",
            "(канон-закон-результат порожній-список виконано)",
        ),
        (
            "(канон-закон-атом-пара (quote left) (quote right))",
            "(канон-закон-результат атом-пара виконано)",
        ),
        (
            "(канон-закон-перше-пара (quote left) (quote right))",
            "(канон-закон-результат перше-пара виконано)",
        ),
        (
            "(канон-закон-решта-пара (quote left) (quote right))",
            "(канон-закон-результат решта-пара виконано)",
        ),
        (
            "(канон-закон-рівність-рефлексивний-атом (quote left))",
            "(канон-закон-результат тотожність-рефлексивний-атом виконано)",
        ),
        (
            "(канон-закон-решта-крапковий)",
            "(канон-закон-результат решта-крапковий виконано)",
        ),
        (
            "(канон-закон-решта-правильний)",
            "(канон-закон-результат решта-правильний виконано)",
        ),
        (
            "(канон-закон-решта-неправильний)",
            "(канон-закон-результат решта-неправильний виконано)",
        ),
        (
            "(канон-закон-цитування-пригнічує-обчислення)",
            "(канон-закон-результат цитування-пригнічує-обчислення виконано)",
        ),
        (
            "(канон-закон-умова-перший-збіг-короткий-ланцюг)",
            "(канон-закон-результат умова-перший-збіг-короткий-ланцюг виконано)",
        ),
        (
            "(канон-закон-символьний-поверхня)",
            "(канон-закон-результат символьна-поверхня виконано)",
        ),
        ("(канон-відповідає?)", "(канон-відповідність виконано)"),
    ];
    for (expr, expected) in cases {
        let actual = eval_program(expr, &mut session)
            .unwrap_or_else(|error| panic!("Canon evaluation failed: {expr}: {error}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "Canon law {expr}");
    }
}

#[test]
fn canon_negative_predicate_polarity_and_exhaustion_are_not_truthiness() {
    let mut session = canon_session();
    // Пара не є атомом: YES і NO тут не взаємозамінні.
    let cases: [(&str, &str); 3] = [
        (
            "(канон-закон-рівність-рефлексивний-атом (quote (left right)))",
            "(канон-закон-результат тотожність-рефлексивний-атом порушено)",
        ),
        (
            "(канон-відповідність-з (quote ()))",
            "(канон-відповідність виконано)",
        ),
        (
            "(канон-відповідність-з (quote ((канон-закон-результат приклад порушено))))",
            "(канон-відповідність порушено)",
        ),
    ];
    for (expr, expected) in cases {
        let actual = eval_program(expr, &mut session)
            .unwrap_or_else(|error| panic!("Canon negative law failed: {expr}: {error}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "Canon branch polarity {expr}");
    }
}
