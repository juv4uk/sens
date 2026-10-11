//! Candidate-only differential witness. Does not replace the live world library
//! until the current D3 reader and the evaluator independently agree with the
//! ordinary pre-migration source. Keep old compatibility calls active meanwhile.
use sens::{
    eval_parsed_expressions, eval_program, parse_mixed_exact_domain_reasoning_source, Session,
};

const CORE: &str = include_str!("../../../lib/core.lisp");
const OLD: &str = include_str!("../../../lib/world.lisp");
const D3: &str = include_str!("../../../tests/fixtures/world-d3-candidate.lisp");

fn world_session(migrated: bool) -> Session {
    let mut s = Session::default();
    eval_program(CORE, &mut s).expect("core bootstrap required for world library");
    if migrated {
        let parsed = parse_mixed_exact_domain_reasoning_source("lib/world.lisp", D3)
            .expect("only explicitly pinned current-world projection may be typed");
        eval_parsed_expressions(&parsed, &mut s)
            .expect("candidate world library should load with D3 identities");
    } else {
        eval_program(OLD, &mut s).expect("historic world source must still load");
    }
    s
}

fn observe(program: &str, migrated: bool) -> Result<String, String> {
    let mut session = world_session(migrated);
    eval_program(program, &mut session)
        .map(|x| x.value.to_string())
        .map_err(|e| format!("{:?}: {}", e.kind, e.message))
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
fn world_d3_candidate_replays_existing_world_operations() {
    for program in [
        "(empty-world)",
        "(world? (empty-world))",
        "(world-parent (empty-world))",
        "(world-journal (empty-world))",
        "(world-metadata (empty-world))",
        "(world-module-missing? (empty-world) (quote unknown))",
        "(world-remove-first (quote x) (quote (a x b)))",
    ] {
        assert_eq!(
            observe(program, true),
            observe(program, false),
            "D3 candidate and historic W8 world disagree: {program}"
        );
    }
}
