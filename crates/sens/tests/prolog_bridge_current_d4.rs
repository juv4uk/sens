//! Виконувані свідки мосту Пролог → Даталог на чинному SENS D4.
//! Протокольні мітки — цитовані дані, не викличні голови Rust.
use sens::{eval_program, load_core_library, Session};

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("чинна бібліотека Core SENS");
    eval_program(
        include_str!("../../../lib/bridge/prolog-to-datalog.lisp"),
        &mut session,
    )
    .expect("завантажити іменований D4 міст справжнім SENS");
    session
}

fn eval(source: &str, session: &mut Session) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| {
            panic!("test_id=prolog-d10-d4 layer=real-SENS input={source} actual={error}")
        })
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
        "(projection-result (projection prolog-substitutions-to-datalog-facts) (source-ref observation-42) (facts ((ancestor bob) (ancestor dave) (ancestor carol))))",
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
        eval(
            "(перетворити-підстановки-пролог-на-факти-даталог (як-є ()))",
            &mut s
        ),
        "(projection-failure malformed-observation)",
    );
}

#[test]
fn d4_bridge_rejects_wrong_or_nonatomic_observation_head() {
    // Справжній SENS виконує негативи. Перенесення тих самих полів під
    // стороннім заголовком НЕ має створювати трьох фальшивих фактів.
    let mut state = session();
    for observation in [
        "(other-observation (source-ref observation-42) (variable ancestor) (values bob))",
        "((unadmitted-head) (source-ref observation-42) (variable ancestor) (values bob))",
    ] {
        let input =
            format!("(перетворити-підстановки-пролог-на-факти-даталог (як-є {observation}))");
        assert_eq!(
            eval(&input, &mut state),
            "(projection-failure malformed-observation)",
            "test_id=prolog-exact-observation-head layer=real-SENS input={input}",
        );
    }
}

#[test]
fn d4_bridge_d1_field_shape_rejects_truncated_extra_and_dotted_rows() {
    // Нативний SENS оцінює чинне Lisp-визначення, Rust лише зіставляє D1.
    let mut state = session();
    for (row, expected) in [
        ("(source-ref observation-42)", "1"),
        ("(source-ref)", "0"),
        ("(source-ref observation-42 extra)", "0"),
        ("(source-ref observation-42 . extra)", "0"),
        ("(variable ancestor)", "1"),
        ("(variable)", "0"),
        ("(variable ancestor extra)", "0"),
    ] {
        let program = format!("(пролог-рядок-рівно-одне-значення? (як-є {row}))");
        assert_eq!(
            eval(&program, &mut state),
            expected,
            "test_id=prolog-d1-row-shape layer=real-SENS input={row}",
        );
    }
}

#[test]
fn d4_bridge_returns_named_errors_for_incomplete_or_surplus_fields() {
    let mut state = session();
    for (fields, expected) in [
        (
            "(source-ref) (variable ancestor) (values bob)",
            "(projection-failure malformed-source-ref)",
        ),
        (
            "(source-ref observation-42 extra) (variable ancestor) (values bob)",
            "(projection-failure malformed-source-ref)",
        ),
        (
            "(source-ref observation-42) (variable) (values bob)",
            "(projection-failure malformed-variable-role)",
        ),
        (
            "(source-ref observation-42) (variable ancestor extra) (values bob)",
            "(projection-failure malformed-variable-role)",
        ),
    ] {
        let program = format!(
            "(перетворити-підстановки-пролог-на-факти-даталог (як-є (prolog-substitution-observation {fields})))"
        );
        assert_eq!(
            eval(&program, &mut state),
            expected,
            "test_id=prolog-named-error layer=real-SENS input={fields}",
        );
    }
}

#[test]
fn d4_bridge_keeps_empty_values_as_valid_empty_facts() {
    let mut state = session();
    let actual = eval(
        "(перетворити-підстановки-пролог-на-факти-даталог (як-є (prolog-substitution-observation (source-ref observation-42) (variable ancestor) (values))))",
        &mut state,
    );
    assert_eq!(
        actual,
        "(projection-result (projection prolog-substitutions-to-datalog-facts) (source-ref observation-42) (facts ()))",
        "test_id=prolog-zero-facts layer=real-SENS: порожні факти допустимі",
    );
}
