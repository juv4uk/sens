use sens::{eval_program, load_core_library, load_fs_library, Environment, ErrorKind, Session};
use sens_host::install;
use std::{
    fs,
    path::{Path, PathBuf},
    time::{SystemTime, UNIX_EPOCH},
};

fn unique_dir(label: &str) -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("clock after unix epoch")
        .as_nanos();
    let path = std::env::temp_dir().join(format!("sens-{label}-{}-{nonce}", std::process::id()));
    fs::create_dir_all(&path).expect("create temp test directory");
    path
}

fn lisp_path(path: &Path) -> String {
    path.to_str()
        .expect("test path must be utf-8")
        .replace('\\', "/")
        .replace('"', "\\\"")
}

fn session(environment: Environment) -> Session {
    install();
    let mut session = Session { environment };
    // `read-file`/`write-file` are now language-owned (lib/fs.lisp) over the
    // raw `read-file-bytes`/`write-file-bytes` host capabilities; every test
    // in this file needs them resolvable, mirroring load_process_library's
    // use in the process/tcp scoping tests.
    load_core_library(&mut session).expect("core library must load for scoping tests");
    load_fs_library(&mut session).expect("fs library must load for scoping tests");
    session
}

fn assert_scope_denied(error: sens::LanguageError, operation: &str) {
    assert_eq!(error.kind, ErrorKind::InvalidForm);
    assert!(
        error.message.contains("outside this session's capability scope"),
        "{operation} should fail at policy boundary, got: {}",
        error.message
    );
}

#[test]
fn trusted_default_remains_unrestricted_for_filesystem() {
    let root = unique_dir("scope-default");
    let path = root.join("visible.txt");
    fs::write(&path, "visible").unwrap();

    let mut session = session(Environment::root());
    let result = eval_program(
        &format!(r#"(read-file "{}")"#, lisp_path(&path)),
        &mut session,
    )
    .expect("trusted default should retain unrestricted host read behavior");
    assert_eq!(result.value.to_string(), "\"visible\"");

    fs::remove_dir_all(root).ok();
}

#[test]
fn read_scope_allows_inside_and_denies_outside() {
    let allowed = unique_dir("scope-read-allowed");
    let outside = unique_dir("scope-read-outside");
    let inside_file = allowed.join("inside.txt");
    let outside_file = outside.join("outside.txt");
    fs::write(&inside_file, "inside").unwrap();
    fs::write(&outside_file, "outside").unwrap();

    let env = Environment::root().with_fs_read_roots(vec![allowed.clone()]);
    let mut session = session(env);

    eval_program(
        &format!(r#"(read-file "{}")"#, lisp_path(&inside_file)),
        &mut session,
    )
    .expect("inside allowed read root should succeed");

    let error = eval_program(
        &format!(r#"(read-file "{}")"#, lisp_path(&outside_file)),
        &mut session,
    )
    .expect_err("outside read root must be denied before filesystem read");
    assert_scope_denied(error, "read-file");

    fs::remove_dir_all(allowed).ok();
    fs::remove_dir_all(outside).ok();
}

#[test]
fn write_scope_allows_new_file_inside_and_denies_outside() {
    let allowed = unique_dir("scope-write-allowed");
    let outside = unique_dir("scope-write-outside");
    let inside_file = allowed.join("new.txt");
    let outside_file = outside.join("new.txt");

    let env = Environment::root().with_fs_write_roots(vec![allowed.clone()]);
    let mut session = session(env);

    eval_program(
        &format!(r#"(write-file "{}" "inside")"#, lisp_path(&inside_file)),
        &mut session,
    )
    .expect("new file directly under allowed write root should succeed");
    assert_eq!(fs::read_to_string(&inside_file).unwrap(), "inside");

    let error = eval_program(
        &format!(r#"(write-file "{}" "outside")"#, lisp_path(&outside_file)),
        &mut session,
    )
    .expect_err("outside write root must be denied before file creation");
    assert_scope_denied(error, "write-file");
    assert!(!outside_file.exists(), "denied write must not create a file");

    fs::remove_dir_all(allowed).ok();
    fs::remove_dir_all(outside).ok();
}

#[test]
fn load_cannot_bypass_read_scope() {
    let allowed = unique_dir("scope-load-allowed");
    let outside = unique_dir("scope-load-outside");
    let source = outside.join("escape.lisp");
    fs::write(&source, "(def escaped-through-load 42)").unwrap();

    let env = Environment::root().with_fs_read_roots(vec![allowed.clone()]);
    let mut session = session(env);
    let error = eval_program(
        &format!(r#"(load "{}")"#, lisp_path(&source)),
        &mut session,
    )
    .expect_err("load must obey the same read scope as read-file");
    assert_scope_denied(error, "load");
    assert!(
        session.environment.get("escaped-through-load").is_none(),
        "denied load must not mutate the session"
    );

    fs::remove_dir_all(allowed).ok();
    fs::remove_dir_all(outside).ok();
}

#[cfg(unix)]
#[test]
fn symlink_inside_allowed_root_cannot_escape_to_outside_file() {
    use std::os::unix::fs::symlink;

    let allowed = unique_dir("scope-symlink-allowed");
    let outside = unique_dir("scope-symlink-outside");
    let outside_file = outside.join("secret.txt");
    let link = allowed.join("looks-inside.txt");
    fs::write(&outside_file, "secret").unwrap();
    symlink(&outside_file, &link).unwrap();

    let env = Environment::root().with_fs_read_roots(vec![allowed.clone()]);
    let mut session = session(env);
    let error = eval_program(
        &format!(r#"(read-file "{}")"#, lisp_path(&link)),
        &mut session,
    )
    .expect_err("canonicalization must reject a symlink that escapes the root");
    assert_scope_denied(error, "read-file");

    fs::remove_dir_all(allowed).ok();
    fs::remove_dir_all(outside).ok();
}

#[test]
fn tcp_connect_deny_all_fails_before_network_access() {
    let env = Environment::root().with_tcp_connect_allowlist(vec![]);
    let mut session = session(env);
    let error = eval_program(r#"(tcp-connect "127.0.0.1" 1)"#, &mut session)
        .expect_err("deny-all connect policy must reject before attempting a connection");
    assert_scope_denied(error, "tcp-connect");
}

#[test]
fn tcp_listen_deny_all_fails_before_bind() {
    let env = Environment::root().with_tcp_listen_allowlist(vec![]);
    let mut session = session(env);
    let error = eval_program(r#"(tcp-listen-raw "127.0.0.1" 0)"#, &mut session)
        .expect_err("deny-all listen policy must reject before binding a socket");
    assert_scope_denied(error, "tcp-listen-raw");
}

#[test]
fn connect_and_listen_policies_are_independent() {
    let env = Environment::root()
        .with_tcp_connect_allowlist(vec![("127.0.0.1".into(), 8000, 9000)])
        .with_tcp_listen_allowlist(vec![("127.0.0.1".into(), 0, 0)]);
    let mut session = session(env);

    eval_program(r#"(tcp-listen-raw "127.0.0.1" 0)"#, &mut session)
        .expect("explicitly allowed loopback ephemeral bind should succeed");

    let error = eval_program(r#"(tcp-connect "127.0.0.1" 7999)"#, &mut session)
        .expect_err("port below connect allow-range must be policy-denied");
    assert_scope_denied(error, "tcp-connect");
}
