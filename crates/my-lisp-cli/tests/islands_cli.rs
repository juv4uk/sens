use std::path::PathBuf;
use std::process::Command;

fn manifest() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../tests/fixtures/islands-manifest-v1.json")
}

#[test]
fn islands_plan_describes_requested_runtimes_without_installing_them() {
    let root = std::env::temp_dir().join(format!(
        "my-lisp-islands-plan-{}",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&root);
    let output = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "plan",
            "--manifest",
            manifest().to_str().expect("UTF-8 manifest path"),
            "--with",
            "prolog,clips",
            "--root",
            root.to_str().expect("UTF-8 root path"),
        ])
        .output()
        .expect("my-lisp CLI must run");

    assert!(
        output.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8(output.stdout).expect("UTF-8 output");
    for required in [
        "prolog",
        "9.2.0",
        "abi: wsm-kernel-c-abi/1",
        "install-key: prolog",
        "BSD-2-Clause",
        "license-acceptance: not-required",
        "apt",
        "entrypoint: swipl",
        "clips",
        "6.4.2",
        "install-key: clips",
        "license-acceptance: required",
        "release-asset",
        "checksum-algorithm: sha256",
        "artifact-format: raw-binary",
        "entrypoint: clips",
        "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "verified-installed: no",
    ] {
        assert!(stdout.contains(required), "plan omits {required}: {stdout}");
    }
    assert!(
        stdout.contains(&root.display().to_string()),
        "plan omits exact destination root: {stdout}"
    );
    assert!(!root.exists(), "read-only plan created {root:?}");
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
    std::fs::write(&manifest_path, format!(r#"{{"protocol":"my-lisp-islands-manifest/1","profiles":[{{"key":"one","islands":["demo"]}}],"islands":[{{"key":"demo","runtime_version":"1","abi_compatibility":"test-abi","install_key":"demo","license":"test","license_acceptance_required":false,"provenance":"test","platforms":[{{"target":"linux-x86_64","provider":"release-asset","url":"file://{}","checksum_algorithm":"sha256","sha256":"{}","artifact_format":"raw-binary","entrypoint":"runtime.bin","probe":["/bin/sh","-c","exit 0"]}}]}}]}}"#, artifact.display(), digest)).expect("manifest");
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
    let status_stdout = String::from_utf8(status.stdout).unwrap();
    assert!(status_stdout.contains("demo 1 linux-x86_64"));
    assert!(status_stdout.contains(": available"));

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
    std::fs::write(&manifest_path, r#"{"protocol":"my-lisp-islands-manifest/1","islands":[{"key":"demo","runtime_version":"1","abi_compatibility":"test-abi","install_key":"demo","license":"test","license_acceptance_required":false,"provenance":"test","platforms":[{"target":"linux-x86_64","provider":"release-asset","url":"https://example.invalid/demo","checksum_algorithm":"sha256","sha256":"bad","artifact_format":"raw-binary","entrypoint":"runtime.bin","probe":["demo","--version"]}]}]}"#).expect("manifest");
    let output = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args(["islands", "plan", "--manifest", manifest_path.to_str().unwrap(), "--with", "demo"])
        .output().expect("CLI");
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("invalid SHA-256"));
}

#[test]
fn islands_manifest_rejects_missing_release_metadata_before_planning() {
    let base = std::env::temp_dir().join(format!(
        "my-lisp-islands-missing-meta-{}",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&base);
    std::fs::create_dir_all(&base).expect("temporary fixture directory");
    let manifest_path = base.join("manifest.json");
    std::fs::write(
        &manifest_path,
        r#"{"protocol":"my-lisp-islands-manifest/1","islands":[{"key":"demo","runtime_version":"1","license":"test","license_acceptance_required":false,"provenance":"test","platforms":[]}]}"#,
    )
    .expect("manifest");

    let output = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "plan",
            "--manifest",
            manifest_path.to_str().unwrap(),
            "--with",
            "demo",
        ])
        .output()
        .expect("CLI");

    assert!(!output.status.success());
    assert!(
        String::from_utf8_lossy(&output.stderr)
            .contains("missing required release metadata")
    );
}

#[test]
fn islands_manifest_rejects_unknown_provider_without_fallback() {
    let base = std::env::temp_dir().join(format!(
        "my-lisp-islands-provider-{}",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&base);
    std::fs::create_dir_all(&base).expect("temporary fixture directory");
    let manifest_path = base.join("manifest.json");
    std::fs::write(
        &manifest_path,
        r#"{"protocol":"my-lisp-islands-manifest/1","islands":[{"key":"demo","runtime_version":"1","abi_compatibility":"test-abi","install_key":"demo","license":"test","license_acceptance_required":false,"provenance":"test","platforms":[{"target":"linux-x86_64","provider":"magic","entrypoint":"demo","probe":["demo","--version"]}]}]}"#,
    )
    .expect("manifest");

    let output = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "plan",
            "--manifest",
            manifest_path.to_str().unwrap(),
            "--with",
            "demo",
        ])
        .output()
        .expect("CLI");

    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("unsupported provider"));
}

