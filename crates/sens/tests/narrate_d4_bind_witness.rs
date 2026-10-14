//! Only transport and execution: the two narration cases and their expected
//! list structures belong to SENS-authored fixture programs, never to Rust.
//! A one-bit mutation changes the final language-owned D1 verdict.

use sens::{
    eval_parsed_expressions, load_core_library, parse_exact_domain_source,
    parse_mixed_exact_domain, parse_mixed_exact_domain_reasoning_source, Session,
};

const LAW: &str = include_str!("../../../tests/fixtures/narrate-d4-bind-law.lisp");
const MUTANT: &str = include_str!("../../../tests/fixtures/narrate-d4-bind-mutant.lisp");

fn make_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("narrate-d4-bind: bootstrap");
    for (path, source) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
    ] {
        let exprs = parse_mixed_exact_domain_reasoning_source(path, source)
            .unwrap_or_else(|error| panic!("narrate-d4-bind: {path} reader: {error}"));
        eval_parsed_expressions(&exprs, &mut session)
            .unwrap_or_else(|error| panic!("narrate-d4-bind: {path} evaluator: {error}"));
    }
    // Existing result-status uses explicit #d1 projections, which are
    // compatibility *text* syntax. A path-pinned reasoning reader respects
    // those without reinterpreting the exact binary source of narrate.lisp.
    let source = include_str!("../../../lib/result-status.lisp");
    let exprs = parse_mixed_exact_domain_reasoning_source("lib/result-status.lisp", source)
        .expect("narrate-d4-bind: pinned result-status reader");
    eval_parsed_expressions(&exprs, &mut session)
        .expect("narrate-d4-bind: result-status evaluator");

    let source = include_str!("../../../lib/narrate.lisp");
    let exprs = parse_exact_domain_source(source)
        .expect("narrate-d4-bind: exact binary narrator reader");
    eval_parsed_expressions(&exprs, &mut session)
        .expect("narrate-d4-bind: narrator evaluator");
    session
}

fn observe(program: &str) -> Option<bool> {
    let mut session = make_session();
    let exprs = parse_mixed_exact_domain(program)
        .expect("narrate-d4-bind: executable SENS fixture reader");
    eval_parsed_expressions(&exprs, &mut session)
        .expect("narrate-d4-bind: SENS self-verdict execution")
        .value
        .as_predicate_bit()
}

#[test]
fn narrate_answer_d4_single_binding_sens_law_and_one_bit_mutant() {
    assert_eq!(LAW.len(), MUTANT.len(), "one-bit mutation changed file width");
    let changes: Vec<_> = LAW.bytes().zip(MUTANT.bytes())
        .filter(|(old, new)| old != new)
        .collect();
    assert_eq!(changes.as_slice(), &[(b'1', b'0')],
        "exactly one D1 source bit must change from YES to NO");

    // Rust only observes the final one-bit verdict produced by SENS.
    // All expected phrases and comparisons are inside the SENS fixtures.
    assert_eq!(observe(LAW), Some(true),
        "test_id=narrate-d4-bind-law layer=transport fixture=tests/fixtures/narrate-d4-bind-law.lisp reproduce=cargo test --locked -p sens --test narrate_d4_bind_witness -- --nocapture");
    assert_eq!(observe(MUTANT), Some(false),
        "test_id=narrate-d4-bind-mutant layer=transport fixture=tests/fixtures/narrate-d4-bind-mutant.lisp reproduce=cargo test --locked -p sens --test narrate_d4_bind_witness -- --nocapture");
}
