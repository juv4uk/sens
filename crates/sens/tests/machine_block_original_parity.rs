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
use std::sync::atomic::{AtomicUsize, Ordering};

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

    static NEXT_EVIDENCE_FILE: AtomicUsize = AtomicUsize::new(0);
    let evidence_path = std::env::temp_dir().join(format!(
        "sens-original-machine-block-parity-{}-{}.json",
        std::process::id(),
        NEXT_EVIDENCE_FILE.fetch_add(1, Ordering::Relaxed)
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

/// Prove the exact original physical T5 artifact and then execute its bindings
/// with *physically encoded* Text7 call-head probes. Source-mode expressions
/// such as "(machine-block-empty)" are deliberately not used for those calls:
/// their Text7 binding keys differ from plain human symbols.
#[test]
fn physical_t5_executes_empty_and_blocks_unencoded_quoted_symbols() {
    let repo = root();
    let historical = historical_observations(&repo);
    let source_path = repo.join(ORIGINAL);
    let source_bytes = fs::read(&source_path).expect("read pinned original source bytes");

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

    static NEXT_WORKSPACE: AtomicUsize = AtomicUsize::new(0);
    let work = std::env::temp_dir().join(format!(
        "sens-machine-block-physical-t5-{}-{}",
        std::process::id(),
        NEXT_WORKSPACE.fetch_add(1, Ordering::Relaxed)
    ));
    assert!(!work.exists(), "never reuse/overwrite a prior physical-T5 test workspace");

    let original_input = work.join("original-source");
    let probe_input = work.join("source-with-probes");
    let original_output = work.join("original-out");
    let probe_output = work.join("probe-out");
    let original_report = work.join("original-report.json");
    let probe_report = work.join("probe-report.json");
    fs::create_dir_all(original_input.join("lib/machine")).expect("create original source root");
    fs::create_dir_all(probe_input.join("lib/machine")).expect("create probe source root");

    // First migrate the byte-for-byte original source alone. This is the exact
    // physical candidate shape that admission would evaluate; it is never
    // copied into the repository by this test.
    fs::write(original_input.join(ORIGINAL), &source_bytes)
        .expect("copy exact original source bytes");
    let original_migration = Command::new("python3")
        .arg(repo.join("scripts/migrate-three-pass.py"))
        .arg(&original_input)
        .arg("--out").arg(&original_output)
        .arg("--source-era").arg("legacy")
        .arg("--report").arg(&original_report)
        .current_dir(&repo)
        .output()
        .expect("run canonical migrator on the unmodified original");
    assert!(original_migration.status.success(),
        "original-only migration BLOCKED: stdout={} stderr={}",
        String::from_utf8_lossy(&original_migration.stdout),
        String::from_utf8_lossy(&original_migration.stderr));

    let original_manifest: Json = serde_json::from_slice(
        &fs::read(&original_report).expect("read original migration report")
    ).expect("valid original migration report");
    assert_eq!(original_manifest["schema"], "sens-three-pass-t5-migration/v3");
    assert_eq!(original_manifest["summary"]["files_seen"], 1);
    assert_eq!(original_manifest["summary"]["files_written"], 1);
    assert_eq!(original_manifest["summary"]["files_blocked"], 0);
    assert_eq!(original_manifest["files"][0]["path"], ORIGINAL);
    assert_eq!(original_manifest["files"][0]["source_blob_sha"], GIT_BLOB);
    let original_blob = Command::new("git")
        .args(["hash-object", "--"])
        .arg(original_input.join(ORIGINAL))
        .current_dir(&repo)
        .output()
        .expect("read original source Git blob");
    assert!(original_blob.status.success(), "git hash-object must accept original source");
    assert_eq!(String::from_utf8_lossy(&original_blob.stdout).trim(), GIT_BLOB);

    let original_physical_path = original_output.join(Path::new(ORIGINAL).with_extension("sens"));
    let original_physical = fs::read(&original_physical_path)
        .expect("read physical T5 generated from exact original source");
    let original_visible = sens::open_ternary_program(&original_physical)
        .expect("original physical T5 must decode through current codec");
    let original_forms = sens::parse_canonical_binary(&original_visible)
        .expect("original physical T5 must pass canonical D2 parser");
    assert_eq!(original_forms.len(), 6, "original has six top-level definitions");

    // Probe the case that the existing canonical source vocabulary can
    // actually express: a zero-argument global call whose Text7 target is
    // resolved from the six preceding physical DEFINE forms.
    let mut probe_bytes = source_bytes.clone();
    if !probe_bytes.ends_with(b"\n") {
        probe_bytes.push(b'\n');
    }
    probe_bytes.extend_from_slice(cases[0].1.as_bytes());
    probe_bytes.push(b'\n');
    fs::write(probe_input.join(ORIGINAL), &probe_bytes)
        .expect("write external empty-call probe source");
    let probe_migration = Command::new("python3")
        .arg(repo.join("scripts/migrate-three-pass.py"))
        .arg(&probe_input)
        .arg("--out").arg(&probe_output)
        .arg("--source-era").arg("legacy")
        .arg("--report").arg(&probe_report)
        .current_dir(&repo)
        .output()
        .expect("run canonical migrator on physical empty-call probe");
    assert!(probe_migration.status.success(),
        "single supported physical Text7 call was BLOCKED: stdout={} stderr={}",
        String::from_utf8_lossy(&probe_migration.stdout),
        String::from_utf8_lossy(&probe_migration.stderr));
    let probe_manifest: Json = serde_json::from_slice(
        &fs::read(&probe_report).expect("read empty-call probe report")
    ).expect("valid empty-call probe report");
    assert_eq!(probe_manifest["summary"]["files_written"], 1);
    assert_eq!(probe_manifest["summary"]["files_blocked"], 0);
    let probe_source_path = probe_input.join(ORIGINAL);
    let probe_blob = Command::new("git")
        .args(["hash-object", "--"])
        .arg(&probe_source_path)
        .current_dir(&repo)
        .output()
        .expect("read actual Git blob identity for ephemeral probe source");
    assert!(probe_blob.status.success(), "git hash-object must accept probe source");
    let actual_probe_blob = String::from_utf8_lossy(&probe_blob.stdout).trim().to_owned();
    assert_eq!(probe_manifest["files"][0]["source_blob_sha"], actual_probe_blob);
    assert_eq!(probe_manifest["files"][0]["status"], "written");
    assert_ne!(actual_probe_blob, GIT_BLOB,
        "observer probe is not itself the immutable original blob");

    let probe_physical_path = probe_output.join(Path::new(ORIGINAL).with_extension("sens"));
    let probe_physical = fs::read(&probe_physical_path)
        .expect("read physical T5 containing the empty Text7 call");
    let probe_visible = sens::open_ternary_program(&probe_physical)
        .expect("physical probe T5 must decode through current codec");
    let probe_forms = sens::parse_canonical_binary(&probe_visible)
        .expect("physical probe T5 must pass canonical D2 parser");
    assert_eq!(probe_forms.len(), original_forms.len() + 1);
    for (index, (original_form, probe_form)) in original_forms.iter()
        .zip(probe_forms.iter())
        .enumerate()
    {
        assert_eq!(format!("{original_form:?}"), format!("{probe_form:?}"),
            "adding the empty-call probe changed original physical form {index}");
    }

    // Load the six definitions from the original-only T5 and execute the call
    // only after decoding its own contextual Text7 frame from packed bytes.
    let mut session = Session::default();
    load_core_library(&mut session).expect("load existing Lisp-owned Core4");
    sens::eval_parsed_expressions(&original_forms, &mut session)
        .expect("execute exact original definitions from physical T5");
    let empty_call = &probe_forms[original_forms.len()];
    let actual = sens::eval_parsed_expressions(std::slice::from_ref(empty_call), &mut session)
        .expect("physical T5 zero-argument global call must execute")
        .value.to_string();
    let expected = observable_to_lisp(&historical["empty"]);
    assert_eq!(actual, expected, "physical T5 empty case must match historical oracle");
    println!("MACHINE_BLOCK_PHYSICAL_T5_CASE=empty OBSERVABLE={actual}");

    // The remaining eight witnesses require quoted symbol data (mov, r1, r2,
    // branch, labels, etc.). D7/Text7 is currently admitted only in proven
    // binder/reference roles, not as an implicit symbol value. Preserve the
    // fail-closed contract: capture the exact blocker, publish no .sens, and
    // keep this gap visible instead of retagging ordinary W7/list data.
    let blocked_input = work.join("source-with-unencoded-symbol-data");
    let blocked_output = work.join("blocked-output");
    let blocked_report = work.join("blocked-report.json");
    fs::create_dir_all(blocked_input.join("lib/machine"))
        .expect("create external blocked-data source root");
    let mut blocked_bytes = source_bytes.clone();
    if !blocked_bytes.ends_with(b"\n") {
        blocked_bytes.push(b'\n');
    }
    for (_, expression) in &cases[1..] {
        blocked_bytes.extend_from_slice(expression.as_bytes());
        blocked_bytes.push(b'\n');
    }
    fs::write(blocked_input.join(ORIGINAL), &blocked_bytes)
        .expect("write external symbol-data probe");
    let blocked_migration = Command::new("python3")
        .arg(repo.join("scripts/migrate-three-pass.py"))
        .arg(&blocked_input)
        .arg("--out").arg(&blocked_output)
        .arg("--source-era").arg("legacy")
        .arg("--report").arg(&blocked_report)
        .current_dir(&repo)
        .output()
        .expect("run canonical migrator on unsupported symbol-data probe");
    assert!(!blocked_migration.status.success(),
        "unencoded quoted symbols must BLOCK rather than become nonbinary T5");
    let blocked_manifest: Json = serde_json::from_slice(
        &fs::read(&blocked_report).expect("read blocked symbol-data report")
    ).expect("valid blocked symbol-data report");
    assert_eq!(blocked_manifest["summary"]["files_written"], 0);
    assert_eq!(blocked_manifest["summary"]["files_blocked"], 1);
    let blocker = blocked_manifest["files"][0]["reason"].as_str().unwrap_or("");
    assert!(blocker.contains("requires exact D1..D9 0/1 word"),
        "expected explicit exact-word blocker, got: {blocker}");
    assert!(blocker.contains("mov"),
        "report should identify the first unsupported symbol payload, got: {blocker}");
    assert!(!blocked_output.join(Path::new(ORIGINAL).with_extension("sens")).exists(),
        "blocked symbol data must not leave a candidate .sens");
    let blocked_source_path = blocked_input.join(ORIGINAL);
    let blocked_blob = Command::new("git")
        .args(["hash-object", "--"])
        .arg(&blocked_source_path)
        .current_dir(&repo)
        .output()
        .expect("read Git blob identity for the blocked probe");
    assert!(blocked_blob.status.success(), "git hash-object must accept blocked probe");
    assert_eq!(
        blocked_manifest["files"][0]["source_blob_sha"],
        String::from_utf8_lossy(&blocked_blob.stdout).trim()
    );

    fs::remove_dir_all(&work).expect("remove isolated external physical-T5 workspace");
    println!("MACHINE_BLOCK_PHYSICAL_T5_ORACLE=empty 1/1; QUOTED_SYMBOL_DATA=BLOCKED_WITH_REASON; ORIGINAL_REPOSITORY_WRITTEN=false; RELEASE_ADMITTED=false");
}

#[test]
fn structural_historical_oracle_expected_values_are_unambiguous() {
    assert_eq!(observable_to_lisp(&serde_json::json!([])), "()");
    assert_eq!(observable_to_lisp(&serde_json::json!([["mov",["r1","r2"]],["branch","L1"]])),
               "((mov (r1 r2)) (branch L1))");
    assert_eq!(observable_to_lisp(&serde_json::json!(["nop"])), "(nop)");
}
