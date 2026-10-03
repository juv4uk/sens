use std::fs;
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};

use wsm_clips_kernel::ClipsKernel;
use wsm_common_lisp_kernel::CommonLispKernel;
use wsm_prolog_kernel::PrologKernel;

static NEXT_RUN_ID: AtomicU64 = AtomicU64::new(0);

fn run_source(source: &str, mechanism_lab: bool) -> (bool, String, String) {
    let run_id = NEXT_RUN_ID.fetch_add(1, Ordering::Relaxed);
    let dir = std::env::temp_dir().join(format!(
        "sens-raw-invoke-current-{}-{}-{run_id}",
        std::process::id(),
        if mechanism_lab { "mechanism-lab" } else { "core" }
    ));
    let _ = fs::remove_dir_all(&dir);
    fs::create_dir_all(&dir).expect("temporary test directory");
    let file = dir.join("invoke.lisp");
    fs::write(&file, source).expect("source");

    let mut command = Command::new(env!("CARGO_BIN_EXE_sens"));
    if mechanism_lab {
        command.arg("--lab=mechanism");
    }
    let output = command
        .arg(&file)
        .output()
        .expect("canonical sens binary");

    let stdout = String::from_utf8_lossy(&output.stdout).into_owned();
    let stderr = String::from_utf8_lossy(&output.stderr).into_owned();
    let _ = fs::remove_dir_all(&dir);
    (output.status.success(), stdout, stderr)
}

#[test]
fn registration_stays_unavailable_under_default_core() {
    let (ok, _stdout, stderr) =
        run_source(r#"(10101000 "datalog" "path")"#, false);
    assert!(!ok, "default Core must not inherit mechanism-lab raw admission");
    assert!(
        stderr.contains("SENS function has no admitted callable mechanism: 10101000"),
        "stderr: {stderr}"
    );
}

#[test]
fn exact_10101000_reaches_datalog_only_after_explicit_mechanism_lab() {
    let (ok, stdout, stderr) =
        run_source(r#"(10101000 "datalog" "path")"#, true);
    assert!(ok, "stderr: {stderr}");
    assert!(
        stdout.contains("island-native-observation") && stdout.contains("datalog"),
        "stdout: {stdout}"
    );
    assert!(stdout.contains("path(1,4)"), "stdout: {stdout}");
}

#[test]
fn unknown_mechanism_and_wrong_bounded_payload_fail_named() {
    let (ok, _stdout, stderr) =
        run_source(r#"(10101000 "imaginary-kernel" "payload")"#, true);
    assert!(!ok);
    assert!(
        stderr.contains("unsupported raw island mechanism: imaginary-kernel"),
        "stderr: {stderr}"
    );

    let (ok, _stdout, stderr) =
        run_source(r#"(10101000 "datalog" "unknown-relation")"#, true);
    assert!(!ok);
    assert!(
        stderr.contains("Datalog bounded raw-invoke witness accepts only the relation payload"),
        "stderr: {stderr}"
    );
}

#[test]
fn exact_10101000_reaches_common_lisp_when_runtime_is_available() {
    if CommonLispKernel::default().version().is_err() {
        eprintln!("SKIP: Common Lisp runtime unavailable");
        return;
    }
    let (ok, stdout, stderr) =
        run_source(r#"(10101000 "common-lisp" "(+ 2 3)")"#, true);
    assert!(ok, "stderr: {stderr}");
    assert!(stdout.contains("common-lisp"), "stdout: {stdout}");
    assert!(stdout.contains("5"), "stdout: {stdout}");
}

#[test]
fn exact_10101000_reaches_prolog_when_runtime_is_available() {
    if PrologKernel::default().version().is_err() {
        eprintln!("SKIP: SWI-Prolog unavailable");
        return;
    }
    let (ok, stdout, stderr) =
        run_source(r#"(10101000 "prolog" "ancestor(alice, X)")"#, true);
    assert!(ok, "stderr: {stderr}");
    assert!(stdout.contains("prolog"), "stdout: {stdout}");
    assert!(stdout.contains("bob"), "stdout: {stdout}");
    assert!(stdout.contains("carol"), "stdout: {stdout}");
    assert!(stdout.contains("dave"), "stdout: {stdout}");
}

#[test]
fn exact_10101000_reaches_clips_when_runtime_is_available() {
    if ClipsKernel::discover().is_err() {
        eprintln!("SKIP: CLIPS runtime unavailable");
        return;
    }
    let (ok, stdout, stderr) =
        run_source(r#"(10101000 "clips" "run")"#, true);
    assert!(ok, "stderr: {stderr}");
    assert!(stdout.contains("clips"), "stdout: {stdout}");
    assert!(stdout.contains("fired=1"), "stdout: {stdout}");
}
