use sens::{load_core_library, load_time_library, Session, Value};


/// Назва з таблиці функцій веде до коду, що має примітив (хостовий механізм).
fn is_raw_primitive(name: &str) -> bool {
    sens::semantic_registry_export::semantic_id_for_admitted_surface(name)
        .and_then(sens::semantic_registry_export::function_role)
        == Some("primitive")
}

#[test]
fn raw_host_time_surface_is_small_and_semantic_names_are_absent() {
    let session = Session::default();

    for name in [
        "mono-ns",
        "unix-time-now",
        "ntp-query-raw",
        "timezone-declarations-raw",
    ] {
        // Після #1477 сирі хостові механізми — примітиви за кодом СЕНС,
        // а не прив'язки Value::Builtin за назвою.
        assert!(is_raw_primitive(name), "{name} must remain a raw host primitive");
    }

    for name in ["mono-ms", "utc-now", "internet-time-sync", "timezone-detect"] {
        assert!(
            session.environment.get(name).is_none(),
            "{name} is semantic policy and must not reappear in the root host surface"
        );
    }
}

#[test]
fn time_library_builds_public_meanings_over_raw_host_observations() {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    load_time_library(&mut session).unwrap();

    for name in ["mono-ms", "utc-now", "internet-time-sync", "timezone-detect"] {
        assert!(
            matches!(session.environment.get(name), Some(Value::Closure(_))),
            "{name} must be language-owned after lib/time.my loads"
        );
    }

    for name in [
        "mono-ns",
        "unix-time-now",
        "ntp-query-raw",
        "timezone-declarations-raw",
    ] {
        assert!(is_raw_primitive(name), "{name} must stay the underlying raw host mechanism");
    }
}
