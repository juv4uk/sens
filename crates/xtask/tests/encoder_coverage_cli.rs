//! #176 (MACHINE-ISA-3) witnesses for
//! `cargo xtask generate-encoder-coverage`. Same CLI-black-box convention
//! as xed_import_cli.rs.

use std::path::PathBuf;
use std::process::Command;

fn repo_root() -> PathBuf {
    PathBuf::from(concat!(env!("CARGO_MANIFEST_DIR"), "/../.."))
}

fn fixture(name: &str) -> PathBuf {
    PathBuf::from(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/tests/fixtures/encoder-coverage"
    ))
    .join(name)
}

fn run_generate(evidence: &std::path::Path, out: &std::path::Path) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root())
        .arg("generate-encoder-coverage")
        .arg("--evidence")
        .arg(evidence)
        .arg("--out")
        .arg(out)
        .output()
        .expect("failed to run xtask generate-encoder-coverage")
}

/// Acceptance: the coverage report is reproducible and CI-checkable, the
/// same way #175's evidence import is.
#[test]
fn check_flag_passes_against_committed_coverage() {
    let output = Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root())
        .arg("generate-encoder-coverage")
        .arg("--check")
        .output()
        .expect("failed to run xtask generate-encoder-coverage --check");

    assert!(
        output.status.success(),
        "committed coverage.lisp is stale:\nstdout: {}\nstderr: {}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}

/// #176 acceptance: "coverage report has no admitted form with
/// accidental/missing encoder path". Every distinct (extension, ICLASS)
/// pair present in the real #175 evidence must appear in the real coverage
/// report exactly once -- proven independently of the generator's own
/// internals by counting both files directly. Grouping by extension too
/// (not bare ICLASS) matters: MOVD is legitimately admitted twice, once
/// under MMX (GPR<->MMX) and once under SSE2 (GPR<->XMM) -- two different
/// instructions that happen to share a mnemonic, not a duplicate.
#[test]
fn every_admitted_extension_iclass_pair_has_exactly_one_coverage_entry() {
    fn extension_iclass_pairs(text: &str) -> Vec<(String, String)> {
        // Field order differs between machine-evidence.lisp (extension
        // before iclass) and coverage.lisp (iclass before extension), so
        // buffer both per block and flush whenever a new `(form`/`(coverage`
        // block starts, rather than assuming one field always precedes
        // the other.
        let mut extension: Option<String> = None;
        let mut iclass: Option<String> = None;
        let mut pairs = Vec::new();
        let flush = |extension: &mut Option<String>,
                     iclass: &mut Option<String>,
                     pairs: &mut Vec<(String, String)>| {
            if let (Some(e), Some(i)) = (extension.take(), iclass.take()) {
                pairs.push((e, i));
            }
        };
        for line in text.lines() {
            let trimmed = line.trim();
            if trimmed == "(form" || trimmed == "(coverage" {
                flush(&mut extension, &mut iclass, &mut pairs);
            } else if let Some(rest) = trimmed.strip_prefix("(extension ") {
                extension = rest.strip_suffix(')').map(str::to_string);
            } else if let Some(rest) = trimmed.strip_prefix("(iclass \"") {
                iclass = rest.strip_suffix("\")").map(str::to_string);
            }
        }
        flush(&mut extension, &mut iclass, &mut pairs);
        pairs
    }

    let evidence = std::fs::read_to_string(
        repo_root().join("lib/machine/xed/generated/machine-evidence.lisp"),
    )
    .expect("read machine-evidence.lisp");
    let coverage = std::fs::read_to_string(repo_root().join("lib/machine/encoding/coverage.lisp"))
        .expect("read coverage.lisp");

    let mut evidence_pairs = extension_iclass_pairs(&evidence);
    evidence_pairs.sort();
    evidence_pairs.dedup();
    let coverage_pairs = extension_iclass_pairs(&coverage);

    for pair in &evidence_pairs {
        let occurrences = coverage_pairs.iter().filter(|p| *p == pair).count();
        assert_eq!(
            occurrences, 1,
            "(extension, ICLASS) pair {pair:?} appears {occurrences} times in coverage.lisp, must appear exactly once"
        );
    }
    assert_eq!(
        evidence_pairs.len(),
        coverage_pairs.len(),
        "coverage.lisp must have no extra (extension, ICLASS) pairs beyond what #175 admits"
    );
}

/// Every entry must be one of the two allowed statuses -- no silent third
/// outcome (e.g. a typo'd status string that neither "partial" nor
/// "not-yet-implemented" checks would catch).
#[test]
fn every_coverage_entry_has_an_allowed_status() {
    let coverage = std::fs::read_to_string(repo_root().join("lib/machine/encoding/coverage.lisp"))
        .expect("read coverage.lisp");
    let status_lines: Vec<&str> = coverage
        .lines()
        .map(str::trim)
        .filter(|line| line.starts_with("(status "))
        .collect();
    assert!(!status_lines.is_empty());
    for line in status_lines {
        assert!(
            line == "(status partial)" || line == "(status not-yet-implemented)",
            "unexpected coverage status line: {line}"
        );
    }
}

/// Negative witness: a curated "partial" ICLASS that #175's evidence no
/// longer admits must fail closed rather than silently disappearing or
/// being reported against a nonexistent form.
#[test]
fn stale_partial_iclass_not_in_evidence_fails_closed() {
    let temp_dir =
        std::env::temp_dir().join(format!("encoder-coverage-stale-{}", std::process::id()));
    std::fs::create_dir_all(&temp_dir).expect("create temp dir");
    let out = temp_dir.join("coverage.lisp");

    // This fixture's evidence admits only ICLASSes the encoder does NOT
    // cover (no RET_NEAR/MOV/ADD at all), so the curated partial table
    // names ICLASSes the fixture never admits.
    let output = run_generate(&fixture("no-implemented-iclasses.lisp"), &out);

    assert!(
        !output.status.success(),
        "a curated partially-implemented ICLASS missing from the evidence must fail closed"
    );
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("RET_NEAR") || stderr.contains("MOV") || stderr.contains("ADD"),
        "failure must name the stale curated ICLASS: {stderr}"
    );

    let _ = std::fs::remove_dir_all(&temp_dir);
}

/// Positive control for the fixture format itself: a minimal evidence file
/// that does admit RET_NEAR imports cleanly and marks it partial.
#[test]
fn minimal_evidence_with_ret_near_is_marked_partial() {
    let temp_dir =
        std::env::temp_dir().join(format!("encoder-coverage-minimal-{}", std::process::id()));
    std::fs::create_dir_all(&temp_dir).expect("create temp dir");
    let out = temp_dir.join("coverage.lisp");

    let output = run_generate(&fixture("minimal-with-ret-near.lisp"), &out);
    assert!(
        output.status.success(),
        "minimal evidence with RET_NEAR admitted must succeed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let rendered = std::fs::read_to_string(&out).expect("read generated coverage");
    assert!(rendered.contains("(iclass \"RET_NEAR\")"));
    assert!(rendered.contains("(status partial)"));

    let _ = std::fs::remove_dir_all(&temp_dir);
}
