use std::process::Command;

#[test]
fn cli_export_produces_expected_s_expression_for_target_fixture() {
    let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    let output = Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root)
        .arg("external-oracle")
        .arg("export")
        .arg("--fixture")
        .arg("F-8bc31cae9e7e39b9")
        .output()
        .expect("failed to run xtask");

    assert!(output.status.success(), "xtask must exit 0");
    let stdout = String::from_utf8(output.stdout).expect("stdout must be utf-8");

    assert!(stdout.contains("(protocol . external-oracle/1)"));
    assert!(stdout.contains("(fixture-id . \"F-8bc31cae9e7e39b9\")"));
    assert!(stdout.contains("(oracle . wolfram-language)"));
    assert!(stdout.contains("(query . \"Fold[Divide, {5, 6, 8, 7}]\")"));
    assert!(stdout.contains("(expected . \"5/336\")"));
}

