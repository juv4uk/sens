//! Canonical data-only reasoning outcomes.
//! `reason` / `reason-in` keep their historical compatibility results while
//! result-status.my provides explicit observations without information collapse.

use sens::{eval_program, Session};

fn eval_result_status(source: &str) -> String {
    let mut session = Session::default();
    sens::load_core_library(&mut session).unwrap();
    eval_program(include_str!("../../../lib/result-status.lisp"), &mut session).unwrap();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

fn eval_reason_observation(source: &str) -> String {
    let mut session = Session::default();
    sens::load_core_library(&mut session).unwrap();
    eval_program(include_str!("../../../lib/unify.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/reason.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/result-status.lisp"), &mut session).unwrap();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn make_proved_preserves_statement_and_all_results() {
    assert_eq!(
        eval_result_status(
            r#"(make-proved (quote (parent alice bob)) (quote ((subst-a proof-a) (subst-b proof-b))))"#
        ),
        "(proved (parent alice bob) ((subst-a proof-a) (subst-b proof-b)))"
    );
}

#[test]
fn make_unknown_tags_a_subject() {
    assert_eq!(
        eval_result_status(r#"(make-unknown (quote no-rules-for-predicate))"#),
        "(unknown no-rules-for-predicate)"
    );
}

#[test]
fn make_partial_tags_a_value_and_a_bound() {
    assert_eq!(
        eval_result_status(r#"(make-partial (quote ()) (quote (depth . 12)))"#),
        "(partial () (depth . 12))"
    );
}

#[test]
fn make_blocked_tags_a_reason() {
    assert_eq!(
        eval_result_status(
            r#"(make-blocked (quote (depends-on PANINI-BRIDGE-MY-LISP-SYNTAX-CONVERSION)))"#
        ),
        "(blocked (depends-on PANINI-BRIDGE-MY-LISP-SYNTAX-CONVERSION))"
    );
}

#[test]
fn make_disputed_tags_evidence() {
    assert_eq!(
        eval_result_status(r#"(make-disputed (list (quote proof-a) (quote proof-b)))"#),
        "(disputed (proof-a proof-b))"
    );
}

#[test]
fn make_invalid_keeps_reason_and_payload() {
    assert_eq!(
        eval_result_status(r#"(make-invalid (quote malformed-goal) 42)"#),
        "(invalid malformed-goal 42)"
    );
}

#[test]
fn result_status_extracts_every_canonical_tag() {
    for (source, expected) in [
        ("(result-status (make-proved (quote x) (quote ())))", "proved"),
        ("(result-status (make-unknown (quote x)))", "unknown"),
        ("(result-status (make-partial 1 2))", "partial"),
        ("(result-status (make-blocked (quote x)))", "blocked"),
        ("(result-status (make-disputed (quote ())))", "disputed"),
        ("(result-status (make-invalid (quote x) 1))", "invalid"),
    ] {
        assert_eq!(eval_result_status(source), expected);
    }
}

#[test]
fn result_payload_extracts_everything_after_the_tag() {
    assert_eq!(
        eval_result_status(r#"(result-payload (make-partial 1 2))"#),
        "(1 2)"
    );
}

#[test]
fn an_ordinary_value_is_not_a_tagged_result() {
    assert_eq!(eval_result_status(r#"(result-tagged? 42)"#), "()");
    assert_eq!(
        eval_result_status(r#"(result-tagged? (quote (a b c)))"#),
        "()"
    );
}

#[test]
fn result_status_of_an_untagged_value_is_nil() {
    assert_eq!(eval_result_status(r#"(result-status 42)"#), "()");
}

#[test]
fn reason_observe_reports_positive_proof_without_changing_reason() {
    let source = r#"
        (let ((rules (quote (((parent alice bob))))))
          (reason-observe (quote (parent alice bob)) rules))
    "#;
    assert_eq!(
        eval_reason_observation(source),
        "(proved (parent alice bob) ((() (proved (parent alice bob) (parent alice bob) ()))))"
    );
}

#[test]
fn reason_observe_reports_an_explicit_negative_as_proved_opposite() {
    let source = r#"
        (let ((rules (quote (((not? (mortal socrates)))))))
          (second (reason-observe (quote (mortal socrates)) rules)))
    "#;
    assert_eq!(
        eval_reason_observation(source),
        "(not? (mortal socrates))"
    );
}

#[test]
fn reason_observe_reports_dispute_when_both_sides_are_provable() {
    let source = r#"
        (let ((rules (quote (
                 ((mortal socrates))
                 ((not? (mortal socrates)))
               ))))
          (let ((outcome (reason-observe (quote (mortal socrates)) rules)))
            (list (result-status outcome) (length (second outcome)))))
    "#;
    assert_eq!(eval_reason_observation(source), "(disputed 2)");
}

#[test]
fn reason_observe_preserves_every_successful_alternative() {
    let source = r#"
        (let ((rules (quote (
                 ((edge a z))
                 ((edge b z))
                 ((edge c z))
               ))))
          (length
            (third
              (reason-observe
                (list (quote edge) (logic-var (quote x)) (quote z))
                rules))))
    "#;
    assert_eq!(eval_reason_observation(source), "3");
}

#[test]
fn reason_observe_rejects_malformed_goal_as_data() {
    assert_eq!(
        eval_reason_observation(r#"(reason-observe 42 (quote ()))"#),
        "(invalid invalid-goal 42)"
    );
}
