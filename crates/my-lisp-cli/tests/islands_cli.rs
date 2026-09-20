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
fn islands_install_dry_run_plans_versioned_paths_without_creating_them() {
    let root = std::env::temp_dir().join(format!("my-lisp-islands-test-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&root);
    let output = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands", "install", "--manifest",
            manifest().to_str().expect("UTF-8 manifest path"),
            "--profile", "four-kernel", "--root",
            root.to_str().expect("UTF-8 root path"), "--dry-run",
        ])
        .output()
        .expect("my-lisp CLI must run");

    assert!(output.status.success(), "stderr: {}", String::from_utf8_lossy(&output.stderr));
    let stdout = String::from_utf8(output.stdout).expect("UTF-8 output");
    assert!(stdout.contains("dry-run"), "{stdout}");
    assert!(stdout.contains("prolog/9.2.0/linux-x86_64"), "{stdout}");
    assert!(!root.exists(), "dry-run created {root:?}");
}

#[test]
fn islands_install_apply_verifies_file_artifact_before_publishing_it() {
    let base = std::env::temp_dir().join(format!("my-lisp-islands-apply-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&base);
    std::fs::create_dir_all(&base).expect("temporary fixture directory");
    let artifact = base.join("runtime.bin");
    std::fs::write(&artifact, b"island-runtime").expect("fixture artifact");
    let digest = my_lisp::sha256_source(b"island-runtime").iter().map(|byte| format!("{byte:02x}")).collect::<String>();
    let manifest_path = base.join("manifest.json");
    std::fs::write(&manifest_path, format!(r#"{{"protocol":"my-lisp-islands-manifest/1","profiles":[{{"key":"one","islands":["demo"]}}],"islands":[{{"key":"demo","runtime_version":"1","license":"test","provenance":"test","platforms":[{{"target":"linux-x86_64","provider":"release-asset","url":"file://{}","sha256":"{}"}}]}}]}}"#, artifact.display(), digest)).expect("manifest");
    let root = base.join("installed");
    let output = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args(["islands", "install", "--manifest", manifest_path.to_str().unwrap(), "--profile", "one", "--root", root.to_str().unwrap(), "--apply"])
        .output().expect("CLI");
    assert!(output.status.success(), "{}", String::from_utf8_lossy(&output.stderr));
    assert_eq!(std::fs::read(root.join("demo/1/linux-x86_64/runtime.bin")).unwrap(), b"island-runtime");
    let status = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args(["islands", "status", "--manifest", manifest_path.to_str().unwrap(), "--root", root.to_str().unwrap()])
        .output().expect("status CLI");
    assert!(status.status.success(), "{}", String::from_utf8_lossy(&status.stderr));
    assert!(String::from_utf8(status.stdout).unwrap().contains("demo: available"));

    let second = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args(["islands", "install", "--manifest", manifest_path.to_str().unwrap(), "--profile", "one", "--root", root.to_str().unwrap(), "--apply"])
        .output().expect("idempotent install CLI");
    assert!(second.status.success(), "{}", String::from_utf8_lossy(&second.stderr));
    assert!(String::from_utf8(second.stdout).unwrap().contains("already installed"));
}

#[test]
fn islands_manifest_rejects_malformed_release_checksum() {
    let base = std::env::temp_dir().join(format!("my-lisp-islands-invalid-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&base);
    std::fs::create_dir_all(&base).expect("temporary fixture directory");
    let manifest_path = base.join("manifest.json");
    std::fs::write(&manifest_path, r#"{"protocol":"my-lisp-islands-manifest/1","islands":[{"key":"demo","runtime_version":"1","license":"test","provenance":"test","platforms":[{"target":"linux-x86_64","provider":"release-asset","sha256":"bad"}]}]}"#).expect("manifest");
    let output = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args(["islands", "plan", "--manifest", manifest_path.to_str().unwrap(), "--with", "demo"])
        .output().expect("CLI");
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("invalid SHA-256"));
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
