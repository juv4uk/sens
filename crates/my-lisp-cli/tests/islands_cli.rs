use std::path::PathBuf;
use std::process::Command;

fn manifest() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../tests/fixtures/islands-manifest-v1.json")
}

#[test]
fn islands_plan_describes_requested_runtimes_without_installing_them() {
    let output = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "plan",
            "--manifest",
            manifest().to_str().expect("UTF-8 manifest path"),
            "--with",
            "prolog,clips",
        ])
        .output()
        .expect("my-lisp CLI must run");

    assert!(output.status.success(), "stderr: {}", String::from_utf8_lossy(&output.stderr));
    let stdout = String::from_utf8(output.stdout).expect("UTF-8 output");
    for required in [
        "prolog",
        "9.2.0",
        "BSD-2-Clause",
        "apt",
        "clips",
        "6.4.2",
        "release-asset",
        "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    ] {
        assert!(stdout.contains(required), "plan omits {required}: {stdout}");
    }
}

#[test]
fn islands_plan_expands_the_four_kernel_profile_from_manifest() {
    let output = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands", "plan", "--manifest",
            manifest().to_str().expect("UTF-8 manifest path"),
            "--profile", "four-kernel",
        ])
        .output()
        .expect("my-lisp CLI must run");

    assert!(output.status.success(), "stderr: {}", String::from_utf8_lossy(&output.stderr));
    let stdout = String::from_utf8(output.stdout).expect("UTF-8 output");
    assert!(stdout.contains("prolog"), "{stdout}");
    assert!(stdout.contains("clips"), "{stdout}");
}

#[test]
fn islands_status_keeps_absent_and_unsupported_distinct_for_selected_target() {
    let output = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "status",
            "--manifest",
            manifest().to_str().expect("UTF-8 manifest path"),
            "--target",
            "windows-x86_64",
        ])
        .output()
        .expect("my-lisp CLI must run");

    assert!(output.status.success(), "stderr: {}", String::from_utf8_lossy(&output.stderr));
    let stdout = String::from_utf8(output.stdout).expect("UTF-8 output");
    assert!(stdout.contains("prolog: unsupported"), "{stdout}");
    assert!(stdout.contains("clips: unsupported"), "{stdout}");
}
