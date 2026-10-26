#[test]
fn release_workflow_blocks_island_manifest_without_native_provenance_proof() {
    let workflow = include_str!("../../../.github/workflows/release.yml");
    let manifest = include_str!("../../../packaging/islands-manifest-v1.json");

    assert!(workflow.contains("packaging/islands-manifest-v1.json"));
    assert!(workflow.contains("CLIPS_VENDOR_ARCHIVE=NOT_VERIFIED"));
    assert!(workflow.contains("non-SHA, byte-exact provenance proof"));
    assert!(!workflow.contains("sha256sum packaging/vendor/clips_windows_projects_642.zip"));
    assert!(workflow.contains("islands-manifest-v1.json"));
    assert!(manifest.contains("sens-islands-manifest-1"));
    assert!(manifest.contains("\"four-kernel\""));
    assert!(manifest.contains("\"common-lisp\""));
    assert!(manifest.contains("\"prolog\""));
    assert!(manifest.contains("\"clips\""));
    assert!(manifest.contains("\"datalog\""));
}
