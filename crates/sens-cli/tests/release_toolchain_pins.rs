use std::fs;
use std::path::{Path, PathBuf};

const RELEASE_WORKFLOWS: &[&str] = &[
    ".github/workflows/release.yml",
    ".github/workflows/release-preflight.yml",
    ".github/workflows/release-smoke-short.yml",
    ".github/workflows/current-binary-preflight.yml",
    ".github/workflows/publish-binary-master.yml",
];
const RELEASE_GATING_WORKFLOWS: &[&str] = &[
    ".github/workflows/ci.yml",
    ".github/workflows/ci-hosted.yml",
    ".github/workflows/important-file-guard.yml",
    ".github/workflows/binary-program-e2e.yml",
    ".github/workflows/vertical-day-smoke.yml",
    ".github/workflows/vertical-day-immutable-smoke.yml",
    ".github/workflows/triple-projection-gate.yml",
    ".github/workflows/physical-binary-sens-cli.yml",
    ".github/workflows/audit-t5-program-syntax.yml",
];
const TOOLCHAIN_ACTION: &str = "dtolnay/rust-toolchain";

fn root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repository root must exist")
}

fn pinned_rust_channel(root: &Path) -> String {
    let path = root.join("rust-toolchain.toml");
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("RELEASE_PINS_BLOCKED: {}: {error}", path.display()));
    for line in source.lines() {
        let line = line.trim();
        if let Some(value) = line.strip_prefix("channel") {
            if let Some(value) = value.trim().strip_prefix('=') {
                let value = value.trim().trim_matches('"').trim_matches('\'');
                assert!(!value.is_empty(), "RELEASE_PINS_BLOCKED: empty toolchain channel");
                return value.to_owned();
            }
        }
    }
    panic!("RELEASE_PINS_BLOCKED: rust-toolchain.toml has no [toolchain].channel");
}

fn is_step(line: &str) -> bool {
    let line = line.trim_start();
    line.starts_with("- ") || line.starts_with("-\t")
}

fn action_reference(line: &str) -> Option<&str> {
    let line = line.trim_start();
    let line = line.strip_prefix("- ").unwrap_or(line).trim_start();
    let value = line.strip_prefix("uses:")?.trim();
    value.split_whitespace().next()
}

fn requested_toolchain(line: &str) -> Option<&str> {
    let line = line.trim_start();
    let value = line.strip_prefix("toolchain:")?.trim();
    Some(value.trim_matches('"').trim_matches('\''))
}

fn pinned_sha(value: &str) -> bool {
    value.len() == 40 && value.bytes().all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
}

fn verify_workflow(root: &Path, relative: &str, rust_channel: &str) {
    let path = root.join(relative);
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("RELEASE_PINS_BLOCKED: {} is missing/unreadable: {error}", relative));
    let mut block: Vec<&str> = Vec::new();
    let mut blocks: Vec<Vec<&str>> = Vec::new();
    for line in source.lines() {
        if is_step(line) {
            if !block.is_empty() {
                blocks.push(std::mem::take(&mut block));
            }
            block.push(line);
        } else if !block.is_empty() {
            block.push(line);
        }
    }
    if !block.is_empty() {
        blocks.push(block);
    }

    for (index, block) in blocks.iter().enumerate() {
        let mut action: Option<&str> = None;
        let mut toolchains: Vec<&str> = Vec::new();
        for line in block {
            if let Some(value) = action_reference(line) {
                action = Some(value);
            }
            if let Some(value) = requested_toolchain(line) {
                toolchains.push(value);
            }
        }
        let Some(value) = action else { continue };
        if value.starts_with("./") {
            continue;
        }
        let (name, pin) = value.rsplit_once('@').unwrap_or_else(|| {
            panic!("RELEASE_PINS_BLOCKED: {relative}:step{} action has no immutable ref: {value}", index + 1)
        });
        if name == TOOLCHAIN_ACTION {
            assert_eq!(
                pin, rust_channel,
                "RELEASE_PINS_BLOCKED: {relative}:step{} toolchain ref {pin} != {rust_channel}",
                index + 1
            );
            for requested in toolchains {
                assert_eq!(
                    requested, rust_channel,
                    "RELEASE_PINS_BLOCKED: {relative}:step{} with.toolchain {requested} != {rust_channel}",
                    index + 1
                );
            }
        } else {
            assert!(
                pinned_sha(pin),
                "RELEASE_PINS_BLOCKED: {relative}:step{} {name} is not pinned to a 40-hex SHA (got {pin:?})",
                index + 1
            );
        }
    }
}

#[test]
fn release_path_workflows_pin_rust_and_all_external_actions() {
    let root = root();
    let rust_channel = pinned_rust_channel(&root);
    let mut paths = Vec::from(RELEASE_WORKFLOWS);
    paths.extend_from_slice(RELEASE_GATING_WORKFLOWS);
    paths.sort_unstable();
    paths.dedup();
    assert_eq!(paths.len(), 14, "release pin inventory changed; review scope explicitly");
    for relative in paths {
        verify_workflow(&root, relative, &rust_channel);
    }
}
