use sens::{eval_program, load_core_library, load_process_library, Session, Value};

fn process_session() -> Session {
    sens_host::install();
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    load_process_library(&mut session).unwrap();
    session
}

#[test]
fn process_result_text_decoding_is_language_owned() {
    let mut session = process_session();
    let result = eval_program(
        "(process-result->text (quote (process-result 0 (65 194 162) (226 130 172))))",
        &mut session,
    )
    .expect("pure process-result interpretation should succeed");

    assert_eq!(
        result.value.to_string(),
        "(decoded-process 0 \"A¢\" \"€\")"
    );
}

#[test]
fn process_result_text_rejects_invalid_utf8_without_lossy_replacement() {
    let mut session = process_session();
    let result = eval_program(
        "(process-result->text (quote (process-result 0 (255) ())))",
        &mut session,
    )
    .expect("invalid UTF-8 should be a language-level rejection value");

    assert_eq!(result.value.to_string(), "(rejected stdout-invalid-utf8)");
}

#[test]
fn process_run_text_composes_raw_host_bytes_with_lisp_utf8() {
    let mut session = process_session();
    let source = r#"
        (process-run-text
          "python3"
          (quote ("-c"
                   "import sys; sys.stdout.buffer.write('€'.encode()); sys.stderr.buffer.write('¢'.encode())")))
    "#;

    let result = eval_program(source, &mut session).expect("process text adapter should succeed");
    assert_eq!(result.value.to_string(), "(decoded-process 0 \"€\" \"¢\")");
}

#[test]
fn public_process_run_binding_is_already_a_lisp_closure() {
    let mut session = process_session();
    assert!(matches!(
        session.environment.get("process-run"),
        Some(Value::Closure(_))
    ));

    // The host never registers a `process-run` capability (see
    // `process_surface.rs`'s `host_installs_only_the_raw_process_capability`);
    // `process-run` is only ever this Lisp closure. Capture the environment
    // binding under a capability-free spelling to prove the closure itself
    // already implements the public compatibility result shape through
    // `process-run-raw`.
    let source = r#"
        (def language-process-run process-run)
        (language-process-run
          "python3"
          (quote ("-c" "print('language-owned')")))
    "#;
    let result = eval_program(source, &mut session).expect("language-owned process closure should run");
    assert_eq!(result.value.to_string(), "(0 \"language-owned\\n\" \"\")");
}
