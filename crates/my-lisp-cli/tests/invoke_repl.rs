use std::fs;
use std::process::Command;

fn run_source(source: &str) -> (bool, String, String) {
    let dir = std::env::temp_dir().join(format!(
        "my-lisp-invoke-repl-test-{}",
        std::process::id()
    ));
    let _ = fs::remove_dir_all(&dir);
    fs::create_dir_all(&dir).expect("temporary test directory");
    let file = dir.join("invoke.lisp");
    fs::write(&file, source).expect("source");
    let output = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .arg(&file)
        .output()
        .expect("my-lisp binary");
    let stdout = String::from_utf8_lossy(&output.stdout).into_owned();
    let stderr = String::from_utf8_lossy(&output.stderr).into_owned();
    let _ = fs::remove_dir_all(&dir);
    (output.status.success(), stdout, stderr)
}

#[test]
fn ukrainian_invoke_reaches_common_lisp_as_native_observation() {
    let (ok, stdout, stderr) = run_source(r#"(викликати 'common-lisp "(+ 2 3)")"#);
    assert!(ok, "stderr: {stderr}");
    assert!(
        stdout.contains(r#"(island-native-observation common-lisp "5")"#),
        "stdout: {stdout}"
    );
}

#[test]
fn ukrainian_invoke_reaches_prolog_as_native_observation() {
    let (ok, stdout, stderr) =
        run_source(r#"(викликати 'prolog "ancestor(alice, X)")"#);
    assert!(ok, "stderr: {stderr}");
    assert!(
        stdout.contains(r#"(island-native-observation prolog "[bob,carol,dave]")"#),
        "stdout: {stdout}"
    );
}

#[test]
fn ukrainian_invoke_reaches_clips_as_native_observation() {
    let (ok, stdout, stderr) = run_source(r#"(викликати 'clips "run")"#);
    assert!(ok, "stderr: {stderr}");
    assert!(
        stdout.contains(r#"(island-native-observation clips "fired=1")"#),
        "stdout: {stdout}"
    );
}

#[test]
fn ukrainian_invoke_reaches_datalog_as_native_observation() {
    let (ok, stdout, stderr) = run_source(r#"(викликати 'datalog "path")"#);
    assert!(ok, "stderr: {stderr}");
    assert!(stdout.contains("(island-native-observation datalog"), "stdout: {stdout}");
    assert!(stdout.contains("path(1,4)"), "stdout: {stdout}");
}

#[test]
fn invoke_unknown_kernel_fails_named() {
    let (ok, _stdout, stderr) =
        run_source(r#"(викликати 'imaginary-kernel "payload")"#);
    assert!(!ok, "unknown kernel must fail closed");
    assert!(
        stderr.contains("unsupported kernel: imaginary-kernel"),
        "stderr: {stderr}"
    );
}

#[test]
fn invoke_rejects_wrong_bounded_native_payload_named() {
    let (ok, _stdout, stderr) = run_source(r#"(викликати 'datalog "unknown-relation")"#);
    assert!(!ok, "unsupported native payload must fail closed");
    assert!(
        stderr.contains("Datalog bounded REPL witness accepts only the relation payload"),
        "stderr: {stderr}"
    );
}
