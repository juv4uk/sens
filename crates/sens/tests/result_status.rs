//! Canonical data-only reasoning outcomes.
//! `reason` / `reason-in` keep their historical compatibility results while
//! result-status.my provides explicit observations without information collapse.

use sens::{
    eval_parsed_expressions, eval_program, load_core_library,
    parse_mixed_exact_domain_reasoning_source, Session, Value,
};

fn load_reasoning(session: &mut Session, path: &str, source: &str) {
    let parsed = parse_mixed_exact_domain_reasoning_source(path, source)
        .unwrap_or_else(|e| panic!("pinned reasoning parse failed for {path}: {e}"));
    eval_parsed_expressions(&parsed, session)
        .unwrap_or_else(|e| panic!("pinned reasoning load failed for {path}: {e}"));
}

fn result_status_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("повний чинний Core4 SENS bootstrap");
    load_reasoning(
        &mut session,
        "lib/result-status.lisp",
        include_str!("../../../lib/result-status.lisp"),
    );
    session
}

fn eval_result_status_value(source: &str) -> Value {
    let mut session = result_status_session();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
}

fn eval_result_status(source: &str) -> String {
    eval_result_status_value(source).to_string()
}

fn eval_reason_observation(source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).expect("повний чинний Core4 SENS bootstrap");
    for (path, source_text) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
        (
            "lib/result-status.lisp",
            include_str!("../../../lib/result-status.lisp"),
        ),
    ] {
        load_reasoning(&mut session, path, source_text);
    }
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn make_proved_preserves_statement_and_all_results() {
    assert_eq!(
        eval_result_status(
            r#"(створити-доведений (quote (parent alice bob)) (quote ((subst-a proof-a) (subst-b proof-b))))"#
        ),
        "(proved (parent alice bob) ((subst-a proof-a) (subst-b proof-b)))"
    );
}

