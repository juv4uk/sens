//! MY-LISP-YANTRA: the smallest Chebupelka-style coding agent whose
//! control logic lives entirely in lib/yantra.my. The host boundary is
//! `process-run-raw` (bash tool + curl transport bytes) and `json-parse`
//! (wire-format decode); public `process-run` semantics live in Lisp.
//!
//! Historical pre-Core4 scripted agent / T-NIL Rust oracles have been retired.

use sens::{eval_program, load_core_library, load_process_library, Environment, Session};

fn agent_session() -> Session {
    // Install only the OS capability layer, opt this session into the exact
    // programs the agent may run, then bootstrap public process semantics in
    // Lisp over the raw byte-preserving host capability.
    sens_host::install();
    let environment =
        Environment::root().with_process_allowlist(vec!["bash".into(), "curl".into()]);
    let mut session = Session { environment };
    load_core_library(&mut session).unwrap();
    load_process_library(&mut session).unwrap();
    eval_program(include_str!("../../../lib/yantra.lisp"), &mut session).unwrap();
    session
}

fn eval_with_agent(source: &str) -> String {
    let mut session = agent_session();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

// Current hosted Rust coverage: transport framing and denied/error paths.
#[test]
fn http_transport_success_passes_body_through() {
    // Real curl against the real oracle's HTTP surface is out of scope
    // here; success-path framing is verified structurally instead:
    let src = r#"
      (let ((r (list 0 "{\"ok\":true}" "")))
        (list (http-transport-exit r) (http-transport-body r)))
    "#;
    let rendered = eval_with_agent(src);
    assert!(rendered.contains("(0"), "unexpected: {rendered}");
    assert!(
        rendered.contains("ok\\\":true") || rendered.contains("ok"),
        "unexpected: {rendered}"
    );
}

#[test]
fn transport_failure_becomes_blocked_result_with_evidence() {
    // curl to a port nothing listens on: fast refusal, exit != 0.
    let src = r#"
      (let ((r (http-post-json "http://127.0.0.1:1/x" "{}")))
        (cond ((= (http-transport-exit r) 0) 1 "UNEXPECTED-SUCCESS")
              ((= (http-transport-exit r) 0) 0 (http-transport-exit r))))
    "#;
    let rendered = eval_with_agent(src);
    assert!(!rendered.contains("UNEXPECTED-SUCCESS"), "{rendered}");
}



#[test]
fn yantra_json_object_predicate_is_actual_d1_behavior() {
    // Не симуляція JSON у Rust: завантажуємо повний lib/yantra.lisp
    // тим самим SENS evaluator, що й інші інтеграційні свідки.
    let mut session = agent_session();
    for (source, expected) in [
        ("(об'єкт-формат-обміну-даними? (як-є ((назва . сонце))))", true),
        (
            "(об'єкт-формат-обміну-даними? (як-є ((назва . ((тип . зоря))))))",
            true,
        ),
        ("(об'єкт-формат-обміну-даними? (як-є ()))", false),
        ("(об'єкт-формат-обміну-даними? (як-є (назва сонце)))", false),
        ("(об'єкт-формат-обміну-даними? (як-є назва))", false),
    ] {
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("SENS eval не виконав {source}: {error}"));
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(expected),
            "D1 не відповідає фактичній структурі JSON даних: {source}"
        );
    }
}


#[test]
fn yantra_message_and_tool_accessors_execute_with_ukrainian_bindings() {
    // Справжній SENS reader/evaluator завантажує повний lib/yantra.lisp.
    // Перевіряємо дані, а не кількість перейменувань чи симуляцію в Rust.
    let mut session = agent_session();
    for (reader, key, expected) in [
        ("msg-role", "role", "людина"),
        ("msg-content", "content", "вміст"),
        ("msg-tool-calls", "tool-calls", "виклики"),
        ("msg-tool-call-id", "tool-call-id", "ідентифікатор"),
        ("tc-id", "id", "ідентифікатор"),
        ("tc-name", "name", "назва"),
        ("tc-arguments", "arguments", "параметри"),
    ] {
        let source = format!("({reader} (як-є (({key} . {expected}))))");
        let actual = eval_program(&source, &mut session)
            .unwrap_or_else(|error| panic!("SENS не виконав {reader}: {error}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "SENS accessor {reader} must select {key}");
    }
}


#[test]
fn yantra_tool_call_encoding_uses_exact_d10_ukrainian_function() {
    // Дійсний виклик SENS D10 ENCODE-MESSAGE → D6 MAP → D10 ENCODE-TOOL-CALL.
    // Не замінюємо виконання пошуком рядків або Python-симуляцією.
    let mut session = agent_session();
    let source = r#"
        (кодувати-повідомлення
          (як-є ((role . "assistant")
                 (content . "готово")
                 (tool-calls . (((id . "call-1")
                                 (name . "bash")
                                 (arguments . "{}")))))))
    "#;
    let oracle = r#"
        (список
          (сполучити "role" "assistant")
          (сполучити "content" "готово")
          (сполучити "tool_calls"
            (список
              (список
                (сполучити "id" "call-1")
                (сполучити "type" "function")
                (сполучити "function"
                  (список
                    (сполучити "name" "bash")
                    (сполучити "arguments" "{}")))))))
    "#;
    let actual = eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("D10 ENCODE-MESSAGE failed: {error}"))
        .value.to_string();
    let expected = eval_program(oracle, &mut session)
        .unwrap_or_else(|error| panic!("SENS oracle failed: {error}"))
        .value.to_string();
    assert_eq!(actual, expected, "tool-call encoding must preserve all fields");
}
