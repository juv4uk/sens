//! D3/D9 migration witness for the Lisp-owned forward and knowledge engines.
//!
//! Frozen W8 files remain provenance only. They used the old NIL-as-false
//! conditional convention, so executing them with the ratified exact-D1 COND
//! would test a retired law rather than current behavior.
use sens::{eval_parsed_expressions, eval_program, parse_mixed_exact_domain_reasoning_source, Session};

const CORE: &str = include_str!("../../../lib/core.lisp");
const UNIFY: &str = include_str!("../../../lib/unify.lisp");
const REASON: &str = include_str!("../../../lib/reason.lisp");
const FORWARD_OLD: &str = include_str!("../../../tests/fixtures/forward-d3-before.lisp");
const FORWARD_D3: &str = include_str!("../../../lib/forward.lisp");
const KNOWLEDGE_OLD: &str = include_str!("../../../tests/fixtures/knowledge-d3-before.lisp");
const KNOWLEDGE_D3: &str = include_str!("../../../lib/knowledge.lisp");

fn session() -> Session {
    let mut session = Session::default();
    sens::eval_core_library_source(CORE, &mut session)
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
        ("(запустити-правило (як-є ((fact a) (derived a))) (як-є (fact a)))", "(derived a)"),
        ("(запустити-правило (як-є ((fact a) (derived a))) (як-є (fact b)))", "no-match"),
        ("(запустити-правило-на-факти (як-є ((fact a) (derived a))) (як-є ()))", "()"),
    ] {
        assert_eq!(observed(program), expected, "current reasoning behavior changed: {program}");
    }
}

// Цей свідок виконує поточні lib/core, lib/unify, lib/reason, lib/forward
// через справжній SENS reader/evaluator, не Python-симуляцію.
#[test]
fn compound_success_bypasses_atom_only_eq_and_skips_atomic_no_match() {
    let mut runtime = session();
    for (program, expected) in [
        (
            "(запустити-правило-на-факти (як-є ((факт а) (наслідок а))) (як-є ((факт а) (факт б))))",
            "((наслідок а))",
        ),
        (
            "(запустити-правило-на-факти (як-є ((факт а) (наслідок а))) (як-є ((факт б))))",
            "()",
        ),
        (
            "(запустити-правило-на-факти (як-є ((факт а) (наслідок а))) (як-є ((факт а) (факт б) (факт а))))",
            "((наслідок а) (наслідок а))",
        ),
        // TMS: результат (факт . підтримка), а не губиться в атомарній гілці.
        (
            "(запустити-правило-система-істини (як-є ((факт а) (наслідок а))) (як-є (факт а)))",
            "((наслідок а) (факт а))",
        ),
        (
            "(запустити-правило-на-факти-система-істини (як-є ((факт а) (наслідок а))) (як-є ((факт а) (факт б))))",
            "(((наслідок а) (факт а)))",
        ),
        (
            "(запустити-правило-на-факти-система-істини (як-є ((факт а) (наслідок а))) (як-є ((факт б))))",
            "()",
        ),
        // JTMS: кожен доказ зберігає власний список підтримок.
        (
            "(запустити-правило-система-обґрунтувань (як-є ((факт а) (наслідок а))) (як-є (факт а)))",
            "((наслідок а) ((факт а)))",
        ),
        (
            "(запустити-правило-на-факти-система-обґрунтувань (як-є ((факт а) (наслідок а))) (як-є ((факт а) (факт б))))",
            "(((наслідок а) ((факт а))))",
        ),
        (
            "(запустити-правило-на-факти-система-обґрунтувань (як-є ((факт а) (наслідок а))) (як-є ((факт б))))",
            "()",
        ),
    ] {
        let value = eval_program(program, &mut runtime)
            .unwrap_or_else(|error| panic!("SENS Forward failed for {program}: {error:?}"))
            .value
            .to_string();
        assert_eq!(value, expected, "Forward must preserve successful compound facts and their order");
    }
}
