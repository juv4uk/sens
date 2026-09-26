use std::process::Command;

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
    let source = "; comment keeps (+ 9 9)\n(define f\n  (lambda (x)\n    (+ x 2)))\n(quote (+ 3 4))\n";
    let path = temp_file("format", source);

    let check = tool()
        .args(["--check", path.to_str().expect("utf8 path")])
        .output()
        .expect("run check");
    assert_eq!(check.status.code(), Some(1));
    assert_eq!(std::fs::read_to_string(&path).expect("read unchanged"), source);
    let check_out = String::from_utf8_lossy(&check.stdout);
    assert!(check_out.contains("convertible=4"), "{check_out}");

    let apply = tool()
        .arg(&path)
        .output()
        .expect("run apply");
    assert!(apply.status.success(), "{}", String::from_utf8_lossy(&apply.stderr));

    let rewritten = std::fs::read_to_string(&path).expect("read rewritten");
    let _ = std::fs::remove_file(&path);
    assert_eq!(
        rewritten,
        "; comment keeps (+ 9 9)\n(00001001 f\n  (00001000 (x)\n    (00001100 x 2)))\n(00000001 (+ 3 4))\n"
    );
}

#[test]
fn check_is_clean_after_all_convertible_heads_are_migrated() {
    let path = temp_file("clean", "(00001001 f (00001000 (x) (00000101 x)))\n");

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
fn arithmetic_shadowing_is_not_rewritten() {
    let source = "(lambda (+) (+ 1 2))\n(+ 1 2 3)\n(< 1 2 3)\n";
    let path = temp_file("shadow", source);

    let apply = tool().arg(&path).output().expect("run apply");
    assert!(apply.status.success());
    let rewritten = std::fs::read_to_string(&path).expect("read rewritten");
    let _ = std::fs::remove_file(&path);

    assert_eq!(
        rewritten,
        "(00001000 (+) (+ 1 2))\n(00001100 1 2 3)\n(00011010 1 2 3)\n"
    );
}
