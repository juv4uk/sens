//! Black-box proof that the CLI no longer dispatches literal `process-run`
//! through the legacy host semantic capability.
//! Чорноскриньковий доказ, що CLI більше не передає буквальний `process-run`
//! у стару host-семантичну capability.

use std::process::Command;

fn sens() -> Command {
    let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    let mut command = Command::new(env!("CARGO_BIN_EXE_sens"));
    command.current_dir(repo_root);
    command
}

#[test]
fn cli_literal_process_run_rejects_invalid_utf8_in_lisp_instead_of_lossy_host_decoding() {
    let path = std::env::temp_dir().join("sens-process-language-owned.lisp");
    std::fs::write(
        &path,
        r#"(process-run
             "python3"
             (quote ("-c" "import sys; sys.stdout.buffer.write(bytes([255]))")))"#,
    )
    .expect("should write process fixture");

    let output = sens()
        .arg(path.to_str().expect("UTF-8 temp path"))
        .output()
        .expect("CLI should run");
    let _ = std::fs::remove_file(&path);

    assert!(
        output.status.success(),
        "CLI failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8(output.stdout).expect("CLI stdout itself should be UTF-8");
    assert_eq!(stdout.trim(), "(rejected stdout-invalid-utf8)");
    assert!(!stdout.contains('�'), "lossy host replacement leaked into CLI output");
}

#[test]
fn cli_literal_process_run_keeps_the_compatible_text_result_shape_for_valid_utf8() {
    let path = std::env::temp_dir().join("sens-process-compatible-shape.lisp");
    std::fs::write(
        &path,
        r#"(process-run
             "python3"
             (quote ("-c" "import sys; sys.stdout.write('ok')")))"#,
    )
    .expect("should write process fixture");

    let output = sens()
        .arg(path.to_str().expect("UTF-8 temp path"))
        .output()
        .expect("CLI should run");
    let _ = std::fs::remove_file(&path);

    assert!(
        output.status.success(),
        "CLI failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8(output.stdout).expect("CLI stdout should be UTF-8");
    assert_eq!(stdout.trim(), "(0 \"ok\" \"\")");
}
