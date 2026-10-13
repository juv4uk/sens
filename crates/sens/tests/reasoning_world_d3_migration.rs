//! D3 migration witness for the Lisp-owned immutable world layer.
//!
//! The frozen W8 source is retained as provenance, but it cannot be executed
//! as a semantic oracle after COND was ratified to accept exact D1 only:
//! historical NIL-as-false is intentionally no longer a current language law.
use sens::{eval_parsed_expressions, eval_program, parse_mixed_exact_domain_reasoning_source, Expr, ExprKind, Session};

const CORE: &str = include_str!("../../../lib/core.lisp");
const OLD: &str = include_str!("../../../tests/fixtures/world-d3-before.lisp");
const D3: &str = include_str!("../../../lib/world.lisp");

fn world_session() -> Session {
    let mut session = Session::default();
    sens::eval_pinned_legacy_core_source("lib/core.lisp", CORE, &mut session)
        .expect("source-pinned core required for world library");
    let parsed = parse_mixed_exact_domain_reasoning_source("lib/world.lisp", D3)
        .expect("only explicitly pinned current-world projection may be typed");
    eval_parsed_expressions(&parsed, &mut session)
        .expect("current world library should load with exact domain identities");
    session
}

fn observe(program: &str) -> String {
    let mut session = world_session();
    eval_program(program, &mut session)
        .unwrap_or_else(|error| panic!("current D3 world failed for {program}: {error:?}"))
        .value
        .to_string()
}

#[test]
fn world_d3_candidate_does_not_rewrite_w8_quote_data() {
    assert!(OLD.contains("(00000111"));
    assert!(!D3.contains("(00000111"));
    assert!(D3.contains("(110"));
    assert!(D3.contains("(101"));
    assert!(D3.contains("(010"));
    assert_eq!(
        parse_mixed_exact_domain_reasoning_source("lib/not-world.lisp", D3)
            .expect_err("unapproved path must fail closed").kind,
        sens::ErrorKind::Parse
    );
}

#[test]
fn world_d3_current_semantics_replay_the_frozen_behavioral_witnesses() {
    for (program, expected) in [
        ("(empty-world)", "(world () () ())"),
        ("(world? (empty-world))", "1"),
        ("(world-parent (empty-world))", "()"),
        ("(world-journal (empty-world))", "()"),
        ("(world-metadata (empty-world))", "()"),
        ("(world-module-missing? (empty-world) (quote unknown))", "1"),
        ("(world-remove-first (quote x) (quote (a x b)))", "(a b)"),
    ] {
        assert_eq!(observe(program), expected, "current D3 world changed: {program}");
    }
}


#[test]
fn world_recognizer_requires_exact_four_element_proper_list() {
    for (program, expected) in [
        ("(world? (empty-world))", "1"),
        ("(world? (quote (world () () ())))", "1"),
        ("(world? (quote (world)))", "0"),
        ("(world? (quote (world parent)))", "0"),
        ("(world? (quote (world parent journal)))", "0"),
        ("(world? (quote (world parent journal metadata extra)))", "0"),
        ("(world? (quote (not-world parent journal metadata)))", "0"),
        ("(world? (quote ()))", "0"),
    ] {
        assert_eq!(
            observe(program),
            expected,
            "world? must accept only the exact snapshot shape: {program}"
        );
    }
}

fn collect_call_head_widths(expr: &Expr, widths: &mut Vec<usize>) {
    let ExprKind::List(items) = &expr.kind else {
        return;
    };
    if let Some(Expr { kind: ExprKind::DomainIdentity(identity), .. }) = items.first() {
        widths.push(identity.width());
    }
    for item in items.iter() {
        collect_call_head_widths(item, widths);
    }
}

#[test]
fn world_shape_validator_uses_only_exact_d3_and_d4_call_heads() {
    let parsed = parse_mixed_exact_domain_reasoning_source("lib/world.lisp", D3)
        .expect("current immutable-world source must parse");
    let definition = parsed
        .iter()
        .find(|expression| {
            let ExprKind::List(items) = &expression.kind else {
                return false;
            };
            matches!(
                items.get(1).map(|item| &item.kind),
                Some(ExprKind::Symbol(name)) if name.as_ref() == "world?"
            )
        })
        .expect("the source must define world?");

    let mut widths = Vec::new();
    collect_call_head_widths(definition, &mut widths);
    widths.sort_unstable();
    widths.dedup();
    assert_eq!(
        widths,
        vec![3, 4],
        "world? should use D3 structure plus D4 NULL, not LENGTH or a wider helper"
    );
}
