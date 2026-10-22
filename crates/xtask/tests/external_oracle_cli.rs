use std::process::Command;

#[test]
fn cli_export_projects_nested_current_exact_quotient_calls() {
    let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    let output = Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root)
        .arg("external-oracle")
        .arg("export")
        .arg("--fixture")
        .arg("F-8bc31cae9e7e39b9")
        .output()
        .expect("failed to run xtask");

    let stdout = String::from_utf8(output.stdout).expect("stdout must be utf-8");

    assert!(stdout.contains("(protocol . external-oracle/1)"));
    assert!(stdout.contains("(fixture-id . \"F-8bc31cae9e7e39b9\")"));
    assert!(
        output.status.success(),
        "current exact quotient fixture must export"
    );
    assert!(stdout.contains("(oracle . wolfram-language)"));
    assert!(stdout.contains("(query . \"Divide[Divide[Divide[5, 6], 8], 7]\")"));
    assert!(stdout.contains("(expected . \"5/336\")"));
}
