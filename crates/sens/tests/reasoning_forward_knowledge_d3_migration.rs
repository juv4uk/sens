//! D3/D9 migration witness for the Lisp-owned forward and knowledge engines.
//!
//! Frozen W8 files remain provenance only. They used the old NIL-as-false
//! conditional convention, so executing them with the ratified exact-D1 COND
//! would test a retired law rather than current behavior.
use sens::{eval_parsed_expressions, eval_program, parse_mixed_exact_domain_reasoning_source, Expr, ExprKind, Session};

const CORE: &str = include_str!("../../../lib/core.lisp");
const UNIFY: &str = include_str!("../../../lib/unify.lisp");
const REASON: &str = include_str!("../../../lib/reason.lisp");
const FORWARD_OLD: &str = include_str!("../../../tests/fixtures/forward-d3-before.lisp");
const FORWARD_D3: &str = include_str!("../../../lib/forward.lisp");
const KNOWLEDGE_OLD: &str = include_str!("../../../tests/fixtures/knowledge-d3-before.lisp");
const KNOWLEDGE_D3: &str = include_str!("../../../lib/knowledge.lisp");

fn session() -> Session {
    let mut session = Session::default();
    sens::eval_pinned_legacy_core_source("lib/core.lisp", CORE, &mut session)
        .expect("source-pinned exact-width legacy core bootstrap");
    for (path, source) in [
        ("lib/unify.lisp", UNIFY),
        ("lib/reason.lisp", REASON),
        ("lib/forward.lisp", FORWARD_D3),
        ("lib/knowledge.lisp", KNOWLEDGE_D3),
    ] {
        let parsed = parse_mixed_exact_domain_reasoning_source(path, source)
            .expect("authorized reasoning source must parse");
        eval_parsed_expressions(&parsed, &mut session)
            .unwrap_or_else(|error| panic!("current reasoning source {path} must load: {error:?}"));
    }
    session
}

fn observed(program: &str) -> String {
    eval_program(program, &mut session())
        .unwrap_or_else(|error| panic!("reasoning witness {program} failed: {error:?}"))
        .value
        .to_string()
}

#[test]
fn candidate_forward_and_knowledge_have_only_exact_d3_executable_heads() {
    for (original, projection) in [
        (FORWARD_OLD, FORWARD_D3),
        (KNOWLEDGE_OLD, KNOWLEDGE_D3),
    ] {
        assert!(original.contains("(00000111"));
        assert!(!projection.contains("(00000111"));
        assert!(projection.contains("(110"));
        assert!(projection.contains("(010"));
        assert!(projection.contains("(101"));
    }
}

#[test]
fn reasoning_d3_d9_projections_replay_frozen_bounded_behavior() {
    for (program, expected) in [
        ("(module-journal-events (quote example) (quote ()))", "()"),
        ("(module-journal-events (quote example) (quote ((tell example (fact a)))))", "((tell example (fact a)))"),
        ("(fire-rule (quote ((fact a) (derived a))) (quote (fact a)))", "(derived a)"),
        ("(fire-rule (quote ((fact a) (derived a))) (quote (fact b)))", "no-match"),
        ("(fire-rule-on-facts (quote ((fact a) (derived a))) (quote ()))", "()"),
    ] {
        assert_eq!(observed(program), expected, "current reasoning behavior changed: {program}");
    }
}


#[test]
fn knowledge_var_and_negation_require_exactly_one_argument() {
    for (program, expected) in [
        ("(knowledge-term-valid? (quote (var x)))", "1"),
        ("(knowledge-term-valid? (quote (var)))", "0"),
        ("(knowledge-term-valid? (quote (var x extra)))", "0"),
        ("(knowledge-goal-valid? (quote (not? (mortal socrates))))", "1"),
        ("(knowledge-goal-valid? (quote (not?)))", "0"),
        ("(knowledge-goal-valid? (quote (not? (mortal socrates) extra)))", "0"),
        ("(knowledge-goal-valid? (quote (not (mortal socrates))))", "1"),
    ] {
        assert_eq!(
            observed(program),
            expected,
            "Перевірка знань має вимагати точно один аргумент: {program}"
        );
    }
}

fn collect_call_head_coordinates(expr: &Expr, coordinates: &mut Vec<(usize, u16)>) {
    let ExprKind::List(items) = &expr.kind else {
        return;
    };
    if let Some(Expr { kind: ExprKind::DomainIdentity(identity), .. }) = items.first() {
        coordinates.push((identity.width(), identity.packed_bits()));
    }
    for item in items.iter() {
        collect_call_head_coordinates(item, coordinates);
    }
}

fn named_definition<'a>(forms: &'a [Expr], name: &str) -> &'a Expr {
    forms.iter().find(|expression| {
        let ExprKind::List(items) = &expression.kind else {
            return false;
        };
        matches!(
            items.get(1).map(|item| &item.kind),
            Some(ExprKind::Symbol(symbol)) if symbol.as_ref() == name
        )
    }).unwrap_or_else(|| panic!("немає визначення Lisp: {name}"))
}

#[test]
fn knowledge_unary_validators_use_only_exact_d3_d4_structure() {
    assert!(!KNOWLEDGE_D3.contains("(000000 term)"));
    assert!(!KNOWLEDGE_D3.contains("(000000 goal)"));
    assert!(!KNOWLEDGE_D3.contains("(unify-equal? (000000"));
    for name in ["knowledge-term-valid?", "knowledge-goal-valid?"] {
        let forms = parse_mixed_exact_domain_reasoning_source("lib/knowledge.lisp", KNOWLEDGE_D3)
            .expect("джерело знань має зберігати точні домени голів викликів");
        let mut coordinates = Vec::new();
        collect_call_head_coordinates(named_definition(&forms, name), &mut coordinates);
        coordinates.sort_unstable();
        coordinates.dedup();
        let widths = coordinates
            .iter()
            .map(|(width, _)| *width)
            .collect::<std::collections::BTreeSet<_>>();
        assert_eq!(
            widths,
            [3usize, 4usize].into_iter().collect(),
            "{name} не має використовувати D6 LENGTH, W8 EQUAL або некваліфікований ширший засіб"
        );
        for required in [(3, 0b010), (3, 0b011), (3, 0b110), (4, 0b1001)] {
            assert!(
                coordinates.contains(&required),
                "{name} бракує D{}:{:0width$b}",
                required.0,
                required.1,
                width = required.0
            );
        }
    }
}
