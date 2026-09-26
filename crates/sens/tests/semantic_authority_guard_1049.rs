use std::fs;

#[test]
fn semantic_authority_guard_is_lisp_owned() {
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let guard = fs::read_to_string(root.join("scripts/semantic-authority-guard.lisp"))
        .expect("#1347 guard must exist");
    let enforcer = fs::read_to_string(root.join("scripts/semantic-authority-guard-enforce.lisp"))
        .expect("#1347 enforcer must exist");
    let runner = fs::read_to_string(root.join("scripts/test-semantic-authority-guard.sh"))
        .expect("#1347 witness runner must exist");

    assert!(guard.contains("ASYMMETRIC-SEMANTIC-FIREWALL"));
    assert!(guard.contains("language-authority-source?"));
    assert!(guard.contains("host-to-language-authority-leak"));
    assert!(guard.contains("semantic-authority-claim?"));
    assert!(guard.contains("allowed-local-implementation"));
    assert!(guard.contains("do not even inspect host implementation text"));

    // #1049 policy is intentionally retired: local host semantics no longer
    // require path+digest review and are not classified as violations.
    assert!(!guard.contains("sid-to-meaning-authority"));
    assert!(!guard.contains("surface-name-to-meaning-dispatch"));
    assert!(!guard.contains("island-native-operator-to-sid"));
    assert!(!guard.contains("isa-to-sid-authority"));
    assert!(!guard.contains("host-fallback-meaning"));
    assert!(!guard.contains("authority-reviews"));
    assert!(!guard.contains("reviewed-digest?"));
    assert!(!guard.contains("sha256-hex source"));

    // The self-test proves the asymmetry directly.
    assert!(runner.contains("forbidden-sid-meaning.rs allowed"));
    assert!(runner.contains("forbidden-fallback.rs allowed"));
    assert!(runner.contains("forbidden-lisp-host-authority.lisp violation"));
    assert!(runner.contains("allowed-lisp-host-evidence.lisp allowed"));

    assert!(enforcer.contains("semantic-authority-violation"));
    assert!(enforcer.contains("(car ())"));
    assert!(!root.join("scripts/semantic_authority_guard.py").exists());
}
