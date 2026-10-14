//! Живий oracle: реальний Lisp-owned occurs-check, без симуляції helper.
//! D6 LET вилучений, body перенесений до точної D4 LAMBDA.
use sens::{
    eval_parsed_expressions, eval_pinned_legacy_core_source,
    parse_mixed_exact_domain, parse_mixed_exact_domain_reasoning_source, Session,
};

fn session() -> Session {
    let mut session = Session::default();
    eval_pinned_legacy_core_source(
        "lib/core.lisp",
        include_str!("../../../lib/core.lisp"),
        &mut session,
    )
    .expect("legacy bootstrap must load by pinned path");
    let expressions = parse_mixed_exact_domain_reasoning_source(
        "lib/unify.lisp",
        include_str!("../../../lib/unify.lisp"),
    )
    .expect("real exact D3/D4 unify source must parse");
    eval_parsed_expressions(&expressions, &mut session)
        .expect("real Lisp unifier must load");
    session
}

fn observed(session: &mut Session, source: &str) -> String {
    let expressions = parse_mixed_exact_domain(source).expect("query exact-domain parse");
    eval_parsed_expressions(&expressions, session)
        .unwrap_or_else(|error| panic!("occurs-check failed for {source}: {error:?}"))
        .value.to_string()
}

#[test]
fn occurs_check_rejects_self_reference_and_accepts_acyclic_term() {
    let mut session = session();
    for (source, expected) in [
        ("(occurs-check? (001 (var x)) (001 (var x)) (001 ()))", "1"),
        ("(occurs-check? (001 (var x)) (001 (f (var x))) (001 ()))", "1"),
        ("(occurs-check? (001 (var x)) (001 (f y)) (001 ()))", "0"),
        ("(occurs-check? (001 (var x)) (001 y) (001 ()))", "0"),
    ] {
        assert_eq!(observed(&mut session, source), expected, "{source}");
    }
}

#[test]
fn one_walk_helper_preserves_frozen_inner_cond_body() {
    let mut session = session();
    for (source, expected) in [
        ("(уніфікація-входження-розв'язано? (001 (var x)) (001 (var x)) (001 ()))", "1"),
        ("(уніфікація-входження-розв'язано? (001 (var x)) (001 y) (001 ()))", "0"),
    ] {
        assert_eq!(observed(&mut session, source), expected, "{source}");
    }
}

#[test]
fn native_unify_d1_self_verdict_and_one_bit_mutant() {
    // CI/host транспортує джерела, не визначає істину для окремих випадків.
    // Позитивні/негативні закони задані тільки у двох SENS-програмах.
    const LAW: &str = include_str!("../../../tests/fixtures/unify-exact-d1-law.lisp");
    const MUTANT: &str = include_str!("../../../tests/fixtures/unify-exact-d1-mutant.lisp");

    // Суто механічна перевірка: рівна довжина та один інвертований біт ASCII.
    assert_eq!(LAW.len(), MUTANT.len(), "mutation changed source width");
    let byte_diffs: Vec<u8> = LAW.bytes().zip(MUTANT.bytes())
        .map(|(left, right)| left ^ right)
        .filter(|delta| *delta != 0)
        .collect();
    assert_eq!(byte_diffs, vec![1], "negative SENS witness must flip one bit");

    let mut positive = session();
    let source = parse_mixed_exact_domain(LAW)
        .expect("exact D3/D4 SENS positive fixture must parse");
    let verdict = eval_parsed_expressions(&source, &mut positive)
        .expect("native SENS must execute the positive unification law");
    assert_eq!(
        verdict.value.to_string(), "1",
        "test_id=UNIFY-D1-LAW layer=eval fixture=tests/fixtures/unify-exact-d1-law.lisp command=cargo test --locked -p sens --test unify_occurs_exact_d3 native_unify_d1_self_verdict_and_one_bit_mutant -- --nocapture"
    );

    let mut negative = session();
    let source = parse_mixed_exact_domain(MUTANT)
        .expect("exact D3/D4 SENS negative fixture must parse");
    match eval_parsed_expressions(&source, &mut negative) {
        Ok(result) => panic!(
            "test_id=UNIFY-D1-MUTANT layer=eval fixture=tests/fixtures/unify-exact-d1-mutant.lisp expected=SENS-REJECT actual={} first_bad_sha=UNRESOLVED command=cargo test --locked -p sens --test unify_occurs_exact_d3 native_unify_d1_self_verdict_and_one_bit_mutant -- --nocapture",
            result.value
        ),
        Err(error) => println!(
            "test_id=UNIFY-D1-MUTANT layer=eval status=SENS-REJECTED error={error:?}"
        ),
    }
}
