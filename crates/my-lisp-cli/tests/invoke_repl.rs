use std::fs;
use std::process::Command;
use wsm_clips_kernel::ClipsKernel;
use wsm_common_lisp_kernel::CommonLispKernel;
use wsm_prolog_kernel::PrologKernel;

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
fn invoke_surfaces_and_direct_sid_share_the_same_datalog_escape_hatch() {
    for source in [
        r#"(invoke 'datalog "path")"#,
        r#"(викликати 'datalog "path")"#,
        r#"(10101000 'datalog "path")"#,
    ] {
        let (ok, stdout, stderr) = run_source(source);
        assert!(ok, "{source}: stderr: {stderr}");
        assert!(stdout.contains("(island-native-observation datalog"), "{stdout}");
        assert!(stdout.contains("path(1,4)"), "{stdout}");
    }
}

#[test]
fn invoke_reaches_common_lisp_when_runtime_is_available() {
    if CommonLispKernel::default().version().is_err() {
        eprintln!("SKIP: Common Lisp runtime unavailable");
        return;
    }
    let (ok, stdout, stderr) = run_source(r#"(викликати 'common-lisp "(+ 2 3)")"#);
    assert!(ok, "stderr: {stderr}");
    assert!(
        stdout.contains(r#"(island-native-observation common-lisp "5")"#),
        "stdout: {stdout}"
    );
}

#[test]
fn invoke_reaches_prolog_when_runtime_is_available() {
    if PrologKernel::default().version().is_err() {
        eprintln!("SKIP: SWI-Prolog unavailable");
        return;
    }
    let (ok, stdout, stderr) =
        run_source(r#"(викликати 'prolog "ancestor(alice, X)")"#);
    assert!(ok, "stderr: {stderr}");
    assert!(
        stdout.contains(r#"(island-native-observation prolog "[bob,carol,dave]")"#),
        "stdout: {stdout}"
    );
}

#[test]
fn invoke_reaches_clips_when_runtime_is_available() {
    if ClipsKernel::discover().is_err() {
        eprintln!("SKIP: CLIPS runtime unavailable");
        return;
    }
    let (ok, stdout, stderr) = run_source(r#"(викликати 'clips "run")"#);
    assert!(ok, "stderr: {stderr}");
    assert!(
        stdout.contains(r#"(island-native-observation clips "fired=1")"#),
        "stdout: {stdout}"
    );
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
    let (ok, _stdout, stderr) =
        run_source(r#"(викликати 'datalog "unknown-relation")"#);
    assert!(!ok, "unsupported native payload must fail closed");
    assert!(
        stderr.contains("Datalog bounded REPL witness accepts only the relation payload"),
        "stderr: {stderr}"
    );
}
