use sens::{installed_capabilities, load_core_library, load_tcp_library, Session, Value};
use sens_host::install;

#[test]
fn tcp_public_bindings_are_language_owned_over_raw_mechanisms() {
    install();
    let installed = installed_capabilities();
    assert!(installed.iter().any(|name| name == "tcp-listen-raw"));
    assert!(installed.iter().any(|name| name == "tcp-read-raw"));
    assert!(installed.iter().any(|name| name == "tcp-write-raw"));
    assert!(!installed.iter().any(|name| name == "tcp-listen"));
    assert!(!installed.iter().any(|name| name == "tcp-read"));
    assert!(!installed.iter().any(|name| name == "tcp-write"));

    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    assert!(session.environment.get("tcp-listen").is_none());
    assert!(session.environment.get("tcp-read").is_none());
    assert!(session.environment.get("tcp-write").is_none());

    load_tcp_library(&mut session).unwrap();
    assert!(matches!(
        session.environment.get("tcp-listen"),
        Some(Value::Closure(_))
    ));
    assert!(matches!(
        session.environment.get("tcp-read"),
        Some(Value::Closure(_))
    ));
    assert!(matches!(
        session.environment.get("tcp-write"),
        Some(Value::Closure(_))
    ));
}
