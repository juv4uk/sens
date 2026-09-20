use std::fs;
use std::path::PathBuf;
use std::process::Command;

use my_lisp::parse;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(|p| p.parent())
        .expect("repo root")
        .to_path_buf()
}

fn read(path: &str) -> String {
    fs::read_to_string(repo_root().join(path))
        .unwrap_or_else(|error| panic!("{path} must be readable: {error}"))
}

#[test]
fn binary_sid_handoff_points_only_to_the_canonical_lisp_registry() {
    let handoff = read("contracts/sid-registry-handoff-996.lisp");
    let forms = parse(&handoff).expect("handoff must be readable Lisp data");
    assert_eq!(forms.len(), 1, "handoff must be one metadata form");

    assert!(handoff.contains(
        r#"(authority-source . "lib/surface/semantic-registry.lisp")"#
    ));
    assert!(handoff.contains("(identity-width-bits . 8)"));
    assert!(handoff.contains("(canonical-id-encoding . binary-token)"));
    assert!(handoff.contains("(projection-policy . derived-only)"));
    assert!(handoff.contains("(meaning-owner . my-lisp)"));

    for forbidden in [
        "decimal-shadow-registry",
        "string-sid-shadow-registry",
        "hand-maintained-projection",
        "consumer-redefinition",
    ] {
        assert!(
            handoff.contains(forbidden),
            "handoff must fail closed against {forbidden}"
        );
    }
}

#[test]
fn canonical_registry_preserves_one_contiguous_8_bit_binary_axis() {
    let registry = read("lib/surface/semantic-registry.lisp");
    let mut ids = Vec::new();

    for line in registry.lines() {
        let trimmed = line.trim_start();
        if !trimmed.starts_with('(') || trimmed.len() < 10 {
            continue;
        }
        let candidate = &trimmed[1..9];
        if candidate.len() == 8
            && candidate.bytes().all(|byte| byte == b'0' || byte == b'1')
            && trimmed.as_bytes().get(9) == Some(&b' ')
        {
            ids.push(candidate.to_owned());
        }
    }

    assert_eq!(ids.len(), 170, "handoff must cover every canonical registry row");
    for (expected, bits) in ids.iter().enumerate() {
        let parsed = u8::from_str_radix(bits, 2)
            .unwrap_or_else(|error| panic!("invalid binary SID {bits}: {error}"));
        assert_eq!(
            usize::from(parsed),
            expected,
            "canonical registry must remain one contiguous binary SID axis"
        );
    }
    assert_eq!(ids.first().map(String::as_str), Some("00000000"));
    assert_eq!(ids.last().map(String::as_str), Some("10101001"));
}

#[test]
fn pinned_registry_content_revision_matches_git_blob_identity() {
    let handoff = read("contracts/sid-registry-handoff-996.lisp");
    let marker = r#"(source-git-blob . ""#;
    let start = handoff
        .find(marker)
        .expect("handoff must pin source-git-blob")
        + marker.len();
    let rest = &handoff[start..];
    let end = rest.find('"').expect("source-git-blob must close its string");
    let pinned = &rest[..end];

    assert_eq!(pinned.len(), 40, "Git blob identity must be a full SHA-1");
    assert!(pinned.bytes().all(|b| b.is_ascii_hexdigit()));

    let output = Command::new("git")
        .current_dir(repo_root())
        .args(["hash-object", "lib/surface/semantic-registry.lisp"])
        .output()
        .expect("git hash-object must be available in repository tests");
    assert!(output.status.success(), "git hash-object failed");
    let actual = String::from_utf8(output.stdout)
        .expect("git hash-object output must be UTF-8");
    assert_eq!(
        actual.trim(),
        pinned,
        "canonical registry changed: refresh #996 handoff pin explicitly"
    );
}

#[test]
fn handoff_does_not_copy_any_semantic_row_table() {
    let handoff = read("contracts/sid-registry-handoff-996.lisp");
    let binary_tokens = handoff
        .split(|c: char| c.is_whitespace() || matches!(c, '(' | ')' | '"'))
        .filter(|token| {
            token.len() == 8 && token.bytes().all(|b| b == b'0' || b == b'1')
        })
        .collect::<Vec<_>>();

    assert!(
        binary_tokens.is_empty(),
        "handoff metadata must not duplicate canonical SID rows: {binary_tokens:?}"
    );
}
