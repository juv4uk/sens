use std::fs;

#[test]
fn semantic_authority_guard_is_lisp_owned() {
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let guard = fs::read_to_string(root.join("scripts/semantic-authority-guard.lisp"))
        .expect("#1049 guard must exist");
    let enforcer = fs::read_to_string(root.join("scripts/semantic-authority-guard-enforce.lisp"))
        .expect("#1049 enforcer must exist");
    let runner = fs::read_to_string(root.join("scripts/test-semantic-authority-guard.sh"))
        .expect("#1049 witness runner must exist");
    assert!(guard.contains("sid-to-meaning-authority"));
    assert!(guard.contains("surface-name-to-meaning-dispatch"));
    assert!(guard.contains("island-native-operator-to-sid"));
    assert!(guard.contains("isa-to-sid-authority"));
    assert!(guard.contains("host-fallback-meaning"));
    assert!(guard.contains("allowed-generated-projection"));
    assert!(guard.contains("(read-file path)"));
    assert!(enforcer.contains("semantic-authority-violation"));
    assert!(enforcer.contains("(car ())"));
    assert!(runner.contains("forbidden-sid-meaning.rs"));
    assert!(runner.contains("allowed-generated-projection.rs"));
    assert!(!root.join("scripts/semantic_authority_guard.py").exists());
}
