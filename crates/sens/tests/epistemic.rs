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

// --- source-ref? ------------------------------------------------------

#[test]
fn source_ref_accepts_all_four_tags_with_nonempty_payload() {
    assert_eq!(
        eval_epistemic(r#"(source-ref? (quote (digest "sha256:abc")))"#),
        "t"
    );
    assert_eq!(
        eval_epistemic(
            r#"(source-ref? (quote (proof (goal (ancestor alice dana)) (world addr))))"#
        ),
        "t"
    );
    assert_eq!(
        eval_epistemic(r#"(source-ref? (quote (test (fixture conformance.my) (case x))))"#),
        "t"
    );
    assert_eq!(
        eval_epistemic(r#"(source-ref? (quote (observation host-capabilities-v1)))"#),
        "t"
    );
}

#[test]
fn source_ref_rejects_unknown_tag() {
    assert_eq!(
        eval_epistemic(r#"(source-ref? (quote (hearsay "someone said so")))"#),
        "()"
    );
}

#[test]
fn source_ref_rejects_empty_payload() {
    assert_eq!(eval_epistemic(r#"(source-ref? (quote (digest)))"#), "()");
}

#[test]
fn source_ref_rejects_atoms() {
    assert_eq!(eval_epistemic(r#"(source-ref? (quote digest))"#), "()");
    assert_eq!(eval_epistemic(r#"(source-ref? 42)"#), "()");
}

// --- observation? -------------------------------------------------------


#[test]
fn observation_rejects_a_bare_source_ref_variant_of_the_same_tag() {
    // (observation local-run) is a source-ref's `observation` variant
    // (tag + bare atom payload), not a full Observation record. A
    // tag-only check would misclassify it; observation? must not.
    assert_eq!(
        eval_epistemic(r#"(observation? (quote (observation local-run)))"#),
        "()"
    );
}

#[test]
fn observation_rejects_wrong_tag() {
    assert_eq!(
        eval_epistemic(
            r#"(observation? (quote (claim (statement x) (source (digest "d")) (review proposed))))"#
        ),
        "()"
    );
}

#[test]
fn observation_rejects_missing_statement_field() {
    assert_eq!(
        eval_epistemic(r#"(observation? (quote (observation (source (digest "d")))))"#),
        "()"
    );
}

#[test]
fn observation_rejects_extra_trailing_field() {
    assert_eq!(
        eval_epistemic(
            r#"(observation? (quote (observation (source (digest "d")) (statement x) (extra y))))"#
        ),
        "()"
    );
}

// --- claim? ---------------------------------------------------------


#[test]
fn claim_rejects_wrong_tag() {
    assert_eq!(
        eval_epistemic(r#"(claim? (quote (observation (source (digest "d")) (statement x))))"#),
        "()"
    );
}

#[test]
fn claim_rejects_review_outside_the_finite_enum() {
    assert_eq!(
        eval_epistemic(
            r#"(claim? (quote (claim (statement x) (source (digest "d")) (review maybe))))"#
        ),
        "()"
    );
}


#[test]
fn claim_rejects_extra_trailing_field() {
    assert_eq!(
        eval_epistemic(
            r#"(claim? (quote (claim (statement x) (source (digest "d")) (review proposed) (extra y))))"#
        ),
        "()"
    );
}

// --- evidence? --------------------------------------------------------


#[test]
fn evidence_rejects_outcome_outside_the_finite_enum() {
    assert_eq!(
        eval_epistemic(
            r#"(evidence? (quote (evidence (claim-ref (claim-ref x)) (method live-test) (outcome maybe) (source-ref (digest "d")))))"#
        ),
        "()"
    );
}


#[test]
fn evidence_rejects_extra_trailing_field() {
    assert_eq!(
        eval_epistemic(
            r#"(evidence? (quote (evidence (claim-ref (claim-ref x)) (method live-test) (outcome supports) (source-ref (digest "d")) (extra y))))"#
        ),
        "()"
    );
}

// --- intent? ----------------------------------------------------------


#[test]
fn intent_rejects_missing_field() {
    assert_eq!(
        eval_epistemic(
            r#"(intent? (quote (intent (goal (build cml)) (requires (process:cargo)))))"#
        ),
        "()"
    );
}

#[test]
fn intent_rejects_extra_trailing_field() {
    assert_eq!(
        eval_epistemic(
            r#"(intent? (quote (intent (goal (build cml)) (requires (process:cargo)) (stop-on x) (produces y) (extra z))))"#
        ),
        "()"
    );
}

// --- accessors --------------------------------------------------------


// --- supporting-evidence -------------------------------------------------
// Renamed from evidence-supports? (owner-directed audit, 2026-09-02):
// once every check passes, the function is already holding the matched
// `evidence` record, so it returns that record instead of a bare `t` --
// a retrieval function, not a predicate, per the audit's own three-way
// split (structural predicate / classification / retrieval). `()` on
// no match is unchanged, so `cond`/`if` truthiness callers need no
// change at all -- only callers who want the evidence itself gain
// something.

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
         (t (quote unreachable)))"#;

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

// --- intent-capabilities-satisfied? -------------------------------------


#[test]
fn intent_capabilities_satisfied_is_false_when_a_requirement_is_missing() {
    // The CML build blocker fixture: intent requires process:cargo, the
    // snapshot lacks it.
    assert_eq!(
        eval_epistemic(
            r#"(intent-capabilities-satisfied?
                 (make-intent (quote (build cml)) (quote (process:cargo tcp-client)) (quote (missing-capability)) (quote (build-artifact cml)))
                 (quote (process:git tcp-client)))"#
        ),
        "()"
    );
}

#[test]
fn intent_capabilities_satisfied_is_false_for_a_malformed_intent() {
    assert_eq!(
        eval_epistemic(
            r#"(intent-capabilities-satisfied? (quote (intent (goal x))) (quote (process:cargo)))"#
        ),
        "()"
    );
}

// --- canonical round trip: read(write-to-string(value)) = value --------
