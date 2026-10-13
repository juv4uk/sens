//! B2: presentation must preserve the semantic distinction established by
//! lib/result-status.my instead of collapsing every non-proof into one phrase.

use sens::{
    eval_parsed_expressions, eval_program, parse_exact_domain_source,
    parse_mixed_exact_domain_reasoning_source, Session,
};

fn eval_outcome_value(source: &str) -> sens::Value {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    // These reasoning libraries contain exact D9 call heads; use their
    // source-pinned reader rather than the legacy numeric compatibility parser.
    for (path, source) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
    ] {
        let parsed = parse_mixed_exact_domain_reasoning_source(path, source)
            .unwrap_or_else(|error| panic!("exact reasoning parse failed for {path}: {error}"));
        eval_parsed_expressions(&parsed, &mut session)
            .unwrap_or_else(|error| panic!("exact reasoning load failed for {path}: {error}"));
    }

    // result-status.lisp and narrate.lisp carry exact-width D8/D9 words.
    // Do not load either through the ordinary compatibility reader: it can
    // interpret e.g. 11110111 as a numeric value instead of a domain identity.
    let statuses = parse_exact_domain_source(include_str!("../../../lib/result-status.lisp"))
        .expect("canonical result-status source must preserve each domain width");
    eval_parsed_expressions(&statuses, &mut session)
        .expect("exact-domain result-status library must load");

    let narration = parse_exact_domain_source(include_str!("../../../lib/narrate.lisp"))
        .expect("canonical narration source must preserve each domain width");
    eval_parsed_expressions(&narration, &mut session)
        .expect("exact-domain narration library must load");

    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
}

fn eval_outcome_narration(source: &str) -> String {
    eval_outcome_value(source).to_string()
}

#[test]
fn arity_predicate_returns_exact_d1_for_valid_and_invalid_shapes() {
    // COND consumes exact D1 only: host truthiness and structural Nil are not predicates.
    let cases = [
        ("(narrate-outcome-arity? (quote (unknown subject)) 2)", true),
        ("(narrate-outcome-arity? (quote (proved statement results)) 3)", true),
        ("(narrate-outcome-arity? (quote (unknown)) 2)", false),
        ("(narrate-outcome-arity? (quote (partial value bound extra)) 3)", false),
        ("(narrate-outcome-arity? 42 2)", false),
    ];

    for (source, expected) in cases {
        let actual = eval_outcome_value(source).as_predicate_bit();
        assert_eq!(
            actual,
            Some(expected),
            "{source}: expected an exact D1 PredicateBit, not host truthiness"
        );
    }
}
#[test]
fn proved_outcome_keeps_the_ground_answer_and_real_premise() {
    let source = r#"
        (let* ((rules (quote (((has (var x) mass) (planet (var x)))
                              ((planet earth)))))
               (goal (quote (has earth mass))))
          (narrate-outcome (reason-observe goal rules)))
    "#;
    assert_eq!(
        eval_outcome_narration(source),
        "(proved earth has mass because earth is a planet)"
    );
}

#[test]
fn disputed_outcome_keeps_both_evidence_sides_visible() {
    let source = r#"
        (let* ((rules (quote (((mortal socrates))
                              ((not? (mortal socrates))))))
               (narration
                 (narrate-outcome
                   (reason-observe (quote (mortal socrates)) rules))))
          (list (car narration)
                (second narration)
                (third narration)
                (length (fourth narration))))
    "#;
    assert_eq!(
        eval_outcome_narration(source),
        "(disputed because both-sides-have-evidence 2)"
    );
}

#[test]
fn invalid_outcome_names_validation_failure_and_payload() {
    assert_eq!(
        eval_outcome_narration(
            r#"(narrate-outcome (make-invalid (quote invalid-goal) 42))"#
        ),
        "(invalid because invalid-goal payload 42)"
    );
}

#[test]
fn partial_and_blocked_do_not_collapse_into_unknown() {
    assert_eq!(
        eval_outcome_narration(
            r#"(narrate-outcome (make-partial (quote ()) (quote (depth . 12))))"#
        ),
        "(partial value () bound (depth . 12))"
    );
    assert_eq!(
        eval_outcome_narration(
            r#"(narrate-outcome (make-blocked (quote (depends-on corpus))))"#
        ),
        "(blocked because (depends-on corpus))"
    );
}

#[test]
fn malformed_or_unknown_outcome_shape_is_presented_as_invalid() {
    assert_eq!(
        eval_outcome_narration(r#"(narrate-outcome 42)"#),
        "(invalid outcome-shape 42)"
    );
    assert_eq!(
        eval_outcome_narration(r#"(narrate-outcome (quote (mystery payload)))"#),
        "(invalid outcome-tag mystery)"
    );
    assert_eq!(
        eval_outcome_narration(r#"(narrate-outcome (quote (unknown)))"#),
        "(invalid outcome-shape (unknown))"
    );
    assert_eq!(
        eval_outcome_narration(r#"(narrate-outcome (quote ((bad-tag) payload)))"#),
        "(invalid outcome-tag (bad-tag))"
    );
}
