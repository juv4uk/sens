//! D3 migration witness for the Lisp-owned immutable world layer.
//!
//! The frozen W8 source is retained as provenance, but it cannot be executed
//! as a semantic oracle after COND was ratified to accept exact D1 only:
//! historical NIL-as-false is intentionally no longer a current language law.
use sens::{eval_parsed_expressions, eval_program, parse_mixed_exact_domain_reasoning_source, Session};

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
