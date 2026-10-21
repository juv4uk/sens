//! Виконувані свідки мосту Пролог → Даталог на чинному SENS D4.
//! Протокольні мітки — цитовані дані, не викличні голови Rust.
use sens::{eval_program, load_core_library, Session};

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("чинна бібліотека Core SENS");
    eval_program(include_str!("../../../lib/bridge/prolog-to-datalog.lisp"), &mut session)
        .expect("завантажити іменований D4 міст справжнім SENS");
    session
}

fn eval(source: &str, session: &mut Session) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("test_id=prolog-d10-d4 layer=real-SENS input={source} actual={error}"))
        .value
        .to_string()
}

#[test]
fn d4_bridge_projects_three_real_facts_and_keeps_protocol_identity() {
    let got = eval(
        "(перетворити-підстановки-пролог-на-факти-даталог         (як-є (prolog-substitution-observation         (source-ref observation-42) (variable ancestor) (values bob dave carol))))",
        &mut session(),
    );
    assert_eq!(
        got,
        "(projection-result (projection prolog-substitutions-to-datalog-facts)          (source-ref observation-42) (facts ((ancestor bob) (ancestor dave) (ancestor carol))))",
        "D10 проєкція належить SENS, а не host"
    );
}

#[test]
fn d4_bridge_rejects_missing_source_and_malformed_observation() {
    let mut s = session();
    assert_eq!(
        eval("(перетворити-підстановки-пролог-на-факти-даталог               (як-є (prolog-substitution-observation (variable ancestor) (values bob))))", &mut s),
        "(projection-failure missing-source-ref)",
    );
    assert_eq!(
        eval("(перетворити-підстановки-пролог-на-факти-даталог (як-є ()))", &mut s),
        "(projection-failure malformed-observation)",
    );
}

#[test]
fn d4_bridge_refuses_truncated_and_ambiguous_protocol_fields() {
    let mut s = session();
    // SENS виконує справжні DEFINE з lib/bridge/prolog-to-datalog.lisp.
    // Синтетичні протокольні записи лише вхідні дані, не Rust-оракул.
    for (case, fields, expected) in [
        (
            "source-no-value",
            "(source-ref) (variable ancestor) (values bob)",
            "(projection-failure missing-source-ref)",
        ),
        (
            "source-extra-value",
            "(source-ref observation-42 duplicate) (variable ancestor) (values bob)",
            "(projection-failure malformed-source-ref)",
        ),
        (
            "variable-no-role",
            "(source-ref observation-42) (variable) (values bob)",
            "(projection-failure missing-variable-role)",
        ),
        (
            "variable-extra-role",
            "(source-ref observation-42) (variable ancestor duplicate) (values bob)",
            "(projection-failure malformed-variable-role)",
        ),
        (
            "values-dotted-tail",
            "(source-ref observation-42) (variable ancestor) (values bob . dave)",
            "(projection-failure malformed-values)",
        ),
    ] {
        let source = format!(
            "(перетворити-підстановки-пролог-на-факти-даталог (як-є (prolog-substitution-observation {fields})))"
        );
        let actual = eval(&source, &mut s);
        assert_eq!(
            actual, expected,
            "test_id=prolog-datalog-shape layer=SENS-eval case={case} input={source} expected={expected} actual={actual}"
        );
    }
}
