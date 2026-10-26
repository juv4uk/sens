#[test]
fn release_pipeline_excludes_unproven_island_manifest_and_compares_exact_bytes() {
    let workflow = include_str!("../../../.github/workflows/release.yml");
    let publisher = include_str!("../../../.github/workflows/release-publish.yml");
    let manifest = include_str!("../../../packaging/islands-manifest-v1.json");

    assert!(!workflow.contains("islands-manifest-v1.json"));
    assert!(!publisher.contains("islands-manifest-v1.json"));
    assert!(publisher.contains("cmp --"));
    assert!(!publisher.contains("python3"));
    assert!(!publisher.contains("sha256sum"));

    assert!(manifest.contains("sens-islands-manifest-1"));
    assert!(manifest.contains("\"four-kernel\""));
    assert!(manifest.contains("\"common-lisp\""));
    assert!(manifest.contains("\"prolog\""));
    assert!(manifest.contains("\"clips\""));
    assert!(manifest.contains("\"datalog\""));
}
