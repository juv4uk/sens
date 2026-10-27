use std::process::Command;

// Лише тестова основа: production Rust не залежить від текстового API Core4.
const CORE_LIBRARY_SOURCE: &str = include_str!("../../../lib/core4.lisp");

fn tool() -> Command {
    Command::new(env!("CARGO_BIN_EXE_sens-to-sens"))
}

fn temp_file(name: &str, source: &str) -> std::path::PathBuf {
    let path = std::env::temp_dir().join(format!(
        "sens-to-sens-{}-{}-{name}.lisp",
        std::process::id(),
        std::thread::current().name().unwrap_or("test")
    ));
    std::fs::write(&path, source).expect("write temp source");
    path
}

#[test]
fn check_reports_without_writing_then_apply_preserves_formatting() {
    let source =
        "; comment keeps (+ 9 9)\n(define f\n  (lambda (x)\n    (+ x 2)))\n(quote (+ 3 4))\n";
    let path = temp_file("format", source);

    let check = tool()
        .args(["--check", path.to_str().expect("utf8 path")])
        .output()
        .expect("run check");
    assert_eq!(check.status.code(), Some(1));
    assert_eq!(
        std::fs::read_to_string(&path).expect("read unchanged"),
        source
    );
    let check_out = String::from_utf8_lossy(&check.stdout);
    assert!(check_out.contains("convertible=4"), "{check_out}");

    let apply = tool().arg(&path).output().expect("run apply");
    assert!(
        apply.status.success(),
        "{}",
        String::from_utf8_lossy(&apply.stderr)
    );

    let rewritten = std::fs::read_to_string(&path).expect("read rewritten");
    let _ = std::fs::remove_file(&path);
    assert_eq!(
        rewritten,
        "; comment keeps (+ 9 9)\n(00001001 f\n  (00001000 (x)\n    (00001100 x 2)))\n(00000001 (+ 3 4))\n"
    );
}

#[test]
fn check_is_clean_after_all_currently_convertible_heads_are_migrated() {
    let source = "(00001001 f (00001000 (x) (00100111 x)))\n";
    let path = temp_file("clean", source);

    let check = tool()
        .args(["--check", path.to_str().expect("utf8 path")])
        .output()
        .expect("run check");
    let _ = std::fs::remove_file(&path);

    assert!(check.status.success());
    let stdout = String::from_utf8_lossy(&check.stdout);
    assert!(stdout.contains("convertible=0"), "{stdout}");
}

#[test]
fn current_core_library_is_already_fully_migrated() {
    // M1 (#1447) and the --language pass (#1520) moved every call head of the
    // core library to SENS codes; the tool finds nothing left in either mode.
    let path = temp_file("core-library", CORE_LIBRARY_SOURCE);
    for args in [vec!["--check"], vec!["--check", "--language"]] {
        let check = tool()
            .args(&args)
            .arg(&path)
            .output()
            .expect("run core check");
        let stdout = String::from_utf8_lossy(&check.stdout);
        assert!(check.status.success(), "{args:?}: {stdout}");
        assert!(stdout.contains("convertible=0"), "{args:?}: {stdout}");
    }
    let _ = std::fs::remove_file(&path);


}

