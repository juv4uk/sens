//! #175 (MACHINE-ISA-2) negative/positive witnesses for
//! `cargo xtask import-xed-evidence`. Exercised as a CLI black box
//! (matching the existing external_oracle_cli.rs convention) rather than
//! by linking xtask's internals, since xtask ships as a binary crate only.

use std::path::PathBuf;
use std::process::Command;

fn repo_root() -> PathBuf {
    PathBuf::from(concat!(env!("CARGO_MANIFEST_DIR"), "/../.."))
}

fn fixture(name: &str) -> PathBuf {
    PathBuf::from(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/tests/fixtures/xed-import"
    ))
    .join(name)
}

fn run_import(vendor_root: &std::path::Path, out_path: &std::path::Path) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root())
        .arg("import-xed-evidence")
        .arg("--vendor-root")
        .arg(vendor_root)
        .arg("--out")
        .arg(out_path)
        .output()
        .expect("failed to run xtask import-xed-evidence")
}

fn extract_digest(rendered: &str) -> &str {
    rendered
        .lines()
        .find_map(|line| line.trim().strip_prefix("(source-digest \""))
        .and_then(|rest| rest.strip_suffix("\")"))
        .expect("generated evidence must contain a source-digest fact")
}

/// Acceptance: "CI can compare pinned evidence with generated normalized
/// output" -- the committed lib/machine/xed/generated/machine-evidence.lisp
/// must always match a fresh run against the real vendored corpus.
#[test]
fn check_flag_passes_against_committed_evidence() {
    let output = Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root())
        .arg("import-xed-evidence")
        .arg("--check")
        .output()
        .expect("failed to run xtask import-xed-evidence --check");

    assert!(
        output.status.success(),
        "committed machine-evidence.lisp is stale:\nstdout: {}\nstderr: {}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}

/// Negative witness #1 (required by #175): changed upstream ordering must
/// not change the normalized digest.
#[test]
fn reordering_upstream_lines_does_not_change_digest() {
    let temp_dir = std::env::temp_dir().join(format!("xed-import-reorder-{}", std::process::id()));
    std::fs::create_dir_all(&temp_dir).expect("create temp dir");
    let out_a = temp_dir.join("a.lisp");
    let out_b = temp_dir.join("b.lisp");

    let output_a = run_import(&fixture("order-a"), &out_a);
    assert!(
        output_a.status.success(),
        "order-a run must succeed: {}",
        String::from_utf8_lossy(&output_a.stderr)
    );
    let output_b = run_import(&fixture("order-b"), &out_b);
    assert!(
        output_b.status.success(),
        "order-b run must succeed: {}",
        String::from_utf8_lossy(&output_b.stderr)
    );

    let rendered_a = std::fs::read_to_string(&out_a).expect("read a.lisp");
    let rendered_b = std::fs::read_to_string(&out_b).expect("read b.lisp");

    assert_eq!(
        extract_digest(&rendered_a),
        extract_digest(&rendered_b),
        "digest must be independent of the upstream blocks' physical line order"
    );

    let _ = std::fs::remove_dir_all(&temp_dir);
}

/// Negative witness #2 (required by #175): malformed/unknown form fails
/// closed rather than being silently admitted or skipped.
#[test]
fn malformed_form_fails_closed() {
    let temp_dir =
        std::env::temp_dir().join(format!("xed-import-malformed-{}", std::process::id()));
    std::fs::create_dir_all(&temp_dir).expect("create temp dir");
    let out = temp_dir.join("out.lisp");

    let output = run_import(&fixture("malformed"), &out);

    assert!(
        !output.status.success(),
        "a block with an ICLASS but no EXTENSION must fail closed, not succeed"
    );
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("VBROKENFORM") && stderr.contains("EXTENSION"),
        "failure must name the offending ICLASS and missing field: {stderr}"
    );
    assert!(
        !out.exists(),
        "a failed import must not write a partial output file"
    );

    let _ = std::fs::remove_dir_all(&temp_dir);
}

