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


const META_EVAL_MUTUAL_D4_LAW: &str =
    include_str!("../../../tests/semantic/meta-eval-mutual-d4-law.bits");

/// Механічний транспорт: зміст перевірок і їхній очікуваний D1=1
/// належать виключно виконуваним бітовим формам SENS.
#[test]
fn meta_eval_mutual_d4_exact_sens_self_verdict() {
    assert!(
        META_EVAL_MUTUAL_D4_LAW
            .bytes()
            .all(|byte| matches!(byte, b'0' | b'1' | b' ' | b'\n' | b'\r' | b'\t')),
        "SENS must own all semantic assertions in exact binary source"
    );
    let forms = parse_canonical_binary(META_EVAL_MUTUAL_D4_LAW)
        .expect("canonical D2 framing and exact D1/D3/D4/D7 words");
    assert_eq!(forms.len(), 4, "one executable binary SENS self-proof per line");

    for (index, form) in forms.iter().enumerate() {
        let result = eval_parsed_expressions(
            std::slice::from_ref(form), &mut Session::default(),
        )
        .unwrap_or_else(|error| panic!("binary SENS self-proof {} failed to execute: {error}", index + 1))
        .value;
        assert_eq!(
            result.as_predicate_bit(), Some(true),
            "binary SENS self-proof {} did not produce exact D1 YES: {result}",
            index + 1
        );
    }
}
