//! RELEASE-VERSION-PARITY: every canonical crate must carry the same
//! version, because scripts/release.my bumps them together with one sed
//! and the release tag is a single version for the whole workspace.
//!
//! This test exists because sens-lsp joined the release list late and
//! silently kept 0.1.0 through the l0.25.0 release — drift no other check
//! would have caught. If you add a canonical crate, add its Cargo.toml to
//! scripts/release.lisp's bump list AND to CRATE_MANIFESTS below.

use std::path::Path;

/// The five canonical crates bumped by scripts/release.my, in the same
/// order the script lists them.
const CRATE_MANIFESTS: &[&str] = &[
    "crates/sens/Cargo.toml",
    "crates/sens-cli/Cargo.toml",
    "crates/sens-literate/Cargo.toml",
    "crates/sens-wasm/Cargo.toml",
    "crates/sens-lsp/Cargo.toml",
    "crates/sens-host/Cargo.toml",
    "crates/sens-semantic/Cargo.toml",
];

fn manifest_version(repo_root: &Path, manifest: &str) -> String {
    let text = std::fs::read_to_string(repo_root.join(manifest))
        .unwrap_or_else(|e| panic!("cannot read {manifest}: {e}"));
    // First `version = "..."` under [package]; these manifests are simple,
    // and the release script edits exactly this line with its sed.
    let section = text.split("[package]").nth(1).expect("[package] section");
    let line = section
        .lines()
        .find(|l| l.trim_start().starts_with("version ="))
        .unwrap_or_else(|| panic!("{manifest}: no package version line"));
    line.trim()
        .strip_prefix("version =")
        .expect("version assignment")
        .trim()
        .trim_matches('"')
        .to_string()
}

#[test]
fn all_canonical_crates_share_one_release_version() {
    // CARGO_MANIFEST_DIR of this test is crates/sens-lsp/tests.
    let repo_root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent() // crates/
        .and_then(Path::parent)
        .expect("repo root")
        .to_path_buf();

    let versions: Vec<(String, String)> = CRATE_MANIFESTS
        .iter()
        .map(|m| (m.to_string(), manifest_version(&repo_root, m)))
        .collect();

    let (_, expected) = &versions[0];
    for (manifest, version) in &versions {
        assert_eq!(
            version, expected,
            "version drift: {manifest} is {version}, but {} is {expected} — \
             add it to scripts/release.lisp's bump list or fix the version",
            versions[0].0
        );
    }
}


// Native replacement for scripts/check-release-version-alignment.py.
// This is packaging provenance only: it grants no semantic or release GO.
const RELEASE_EXPECTED_VERSION: &str = "0.42.1";
const RELEASE_EXPECTED_TAG: &str = "s0.42.1";
const RELEASE_CRATES: &[&str] = &[
    "sens",
    "sens-cli",
    "sens-host",
    "sens-literate",
    "sens-lsp",
    "sens-semantic",
    "sens-wasm",
];

#[derive(Clone, Debug, PartialEq, Eq)]
struct LockPackage {
    name: Option<String>,
    version: Option<String>,
    source: Option<String>,
}

fn release_repo_root() -> std::path::PathBuf {
    std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(std::path::Path::parent)
        .expect("repository root")
        .to_path_buf()
}

fn quoted_value(line: &str, key: &str) -> Option<String> {
    let line = line.trim();
    let value = line.strip_prefix(key)?.trim();
    let value = value.strip_prefix('"')?;
    Some(value.split('"').next()?.to_string())
}

fn package_manifest_version(text: &str, path: &str) -> String {
    let mut in_package = false;
    for line in text.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with('[') {
            in_package = trimmed == "[package]";
            continue;
        }
        if in_package {
            if let Some(version) = quoted_value(trimmed, "version =") {
                return version;
            }
        }
    }
    panic!("RELEASE_BLOCKED: {path}: package.version missing")
}

fn parse_lock_packages(text: &str) -> Vec<LockPackage> {
    let mut entries = Vec::new();
    let mut current: Option<LockPackage> = None;
    for line in text.lines() {
        if line.trim() == "[[package]]" {
            if let Some(entry) = current.take() {
                entries.push(entry);
            }
            current = Some(LockPackage {
                name: None,
                version: None,
                source: None,
            });
            continue;
        }
        let Some(entry) = current.as_mut() else {
            continue;
        };
        if entry.name.is_none() {
            entry.name = quoted_value(line, "name =");
        }
        if entry.version.is_none() {
            entry.version = quoted_value(line, "version =");
        }
        if entry.source.is_none() {
            entry.source = quoted_value(line, "source =");
        }
    }
    if let Some(entry) = current {
        entries.push(entry);
    }
    entries
}

fn validate_release_lock(
    rows: &[LockPackage],
    expected: &str,
) -> Result<std::collections::BTreeMap<String, String>, String> {
    let mut found = std::collections::BTreeMap::new();
    for row in rows {
        let Some(name) = row.name.as_deref() else {
            continue;
        };
        if !RELEASE_CRATES.contains(&name) {
            continue;
        }
        if found.contains_key(name) {
            return Err(format!("Cargo.lock: duplicate release package {name}"));
        }
        let version = row.version.as_deref().unwrap_or("");
        if version != expected {
            return Err(format!(
                "Cargo.lock: {name} version {version:?} != {expected:?}"
            ));
        }
        if row.source.is_some() {
            return Err(format!(
                "Cargo.lock: release package {name} must be local, not registry/git"
            ));
        }
        found.insert(name.to_string(), version.to_string());
    }
    for name in RELEASE_CRATES {
        if !found.contains_key(*name) {
            return Err(format!("Cargo.lock: missing local release package {name}"));
        }
    }
    Ok(found)
}

