//! Живі SENS-свідки обчислення D1 у сценаріях, без TCP або Python-eval.
//! Виконуємо справжні визначення з їхніх .lisp файлів, не копію логіки в Rust.
use sens::{
    eval_parsed_expressions, eval_program, load_core_library, parse_mixed_exact_domain, Session,
};

fn install_section(source: &str, begin: &str, end: &str, session: &mut Session) {
    let from = source
        .find(begin)
        .expect("test_id=script-d1 source definition exists");
    let to = source[from..]
        .find(end)
        .expect("test_id=script-d1 definition boundary");
    let fragment = &source[from..from + to];
    let forms = parse_mixed_exact_domain(fragment)
        .unwrap_or_else(|error| panic!("test_id=script-d1 layer=reader input={begin}: {error}"));
    eval_parsed_expressions(&forms, session)
        .unwrap_or_else(|error| panic!("test_id=script-d1 layer=SENS define={begin}: {error}"));
}

#[test]
fn oracle_batch_filters_real_quoted_fixtures_with_d1_predicates() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("test_id=oracle-batch-d1 SENS core");
    let source = include_str!("../../../scripts/oracle-batch.lisp");
    install_section(
        source,
        "(визначити вибрати-лише-приклади",
        "\n; Один запис інвентарю",
        &mut session,
    );
    for (input, expected) in [
        ("(як-є ())", "(як-є ())"),
        ("(як-є ((note a)))", "(як-є ())"),
        (
            "(як-є ((note a) (fixture b) ignored (fixture c)))",
            "(як-є ((fixture b) (fixture c)))",
        ),
    ] {
        let observed_source = format!("(вибрати-лише-приклади {input})");
        let observed = eval_program(&observed_source, &mut session).unwrap_or_else(|error| {
            panic!("test_id=oracle-batch-d1 layer=SENS input={input} actual=ERROR {error}")
        });
        let expected_value = eval_program(expected, &mut session).unwrap_or_else(|error| {
            panic!("test_id=oracle-batch-d1 expected quoted data: {error}")
        });
        assert_eq!(
            observed.value, expected_value.value,
            "test_id=oracle-batch-d1 layer=SENS input={input} expected={expected}"
        );
    }
}

#[test]
fn function_listing_empty_input_evaluates_real_d1_without_textual_true() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("test_id=gen-functions-d1 SENS core");
    let source = include_str!("../../../scripts/gen-functions.lisp");
    install_section(
        source,
        "(визначити видати-пару",
        "\n(видати вбудовані)",
        &mut session,
    );
    let observed = eval_program("(видати (як-є ()))", &mut session)
        .expect("test_id=gen-functions-d1 layer=SENS empty list");
    let expected =
        eval_program("(як-є ())", &mut session).expect("test_id=gen-functions-d1 quoted D3 empty");
    assert_eq!(
        observed.value, expected.value,
        "test_id=gen-functions-d1 layer=SENS input=() expected=D3:000 empty"
    );
}

#[test]
fn oracle_batch_selects_cli_peer_with_live_sens_cond() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("test_id=oracle-batch-peer SENS core");
    let source = include_str!("../../../scripts/oracle-batch.lisp");
    install_section(
        source,
        "(визначити адреса-оракула",
        "\n(визначити обчислити-через-оракул",
        &mut session,
    );

    // Відсутній аргумент: старий вузол зберігається, D1 вирішує першу гілку.
    session.environment.define("*argv*", sens::Value::Nil);
    let default_peer = eval_program("(адреса-оракула)", &mut session)
        .expect("test_id=oracle-batch-peer layer=SENS default D1");
    assert_eq!(
        default_peer.value,
        sens::Value::String(std::rc::Rc::from("100.113.68.50")),
        "test_id=oracle-batch-peer input=empty-argv expected=old-peer",
    );

    // Явний локальний вузол: друга гілка SENS читає перший елемент списку.
    session.environment.define(
        "*argv*",
        sens::Value::list([sens::Value::String(std::rc::Rc::from("127.0.0.1"))]),
    );
    let selected_peer = eval_program("(адреса-оракула)", &mut session)
        .expect("test_id=oracle-batch-peer layer=SENS explicit D1");
    assert_eq!(
        selected_peer.value,
        sens::Value::String(std::rc::Rc::from("127.0.0.1")),
        "test_id=oracle-batch-peer input=local-argv expected=local-peer",
    );
}
