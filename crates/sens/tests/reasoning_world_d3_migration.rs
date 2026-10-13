//! Mechanical source-boundary witness for the Lisp-owned immutable-world layer.
//! Behavioral expectations are SENS-owned in tests/semantic/world-exact-arity-witness.lisp.

use sens::{parse_mixed_exact_domain_reasoning_source, ErrorKind};

const OLD: &str = include_str!("../../../tests/fixtures/world-d3-before.lisp");
const D3: &str = include_str!("../../../lib/world.lisp");

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
        ErrorKind::Parse
    );
}
