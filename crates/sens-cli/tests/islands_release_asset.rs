#[test]
fn release_workflow_publishes_the_versioned_island_manifest() {
    let workflow = include_str!("../../../.github/workflows/release.yml");
    let manifest = include_str!("../../../packaging/islands-manifest-v1.json");

    assert!(workflow.contains("packaging/islands-manifest-v1.json"));
    assert!(workflow.contains("sha256sum"));
    assert!(workflow.contains("islands-manifest-v1.json"));
    assert!(manifest.contains("sens-islands-manifest/1"));
    assert!(manifest.contains("\"four-kernel\""));
    assert!(manifest.contains("\"common-lisp\""));
    assert!(manifest.contains("\"prolog\""));
    assert!(manifest.contains("\"clips\""));
    assert!(manifest.contains("\"datalog\""));
}
