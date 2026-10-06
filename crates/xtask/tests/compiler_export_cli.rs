use std::process::Command;

#[test]
fn compiler_export_emits_sens_owned_role_and_provenance() {
    let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    let output = Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root)
        .arg("compiler-export")
        .arg("--fixture")
        .arg("car-nested-pair")
        .output()
        .expect("compiler-export should execute");

    assert!(
        output.status.success(),
        "compiler-export failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("(schema . compiler-semantic-input/1)"));
    assert!(stdout.contains("(fixture-id . \"car-nested-pair\")"));
    assert!(stdout.contains("(domain . D3) (bits . 100)"));
    assert!(stdout.contains("(execution-role . selector-head)"));
    assert!(stdout.contains("(repository . \"juv4uk/sens\")"));
    assert!(stdout.contains("(contract . 11.6)"));
    assert!(stdout.contains("(mechanism-status . unknown)"));
    assert!(stdout.contains("(mechanism-ref . ())"));

    for forbidden in [
        "cuda",
        "futhark",
        "cml",
        "PrimOp",
        "SLOT",
        "Sid8",
        "Sens8",
    ] {
        assert!(
            !stdout.contains(forbidden),
            "compiler semantic export leaked target/legacy vocabulary: {forbidden}"
        );
    }

    let output2 = Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root)
        .arg("compiler-export")
        .arg("--fixture")
        .arg("car-nested-pair")
        .output()
        .expect("second compiler-export should execute");

    assert_eq!(output.stdout, output2.stdout, "export must be deterministic");
}

#[test]
fn compiler_export_rejects_unknown_fixture() {
    let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    let output = Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root)
        .args(["compiler-export", "--fixture", "does-not-exist"])
        .output()
        .expect("compiler-export should execute");

    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("fixture not found"));
}


#[test]
fn compiler_export_default_is_full_d3_d4_nucleus_closure() {
    let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    let output = Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root)
        .arg("compiler-export")
        .output()
        .expect("full compiler-export should execute");

    assert!(
        output.status.success(),
        "compiler-export failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    let stdout = String::from_utf8_lossy(&output.stdout);
    assert_eq!(
        stdout.matches("(compiler-semantic-request").count(),
        9,
        "current selfhost export must contain exactly the nine admitted compiler roles"
    );

    assert!(stdout.contains("(identity . ((domain . D3) (bits . 001)))"));
    assert!(stdout.contains("(execution-role . quote-form)"));
    assert!(stdout.contains("(identity . ((domain . D4) (bits . 0010)))"));
    assert!(stdout.contains("(execution-role . lambda-form)"));
    assert!(stdout.contains("(identity . ((domain . D4) (bits . 0011)))"));
    assert!(stdout.contains("(execution-role . define-form)"));
    assert!(stdout.contains("contracts/d4-bootstrap-ratification.lisp"));
    assert!(stdout.contains("knowledge/d4-bootstrap-compiler-structure-projection.json"));

    assert!(!stdout.contains("(domain . D8)"));
    for forbidden in [
        "cuda",
        "futhark",
        "cml",
        "PrimOp",
        "SLOT",
        "Sid8",
        "Sens8",
    ] {
        assert!(
            !stdout.contains(forbidden),
            "full compiler export leaked target/legacy vocabulary: {forbidden}"
        );
    }

    let output2 = Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root)
        .arg("compiler-export")
        .output()
        .expect("second full compiler-export should execute");
    assert_eq!(output.stdout, output2.stdout, "full export must be deterministic");
}

#[test]
fn compiler_export_can_select_generated_d4_role_fixture() {
    let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    let output = Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root)
        .args(["compiler-export", "--fixture", "role-d4-0010-lambda-form"])
        .output()
        .expect("D4 compiler fixture export should execute");

    assert!(
        output.status.success(),
        "D4 fixture export failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert_eq!(stdout.matches("(compiler-semantic-request").count(), 1);
    assert!(stdout.contains("(domain . D4) (bits . 0010)"));
    assert!(stdout.contains("(execution-role . lambda-form)"));
    assert!(stdout.contains("contracts/d4-bootstrap-ratification.lisp"));
}
