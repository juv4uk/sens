//! ORIGINAL machine-block: independent historical Python vs current Rust SENS.
//!
//! IMPORTANT: This proves ONLY observable parity while both runtimes execute
//! the same immutable original .lisp source. It does NOT admit a physical .sens,
//! prove current D2 grammar for converted bytes, or grant release authority.
use sens::{eval_program, load_core_library, Session};
use serde_json::Value as Json;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

const ORIGINAL: &str = "lib/machine/block.lisp";
const GIT_BLOB: &str = "200201b741787c4e144ad4194848acf51d7b439e";

fn root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repository root")
}

/// This is an independent historical evaluator, not Rust SENS.
fn historical_observations(repo: &Path) -> Json {
    let source = repo.join(ORIGINAL);
    let pin = Command::new("git")
        .args(["hash-object", "--"])
        .arg(&source)
        .current_dir(repo)
        .output()
        .expect("git source SHA must be readable");
    assert!(pin.status.success(), "git hash-object failed");
    assert_eq!(String::from_utf8_lossy(&pin.stdout).trim(), GIT_BLOB,
        "the exact pre-existing original Lisp source changed");

    let evidence_path = std::env::temp_dir().join(format!(
        "sens-original-machine-block-parity-{}.json", std::process::id()
    ));
    assert!(!evidence_path.exists(), "do not overwrite existing oracle evidence");
    let witness = Command::new("python3")
        .arg("tests/test_machine_block_historical_oracle.py")
        .arg("--emit-json")
        .arg(&evidence_path)
        .current_dir(repo)
        .output()
        .expect("separate historical source evaluator must run");
    assert!(witness.status.success(),
        "historical evaluator failed: {}", String::from_utf8_lossy(&witness.stderr));
    let bytes = fs::read(&evidence_path).expect("read historical observable evidence");
    fs::remove_file(&evidence_path).expect("remove temporary, not repository, evidence");
    let report: Json = serde_json::from_slice(&bytes).expect("historical oracle JSON");

    assert_eq!(report["schema"], "sens-machine-block-historical-oracle/v1");
    assert_eq!(report["status"], "HISTORICAL_SIDE_ONLY");
    assert_eq!(report["source"], ORIGINAL);
    assert_eq!(report["source_git_blob_sha1"], GIT_BLOB);
    assert_eq!(report["case_count"], 9);
    assert_eq!(report["current_sens_semantic_parity"], "NOT_VERIFIED");
    assert_eq!(report["release_admitted"], false);
    report["cases"].clone()
}

/// Format only *observable data* returned by the independent Python oracle.
/// No Lisp evaluator, resolver, opcode map, or current SENS compiler is reused.
fn observable_to_lisp(value: &Json) -> String {
    match value {
        Json::Array(items) => format!("({})", items.iter()
            .map(observable_to_lisp).collect::<Vec<_>>().join(" ")),
        Json::String(atom) if !atom.is_empty() && atom.bytes()
            .all(|c| c.is_ascii_alphanumeric() || c == b'-' || c == b'_') =>
            atom.clone(),
        other => panic!("unadmitted historical observable data: {other}"),
    }
}

#[test]
fn historical_and_current_rust_execution_match_for_nine_immutable_calls() {
    let repo = root();
    let original = historical_observations(&repo);
    let source = fs::read_to_string(repo.join(ORIGINAL))
        .expect("original machine-block Lisp source exists");

    let mut session = Session::default();
    load_core_library(&mut session).expect("bootstrap current SENS");
    eval_program(&source, &mut session)
        .expect("CURRENT SENS interpreter must execute actual original definitions");

    // Each expression runs CURRENT Rust SENS; the expected structural values
    // are emitted by a SEPARATE original historical Python interpreter.
    let cases = [
        ("empty", "(machine-block-empty)"),
        ("one_nested", "(machine-block-one (quote (mov (r1 r2))))"),
        ("append", "(machine-block-append (quote ((mov (r1 r2)) (branch L1))) (quote ret))"),
        ("concat", "(machine-block-concat (quote ((mov (r1 r2)) (branch L1))) (quote ((label L2))))"),
        ("forms", "(machine-block-forms (quote ((mov (r1 r2)) (branch L1))))"),
        ("identity", "(machine-block (quote ((mov (r1 r2)) (branch L1))))"),
        ("append_empty", "(machine-block-append (quote ()) (quote nop))"),
        ("concat_left_empty", "(machine-block-concat (quote ()) (quote ((mov (r1 r2)) (branch L1))))"),
        ("concat_right_empty", "(machine-block-concat (quote ((mov (r1 r2)) (branch L1))) (quote ()))"),
    ];
    assert_eq!(original.as_object().expect("case keyed observations").len(), cases.len());
    for (name, current_expression) in cases {
        let expected = observable_to_lisp(&original[name]);
        let actual = eval_program(current_expression, &mut session)
            .unwrap_or_else(|e| panic!("CURRENT SENS failed {name}: {e}"))
            .value.to_string();
        assert_eq!(actual, expected,
            "original-source historical and current Rust observations diverge for {name}");
        println!("MACHINE_BLOCK_PARITY_CASE={name} OBSERVABLE={actual}");
    }
    println!("MACHINE_BLOCK_CURRENT_TEXT_PARITY=9/9; PHYSICAL_T5_ORACLE=NOT_VERIFIED");
}

#[test]
fn structural_historical_oracle_expected_values_are_unambiguous() {
    assert_eq!(observable_to_lisp(&serde_json::json!([])), "()");
    assert_eq!(observable_to_lisp(&serde_json::json!([["mov",["r1","r2"]],["branch","L1"]])),
               "((mov (r1 r2)) (branch L1))");
    assert_eq!(observable_to_lisp(&serde_json::json!(["nop"])), "(nop)");
}