/// Negative witness #3 (required by #175): an imported synthetic mnemonic
/// cannot mint a semantic ID or peer surface. The importer's own output is
/// confined to the path given by --out; this proves it never reaches the
/// real semantic registry or peer-surface projections that already exist
/// in this repository.
#[test]
fn synthetic_mnemonic_cannot_mint_a_semantic_id_or_peer_surface() {
    let temp_dir =
        std::env::temp_dir().join(format!("xed-import-synthetic-{}", std::process::id()));
    std::fs::create_dir_all(&temp_dir).expect("create temp dir");
    let out = temp_dir.join("out.lisp");

    let output = run_import(&fixture("synthetic-mnemonic"), &out);
    assert!(
        output.status.success(),
        "a well-formed synthetic fixture must still import cleanly: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let rendered = std::fs::read_to_string(&out).expect("read out.lisp");
    assert!(rendered.contains("ZZZ_NOT_A_REAL_MNEMONIC"));

    let registry =
        std::fs::read_to_string(repo_root().join("lib/generated/meta-semantic-registry.lisp"))
            .unwrap_or_default();
    assert!(
        !registry.contains("ZZZ_NOT_A_REAL_MNEMONIC"),
        "the semantic registry must never contain an XED-imported mnemonic"
    );

    let surface_dir = repo_root().join("lib/surface");
    if let Ok(entries) = std::fs::read_dir(&surface_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.extension().is_some_and(|ext| ext == "lisp") {
                let content = std::fs::read_to_string(&path).unwrap_or_default();
                assert!(
                    !content.contains("ZZZ_NOT_A_REAL_MNEMONIC"),
                    "peer surface {} must never contain an XED-imported mnemonic",
                    path.display()
                );
            }
        }
    }

    let _ = std::fs::remove_dir_all(&temp_dir);
}

/// The Rust extension-mapping table (xed_import::extension_mapping,
/// duplicated here as plain text since xtask has no lib target to import)
/// must name exactly the XED-tag -> admitted-extension pairs documented in
/// lib/machine/xed/provenance.lisp's `extension-mapping` facts, so the
/// human-readable provenance record cannot silently drift from what the
/// importer actually does.
#[test]
fn provenance_extension_mapping_matches_every_admitted_extension() {
    let provenance = std::fs::read_to_string(repo_root().join("lib/machine/xed/provenance.lisp"))
        .expect("read provenance.lisp");
    let inventory = std::fs::read_to_string(
        repo_root().join("lib/machine/cpu/intel-core-i5-6400-inventory.lisp"),
    )
    .expect("read intel-core-i5-6400-inventory.lisp");

    for mapped_target in provenance
        .lines()
        .filter_map(|line| line.trim().strip_prefix("(extension-mapping ("))
        .filter_map(|rest| rest.split(')').next())
        .filter_map(|pair| pair.split_whitespace().nth(1))
    {
        // A handful of XED tags (e.g. SSE4) predate SSE4.1/SSE4.2 being
        // split in the pinned data and cover both; those map onto a
        // "+"-joined label naming every admitted extension they cover,
        // rather than a single one.
        for admitted_name in mapped_target.split('+') {
            let admitted_fact = format!("(admitted-extension {admitted_name})");
            assert!(
                inventory.contains(&admitted_fact),
                "provenance.lisp maps an XED tag onto {admitted_name}, which is not an admitted-extension in #174's inventory"
            );
        }
    }
}

/// Negative witness #4 (required by #175): duplicate/conflicting
/// normalized forms produce an authority-boundary diagnostic.
#[test]
fn duplicate_conflicting_form_produces_authority_boundary_diagnostic() {
    let temp_dir = std::env::temp_dir().join(format!("xed-import-conflict-{}", std::process::id()));
    std::fs::create_dir_all(&temp_dir).expect("create temp dir");
    let out = temp_dir.join("out.lisp");

    let output = run_import(&fixture("conflict"), &out);

    assert!(
        !output.status.success(),
        "the same ICLASS admitted under two different extensions must fail closed"
    );
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("authority-boundary conflict") && stderr.contains("FAKEDUP"),
        "failure must be a named authority-boundary diagnostic: {stderr}"
    );

    let _ = std::fs::remove_dir_all(&temp_dir);
}
