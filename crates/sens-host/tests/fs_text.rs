use sens::{
    capability_installed, eval_program, load_core_library, load_fs_library, Session, Value,
};
use std::{
    fs,
    path::{Path, PathBuf},
    time::{SystemTime, UNIX_EPOCH},
};

fn unique_path(label: &str) -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("clock after unix epoch")
        .as_nanos();
    std::env::temp_dir().join(format!("sens-{label}-{}-{nonce}", std::process::id()))
}

fn lisp_path(path: &Path) -> String {
    path.to_str()
        .expect("test path must be utf-8")
        .replace('\\', "/")
        .replace('"', "\\\"")
}

fn fs_session() -> Session {
    sens_host::install();
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    load_fs_library(&mut session).unwrap();
    session
}

/// Host registers only current raw byte/text-boundary capabilities; public
/// Ukrainian `читати-файл`/`записати-файл` are language-owned.
#[test]
fn host_installs_only_the_raw_file_capabilities() {
    sens_host::install();

    assert!(capability_installed("читати-сирий-текст-файла"));
    assert!(capability_installed("записати-байти-файла"));
    assert!(
        !capability_installed("читати-файл"),
        "public read-file semantics must not return to the host registry"
    );
    assert!(
        !capability_installed("записати-файл"),
        "public write-file semantics must not return to the host registry"
    );
}

#[test]
fn public_read_file_and_write_file_appear_only_as_language_bindings() {
    sens_host::install();
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();

    assert!(session.environment.get("читати-файл").is_none());
    assert!(session.environment.get("записати-файл").is_none());
    load_fs_library(&mut session).unwrap();
    assert!(matches!(
        session.environment.get("читати-файл"),
        Some(Value::Closure(_))
    ));
    assert!(matches!(
        session.environment.get("записати-файл"),
        Some(Value::Closure(_))
    ));
    assert!(!capability_installed("читати-файл"));
    assert!(!capability_installed("записати-файл"));
}

#[test]
fn write_file_then_read_file_round_trips_utf8_text() {
    let mut session = fs_session();
    let path = unique_path("fs-text-roundtrip");
    let source = format!(
        r#"(список (записати-файл "{p}" "hello, свiт, €") (читати-файл "{p}"))"#,
        p = lisp_path(&path)
    );

    eval_program(&source, &mut session).expect("filesystem transport must execute");
    assert_eq!(
        fs::read_to_string(&path).expect("host file bytes must be observable"),
        "hello, свiт, €"
    );

    fs::remove_file(&path).ok();
}

/// Invalid UTF-8 in a file is no longer a raw Rust IO error -- it is the
/// same structured rejection value `utf8-decode-string` already produces for
/// process/TCP bytes, mirroring
/// `process_text.rs`'s `process_result_text_rejects_invalid_utf8_without_lossy_replacement`.
#[test]
fn read_file_rejects_invalid_utf8_without_lossy_replacement() {
    let mut session = fs_session();
    let path = unique_path("fs-text-invalid-utf8");
    fs::write(&path, [0xFFu8]).unwrap();

    let source = format!(r#"(читати-файл "{}")"#, lisp_path(&path));
    eval_program(&source, &mut session)
        .expect("host file read path should remain executable");
    assert_eq!(fs::read(&path).expect("byte fixture persists"), [0xFFu8]);

    fs::remove_file(&path).ok();
}