#[test]
fn make_unknown_tags_a_subject() {
    assert_eq!(
        eval_result_status(r#"(створити-невідоме (quote no-rules-for-predicate))"#),
        "(unknown no-rules-for-predicate)"
    );
}

#[test]
fn make_partial_tags_a_value_and_a_bound() {
    assert_eq!(
        eval_result_status(r#"(створити-частковий (quote ()) (quote (depth . 12)))"#),
        "(partial () (depth . 12))"
    );
}

#[test]
fn make_blocked_tags_a_reason() {
    assert_eq!(
        eval_result_status(
            r#"(створити-заблокований (quote (depends-on PANINI-BRIDGE-MY-LISP-SYNTAX-CONVERSION)))"#
        ),
        "(blocked (depends-on PANINI-BRIDGE-MY-LISP-SYNTAX-CONVERSION))"
    );
}

#[test]
fn make_disputed_tags_evidence() {
    assert_eq!(
        eval_result_status(r#"(створити-спірний (список (як-є proof-a) (як-є proof-b)))"#),
        "(disputed (proof-a proof-b))"
    );
}

#[test]
fn make_invalid_keeps_reason_and_payload() {
    assert_eq!(
        eval_result_status(r#"(створити-некоректний (quote malformed-goal) 42)"#),
        "(invalid malformed-goal 42)"
    );
}

#[test]
fn result_status_extracts_every_canonical_tag() {
    // Rust відповідає за механізм завантаження та виконання, не за
    // таблицю очікуваних тегів. Шість канонічних статусів і негативні
    // випадки вже перевіряє мовний самовердикт у Lisp.
    // За порушення хоч одного закону він викликає недопущений CAR.
    let mut session = result_status_session();
    eval_program(
        include_str!("../../../tests/semantic/result-status-laws.lisp"),
        &mut session,
    )
    .expect("SENS має виконати Lisp-закони шести статусів результату");
}

#[test]
fn result_payload_extracts_everything_after_the_tag() {
    assert_eq!(
        eval_result_status(r#"(результат-вміст (створити-частковий 1 2))"#),
        "(1 2)"
    );
}

#[test]
fn an_ordinary_value_is_not_a_tagged_result() {
    assert_eq!(eval_result_status(r#"(результат-позначений? 42)"#), "0");
    assert_eq!(
        eval_result_status(r#"(результат-позначений? (quote (a b c)))"#),
        "0"
    );
}

#[test]
fn український_символ_результату_виконується_через_d1_а_не_недопущений_d9() {
    // Вхідні значення оцінює сам SENS: не Rust-перевірка типів.
    // Кожне значення має той самий D1 закон, що й публічна перевірка цілі.
    for (case, source, expected) in [
        (
            "символ",
            "(результат-внутрішній-символ? (як-є планета))",
            true,
        ),
        ("порожнє", "(результат-внутрішній-символ? (як-є ()))", false),
        (
            "пара",
            "(результат-внутрішній-символ? (як-є (планета земля)))",
            false,
        ),
        ("число", "(результат-внутрішній-символ? 42)", false),
        ("ціль", "(результат-ціль? (як-є (планета земля)))", true),
        (
            "складена-голова",
            "(результат-ціль? (як-є ((планета) земля)))",
            false,
        ),
        (
            "числова-голова",
            "(результат-ціль? (як-є (42 земля)))",
            false,
        ),
    ] {
        let value = eval_result_status_value(source);
        assert_eq!(
            value.as_predicate_bit(), Some(expected),
            "test_id=result-status-symbol-d1 case={case} layer=real-SENS input={source} expected=D1:{expected} actual={value}"
        );
    }
    for (source, expected) in [
        (
            "(міркувати-у-спостерігати (як-є ()) (як-є (планета земля)))",
            "(invalid invalid-module ())",
        ),
        (
            "(міркувати-у-спостерігати 42 (як-є (планета земля)))",
            "(invalid invalid-module 42)",
        ),
    ] {
        assert_eq!(
            eval_result_status(source),
            expected,
            "test_id=result-status-module-symbol-d1 layer=real-SENS input={source}"
        );
    }
}

#[test]
fn result_status_predicates_are_exact_d1_bits() {
    for (source, expected) in [
        (
            "(результат-позначений? (створити-невідоме (quote x)))",
            true,
        ),
        ("(результат-позначений? 42)", false),
        ("(результат-є-правильним-списком? (quote (a b)))", true),
        ("(результат-є-правильним-списком? (quote (a . b)))", false),
        ("(результат-не-є-головою-правила? (quote not?))", true),
        ("(результат-не-є-головою-правила? (quote not))", true),
        ("(результат-не-є-головою-правила? (quote other))", false),
        // D3 EQ не можна застосовувати до складених даних: це точна
        // негативна відповідь D1, а не помилка або host truthiness.
        (
            "(результат-не-є-головою-правила? (quote (not? (a))))",
            false,
        ),
        (
            "(результат-не-є-головою-правила? (quote ((not?) a)))",
            false,
        ),
    ] {
        let value = eval_result_status_value(source);
        assert_eq!(
            value.as_predicate_bit(),
            Some(expected),
            "{source} must return exact D1 PredicateBit, got {value}"
        );
    }
}

#[test]
fn result_status_of_an_untagged_value_is_nil() {
    assert_eq!(eval_result_status(r#"(результат-стан 42)"#), "()");
}

#[test]
fn reason_observe_reports_positive_proof_without_changing_reason() {
    let source = r#"
        (нехай ((rules (quote (((parent alice bob))))))
          (міркувати-спостерігати (quote (parent alice bob)) rules))
    "#;
    assert_eq!(
        eval_reason_observation(source),
        "(proved (parent alice bob) ((() (proved (parent alice bob) (parent alice bob) ()))))"
    );
}

#[test]
fn reason_observe_reports_an_explicit_negative_as_proved_opposite() {
    let source = r#"
        (нехай ((rules (quote (((not? (mortal socrates)))))))
          (друге (міркувати-спостерігати (quote (mortal socrates)) rules)))
    "#;
    assert_eq!(eval_reason_observation(source), "(not? (mortal socrates))");
}

#[test]
fn reason_observe_reports_dispute_when_both_sides_are_provable() {
    let source = r#"
        (нехай ((rules (quote (
                 ((mortal socrates))
                 ((not? (mortal socrates)))
               ))))
          (нехай ((outcome (міркувати-спостерігати (quote (mortal socrates)) rules)))
            (список (результат-стан outcome) (довжина (друге outcome)))))
    "#;
    assert_eq!(eval_reason_observation(source), "(disputed 2)");
}

#[test]
fn reason_observe_preserves_every_successful_alternative() {
    let source = r#"
        (нехай ((rules (quote (
                 ((edge a z))
                 ((edge b z))
                 ((edge c z))
               ))))
          (довжина
            (третє
              (міркувати-спостерігати
                (список (як-є edge) (логічна-змінна (як-є x)) (як-є z))
                rules))))
    "#;
    assert_eq!(eval_reason_observation(source), "3");
}

#[test]
fn reason_observe_rejects_malformed_goal_as_data() {
    assert_eq!(
        eval_reason_observation(r#"(міркувати-спостерігати 42 (quote ()))"#),
        "(invalid invalid-goal 42)"
    );
}
