//! Mechanical runner for SENS-owned semantic witnesses.
//!
//! The semantic expectation is encoded inside each binary SENS program.
//! Rust loads admitted language libraries and reports only whether the
//! self-verdict program executes successfully. It contains no truth table,
//! expected result value, or duplicate language law.

use sens::{
    eval_parsed_expressions, eval_pinned_legacy_core_source,
    parse_canonical_binary, parse_mixed_exact_domain_reasoning_source, Session,
};

const RESULT_STATUS: &str = include_str!("../../../lib/result-status.lisp");
const RESULT_STATUS_D1_WITNESS: &str =
    include_str!("../../../tests/semantic/result-status-d1-law.bits");

fn load_reasoning(session: &mut Session, path: &str, source: &str) {
    let parsed = parse_mixed_exact_domain_reasoning_source(path, source)
        .unwrap_or_else(|error| panic!("mechanical parse failed for {path}: {error}"));
    eval_parsed_expressions(&parsed, session)
        .unwrap_or_else(|error| panic!("mechanical library load failed for {path}: {error}"));
}

#[test]
fn result_status_exact_d1_binary_self_verdict() {
    assert!(
        RESULT_STATUS_D1_WITNESS
            .bytes()
            .all(|byte| matches!(byte, b'0' | b'1' | b' ' | b'\n' | b'\r' | b'\t')),
        "semantic witness must be exact binary SENS source"
    );

    let mut session = Session::default();
    eval_pinned_legacy_core_source(
        "lib/core.lisp",
        include_str!("../../../lib/core.lisp"),
        &mut session,
    )
    .expect("mechanical Core loader must admit current source");
    load_reasoning(&mut session, "lib/result-status.lisp", RESULT_STATUS);

    let witness = parse_canonical_binary(RESULT_STATUS_D1_WITNESS)
        .expect("binary SENS witness must have canonical D2 framing");
    eval_parsed_expressions(&witness, &mut session)
        .expect("SENS-owned result-status self-verdict rejected");
}
