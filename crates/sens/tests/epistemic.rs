//! epistemic.my v0: opt-in proof-of-expression / epistemic-status data
//! layer (observation/claim/evidence/intent, source-ref, supporting-evidence,
//! intent-capabilities-satisfied?). Kept separate from other test files
//! since this module isn't wired into core.my/reason.my/knowledge.my —
//! see lib/epistemic.lisp's own header comment and the three source docs
//! under docs/ it implements.

use sens::{eval_program, Session};

fn eval_epistemic(source: &str) -> String {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/epistemic.lisp"), &mut session).unwrap();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

// --- Constructors ---------------------------------------------------

#[test]
fn make_observation_builds_the_canonical_shape() {
    assert_eq!(
        eval_epistemic(
            r#"(make-observation (quote (digest "sha256:abc")) (quote (build cml succeeds)))"#
        ),
        r#"(observation (source (digest "sha256:abc")) (statement (build cml succeeds)))"#
    );
}

#[test]
fn make_claim_builds_the_canonical_shape() {
    assert_eq!(
        eval_epistemic(
            r#"(make-claim (quote (build cml succeeds)) (quote (observation local-run)) (quote proposed))"#
        ),
        "(claim (statement (build cml succeeds)) (source (observation local-run)) (review proposed))"
    );
}

#[test]
fn make_evidence_builds_the_canonical_shape() {
    assert_eq!(
        eval_epistemic(
            r#"(make-evidence (quote (claim-ref cml-build-available)) (quote live-test) (quote supports) (quote (test (fixture conformance.my) (case exact-rational-division))))"#
        ),
        "(evidence (claim-ref (claim-ref cml-build-available)) (method live-test) (outcome supports) (source-ref (test (fixture conformance.my) (case exact-rational-division))))"
    );
}

#[test]
fn make_intent_builds_the_canonical_shape() {
    assert_eq!(
        eval_epistemic(
            r#"(make-intent (quote (build cml)) (quote (process:cargo tcp-client)) (quote (missing-capability)) (quote (build-artifact cml)))"#
        ),
        "(intent (goal (build cml)) (requires (process:cargo tcp-client)) (stop-on (missing-capability)) (produces (build-artifact cml)))"
    );
}

// --- accessors --------------------------------------------------------

#[test]
fn observation_accessors_extract_the_bare_values() {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/epistemic.lisp"), &mut session).unwrap();
    let obs = r#"(def o (make-observation (quote (digest "d")) (quote (build cml succeeds))))"#;
    eval_program(obs, &mut session).unwrap();
    assert_eq!(
        eval_program("(observation-source o)", &mut session)
            .unwrap()
            .value
            .to_string(),
        r#"(digest "d")"#
    );
    assert_eq!(
        eval_program("(observation-statement o)", &mut session)
            .unwrap()
            .value
            .to_string(),
        "(build cml succeeds)"
    );
}

#[test]
fn claim_accessors_extract_the_bare_values() {
    assert_eq!(
        eval_epistemic(
            r#"(claim-statement (make-claim (quote (build cml succeeds)) (quote (observation local-run)) (quote proposed)))"#
        ),
        "(build cml succeeds)"
    );
    assert_eq!(
        eval_epistemic(
            r#"(claim-review (make-claim (quote (build cml succeeds)) (quote (observation local-run)) (quote proposed)))"#
        ),
        "proposed"
    );
}

#[test]
fn evidence_accessors_extract_the_bare_values() {
    assert_eq!(
        eval_epistemic(
            r#"(evidence-claim-ref (make-evidence (quote (claim-ref x)) (quote live-test) (quote supports) (quote (digest "d"))))"#
        ),
        "(claim-ref x)"
    );
    assert_eq!(
        eval_epistemic(
            r#"(evidence-method (make-evidence (quote (claim-ref x)) (quote live-test) (quote supports) (quote (digest "d"))))"#
        ),
        "live-test"
    );
    assert_eq!(
        eval_epistemic(
            r#"(evidence-outcome (make-evidence (quote (claim-ref x)) (quote live-test) (quote supports) (quote (digest "d"))))"#
        ),
        "supports"
    );
    assert_eq!(
        eval_epistemic(
            r#"(evidence-source-ref (make-evidence (quote (claim-ref x)) (quote live-test) (quote supports) (quote (digest "d"))))"#
        ),
        r#"(digest "d")"#
    );
}

#[test]
fn intent_accessors_extract_the_bare_values() {
    let program = r#"(make-intent (quote (build cml)) (quote (process:cargo tcp-client)) (quote (missing-capability)) (quote (build-artifact cml)))"#;
    assert_eq!(
        eval_epistemic(&format!("(intent-goal {program})")),
        "(build cml)"
    );
    assert_eq!(
        eval_epistemic(&format!("(intent-requires {program})")),
        "(process:cargo tcp-client)"
    );
    assert_eq!(
        eval_epistemic(&format!("(intent-stop-on {program})")),
        "(missing-capability)"
    );
    assert_eq!(
        eval_epistemic(&format!("(intent-produces {program})")),
        "(build-artifact cml)"
    );
}

// --- supporting-evidence -------------------------------------------------
// Retrieval returns evidence data or structural (); no result is implicit
// D1 truth. Exact-D1 control must be explicit (enforced below).

#[test]
fn supporting_evidence_is_nil_when_outcome_is_not_supports() {
    assert_eq!(
        eval_epistemic(
            r#"(supporting-evidence
                 (make-evidence (quote (claim-ref cml-build-available)) (quote live-test) (quote contradicts) (quote (digest "d")))
                 (quote (claim-ref cml-build-available)))"#
        ),
        "()"
    );
}

#[test]
fn supporting_evidence_is_nil_when_claim_ref_does_not_match() {
    assert_eq!(
        eval_epistemic(
            r#"(supporting-evidence
                 (make-evidence (quote (claim-ref cml-build-available)) (quote live-test) (quote supports) (quote (digest "d")))
                 (quote (claim-ref some-other-claim)))"#
        ),
        "()"
    );
}

#[test]
fn supporting_evidence_record_is_not_implicit_cond_truth() {
    // #3170/#220: supporting-evidence is a retrieval function. A matched
    // evidence record is ordinary data, not a PredicateBit. Canonical D3 COND
    // accepts only exact D1:1 / D1:0 / structural EMPTY (), so callers that
    // want flow control must first ask an explicit predicate question.
    let source = r#"(cond
         ((supporting-evidence
            (make-evidence (quote (claim-ref cml-build-available)) (quote live-test) (quote supports) (quote (digest "d")))
            (quote (claim-ref cml-build-available)))
          (quote flows-through))
         (1 (quote unreachable)))"#;

    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/epistemic.lisp"), &mut session).unwrap();
    let error = eval_program(source, &mut session)
        .expect_err("ordinary evidence data must not become implicit COND truth");

    assert_eq!(error.kind, sens::ErrorKind::Type);
    assert!(
        error.message.contains("COND expects exact D1"),
        "unexpected canonical COND error: {error:?}"
    );
}