#[test]
fn islands_status_reports_probe_failure_without_hiding_version_identity() {
    let base = std::env::temp_dir().join(format!("my-lisp-islands-probe-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&base);
    std::fs::create_dir_all(&base).expect("temporary fixture directory");
    let artifact = base.join("runtime.bin");
    std::fs::write(&artifact, b"runtime").expect("artifact");
    let digest = my_lisp::sha256_source(b"runtime").iter().map(|byte| format!("{byte:02x}")).collect::<String>();
    let manifest_path = base.join("manifest.json");
    std::fs::write(&manifest_path, format!(r#"{{"protocol":"my-lisp-islands-manifest/1","islands":[{{"key":"demo","runtime_version":"2","abi_compatibility":"test-abi","install_key":"demo","license":"test","license_acceptance_required":false,"provenance":"release","platforms":[{{"target":"linux-x86_64","provider":"release-asset","url":"file://{}","checksum_algorithm":"sha256","sha256":"{}","artifact_format":"raw-binary","entrypoint":"runtime.bin","probe":["/bin/sh","-c","exit 7"]}}]}}]}}"#, artifact.display(), digest)).expect("manifest");
    let root = base.join("installed");
    let install = Command::new(env!("CARGO_BIN_EXE_my-lisp")).args(["islands", "install", "--manifest", manifest_path.to_str().unwrap(), "--with", "demo", "--root", root.to_str().unwrap(), "--apply"]).output().expect("install");
    assert!(install.status.success(), "{}", String::from_utf8_lossy(&install.stderr));
    let install_stdout = String::from_utf8(install.stdout).unwrap();
    assert!(install_stdout.contains("published"));
    assert!(install_stdout.contains(": probe-failed"));
    assert!(!install_stdout.contains(": available"));

    let status = Command::new(env!("CARGO_BIN_EXE_my-lisp")).args(["islands", "status", "--manifest", manifest_path.to_str().unwrap(), "--root", root.to_str().unwrap()]).output().expect("status");
    let stdout = String::from_utf8(status.stdout).unwrap();
    assert!(stdout.contains("demo 2 linux-x86_64 release: probe-failed"), "{stdout}");
}

#[test]
fn islands_install_requires_explicit_license_acceptance_before_download() {
    let base = std::env::temp_dir().join(format!(
        "my-lisp-islands-license-{}",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&base);
    std::fs::create_dir_all(&base).expect("temporary fixture directory");

    let artifact = base.join("runtime.bin");
    std::fs::write(&artifact, b"licensed-runtime").expect("artifact");
    let digest = my_lisp::sha256_source(b"licensed-runtime")
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect::<String>();
    let manifest_path = base.join("manifest.json");
    std::fs::write(
        &manifest_path,
        format!(
            r#"{{"protocol":"my-lisp-islands-manifest/1","islands":[{{"key":"demo","runtime_version":"3","abi_compatibility":"test-abi","install_key":"demo","license":"Example-License","license_acceptance_required":true,"provenance":"release","platforms":[{{"target":"linux-x86_64","provider":"release-asset","url":"file://{}","checksum_algorithm":"sha256","sha256":"{}","artifact_format":"raw-binary","entrypoint":"runtime.bin","probe":["/bin/sh","-c","exit 0"]}}]}}]}}"#,
            artifact.display(),
            digest
        ),
    )
    .expect("manifest");

    let root = base.join("installed");
    let rejected = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "install",
            "--manifest",
            manifest_path.to_str().unwrap(),
            "--with",
            "demo",
            "--root",
            root.to_str().unwrap(),
            "--apply",
        ])
        .output()
        .expect("install without acceptance");
    assert!(!rejected.status.success());
    assert!(
        String::from_utf8_lossy(&rejected.stderr).contains("license acceptance required"),
        "{}",
        String::from_utf8_lossy(&rejected.stderr)
    );
    assert!(
        !root.join("demo/3/linux-x86_64/runtime.bin").exists(),
        "license refusal published a runtime"
    );

    let failed_status = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "status",
            "--manifest",
            manifest_path.to_str().unwrap(),
            "--root",
            root.to_str().unwrap(),
        ])
        .output()
        .expect("status after license refusal");
    assert!(
        String::from_utf8(failed_status.stdout)
            .unwrap()
            .contains("demo 3 linux-x86_64 release: failed-install")
    );

    let accepted = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "install",
            "--manifest",
            manifest_path.to_str().unwrap(),
            "--with",
            "demo",
            "--root",
            root.to_str().unwrap(),
            "--apply",
            "--accept-license",
            "demo",
        ])
        .output()
        .expect("install with acceptance");
    assert!(
        accepted.status.success(),
        "{}",
        String::from_utf8_lossy(&accepted.stderr)
    );
    assert!(root.join("demo/3/linux-x86_64/runtime.bin").is_file());
}