fn extract_guix_version(text: &str) -> Option<String> {
    let marker = "(version \"";
    let tail = text.split_once(marker)?.1;
    Some(tail.split('"').next()?.to_string())
}

fn versions_from_release_manifests(
    root: &std::path::Path,
) -> std::collections::BTreeMap<String, String> {
    let mut versions = std::collections::BTreeMap::new();
    for name in RELEASE_CRATES {
        let path = root.join("crates").join(name).join("Cargo.toml");
        assert!(
            path.is_file() && !path.is_symlink(),
            "RELEASE_BLOCKED: missing regular crate manifest {}",
            path.display()
        );
        let text = std::fs::read_to_string(&path)
            .unwrap_or_else(|e| panic!("RELEASE_BLOCKED: {}: {e}", path.display()));
        let version = package_manifest_version(&text, &path.display().to_string());
        assert_eq!(
            version, RELEASE_EXPECTED_VERSION,
            "RELEASE_BLOCKED: crate version drift in {}",
            path.display()
        );
        versions.insert((*name).to_string(), version);
    }
    versions
}

fn verify_release_version_surfaces(root: &std::path::Path) -> Result<(), String> {
    let versions = versions_from_release_manifests(root);
    let lock_path = root.join("Cargo.lock");
    if !lock_path.is_file() || lock_path.is_symlink() {
        return Err("Cargo.lock missing or not a regular file".to_string());
    }
    let lock_text = std::fs::read_to_string(&lock_path)
        .map_err(|e| format!("Cargo.lock unreadable: {e}"))?;
    let locked = validate_release_lock(
        &parse_lock_packages(&lock_text),
        RELEASE_EXPECTED_VERSION,
    )?;
    if locked != versions {
        return Err("Cargo.lock release packages differ from Cargo.toml".to_string());
    }

    let guix_path = root.join("guix.scm");
    let guix = std::fs::read_to_string(&guix_path)
        .map_err(|e| format!("guix.scm unreadable: {e}"))?;
    if extract_guix_version(&guix).as_deref() != Some(RELEASE_EXPECTED_VERSION) {
        return Err("guix.scm version drift".to_string());
    }

    let installer_path = root.join("packaging/install.sh");
    let installer = std::fs::read_to_string(&installer_path)
        .map_err(|e| format!("packaging/install.sh unreadable: {e}"))?;
    let expected_asset = format!("sens-cli_{}_", RELEASE_EXPECTED_VERSION);
    let expected_download = format!("/releases/download/{RELEASE_EXPECTED_TAG}/");
    if !installer.contains(&expected_asset) || !installer.contains(&expected_download) {
        return Err("installer version/tag surface drift".to_string());
    }
    let mut rest = installer.as_str();
    while let Some((_, tail)) = rest.split_once("/releases/download/") {
        let Some((tag, next)) = tail.split_once('/') else {
            break;
        };
        if tag.starts_with('s') && tag.bytes().filter(|b| *b == b'.').count() == 2
            && tag != RELEASE_EXPECTED_TAG
        {
            return Err(format!("installer contains unexpected release tag {tag}"));
        }
        rest = next;
    }

    let release_lisp_path = root.join("scripts/release.lisp");
    let release_lisp = std::fs::read_to_string(&release_lisp_path)
        .map_err(|e| format!("scripts/release.lisp unreadable: {e}"))?;
    if !release_lisp.contains(RELEASE_EXPECTED_VERSION) {
        return Err("scripts/release.lisp required version missing".to_string());
    }
    if let Some((_, suffix)) = release_lisp.split_once("Потрібна одна версія:") {
        if !suffix.chars().take(40).collect::<String>().contains(RELEASE_EXPECTED_VERSION) {
            return Err("scripts/release.lisp required-version line drifted".to_string());
        }
    }
    Ok(())
}

#[test]
fn release_version_alignment_is_consistent_across_native_surfaces() {
    verify_release_version_surfaces(&release_repo_root())
        .unwrap_or_else(|error| panic!("RELEASE_VERSION_ALIGNMENT_BLOCKED: {error}"));
}

#[test]
fn release_version_alignment_fails_closed_on_stale_missing_duplicate_and_registry_mutants() {
    let root = release_repo_root();
    let lock = std::fs::read_to_string(root.join("Cargo.lock")).expect("read Cargo.lock");
    let rows = parse_lock_packages(&lock);
    assert!(validate_release_lock(&rows, RELEASE_EXPECTED_VERSION).is_ok());

    let target = RELEASE_CRATES[0];
    let first = rows
        .iter()
        .position(|row| row.name.as_deref() == Some(target))
        .expect("first release crate exists in lock");

    let mut stale = rows.clone();
    stale[first].version = Some("0.41.0".to_string());
    assert!(validate_release_lock(&stale, RELEASE_EXPECTED_VERSION).is_err(),
        "stale version mutant must be blocked");

    let absent: Vec<_> = rows.iter().filter(|row| row.name.as_deref() != Some(target))
        .cloned().collect();
    assert!(validate_release_lock(&absent, RELEASE_EXPECTED_VERSION).is_err(),
        "missing release crate mutant must be blocked");

    let mut duplicate = rows.clone();
    duplicate.push(rows[first].clone());
    assert!(validate_release_lock(&duplicate, RELEASE_EXPECTED_VERSION).is_err(),
        "duplicate release crate mutant must be blocked");

    let mut external = rows.clone();
    external[first].source = Some(
        "registry+https://github.com/rust-lang/crates.io-index".to_string()
    );
    assert!(validate_release_lock(&external, RELEASE_EXPECTED_VERSION).is_err(),
        "registry impostor mutant must be blocked");
}
