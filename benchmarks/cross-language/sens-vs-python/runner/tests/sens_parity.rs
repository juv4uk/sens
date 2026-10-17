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
    let expressions = parse_exact_domain_source(&source("json-parse-serialize.call.lisp"))
        .expect("explicit D9 JSON identity is accepted by the exact reader");
    let error = eval_parsed_expressions(&expressions, &mut session)
        .expect_err("D9 JSON parse currently has no callable runtime mechanism");
    assert!(
        error.message.contains("D9") || error.message.contains("mechanism"),
        "unexpected JSON mechanism blocker: {error:?}"
    );
}
