//! Лише transport свідка. Семантика та очікування — у двійковому SENS.
//! Жодна Rust-умова не визначає значення Guard-статусів або структурної рівності.

use sens::{eval_parsed_expressions, eval_pinned_legacy_core_source, parse_mixed_exact_domain, Session};

fn load_sens(session: &mut Session, path: &str, source: &str) {
    let forms = parse_mixed_exact_domain(source)
        .unwrap_or_else(|error| panic!("SENS source parse {path}: {error:?}"));
    eval_parsed_expressions(&forms, session)
        .unwrap_or_else(|error| panic!("SENS source execution {path}: {error:?}"));
}

#[test]
fn guard_semantics_are_owned_by_binary_sens() {
    let mut session = Session::default();

    // Bootstrap є тільки механізмом; жодних host-authored expected-cases.
    eval_pinned_legacy_core_source(
        "lib/core.lisp",
        include_str!("../../../lib/core.lisp"),
        &mut session,
    )
        .expect("SENS core bootstrap transport");

    load_sens(&mut session, "lib/guard.lisp", include_str!("../../../lib/guard.lisp"));
    load_sens(
        &mut session,
        "knowledge/guard-reference.lisp",
        include_str!("../../../knowledge/guard-reference.lisp"),
    );

    let source = include_str!("../../../tests/fixtures/guard-exact-d3-semantic.lisp");
    let forms = parse_mixed_exact_domain(source).expect("SENS semantic witness parse");
    let result = eval_parsed_expressions(&forms, &mut session)
        .expect("SENS semantic witness execution");

    // Спостерігати рівно один D1-біт; усі закони доводить сам SENS.
    assert_eq!(
        result.value.as_predicate_bit(),
        Some(true),
        "двійковий SENS відхилив один або більше власних свідків"
    );
}
