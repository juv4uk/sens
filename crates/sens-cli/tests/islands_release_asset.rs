#[test]
fn release_workflow_publishes_the_versioned_island_manifest() {
    let workflow = include_str!("../../../.github/workflows/release.yml");
    let manifest = include_str!("../../../packaging/islands-manifest-v1.json");

    assert!(workflow.contains("packaging/islands-manifest-v1.json"));
    // Release workflow hashes the downloaded archive with the native shell
    // utility, then checks the exact manifest field before staging it.
    assert!(workflow.contains("sha256sum packaging/vendor/clips_windows_projects_642.zip"));
    assert!(workflow.contains("jq -r '.islands[]"));
    assert!(workflow.contains("test \"$actual\" = \"$expected\""));
    assert!(workflow.contains("islands-manifest-v1.json"));
    assert!(manifest.contains("sens-islands-manifest-1"));
    assert!(manifest.contains("\"four-kernel\""));
    assert!(manifest.contains("\"common-lisp\""));
    assert!(manifest.contains("\"prolog\""));
    assert!(manifest.contains("\"clips\""));
    assert!(manifest.contains("\"datalog\""));
}
