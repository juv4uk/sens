use sens::{
    eval_parsed_expressions, load_core_library, parse_exact_domain_source,
    parse_mixed_exact_domain, Session, Value,
};
use std::{fs, path::PathBuf, rc::Rc};

fn root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..")
}

fn source(relative: &str) -> String {
    fs::read_to_string(root().join("sens").join(relative)).unwrap()
}

fn evaluate_source(session: &mut Session, text: &str) -> Value {
    let expressions =
        parse_mixed_exact_domain(text).expect("current mixed exact-domain source parses");
    eval_parsed_expressions(&expressions, session)
        .expect("current SENS evaluator executes workload source")
        .value
}

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("current Core4 loads");
    session
}

#[test]
fn current_sens_fib_returns_expected_d24_result() {
    let mut session = session();
    evaluate_source(&mut session, &source("fib.setup.lisp"));
    let result = evaluate_source(&mut session, &source("fib.call.lisp"));
    assert_eq!(result.to_string(), "987");
}

#[test]
fn numeric_base_cases_are_executed_by_sens_not_d3_eq() {
    // Обчислює реальний SENS. D24+ умови виконуються D5 «менше?»,
    // а не D3 «тотожне?» над математичними значеннями.
    for (setup, witnesses) in [
        (
            "fib.setup.lisp",
            vec![
                ("(фібоначчі 0)", "0"),
                ("(фібоначчі 1)", "1"),
                ("(фібоначчі 2)", "1"),
                ("(фібоначчі 3)", "2"),
            ],
        ),
        (
            "ackermann.setup.lisp",
            vec![
                ("(аккерман 0 3)", "4"),
                ("(аккерман 1 0)", "2"),
            ],
        ),
        (
            "binary-trees.setup.lisp",
            vec![
                // Листок чинної програми — точний D3 NIL, а не D7-текст.
                ("(створити-дерево 0)", "()"),
                ("(атом? (створити-дерево 0))", "1"),
                ("(перевірити-дерево (створити-дерево 0))", "1"),
                ("(перевірити-дерево (створити-дерево 1))", "3"),
                ("(повторити-дерева 0 0 0)", "0"),
            ],
        ),
    ] {
        let mut evaluator = session();
        evaluate_source(&mut evaluator, &source(setup));
        for (call, expected) in witnesses {
            let value = evaluate_source(&mut evaluator, call);
            assert_eq!(value.to_string(), expected, "{setup}: {call}");
        }
    }
}

#[test]
fn current_sens_ackermann_returns_expected_d24_result() {
    let mut session = session();
    evaluate_source(&mut session, &source("ackermann.setup.lisp"));
    let result = evaluate_source(&mut session, &source("ackermann.call.lisp"));
    assert_eq!(result.to_string(), "61");
}

#[test]
fn current_sens_binary_trees_match_pinned_n10_checks() {
    let mut session = session();
    evaluate_source(&mut session, &source("binary-trees.setup.lisp"));
    let result = evaluate_source(&mut session, &source("binary-trees.call.lisp"));
    assert_eq!(result.to_string(), "(4095 31744 32512 32704 32752 2047)");
}

#[test]
fn json_parse_is_blocked_without_an_admitted_d9_call_mechanism() {
    let mut session = session();
    let document = fs::read_to_string(root().join("fixtures/json-small.json")).unwrap();
    session
        .environment
        .define("json-input", Value::String(Rc::from(document.as_str())));
    let current = source("json-parse-serialize.call.lisp");
    assert!(
        current.contains("(формат-обміну-даними-розібрати json-input)"),
        "чинне D9 джерело мусить використовувати ратифіковану українську поверхню"
    );
    let expressions = parse_exact_domain_source(&current)
        .expect("українське D9 джерело приймається чинним exact reader");
    let lowered = sens::lower_program(&expressions);
    assert!(
        matches!(&lowered[0].kind,
            sens::ExprKind::DomainCall(identity, _)
                if identity.width() == 9 && identity.packed_bits() == 0b110100100),
        "D9 JSON-PARSE має зберігати точний ратифікований код без SID8"
    );
    let error = eval_parsed_expressions(&expressions, &mut session)
        .expect_err("наявність ідентичності D9 не означає runtime-допуску JSON");
    assert!(
        !error.message.is_empty(),
        "відсутній D9 JSON-механізм потребує явної SENS-діагностики"
    );
}
