#[test]
fn release_workflow_publishes_the_versioned_island_manifest() {
    let workflow = include_str!("../../../.github/workflows/release.yml");
    let manifest = include_str!("../../../packaging/islands-manifest-v1.json");

    assert!(workflow.contains("packaging/islands-manifest-v1.json"));
    assert!(workflow.contains("sha256sum"));
    assert!(workflow.contains("islands-manifest-v1.json"));
    assert!(manifest.contains("my-lisp-islands-manifest/1"));
    assert!(manifest.contains(r#""four-kernel""#));
    assert!(manifest.contains(r#""common-lisp""#));
    assert!(manifest.contains(r#""prolog""#));
    assert!(manifest.contains(r#""clips""#));
    assert!(manifest.contains(r#""datalog""#));
}
