use std::fs;
use std::process::Command;

use wsm_clips_kernel::ClipsKernel;
use wsm_common_lisp_kernel::CommonLispKernel;
use wsm_prolog_kernel::PrologKernel;

fn run_source(source: &str, extra: &[&str]) -> (bool, String, String) {
    let dir = std::env::temp_dir().join(format!(
        "sens-raw-invoke-current-{}",
        std::process::id()
    ));
    let _ = fs::remove_dir_all(&dir);
    fs::create_dir_all(&dir).expect("temporary test directory");
    let file = dir.join("invoke.lisp");
    fs::write(&file, source).expect("source");
    let mut command = Command::new(env!("CARGO_BIN_EXE_sens"));
    command.args(extra).arg(&file);
    let output = command.output().expect("sens binary");
    let stdout = String::from_utf8_lossy(&output.stdout).into_owned();
    let stderr = String::from_utf8_lossy(&output.stderr).into_owned();
    let _ = fs::remove_dir_all(&dir);
    (output.status.success(), stdout, stderr)
}

#[test]
fn raw_invoke_requires_core3_admission() {
    let source = r#"(10101000 'datalog "path")"#;

    let (default_ok, _stdout, default_stderr) = run_source(source, &[]);
    assert!(!default_ok, "default Core4 must not inherit Core3 raw admission");
    assert!(
        default_stderr.contains("admitted callable mechanism")
            || default_stderr.contains("mechanism"),
        "stderr: {default_stderr}"
    );

    let (core3_ok, stdout, stderr) = run_source(source, &["--core=3"]);
    assert!(core3_ok, "stderr: {stderr}");
    assert!(stdout.contains("(island-native-observation datalog"), "stdout: {stdout}");
    assert!(stdout.contains("path(1,4)"), "stdout: {stdout}");
}

#[test]
fn human_surfaces_converge_on_the_same_core3_raw_route() {
    let en_name = ["in", "voke"].concat();
    let en_source = format!("({en_name} 'datalog \"path\")");
    let cases = [
        ("en", en_source.as_str()),
        ("uk", r#"(викликати 'datalog "path")"#),
    ];

    for (surface, source) in cases {
        let flag = format!("--surface={surface}");
        let (ok, stdout, stderr) = run_source(source, &["--core=3", &flag]);
        assert!(ok, "{surface} stderr: {stderr}");
        assert!(stdout.contains("(island-native-observation datalog"), "{surface}: {stdout}");
        assert!(stdout.contains("path(1,4)"), "{surface}: {stdout}");
    }
}

#[test]
fn direct_sens_reaches_common_lisp_when_available() {
    if CommonLispKernel::default().version().is_err() {
        eprintln!("SKIP: Common Lisp runtime unavailable");
        return;
    }
    let (ok, stdout, stderr) =
        run_source(r#"(10101000 'common-lisp "(+ 2 3)")"#, &["--core=3"]);
    assert!(ok, "stderr: {stderr}");
    assert!(
        stdout.contains(r#"(island-native-observation common-lisp "5")"#),
        "stdout: {stdout}"
    );
}

#[test]
fn direct_sens_reaches_prolog_when_available() {
    if PrologKernel::default().version().is_err() {
        eprintln!("SKIP: SWI-Prolog unavailable");
        return;
    }
    let (ok, stdout, stderr) =
        run_source(r#"(10101000 'prolog "ancestor(alice, X)")"#, &["--core=3"]);
    assert!(ok, "stderr: {stderr}");
    assert!(
        stdout.contains(r#"(island-native-observation prolog "[bob,carol,dave]")"#),
        "stdout: {stdout}"
    );
}

#[test]
fn direct_sens_reaches_clips_when_available() {
    if ClipsKernel::discover().is_err() {
        eprintln!("SKIP: CLIPS runtime unavailable");
        return;
    }
    let (ok, stdout, stderr) = run_source(r#"(10101000 'clips "run")"#, &["--core=3"]);
    assert!(ok, "stderr: {stderr}");
    assert!(
        stdout.contains(r#"(island-native-observation clips "fired=1")"#),
        "stdout: {stdout}"
    );
}

#[test]
fn raw_invoke_failures_are_named_and_closed() {
    let (ok, _stdout, stderr) = run_source(
        r#"(10101000 'imaginary-kernel "payload")"#,
        &["--core=3"],
    );
    assert!(!ok, "unknown mechanism must fail closed");
    assert!(
        stderr.contains("unsupported raw island mechanism: imaginary-kernel"),
        "stderr: {stderr}"
    );

    let (ok, _stdout, stderr) = run_source(
        r#"(10101000 'datalog "unknown-relation")"#,
        &["--core=3"],
    );
    assert!(!ok, "unsupported payload must fail closed");
    assert!(
        stderr.contains("Datalog bounded raw-invoke witness accepts only the relation payload"),
        "stderr: {stderr}"
    );
}
