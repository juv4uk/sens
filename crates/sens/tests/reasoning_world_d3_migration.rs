//! D3 migration witness for the Lisp-owned immutable world layer.
//!
//! The frozen W8 source is retained as provenance, but it cannot be executed
//! as a semantic oracle after COND was ratified to accept exact D1 only:
//! historical NIL-as-false is intentionally no longer a current language law.
use sens::{eval_parsed_expressions, eval_program, parse_mixed_exact_domain_reasoning_source, Session, Expr, ExprKind};

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

// #5737: mechanical domain-width witness, independent from behavioral checks.
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

#[test]
fn world_shape_source_uses_only_exact_d3_d4_call_heads() {
    let parsed = parse_mixed_exact_domain_reasoning_source("lib/world.lisp", D3)
        .expect("world source must retain exact domain identity");
    let definition = parsed.iter().find(|expression| {
        let ExprKind::List(items) = &expression.kind else { return false; };
        matches!(
            items.get(1).map(|item| &item.kind),
            Some(ExprKind::Symbol(name)) if name.as_ref() == "world?"
        )
    }).expect("world? definition is present");

    let mut coordinates = Vec::new();
    collect_call_head_coordinates(definition, &mut coordinates);
    coordinates.sort_unstable();
    coordinates.dedup();

    let widths = coordinates.iter().map(|(width, _)| *width)
        .collect::<std::collections::BTreeSet<_>>();
    assert_eq!(
        widths,
        [3usize, 4usize].into_iter().collect(),
        "world? may use D3 structure and D4 NULL/definition only"
    );
    for required in [(3, 0b001), (3, 0b010), (3, 0b011), (3, 0b101), (3, 0b110),
                     (4, 0b0010), (4, 0b0011), (4, 0b0101)] {
        assert!(
            coordinates.contains(&required),
            "world? source is missing exact D{}:{:0width$b}",
            required.0,
            required.1,
            width = required.0
        );
    }
}