#[test]
fn islands_checksum_failure_rolls_back_and_reports_failed_install() {
    let base = std::env::temp_dir().join(format!(
        "my-lisp-islands-checksum-{}",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&base);
    std::fs::create_dir_all(&base).expect("temporary fixture directory");

    let artifact = base.join("runtime.bin");
    std::fs::write(&artifact, b"wrong-content").expect("artifact");
    let manifest_path = base.join("manifest.json");
    let wrong_digest = "0000000000000000000000000000000000000000000000000000000000000000";
    std::fs::write(
        &manifest_path,
        format!(
            r#"{{"protocol":"my-lisp-islands-manifest/1","islands":[{{"key":"demo","runtime_version":"4","abi_compatibility":"test-abi","install_key":"demo","license":"test","license_acceptance_required":false,"provenance":"release","platforms":[{{"target":"linux-x86_64","provider":"release-asset","url":"file://{}","checksum_algorithm":"sha256","sha256":"{}","artifact_format":"raw-binary","entrypoint":"runtime.bin","probe":["/bin/sh","-c","exit 0"]}}]}}]}}"#,
            artifact.display(),
            wrong_digest
        ),
    )
    .expect("manifest");

    let root = base.join("installed");
    let install = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "install",
            "--manifest",
            manifest_path.to_str().unwrap(),
            "--with",
            "demo",
            "--root",
            root.to_str().unwrap(),
            "--apply",
        ])
        .output()
        .expect("checksum install");
    assert!(!install.status.success());
    assert!(String::from_utf8_lossy(&install.stderr).contains("checksum mismatch"));
    assert!(
        !root.join("demo/4/linux-x86_64/runtime.bin").exists(),
        "checksum failure published a runtime"
    );

    let status = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "status",
            "--manifest",
            manifest_path.to_str().unwrap(),
            "--root",
            root.to_str().unwrap(),
        ])
        .output()
        .expect("status");
    assert!(
        String::from_utf8(status.stdout)
            .unwrap()
            .contains("demo 4 linux-x86_64 release: failed-install")
    );
}

