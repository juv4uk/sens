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
    let reviews = fs::read_to_string(root.join("tests/semantic-authority-reviews.lisp"))
        .expect("explicit semantic-authority review manifest must exist");
    assert!(guard.contains("sid-to-meaning-authority"));
    assert!(guard.contains("surface-name-to-meaning-dispatch"));
    assert!(guard.contains("island-native-operator-to-sid"));
    assert!(guard.contains("isa-to-sid-authority"));
    assert!(guard.contains("host-fallback-meaning"));
    assert!(guard.contains("allowed-generated-projection"));
    assert!(guard.contains("\"SemanticId\" \"semantic_id\" \"CanonicalIdentity\""));
    assert!(guard.contains("authority-reviews"));
    assert!(guard.contains("reviewed-source?"));
    assert!(guard.contains("sha256-hex source"));
    assert!(guard.contains("reviewed-digest?"));
    assert!(guard.contains("transport-digest"));
    let digest_fast_path_pos = guard
        .find("(reviewed-digest? path transport-digest authority-reviews)")
        .expect("transported-digest review fast path must exist");
    let read_pos = guard
        .find("(read-file path)")
        .expect("source fallback must still read changed/unreviewed content");
    let classify_pos = guard
        .find("(let ((class (violation-class path source)))")
        .expect("structural classifier fallback must exist");
    assert!(
        digest_fast_path_pos < read_pos,
        "an exact reviewed transported digest must short-circuit before source I/O"
    );
    assert!(
        read_pos < classify_pos,
        "unreviewed content must be read before structural authority classification"
    );
    assert!(reviews.contains("issue-1098"));
    assert!(!reviews.contains("*"));
    for line in reviews.lines().filter(|line| line.starts_with("(review ")) {
        let quoted = line.split('"').collect::<Vec<_>>();
        assert!(quoted.len() >= 4, "review row must carry quoted path and digest: {line}");
        let digest = quoted[3];
        assert_eq!(digest.len(), 64, "review digest must be full SHA-256: {line}");
        assert!(
            digest.bytes().all(|byte| byte.is_ascii_hexdigit()),
            "review digest must be hexadecimal: {line}"
        );
    }
    assert!(enforcer.contains("semantic-authority-violation"));
    assert!(enforcer.contains("(car ())"));
    assert!(runner.contains("forbidden-sid-meaning.rs"));
    assert!(runner.contains("allowed-generated-projection.rs"));
    assert!(!root.join("scripts/semantic_authority_guard.py").exists());
}
