//! Regression witnesses for the Lisp-owned Jev/System-One-like probabilistic decision slice.
//!
//! These tests exercise only the contract/data layer. There is no model call,
//! provider identity, new SID, or Rust Value variant.

use sens::{eval_program, load_core_library, Session};

fn eval_probabilistic_decision(source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    eval_program(
        include_str!("../../../lib/result-status.lisp"),
        &mut session,
    )
    .expect("result-status should load");
    eval_program(
        include_str!("../../../experiments/probabilistic-decision-jev-like.lisp"),
        &mut session,
    )
    .expect("probabilistic decision layer should load");
    eval_program(
        include_str!("../../../research/probabilistic-decision-auto-choice-20261021.lisp"),
        &mut session,
    )
    .expect("automatic choice policy should load");
    eval_program(
        include_str!("../../../research/probabilistic-decision-system-one-20261022.lisp"),
        &mut session,
    )
    .expect("typed System One contract should load");
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn choice_observation_keeps_probability_confidence_and_provenance() {
    let source = r#"
        (let* ((question
                (pd-question-choice
                  (quote route)
                  (quote (billing technical))))
              (observation
                (pd-choice-observe
                  question
                  (quote ((billing 3/4) (technical 1/4)))
                  (quote ((source synthetic) (revision 1))))))
          (list
            (pd-observation-confidence observation)
            (pd-observation-provenance observation)
            (second (pd-choice-policy observation (quote billing) 2/3))))
    "#;

    assert_eq!(
        eval_probabilistic_decision(source),
        r#"(3/4 ((source synthetic) (revision 1)) accept)"#
    );
}

#[test]
fn invalid_choice_distribution_fails_closed_when_not_normalized() {
    let source = r#"
        (let* ((question
                (pd-question-choice
                  (quote route)
                  (quote (billing technical)))))
          (result-status
            (pd-choice-observe
              question
              (quote ((billing 2/3) (technical 1/4)))
              (quote ((source malformed))))))
    "#;

    assert_eq!(eval_probabilistic_decision(source), "invalid");
}

#[test]
fn noul_policy_is_explicit_threshold_control_not_truthiness() {
    let source = r#"
        (let* ((question (pd-question-noul (quote urgent)))
              (observation
                (pd-noul-observe
                  question
                  3/4
                  (quote ((source synthetic))))))
          (list
            (second (pd-noul-policy observation 2/3))
            (second (pd-noul-policy observation 4/5))
            (pd-observation-confidence observation)))
    "#;

    assert_eq!(eval_probabilistic_decision(source), "(accept defer 3/4)");
}

#[test]
fn score_observation_uses_the_same_typed_distribution_contract() {
    let source = r#"
        (let* ((question
                (pd-question-score
                  (quote severity)
                  (quote (low medium high))))
              (observation
                (pd-score-observe
                  question
                  (quote ((low 1/4) (medium 1/2) (high 1/4)))
                  (quote ((source synthetic))))))
          (list
            (car observation)
            (pd-observation-confidence observation)
            (pd-observation-provenance observation)))
    "#;

    assert_eq!(
        eval_probabilistic_decision(source),
        "(score-observation/1 1/2 ((source synthetic)))"
    );
}

#[test]
fn independent_questions_do_not_invent_joint_consistency() {
    let source = r#"
        (let ((left
                (pd-choice-observe
                  (pd-question-choice
                    (quote route)
                    (quote (billing technical)))
                  (quote ((billing 3/4) (technical 1/4)))
                  (quote ((source a)))))
              (right
                (pd-choice-observe
                  (pd-question-choice
                    (quote route-2)
                    (quote (billing technical)))
                  (quote ((billing 1/4) (technical 3/4)))
                  (quote ((source b))))))
          (car (pd-two-question-consistency left right (quote independent))))
    "#;

    assert_eq!(eval_probabilistic_decision(source), "decision-relation-1");
}

#[test]
fn declared_agreement_with_different_distributions_is_disputed() {
    let source = r#"
        (let ((left
                (pd-choice-observe
                  (pd-question-choice
                    (quote route)
                    (quote (billing technical)))
                  (quote ((billing 3/4) (technical 1/4)))
                  (quote ((source a)))))
              (right
                (pd-choice-observe
                  (pd-question-choice
                    (quote route)
                    (quote (billing technical)))
                  (quote ((billing 1/4) (technical 3/4)))
                  (quote ((source b))))))
          (result-status
            (pd-two-question-consistency left right (quote agree))))
    "#;

    assert_eq!(eval_probabilistic_decision(source), "disputed");
}

#[test]
fn noul_policy_rejects_out_of_domain_threshold() {
    let source = r#"
        (let* ((question (pd-question-noul (quote urgent)))
              (observation
                (pd-noul-observe
                  question
                  3/4
                  (quote ((source synthetic))))))
          (result-status
            (pd-noul-policy observation 3/2)))
    "#;

    assert_eq!(eval_probabilistic_decision(source), "invalid");
}

#[test]
fn choice_policy_rejects_out_of_domain_threshold() {
    let source = r#"
        (let* ((question
                (pd-question-choice
                  (quote route)
                  (quote (billing technical))))
              (observation
                (pd-choice-observe
                  question
                  (quote ((billing 3/4) (technical 1/4)))
                  (quote ((source synthetic))))))
          (result-status
            (pd-choice-policy observation (quote billing) 3/2)))
    "#;

    assert_eq!(eval_probabilistic_decision(source), "invalid");
}

#[test]
fn synthetic_witness_carries_one_state_through_three_typed_questions() {
    let source = r#"
        (let ((witness
                (pd-synthetic-witness
                  (quote ((case billing) (revision 1)))
                  (pd-question-choice
                    (quote route)
                    (quote (billing technical)))
                  (pd-question-noul (quote urgent))
                  (pd-question-score
                    (quote severity)
                    (quote (low medium high))))))
          (list
            (car witness)
            (second witness)
            (car (third witness))
            (pd-observation-confidence (fourth witness))
            (pd-observation-confidence (fifth witness))))
    "#;

    assert_eq!(
        eval_probabilistic_decision(source),
        "(probabilistic-witness/1 ((case billing) (revision 1)) choice-observation/1 2/3 1/2)"
    );
}

#[test]
fn automatic_choice_policy_selects_unique_winner_and_defers_unsafe_choices() {
    let selected = r#"
        (let* ((question
                (pd-question-choice
                  (quote route)
                  (quote (billing technical))))
              (observation
                (pd-choice-observe
                  question
                  (quote ((billing 3/4) (technical 1/4)))
                  (quote ((source synthetic) (revision 1)))))
              (decision (правило-автоматичного-вибору observation 2/3)))
          (list
            (second decision)
            (second (fourth decision))
            (pd-observation-provenance (third decision))))
    "#;
    assert_eq!(
        eval_probabilistic_decision(selected),
        "(accept billing ((source synthetic) (revision 1)))"
    );

    let tied = r#"
        (let* ((question
                (pd-question-choice
                  (quote route)
                  (quote (billing technical))))
              (observation
                (pd-choice-observe
                  question
                  (quote ((billing 1/2) (technical 1/2)))
                  (quote ((source synthetic) (case tied)))))
              (decision (правило-автоматичного-вибору observation 1/2)))
          (list
            (second decision)
            (second (fourth decision))
            (second (fifth decision))))
    "#;
    assert_eq!(
        eval_probabilistic_decision(tied),
        "(defer ambiguous-maximum-probability (billing technical))"
    );

    let below_threshold = r#"
        (let* ((question
                (pd-question-choice
                  (quote route)
                  (quote (billing technical))))
              (observation
                (pd-choice-observe
                  question
                  (quote ((billing 3/4) (technical 1/4)))
                  (quote ((source synthetic)))))
              (decision (правило-автоматичного-вибору observation 4/5)))
          (list
            (second decision)
            (second (fourth decision))
            (second (fifth decision))
            (pd-observation-confidence (third decision))))
    "#;
    assert_eq!(
        eval_probabilistic_decision(below_threshold),
        "(defer below-confidence-threshold billing 3/4)"
    );

    let forged_confidence = r#"
        (let* ((question
                (pd-question-choice
                  (quote route)
                  (quote (billing technical))))
              (observation
                (list
                  (quote choice-observation/1)
                  question
                  (quote ((billing 3/4) (technical 1/4)))
                  1/4
                  (quote ((source synthetic))))))
          (result-status (правило-автоматичного-вибору observation 2/3)))
    "#;
    assert_eq!(eval_probabilistic_decision(forged_confidence), "invalid");

    let invalid_threshold = r#"
        (let* ((question
                (pd-question-choice
                  (quote route)
                  (quote (billing technical))))
              (observation
                (pd-choice-observe
                  question
                  (quote ((billing 3/4) (technical 1/4)))
                  (quote ((source synthetic))))))
          (result-status (правило-автоматичного-вибору observation 3/2)))
    "#;
    assert_eq!(eval_probabilistic_decision(invalid_threshold), "invalid");
}

#[test]
fn system_one_validates_one_state_with_parallel_typed_questions_and_answers() {
    // Цей test_id запускається чинним CI після зміни System One джерела.
    // Без посередництва Python/JSON: SENS сам має відрізняти прямі Д1
    // «так» / «ні», а не успадковувати historical T/NIL truthiness.
    for (source, expected) in [
        ("(за-умовою (ні (як-є помилка)) (так (як-є гаразд)))", "гаразд"),
        ("(за-умовою (так (як-є гаразд)) (ні (як-є помилка)))", "гаразд"),
    ] {
        assert_eq!(
            eval_probabilistic_decision(source),
            expected,
            "test_id=system-one-d1-positive-negative layer=actual-SENS source={source}"
        );
    }

    let valid_batch = r#"
      (нехай-послідовно ((state (як-є ((message "double charge") (locale uk))))
             (choice-question (запитання-вибору-системи-один
               (як-є route)
               "Choose the support team for this request."
               (як-є ((billing "Payment or refund issues")
                       (technical "Software malfunction")))))
             (noul-question (запитання-так-ні-системи-один
               (як-є urgent)
               "Does this request need urgent handling?"))
             (score-question (запитання-шкали-системи-один
               (як-є severity)
               "Rate urgency from low to high."
               (як-є ((low "No deadline")
                       (medium "Needed soon")
                       (high "Immediate attention")))))
             (questions (список choice-question noul-question score-question))
             (request (запит-системи-один state questions))
             (answers
               (список
                 (спостерегти-вибір-системи-один choice-question
                   (як-є ((billing 3/4) (technical 1/4)))
                   (як-є ((source synthetic) (question route))))
                 (спостерегти-так-ні noul-question 2/3
                   (як-є ((source synthetic) (question urgent))))
                 (спостерегти-шкалу-системи-один score-question
                   (як-є ((low 1/4) (medium 1/2) (high 1/4)))
                   (як-є ((source synthetic) (question severity))))))
             (response (відповідь-системи-один request answers)))
        (список
          (за-умовою
            ((перевірити-запит-системи-один? request) (як-є valid))
            (так (як-є invalid)))
          (довжина (третє request))
          (за-умовою
            ((відповідь-системи-один-допустима? response request) (як-є valid))
            (так (як-є invalid)))))
    "#;
    assert_eq!(
        eval_probabilistic_decision(valid_batch),
        "(valid 3 valid)"
    );

    let invalid_batches = r#"
      (нехай-послідовно ((state (як-є ((message "double charge"))))
             (choice-question (запитання-вибору-системи-один
               (як-є route)
               "Choose the support team for this request."
               (як-є ((billing "Payment or refund issues")
                       (technical "Software malfunction")))))
             (noul-question (запитання-так-ні-системи-один
               (як-є urgent)
               "Does this request need urgent handling?"))
             (questions (список choice-question noul-question))
             (request (запит-системи-один state questions))
             (choice-answer (спостерегти-вибір-системи-один choice-question
               (як-є ((billing 3/4) (technical 1/4)))
               (як-є ((source synthetic)))))
             (missing (відповідь-системи-один request (список choice-answer)))
             (duplicate (відповідь-системи-один request (список choice-answer choice-answer)))
             (duplicate-question-request
               (запит-системи-один state
                 (список choice-question
                       (запитання-так-ні-системи-один (як-є route) "Does this request require urgent handling?")))))
        (список
          (за-умовою
            ((відповідь-системи-один-допустима? missing request) (як-є valid))
            (так (як-є invalid)))
          (за-умовою
            ((відповідь-системи-один-допустима? duplicate request) (як-є valid))
            (так (як-є invalid)))
          (за-умовою
            ((перевірити-запит-системи-один? duplicate-question-request) (як-є valid))
            (так (як-є invalid)))))
    "#;
    assert_eq!(
        eval_probabilistic_decision(invalid_batches),
        "(invalid invalid invalid)"
    );
}
