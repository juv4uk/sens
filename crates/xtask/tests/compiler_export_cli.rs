use std::process::Command;

fn compiler_export(args: &[&str]) -> std::process::Output {
    let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root)
        .arg("compiler-export")
        .args(args)
        .output()
        .expect("compiler-export should execute")
}

#[test]
fn compiler_export_emits_full_sens_owned_d3_d4_closure() {
    let output = compiler_export(&[]);
    assert!(
        output.status.success(),
        "compiler-export failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    let stdout = String::from_utf8_lossy(&output.stdout);
    assert_eq!(
        stdout.matches("(compiler-semantic-request").count(),
        9,
        "full current compiler closure must export exactly nine requests"
    );
    assert_eq!(stdout.matches("(domain . D3)").count(), 7);
    assert_eq!(stdout.matches("(domain . D4)").count(), 2);

    for role in [
        "quote-form",
        "atom-predicate",
        "selector-tail",
        "selector-head",
        "atom-equality",
        "cond-form",
        "pair-construct",
        "lambda-form",
        "define-form",
    ] {
        assert!(
            stdout.contains(&format!("(execution-role . {role})")),
            "missing SENS-derived compiler role {role}"
        );
    }

    assert!(stdout.contains("(domain . D3) (bits . 010)"));
    assert!(stdout.contains("(domain . D4) (bits . 0010)"));
    assert!(stdout.contains(
        "(authority-ref . \"lib/compiler-nucleus.lisp:compiler-lowering-role-from-laws\")"
    ));
    assert!(stdout.contains(
        "(proof-ref . \"contracts/bija3-l1-l5-ratification.lisp\")"
    ));
    assert!(stdout.contains(
        "(proof-ref . \"contracts/d4-bootstrap-ratification.lisp\")"
    ));
    assert!(stdout.contains("(authority-path . \"language-contract.lisp\")"));
    assert!(stdout.contains("(repository . \"juv4uk/sens\")"));
    assert!(stdout.contains("(contract . 11.8)"));
    assert!(stdout.contains("(mechanism-status . unknown)"));
    assert!(stdout.contains("(mechanism-ref . ())"));
    assert!(stdout.contains("(ідентичність . ((domain . D3) (bits . 010)))"));
    assert!(stdout.contains("(походження . ((repository . \"juv4uk/sens\")"));
    assert!(!stdout.contains("(identity ."));
    assert!(!stdout.contains("(provenance ."));

    for forbidden in [
        "cuda",
        "futhark",
        "juv4uk/cml",
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

    let output2 = compiler_export(&[]);
    assert_eq!(output.stdout, output2.stdout, "export must be deterministic");
}

#[test]
fn compiler_export_preserves_same_payload_at_different_widths() {
    let d3 = compiler_export(&["--fixture", "nucleus-d3-010"]);
    let d4 = compiler_export(&["--fixture", "nucleus-d4-0010"]);
    assert!(d3.status.success());
    assert!(d4.status.success());

    let d3 = String::from_utf8_lossy(&d3.stdout);
    let d4 = String::from_utf8_lossy(&d4.stdout);
    assert!(d3.contains("(domain . D3) (bits . 010)"));
    assert!(d3.contains("(execution-role . atom-predicate)"));
    assert!(d4.contains("(domain . D4) (bits . 0010)"));
    assert!(d4.contains("(execution-role . lambda-form)"));
    assert_ne!(d3, d4);
}

#[test]
fn compiler_export_artifact_mode_wraps_the_canonical_request_without_target_policy() {
    let output = compiler_export(&["--artifact", "--fixture", "nucleus-d3-010"]);
    assert!(
        output.status.success(),
        "compiler-export --artifact failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    let stdout = String::from_utf8_lossy(&output.stdout);
    assert_eq!(stdout.matches("(compilation-artifact").count(), 1);
    assert!(stdout.contains("(schema . compiler-compilation-artifact/1)"));
    assert!(stdout.contains("(semantic-request . (compiler-semantic-request"));
    assert!(stdout.contains("(semantic-request-sha256 . \""));
    assert!(stdout.contains("(artifact-status . canonical-backend-neutral)"));

    for forbidden in ["cuda", "ptx", "sass", "graal", "fpga", "install-target"] {
        assert!(
            !stdout.to_ascii_lowercase().contains(forbidden),
            "compiler artifact leaked backend/install policy: {forbidden}"
        );
    }
}

#[test]
fn compiler_export_rejects_unknown_fixture() {
    let output = compiler_export(&["--fixture", "does-not-exist"]);
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("fixture not found"));
}
