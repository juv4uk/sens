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
            "(canon-law-result empty-list satisfied)",
        ),
        (
            "(канон-закон-атом-пара (quote left) (quote right))",
            "(canon-law-result atom-cons satisfied)",
        ),
        (
            "(канон-закон-перше-пара (quote left) (quote right))",
            "(canon-law-result car-cons satisfied)",
        ),
        (
            "(канон-закон-решта-пара (quote left) (quote right))",
            "(canon-law-result cdr-cons satisfied)",
        ),
        (
            "(канон-закон-рівність-рефлексивний-атом (quote left))",
            "(canon-law-result eq-reflexive-atom satisfied)",
        ),
        (
            "(канон-закон-решта-крапковий)",
            "(canon-law-result cdr-dotted satisfied)",
        ),
        (
            "(канон-закон-решта-правильний)",
            "(canon-law-result cdr-proper satisfied)",
        ),
        (
            "(канон-закон-решта-неправильний)",
            "(canon-law-result cdr-improper satisfied)",
        ),
        (
            "(канон-закон-цитування-пригнічує-обчислення)",
            "(canon-law-result quote-suppresses-evaluation satisfied)",
        ),
        (
            "(канон-закон-умова-перший-збіг-короткий-ланцюг)",
            "(canon-law-result cond-first-match-short-circuit satisfied)",
        ),
        (
            "(канон-закон-символьний-поверхня)",
            "(canon-law-result symbolic-surface satisfied)",
        ),
        ("(канон-відповідає?)", "(canon-conformance satisfied)"),
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
            "(canon-law-result eq-reflexive-atom violated)",
        ),
        (
            "(канон-відповідність-з (quote ()))",
            "(canon-conformance satisfied)",
        ),
        (
            "(канон-відповідність-з (quote ((canon-law-result example violated))))",
            "(canon-conformance violated)",
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
