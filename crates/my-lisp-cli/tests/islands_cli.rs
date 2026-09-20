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
fn islands_plan_uses_four_kernel_profile_by_default() {
    let output = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "plan",
            "--manifest",
            manifest().to_str().expect("UTF-8 manifest path"),
        ])
        .output()
        .expect("my-lisp CLI must run");

    assert!(output.status.success(), "stderr: {}", String::from_utf8_lossy(&output.stderr));
    let stdout = String::from_utf8(output.stdout).expect("UTF-8 output");
    for required in ["common-lisp", "prolog", "clips", "datalog"] {
        assert!(stdout.contains(required), "default four-kernel plan omits {required}: {stdout}");
    }
}

#[test]
fn top_level_install_alias_delegates_to_island_bootstrap() {
    let root = std::env::temp_dir().join(format!("my-lisp-install-alias-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&root);
    let output = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "install",
            "--manifest",
            manifest().to_str().expect("UTF-8 manifest path"),
            "--profile",
            "four-kernel",
            "--root",
            root.to_str().expect("UTF-8 root path"),
            "--dry-run",
        ])
        .output()
        .expect("my-lisp CLI must run");

    assert!(output.status.success(), "stderr: {}", String::from_utf8_lossy(&output.stderr));
    let stdout = String::from_utf8(output.stdout).expect("UTF-8 output");
    assert!(stdout.contains("dry-run"));
    assert!(!root.exists(), "dry-run created {root:?}");
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
    assert!(
        stdout.contains("prolog")
            && (stdout.contains("swi-prolog") || stdout.contains("prolog/9.2.0/linux-x86_64")),
        "{stdout}"
    );
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
    std::fs::write(&manifest_path, format!(r#"{{"protocol":"my-lisp-islands-manifest/1","profiles":[{{"key":"one","islands":["demo"]}}],"islands":[{{"key":"demo","runtime_version":"1","abi_compatibility":"test-abi/1","install_key":"demo","license":"test","provenance":"test","platforms":[{{"target":"linux-x86_64","provider":"release-asset","url":"file://{}","checksum_algorithm":"sha256","sha256":"{}","artifact":"file","artifact_format":"file","entrypoint":"runtime.bin","probe":["/bin/sh","-c","exit 0"]}}]}}]}}"#, artifact.display(), digest)).expect("manifest");
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
    std::fs::write(&manifest_path, r#"{"protocol":"my-lisp-islands-manifest/1","islands":[{"key":"demo","runtime_version":"1","abi_compatibility":"test-abi/1","install_key":"demo","license":"test","provenance":"test","platforms":[{"target":"linux-x86_64","provider":"release-asset","url":"https://example.invalid/runtime.bin","checksum_algorithm":"sha256","sha256":"bad"}]}]}"#).expect("manifest");
    let output = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args(["islands", "plan", "--manifest", manifest_path.to_str().unwrap(), "--with", "demo"])
        .output().expect("CLI");
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("invalid SHA-256"));
}

#[test]
fn islands_manifest_rejects_missing_release_metadata() {
    let base = std::env::temp_dir().join(format!(
        "my-lisp-islands-missing-meta-{}",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&base);
    std::fs::create_dir_all(&base).expect("temporary fixture directory");
    let manifest_path = base.join("manifest.json");
    std::fs::write(
        &manifest_path,
        r#"{"protocol":"my-lisp-islands-manifest/1","islands":[{"key":"demo","runtime_version":"1","license":"test","provenance":"test","platforms":[]}]}"#,
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
    assert!(String::from_utf8_lossy(&output.stderr).contains("missing required release metadata"));
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
    std::fs::write(&manifest_path, format!(r#"{{"protocol":"my-lisp-islands-manifest/1","islands":[{{"key":"demo","runtime_version":"2","abi_compatibility":"test-abi/1","install_key":"demo","license":"test","provenance":"release","platforms":[{{"target":"linux-x86_64","provider":"release-asset","url":"file://{}","checksum_algorithm":"sha256","sha256":"{}","artifact":"file","artifact_format":"file","entrypoint":"runtime.bin","probe":["/bin/sh","-c","exit 7"]}}]}}]}}"#, artifact.display(), digest)).expect("manifest");
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


#[test]
fn islands_plan_reports_exact_destination_and_verified_state_without_mutation() {
    let root = std::env::temp_dir().join(format!(
        "my-lisp-islands-plan-acceptance-{}",
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
            "prolog",
            "--target",
            "linux-x86_64",
            "--root",
            root.to_str().expect("UTF-8 root"),
        ])
        .output()
        .expect("CLI");

    assert!(output.status.success(), "{}", String::from_utf8_lossy(&output.stderr));
    let stdout = String::from_utf8(output.stdout).expect("UTF-8 output");
    for required in [
        "abi: wsm-kernel-c-abi/1",
        "install-key: prolog",
        "license-acceptance: not-required",
        "provenance: system package manager",
        "destination:",
        "verified-installed: no",
        "entrypoint: swipl",
    ] {
        assert!(stdout.contains(required), "plan omits {required}: {stdout}");
    }
    assert!(
        stdout.contains("prolog/distro-managed/linux-x86_64")
            || stdout.contains("prolog/9.2.0/linux-x86_64"),
        "destination path mismatch: {stdout}"
    );
    assert!(!root.exists(), "read-only plan mutated install root");
}

#[test]
fn islands_manifest_rejects_empty_provenance() {
    let base = std::env::temp_dir().join(format!(
        "my-lisp-islands-empty-provenance-{}",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&base);
    std::fs::create_dir_all(&base).expect("temporary fixture directory");
    let manifest_path = base.join("manifest.json");
    std::fs::write(
        &manifest_path,
        r#"{"protocol":"my-lisp-islands-manifest/1","islands":[{"key":"demo","runtime_version":"1","abi_compatibility":"test-abi","install_key":"demo","license":"test","license_acceptance_required":false,"provenance":"","platforms":[]}]}"#,
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
        String::from_utf8_lossy(&output.stderr).contains("missing required release metadata")
    );
}

#[test]
fn islands_install_requires_explicit_license_acceptance_before_download() {
    let base = std::env::temp_dir().join(format!(
        "my-lisp-islands-license-contract-{}",
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
            r#"{{"protocol":"my-lisp-islands-manifest/1","profiles":[{{"key":"one","islands":["demo"]}}],"islands":[{{"key":"demo","runtime_version":"3","abi_compatibility":"test-abi","install_key":"demo","license":"Example-License","license_acceptance_required":true,"provenance":"release","platforms":[{{"target":"linux-x86_64","provider":"release-asset","url":"file://{}","checksum_algorithm":"sha256","sha256":"{}","artifact":"file","artifact_format":"raw-binary","entrypoint":"runtime.bin","probe":["/bin/sh","-c","exit 0"]}}]}}]}}"#,
            artifact.display(),
            digest
        ),
    )
    .expect("manifest");
    let root = base.join("installed");

    let rejected = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands","install","--manifest",manifest_path.to_str().unwrap(),
            "--profile","one","--root",root.to_str().unwrap(),"--apply",
        ])
        .output()
        .expect("install without acceptance");
    assert!(!rejected.status.success());
    assert!(String::from_utf8_lossy(&rejected.stderr).contains("license acceptance required"));
    assert!(!root.join("demo/3/linux-x86_64/runtime.bin").exists());

    let status = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args(["islands","status","--manifest",manifest_path.to_str().unwrap(),"--root",root.to_str().unwrap()])
        .output()
        .expect("status");
    assert!(String::from_utf8(status.stdout).unwrap().contains("demo 3 linux-x86_64 release: failed-install"));

    let accepted = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands","install","--manifest",manifest_path.to_str().unwrap(),
            "--profile","one","--root",root.to_str().unwrap(),"--apply",
            "--accept-license","demo",
        ])
        .output()
        .expect("install with acceptance");
    assert!(accepted.status.success(), "{}", String::from_utf8_lossy(&accepted.stderr));
    assert!(root.join("demo/3/linux-x86_64/runtime.bin").is_file());
}

#[test]
fn islands_verified_artifact_survives_probe_failure_and_status_is_explicit() {
    let base = std::env::temp_dir().join(format!(
        "my-lisp-islands-probe-contract-{}",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&base);
    std::fs::create_dir_all(&base).expect("temporary fixture directory");
    let artifact = base.join("runtime.bin");
    std::fs::write(&artifact, b"probe-runtime").expect("artifact");
    let digest = my_lisp::sha256_source(b"probe-runtime")
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect::<String>();
    let manifest_path = base.join("manifest.json");
    std::fs::write(
        &manifest_path,
        format!(
            r#"{{"protocol":"my-lisp-islands-manifest/1","profiles":[{{"key":"one","islands":["demo"]}}],"islands":[{{"key":"demo","runtime_version":"4","abi_compatibility":"test-abi","install_key":"demo","license":"test","license_acceptance_required":false,"provenance":"release","platforms":[{{"target":"linux-x86_64","provider":"release-asset","url":"file://{}","checksum_algorithm":"sha256","sha256":"{}","artifact":"file","artifact_format":"raw-binary","entrypoint":"runtime.bin","probe":["/bin/sh","-c","exit 7"]}}]}}]}}"#,
            artifact.display(),
            digest
        ),
    )
    .expect("manifest");
    let root = base.join("installed");

    let install = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands","install","--manifest",manifest_path.to_str().unwrap(),
            "--profile","one","--root",root.to_str().unwrap(),"--apply",
        ])
        .output()
        .expect("install");
    assert!(install.status.success(), "{}", String::from_utf8_lossy(&install.stderr));
    let stdout = String::from_utf8(install.stdout).unwrap();
    assert!(stdout.contains(": probe-failed"), "{stdout}");
    assert!(root.join("demo/4/linux-x86_64/runtime.bin").is_file());
    assert!(root.join("demo/4/linux-x86_64/install-record.txt").is_file());

    let status = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args(["islands","status","--manifest",manifest_path.to_str().unwrap(),"--root",root.to_str().unwrap()])
        .output()
        .expect("status");
    assert!(String::from_utf8(status.stdout).unwrap().contains("demo 4 linux-x86_64 release: probe-failed"));
}

#[test]
fn concurrent_release_asset_installs_publish_one_verified_runtime() {
    let base = std::env::temp_dir().join(format!(
        "my-lisp-islands-concurrent-contract-{}",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&base);
    std::fs::create_dir_all(&base).expect("temporary fixture directory");
    let artifact = base.join("runtime.bin");
    std::fs::write(&artifact, b"concurrent-runtime").expect("artifact");
    let digest = my_lisp::sha256_source(b"concurrent-runtime")
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect::<String>();
    let manifest_path = base.join("manifest.json");
    std::fs::write(
        &manifest_path,
        format!(
            r#"{{"protocol":"my-lisp-islands-manifest/1","profiles":[{{"key":"one","islands":["demo"]}}],"islands":[{{"key":"demo","runtime_version":"5","abi_compatibility":"test-abi","install_key":"demo","license":"test","license_acceptance_required":false,"provenance":"release","platforms":[{{"target":"linux-x86_64","provider":"release-asset","url":"file://{}","checksum_algorithm":"sha256","sha256":"{}","artifact":"file","artifact_format":"raw-binary","entrypoint":"runtime.bin","probe":["/bin/sh","-c","exit 0"]}}]}}]}}"#,
            artifact.display(),
            digest
        ),
    )
    .expect("manifest");
    let root = base.join("installed");
    let args = [
        "islands","install","--manifest",manifest_path.to_str().unwrap(),
        "--profile","one","--root",root.to_str().unwrap(),"--apply",
    ];

    let first = Command::new(env!("CARGO_BIN_EXE_my-lisp")).args(args).spawn().expect("first");
    let second = Command::new(env!("CARGO_BIN_EXE_my-lisp")).args(args).spawn().expect("second");
    let first = first.wait_with_output().expect("first output");
    let second = second.wait_with_output().expect("second output");
    assert!(first.status.success(), "{}", String::from_utf8_lossy(&first.stderr));
    assert!(second.status.success(), "{}", String::from_utf8_lossy(&second.stderr));
    assert_eq!(
        std::fs::read(root.join("demo/5/linux-x86_64/runtime.bin")).unwrap(),
        b"concurrent-runtime"
    );
    assert!(root.join("demo/5/linux-x86_64/install-record.txt").is_file());
}


#[test]
fn islands_install_provisions_embedded_datalog_through_transactional_installer() {
    let root = std::env::temp_dir().join(format!(
        "my-lisp-islands-embedded-datalog-{}",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&root);

    let dry_run = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "install",
            "--manifest",
            manifest().to_str().expect("UTF-8 manifest path"),
            "--with",
            "datalog",
            "--root",
            root.to_str().expect("UTF-8 root"),
            "--dry-run",
        ])
        .output()
        .expect("dry-run");
    assert!(
        dry_run.status.success(),
        "{}",
        String::from_utf8_lossy(&dry_run.stderr)
    );
    assert!(
        String::from_utf8_lossy(&dry_run.stdout)
            .contains("install datalog builtin as part of the my-lisp distribution")
    );
    assert!(!root.exists(), "embedded dry-run created {root:?}");

    let apply = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "install",
            "--manifest",
            manifest().to_str().expect("UTF-8 manifest path"),
            "--with",
            "datalog",
            "--root",
            root.to_str().expect("UTF-8 root"),
            "--apply",
        ])
        .output()
        .expect("apply");
    assert!(
        apply.status.success(),
        "{}",
        String::from_utf8_lossy(&apply.stderr)
    );
    assert!(
        String::from_utf8_lossy(&apply.stdout)
            .contains("installed datalog builtin: available (embedded)")
    );

    let target = if cfg!(target_os = "windows") {
        "windows-x86_64"
    } else if cfg!(target_os = "macos") {
        if cfg!(target_arch = "aarch64") {
            "macos-aarch64"
        } else {
            "macos-x86_64"
        }
    } else {
        "linux-x86_64"
    };

    let record = root
        .join("datalog")
        .join("builtin")
        .join(target)
        .join("install-record.txt");
    assert!(
        record.is_file(),
        "installer did not provision Datalog record at {record:?}"
    );
    let record_text = std::fs::read_to_string(&record).expect("Datalog install record");
    assert!(record_text.contains("island=datalog"));
    assert!(record_text.contains("provider=embedded"));
    assert!(record_text.contains("verified=true"));

    let state = root
        .join(".state")
        .join("datalog")
        .join("builtin")
        .join(format!("{target}.status"));
    assert_eq!(
        std::fs::read_to_string(&state)
            .expect("embedded Datalog lifecycle state")
            .trim(),
        "available"
    );

    let second = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .args([
            "islands",
            "install",
            "--manifest",
            manifest().to_str().expect("UTF-8 manifest path"),
            "--with",
            "datalog",
            "--root",
            root.to_str().expect("UTF-8 root"),
            "--apply",
        ])
        .output()
        .expect("second apply");
    assert!(second.status.success());
    assert!(
        String::from_utf8_lossy(&second.stdout)
            .contains("already installed datalog builtin: available (embedded)")
    );

    let _ = std::fs::remove_dir_all(&root);
}
