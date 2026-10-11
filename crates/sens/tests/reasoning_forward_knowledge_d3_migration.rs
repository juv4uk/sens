//! Non-destructive D3 migration rehearsal for the Lisp-owned forward and
//! knowledge engines. Live files stay W8 until candidate/runtime parity holds.
use sens::{eval_parsed_expressions, eval_program, parse_mixed_exact_domain_reasoning_source, Session};

const CORE: &str = include_str!("../../../lib/core.lisp");
const UNIFY: &str = include_str!("../../../lib/unify.lisp");
const REASON: &str = include_str!("../../../lib/reason.lisp");
const FORWARD_OLD: &str = include_str!("../../../tests/fixtures/forward-d3-before.lisp");
const FORWARD_D3: &str = include_str!("../../../lib/forward.lisp");
const KNOWLEDGE_OLD: &str = include_str!("../../../tests/fixtures/knowledge-d3-before.lisp");
const KNOWLEDGE_D3: &str = include_str!("../../../lib/knowledge.lisp");

fn session(migrated: bool) -> Session {
    let mut session = Session::default();
    sens::eval_pinned_legacy_core_source("lib/core.lisp", CORE, &mut session)
        .expect("source-pinned exact-width legacy core bootstrap");
    for (path, source) in [("lib/unify.lisp", UNIFY), ("lib/reason.lisp", REASON)] {
        sens::eval_pinned_reasoning_source(path, source, &mut session)
            .expect("exact-domain reasoning prerequisite bootstrap");
    }
    for (name, old, candidate) in [
        ("lib/forward.lisp", FORWARD_OLD, FORWARD_D3),
        ("lib/knowledge.lisp", KNOWLEDGE_OLD, KNOWLEDGE_D3),
    ] {
        if migrated {
            let parsed = parse_mixed_exact_domain_reasoning_source(name, candidate)
                .expect("authorized reasoning source must parse");
            eval_parsed_expressions(&parsed, &mut session)
                .expect("candidate reasoning source must load");
        } else {
            // The frozen W8 corpus already contains short D3-D6 selectors.
            // The ordinary numeric reader cannot execute it faithfully.
            // Compare *both* variants under the same pinned typed reader.
            sens::eval_pinned_reasoning_source(name, old, &mut session)
                .expect("pre-migration W8 source must load through the same typed reader");
        }
    }
    session
}

fn observed(program: &str, migrated: bool) -> Result<String, String> {
    eval_program(program, &mut session(migrated))
        .map(|x| x.value.to_string())
        .map_err(|error| format!("{:?}: {}", error.kind, error.message))
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
fn reasoning_d3_projections_are_behaviorally_equal_on_bounded_oracle_cases() {
    for program in [
        "(module-journal-events (quote example) (quote ()))",
        "(module-journal-events (quote example) (quote ((tell example (fact a)))))",
        "(fire-rule (quote ((fact a) (derived a))) (quote (fact a)))",
        "(fire-rule (quote ((fact a) (derived a))) (quote (fact b)))",
        "(fire-rule-on-facts (quote ((fact a) (derived a))) (quote ()))",
    ] {
        assert_eq!(
            observed(program, true),
            observed(program, false),
            "forward/knowledge D3 candidate changed behavior for {program}"
        );
    }
}
