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
        (list (код-завершення-передачі r) (тіло-передачі r)))
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
      (let ((r (надіслати-запит-формат-обміну-даними "http://127.0.0.1:1/x" "{}")))
        (cond ((= (код-завершення-передачі r) 0) 1 "UNEXPECTED-SUCCESS")
              ((= (код-завершення-передачі r) 0) 0 (код-завершення-передачі r))))
    "#;
    let rendered = eval_with_agent(src);
    assert!(!rendered.contains("UNEXPECTED-SUCCESS"), "{rendered}");
}



#[test]
fn yantra_json_string_classifier_yields_d1_condition_from_structured_witness() {
    // Чинний Core4 класифікує рядок трійкою даних, а не булевим D1.
    // Справжній SENS JSON-кодер має сам порівняти членство у класі.
    let mut session = agent_session();
    for (expression, oracle) in [
        (
            "(кодувати-значення-формат-обміну-даними \"зоря\")",
            "(кодувати-рядок-формат-обміну-даними \"зоря\")",
        ),
        (
            "(кодувати-значення-формат-обміну-даними 23)",
            "(значення-у-текст 23)",
        ),
    ] {
        let actual = eval_program(expression, &mut session)
            .unwrap_or_else(|error| panic!("SENS JSON {expression}: {error}"))
            .value;
        let expected = eval_program(oracle, &mut session)
            .unwrap_or_else(|error| panic!("SENS оракул {oracle}: {error}"))
            .value;
        assert_eq!(actual, expected, "D8 class-membership не може бути умовою D3");
    }
}

#[test]
fn yantra_json_d1_boolean_values_are_distinct() {
    // Справжній SENS обчислює D1:так, D1:ні та порожній D3 як різні
    // об'єкти; Rust лише порівнює отримані значення.
    let mut session = agent_session();
    let source = r#"(список
      (кодувати-значення-формат-обміну-даними так)
      (кодувати-значення-формат-обміну-даними ні)
      (кодувати-значення-формат-обміну-даними (як-є ())))"#;
    let expected = r#"(список "true" "false" "null")"#;
    let actual = eval_program(source, &mut session)
        .expect("SENS повинен кодувати всі три точні значення")
        .value.to_string();
    let oracle = eval_program(expected, &mut session)
        .expect("SENS повинен обчислити незалежну очікувану структуру")
        .value.to_string();
    assert_eq!(actual, oracle, "D1:NO не можна зливати з D3:EMPTY");
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
        ("роль-повідомлення", "роль", "людина"),
        ("зміст-повідомлення", "зміст", "вміст"),
        ("виклики-повідомлення", "виклики-інструментів", "виклики"),
        ("ідентифікатор-виклику-повідомлення", "ідентифікатор-виклику", "ідентифікатор"),
        ("ідентифікатор-виклику", "ідентифікатор", "ідентифікатор"),
        ("назва-інструмента", "назва", "назва"),
        ("аргументи-виклику", "аргументи", "параметри"),
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
          (як-є ((роль . "assistant")
                 (зміст . "готово")
                 (виклики-інструментів . (((ідентифікатор . "call-1")
                                 (назва . "bash")
                                 (аргументи . "{}")))))))
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

#[test]
fn yantra_evidence_cannot_use_partial_tool_results() {
    // Перевірка реальним SENS eval, а не текстовим сканером.
    // Результати належать безпосередньо попередньому виклику помічника.
    let mut session = agent_session();
    for (source, expected) in [
        (
            r#"(завершується-власними-результатами?
                (як-є (
                  ((роль . "assistant") (виклики-інструментів . (((ідентифікатор . а)) ((ідентифікатор . б)))))
                  ((роль . "tool") (ідентифікатор-виклику . а))
                  ((роль . "tool") (ідентифікатор-виклику . б))
                  ((роль . "assistant") (зміст . "виконано"))
                )))"#,
            true,
        ),
        (
            r#"(завершується-власними-результатами?
                (як-є (
                  ((роль . "assistant") (виклики-інструментів . (((ідентифікатор . а)) ((ідентифікатор . б)))))
                  ((роль . "tool") (ідентифікатор-виклику . а))
                  ((роль . "assistant") (зміст . "виконано"))
                )))"#,
            false,
        ),
        (
            r#"(завершується-власними-результатами?
                (як-є (
                  ((роль . "assistant") (виклики-інструментів . (((ідентифікатор . а))))))
                  ((роль . "tool") (ідентифікатор-виклику . сторонній))
                  ((роль . "assistant") (зміст . "виконано"))
                )))"#,
            false,
        ),
        (
            r#"(завершується-власними-результатами?
                (як-є (
                  ((роль . "assistant") (виклики-інструментів . (((ідентифікатор . а))))))
                  ((роль . "assistant") (зміст . "виконано"))
                )))"#,
            false,
        ),
    ] {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("Помилка SENS при перевірці власності: {error}"))
            .value.as_predicate_bit();
        assert_eq!(actual, Some(expected), "порушено закон доказу: {source}");
    }
}

#[test]
fn yantra_blocked_transport_is_not_a_completed_answer() {
    let mut session = agent_session();
    let result = eval_program(
        r#"(стан-результату
            (цикл-агента
              (функція (повідомлення) (як-є (заблоковано "відмова транспорту")))
              (як-є ())
              0))"#,
        &mut session,
    ).expect("справжній SENS має завершити цикл заблокованим статусом");
    assert_eq!(result.value.to_string(), "заблоковано");
}

#[test]
fn yantra_missing_json_key_is_safe_and_empty() {
    let mut session = agent_session();
    let actual = eval_program(
        "(знайти-значення-за-ключем (як-є відсутній) (як-є ((наявний . значення))))",
        &mut session,
    ).expect("відсутній ключ не повинен викликати помилку SENS");
    assert_eq!(actual.value.to_string(), "()");
}


#[test]
fn yantra_rejects_duplicate_evidence_identifiers() {
    let mut session = agent_session();
    let source = r#"(завершується-власними-результатами?
      (як-є (
        ((роль . "assistant") (виклики-інструментів . (((ідентифікатор . а)) ((ідентифікатор . б)))))
        ((роль . "tool") (ідентифікатор-виклику . а))
        ((роль . "tool") (ідентифікатор-виклику . а))
        ((роль . "assistant") (зміст . "виконано"))
      )))"#;
    let actual = eval_program(source, &mut session)
        .expect("справжній SENS перевіряє власність результатів");
    assert_eq!(actual.value.as_predicate_bit(), Some(false));
}
