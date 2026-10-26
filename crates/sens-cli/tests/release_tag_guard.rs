use std::env;
use std::fs;
use std::path::{Path, PathBuf};

fn root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repository root must exist")
}

fn package_version(root: &Path) -> String {
    let manifest = fs::read_to_string(root.join("crates/sens-cli/Cargo.toml"))
        .expect("RELEASE_BLOCKED: sens-cli Cargo.toml is unreadable");
    let in_package = manifest.split("[package]").nth(1)
        .expect("RELEASE_BLOCKED: sens-cli [package] is missing")
        .split('[').next().unwrap_or("");
    in_package.lines().find_map(|line| {
        let line = line.trim();
        line.strip_prefix("version")
            .and_then(|rest| rest.trim().strip_prefix('='))
            .map(|value| value.trim().trim_matches('"').trim_matches('\'').to_owned())
    }).filter(|value| !value.is_empty())
      .expect("RELEASE_BLOCKED: sens-cli package version is missing")
}

fn canonical_decimal(value: &str) -> bool {
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return false;
    }
    value == "0" || !value.starts_with('0')
}

fn canonical_release_tag(tag: &str) -> bool {
    let Some(version) = tag.strip_prefix('s') else { return false };
    let mut parts = version.split('.');
    let (Some(major), Some(minor), Some(patch), None) =
        (parts.next(), parts.next(), parts.next(), parts.next())
    else {
        return false;
    };
    canonical_decimal(major) && canonical_decimal(minor) && canonical_decimal(patch)
}

fn verify_tag_and_surfaces(root: &Path, tag: &str) -> Result<String, String> {
    if !canonical_release_tag(tag) {
        return Err(format!("invalid canonical release tag {tag:?}"));
    }
    let version = package_version(root);
    let expected_tag = format!("s{version}");
    if tag != expected_tag {
        return Err(format!("tag {tag} != sens-cli package tag {expected_tag}"));
    }

    let installer = fs::read_to_string(root.join("packaging/install.sh"))
        .map_err(|error| format!("installer unreadable: {error}"))?;
    let expected_asset = format!("sens-cli_{version}_");
    let expected_download = format!("/releases/download/{expected_tag}/");
    if !installer.contains(&expected_asset) || !installer.contains(&expected_download) {
        return Err("installer asset/tag surface does not match current package version".to_owned());
    }
    let mut rest = installer.as_str();
    while let Some((_, tail)) = rest.split_once("/releases/download/") {
        let Some((download_tag, next)) = tail.split_once('/') else { break };
        if canonical_release_tag(download_tag) && download_tag != expected_tag {
            return Err(format!("installer contains unexpected release tag {download_tag}"));
        }
        rest = next;
    }

    let release_source = fs::read_to_string(root.join("scripts/release.lisp"))
        .map_err(|error| format!("scripts/release.lisp unreadable: {error}"))?;
    if !release_source.contains(&version) {
        return Err("scripts/release.lisp does not require the current version".to_owned());
    }
    if let Some((_, suffix)) = release_source.split_once("Потрібна одна версія:") {
        if !suffix.chars().take(40).collect::<String>().contains(&version) {
            return Err("scripts/release.lisp version guard is inconsistent".to_owned());
        }
    }
    Ok(version)
}

#[test]
fn release_tag_guard_self_calibrates_on_valid_and_invalid_mutants() {
    let root = root();
    let valid = ["s0.0.0", "s1.2.3", "s42.7.10"];
    for tag in valid {
        assert!(canonical_release_tag(tag), "valid tag rejected: {tag}");
    }
    let invalid = [
        "", "0.42.1", "v0.42.1", "l0.42.1", "s", "s0", "s0.42",
        "s00.42.1", "s0.042.1", "s0.42.01", "s0.42.1-extra",
        "s+1.2.3", "s1..3", "s1.2.3.4",
    ];
    for tag in invalid {
        assert!(!canonical_release_tag(tag), "invalid tag accepted: {tag}");
    }
    let version = package_version(&root);
    let current = format!("s{version}");
    assert_eq!(
        verify_tag_and_surfaces(&root, &current).as_deref(),
        Ok(version.as_str()),
        "current tag/version/installer/release surfaces must agree"
    );
    assert!(
        verify_tag_and_surfaces(&root, "s0.0.0").is_err() && current != "s0.0.0",
        "stale tag mutant must fail closed"
    );
    if let Ok(tag) = env::var("RELEASE_TAG") {
        verify_tag_and_surfaces(&root, &tag)
            .unwrap_or_else(|error| panic!("RELEASE_BLOCKED: {error}"));
    }
}

#[test]
fn release_workflows_accept_only_the_s_tag_prefix() {
    let root = root();
    let release = fs::read_to_string(root.join(".github/workflows/release.yml"))
        .expect("release workflow is readable");
    let publisher = fs::read_to_string(root.join(".github/workflows/release-publish.yml"))
        .expect("release publisher is readable");

    assert!(release.contains("tags: ['s*']"), "release trigger must select s tags");
    assert!(
        release.contains("VERSION=\"${GITHUB_REF_NAME#s}\""),
        "CLI asset version must remove only s"
    );
    assert!(release.contains("-replace '^s',''"), "MSI version must remove only s");
    assert!(
        publisher.contains("test \"$GITHUB_REF_NAME\" = \"s$(python3"),
        "publisher must compare its tag to the s-prefixed package version"
    );
    assert!(!release.contains("tags: ['l*']"), "retired l tags must not trigger release");
    assert!(
        !release.contains("GITHUB_REF_NAME#l"),
        "retired l prefix must not remain in release asset parsing"
    );
}
