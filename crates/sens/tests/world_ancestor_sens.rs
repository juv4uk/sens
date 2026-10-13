//! Native SENS owns the law; Rust is only the source reader, executor, and
//! D1-bit receipt for the exact-width world-ancestry self-verdict.

use sens::{
    eval_parsed_expressions, eval_pinned_legacy_core_source,
    eval_pinned_reasoning_source, parse_mixed_exact_domain, Session,
};

const WORLD_WITNESSES: &str =
    include_str!("../../../tests/semantic/world-exact-arity-witness.lisp");
const ANCESTOR_LAW: &str =
    include_str!("../../../tests/semantic/world-ancestor-d1-law.lisp");
const ANCESTOR_MUTANT: &str =
    include_str!("../../../tests/semantic/world-ancestor-d1-mutant.lisp");

fn world_session() -> Session {
    let mut session = Session::default();
    eval_pinned_legacy_core_source(
        "lib/core.lisp",
        include_str!("../../../lib/core.lisp"),
        &mut session,
    )
    .expect("pinned Core must load before the actual SENS World");
    for (path, source) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
        ("lib/forward.lisp", include_str!("../../../lib/forward.lisp")),
        ("lib/knowledge.lisp", include_str!("../../../lib/knowledge.lisp")),
        ("lib/world.lisp", include_str!("../../../lib/world.lisp")),
    ] {
        eval_pinned_reasoning_source(path, source, &mut session)
            .unwrap_or_else(|error| panic!("SENS library {path}: {error}"));
    }
    session
}

fn native_sens_verdicts(source: &str, fixture: &str, expected: bool) -> usize {
    let parsed = parse_mixed_exact_domain(source)
        .unwrap_or_else(|error| panic!("test_id=world-ancestor layer=parse fixture={fixture} error={error}"));
    assert!(!parsed.is_empty(), "test_id=world-ancestor fixture={fixture} is empty");
    let mut session = world_session();
    for (i, expression) in parsed.iter().enumerate() {
        let result = eval_parsed_expressions(std::slice::from_ref(expression), &mut session)
            .unwrap_or_else(|error| {
                panic!("test_id=world-ancestor layer=eval fixture={fixture} form={i} error={error}")
            });
        let actual = result.value.as_predicate_bit();
        assert_eq!(
            actual,
            Some(expected),
            "test_id=world-ancestor layer=eval fixture={fixture} form={i} expected=D1:{} actual={:?} reproduce='cargo test --locked -p sens --test world_ancestor_sens -- --nocapture'",
            if expected { "1" } else { "0" },
            result.value,
        );
    }
    parsed.len()
}

#[test]
fn world_ancestor_is_proved_by_native_sens() {
    let witnessed = native_sens_verdicts(
        WORLD_WITNESSES,
        "tests/semantic/world-exact-arity-witness.lisp",
        true,
    );
    assert!(witnessed >= 20, "world ancestry self-verdicts must not disappear");
}

#[test]
fn world_ancestor_one_bit_mutant_fails_in_sens() {
    assert_eq!(ANCESTOR_LAW.len(), ANCESTOR_MUTANT.len(), "only the D1 word may change");
    let changes = ANCESTOR_LAW.bytes().zip(ANCESTOR_MUTANT.bytes())
        .filter(|(a, b)| a != b)
        .collect::<Vec<_>>();
    assert_eq!(changes.as_slice(), &[(b'1', b'0')], "one-bit D1 mutation only");
    assert_eq!(native_sens_verdicts(ANCESTOR_LAW, "tests/semantic/world-ancestor-d1-law.lisp", true), 1);
    assert_eq!(native_sens_verdicts(ANCESTOR_MUTANT, "tests/semantic/world-ancestor-d1-mutant.lisp", false), 1);
}
