#[test]
fn release_workflow_publishes_the_versioned_island_manifest() {
    let workflow = include_str!("../../../.github/workflows/release.yml");
    let manifest = include_str!("../../../packaging/islands-manifest-v1.json");

    assert!(workflow.contains("packaging/islands-manifest-v1.json"));
    assert!(manifest.contains("my-lisp-islands-manifest/1"));
}
