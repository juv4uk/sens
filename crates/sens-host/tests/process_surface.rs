use sens::{capability_installed, load_core_library, load_process_library, Session, Value};

#[test]
fn host_installs_only_the_raw_process_capability() {
    sens_host::install();

    assert!(capability_installed("process-run-raw"));
    assert!(
        !capability_installed("process-run"),
        "public process semantics must not return to the host registry"
    );
}

#[test]
fn public_process_run_appears_only_as_a_language_binding() {
    sens_host::install();
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();

    assert!(session.environment.get("process-run").is_none());
    load_process_library(&mut session).unwrap();
    assert!(matches!(
        session.environment.get("process-run"),
        Some(Value::Closure(_))
    ));
    assert!(!capability_installed("process-run"));
}
