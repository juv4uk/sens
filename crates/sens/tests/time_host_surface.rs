use sens::{load_core_library, load_time_library, Session, Value};

#[test]
fn raw_host_time_surface_is_small_and_semantic_names_are_absent() {
    let session = Session::default();

    for name in [
        "mono-ns",
        "unix-time-now",
        "ntp-query-raw",
        "timezone-declarations-raw",
    ] {
        assert!(
            matches!(session.environment.get(name), Some(Value::Builtin(_))),
            "{name} must remain a raw host builtin"
        );
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
        assert!(
            matches!(session.environment.get(name), Some(Value::Builtin(_))),
            "{name} must stay the underlying raw host mechanism"
        );
    }
}