#[test]
fn islands_probe_timeout_keeps_verified_artifact_but_reports_probe_failed() {
    let base = std::env::temp_dir().join(format!(
        "my-lisp-islands-timeout-{}",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&base);
    std::fs::create_dir_all(&base).expect("temporary fixture directory");

    let artifact = base.join("runtime.bin");
    std::fs::write(&artifact, b"timeout-runtime").expect("artifact");
    let digest = my_lisp::sha256_source(b"timeout-runtime")
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect::<String>();
    let manifest_path = base.join("manifest.json");
    std::fs::write(
        &manifest_path,
        format!(
            r#"{{"protocol":"my-lisp-islands-manifest/1","islands":[{{"key":"demo","runtime_version":"5","abi_compatibility":"test-abi","install_key":"demo","license":"test","license_acceptance_required":false,"provenance":"release","platforms":[{{"target":"linux-x86_64","provider":"release-asset","url":"file://{}","checksum_algorithm":"sha256","sha256":"{}","artifact_format":"raw-binary","entrypoint":"runtime.bin","probe":["/bin/sh","-c","sleep 3"]}}]}}]}}"#,
            artifact.display(),
            digest
        ),
    )
    .expect("manifest");

    let root = base.join("installed");
    let install = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "install",
            "--manifest",
            manifest_path.to_str().unwrap(),
            "--with",
            "demo",
            "--root",
            root.to_str().unwrap(),
            "--apply",
        ])
        .output()
        .expect("timeout install");
    assert!(
        install.status.success(),
        "{}",
        String::from_utf8_lossy(&install.stderr)
    );
    let stdout = String::from_utf8(install.stdout).unwrap();
    assert!(stdout.contains(": probe-failed"), "{stdout}");
    assert!(
        root.join("demo/5/linux-x86_64/runtime.bin").is_file(),
        "probe failure removed a verified artifact"
    );

    let status = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "status",
            "--manifest",
            manifest_path.to_str().unwrap(),
            "--root",
            root.to_str().unwrap(),
        ])
        .output()
        .expect("status");
    assert!(
        String::from_utf8(status.stdout)
            .unwrap()
            .contains("demo 5 linux-x86_64 release: probe-failed")
    );
}

#[test]
fn islands_missing_probe_executable_is_probe_failed_not_available() {
    let base = std::env::temp_dir().join(format!(
        "my-lisp-islands-missing-probe-{}",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&base);
    std::fs::create_dir_all(&base).expect("temporary fixture directory");

    let artifact = base.join("runtime.bin");
    std::fs::write(&artifact, b"missing-probe-runtime").expect("artifact");
    let digest = my_lisp::sha256_source(b"missing-probe-runtime")
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect::<String>();
    let manifest_path = base.join("manifest.json");
    std::fs::write(
        &manifest_path,
        format!(
            r#"{{"protocol":"my-lisp-islands-manifest/1","islands":[{{"key":"demo","runtime_version":"6","abi_compatibility":"test-abi","install_key":"demo","license":"test","license_acceptance_required":false,"provenance":"release","platforms":[{{"target":"linux-x86_64","provider":"release-asset","url":"file://{}","checksum_algorithm":"sha256","sha256":"{}","artifact_format":"raw-binary","entrypoint":"runtime.bin","probe":["definitely-not-a-real-my-lisp-probe-executable-892"]}}]}}]}}"#,
            artifact.display(),
            digest
        ),
    )
    .expect("manifest");

    let root = base.join("installed");
    let install = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "install",
            "--manifest",
            manifest_path.to_str().unwrap(),
            "--with",
            "demo",
            "--root",
            root.to_str().unwrap(),
            "--apply",
        ])
        .output()
        .expect("missing probe executable install");
    assert!(
        install.status.success(),
        "{}",
        String::from_utf8_lossy(&install.stderr)
    );
    let stdout = String::from_utf8(install.stdout).unwrap();
    assert!(stdout.contains(": probe-failed"), "{stdout}");
    assert!(!stdout.contains(": available"), "{stdout}");
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
