use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::time::{SystemTime, UNIX_EPOCH};

const SOURCE_RELATIVE: &str = "examples/migrated/smoke-quote.lisp";
const NESTED_SOURCE_RELATIVE: &str = "examples/migrated/smoke-nested.lisp";

struct TempTree(PathBuf);

impl TempTree {
    fn new() -> Self {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("system clock after UNIX epoch")
            .as_nanos();
        let path = std::env::temp_dir().join(format!(
            "sens-compiler-triplet-{}-{nonce}",
            std::process::id()
        ));
        fs::create_dir(&path).expect("create unique triplet temp directory");
        Self(path)
    }

    fn path(&self) -> &Path {
        &self.0
    }
}

impl Drop for TempTree {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

struct Triplet {
    lisp: PathBuf,
    sens: PathBuf,
    view: PathBuf,
}

fn publish_triplet(tree: &TempTree, source_relative: &str) -> Triplet {
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("resolve repository root");
    let mirror = tree.path().join("mirror");
    let report = tree.path().join("triplet-report.json");
    let output = Command::new("python3")
        .current_dir(&repo_root)
        .arg("scripts/publish_verified_uk_triplets.py")
        .arg("--mirror")
        .arg(&mirror)
        .arg("--report")
        .arg(&report)
        .arg("--write")
        .arg(source_relative)
        .output()
        .expect("canonical three-projection publisher should execute");

    assert!(
        output.status.success(),
        "triplet publisher failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(
        report.is_file(),
        "triplet publisher should create its provenance report"
    );
    let report_text = fs::read_to_string(&report).expect("read triplet publisher report");
    assert!(
        report_text.contains("\"original_executables_oracle_certified\": 0"),
        "mechanical triplet projection must not claim semantic-oracle admission"
    );
    assert!(
        report_text.contains("written-mechanical-only-not-oracle-admitted"),
        "publisher status must preserve its explicit semantic-admission boundary"
    );

    let lisp = mirror.join(source_relative);
    let sens = lisp.with_extension("sens");
    let view = lisp.with_extension("");
    assert!(lisp.is_file(), "publisher must stage canonical .lisp");
    assert!(sens.is_file(), "publisher must stage physical .sens");
    assert!(
        view.is_file(),
        "publisher must stage the extensionless bit view"
    );

    Triplet { lisp, sens, view }
}

fn compiler_triplet(sens: &Path, output: &Path) -> Output {
    let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root)
        .args(["compiler-compile", "--triplet"])
        .arg(sens)
        .arg("--out")
        .arg(output)
        .output()
        .expect("compiler-compile CLI should execute")
}

#[test]
fn real_three_projection_publisher_output_reaches_the_sens_compiler() {
    let tree = TempTree::new();
    let triplet = publish_triplet(&tree, SOURCE_RELATIVE);
    let artifact = tree.path().join("artifact.bin");

    let output = compiler_triplet(&triplet.sens, &artifact);
    assert!(
        output.status.success(),
        "compiler-compile --triplet failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let bytes = fs::read(&artifact).expect("accepted triplet wrote compiler evidence");
    assert!(!bytes.is_empty(), "compiler evidence must not be empty");
}

#[test]
fn real_three_projection_nested_program_reaches_the_sens_compiler() {
    let tree = TempTree::new();
    let triplet = publish_triplet(&tree, NESTED_SOURCE_RELATIVE);
    let artifact = tree.path().join("nested-artifact.bin");

    let output = compiler_triplet(&triplet.sens, &artifact);
    assert!(
        output.status.success(),
        "nested three-projection compiler run failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(
        !fs::read(&artifact)
            .expect("nested compiler artifact")
            .is_empty(),
        "nested source must produce a canonical compiler artifact"
    );
}

#[test]
fn mismatched_view_is_blocked_without_publishing_an_artifact() {
    let tree = TempTree::new();
    let triplet = publish_triplet(&tree, SOURCE_RELATIVE);
    fs::write(&triplet.view, b"10 100 00 000 01\n").expect("tamper extensionless view");
    let artifact = tree.path().join("must-not-exist.bin");

    let output = compiler_triplet(&triplet.sens, &artifact);
    assert!(!output.status.success());
    assert!(
        !artifact.exists(),
        "a projection mismatch must not publish compiler evidence"
    );
}

#[test]
fn mismatched_physical_t5_is_blocked_without_publishing_an_artifact() {
    let tree = TempTree::new();
    let triplet = publish_triplet(&tree, SOURCE_RELATIVE);
    let other_tree = TempTree::new();
    let other = publish_triplet(&other_tree, NESTED_SOURCE_RELATIVE);
    fs::copy(&other.sens, &triplet.sens).expect("replace T5 with a different valid program");
    let artifact = tree.path().join("must-not-exist.bin");

    let output = compiler_triplet(&triplet.sens, &artifact);
    assert!(!output.status.success());
    assert!(
        !artifact.exists(),
        "a valid but different physical T5 program must not compile against stale siblings"
    );
}

#[test]
fn missing_final_lf_is_rejected_as_noncanonical_file_projection() {
    let tree = TempTree::new();
    let triplet = publish_triplet(&tree, SOURCE_RELATIVE);
    fs::write(&triplet.view, b"10 001 00 000 01").expect("remove canonical final LF");
    let artifact = tree.path().join("must-not-exist.bin");

    let output = compiler_triplet(&triplet.sens, &artifact);
    assert!(!output.status.success());
    assert!(
        !artifact.exists(),
        "a noncanonical view must not publish compiler evidence"
    );
}

#[test]
fn source_and_machine_view_must_lower_to_the_same_exact_program() {
    let tree = TempTree::new();
    let triplet = publish_triplet(&tree, SOURCE_RELATIVE);
    fs::write(&triplet.lisp, "(атом? ())\n".as_bytes()).expect("tamper source projection");
    let artifact = tree.path().join("must-not-exist.bin");

    let output = compiler_triplet(&triplet.sens, &artifact);
    assert!(!output.status.success());
    assert!(
        !artifact.exists(),
        "source/view identity mismatch must not publish compiler evidence"
    );
}

#[test]
fn sw1_and_triplet_modes_cannot_be_selected_together() {
    let tree = TempTree::new();
    let triplet = publish_triplet(&tree, SOURCE_RELATIVE);
    let sw1 = tree.path().join("input.sw1");
    fs::write(&sw1, b"not a SW1 stream").expect("write negative SW1 control");
    let artifact = tree.path().join("must-not-exist.bin");

    let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    let output = Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root)
        .args(["compiler-compile", "--input"])
        .arg(sw1)
        .arg("--triplet")
        .arg(triplet.sens)
        .arg("--out")
        .arg(&artifact)
        .output()
        .expect("compiler-compile CLI should execute");

    assert!(!output.status.success());
    assert!(
        !artifact.exists(),
        "ambiguous input mode must not publish compiler evidence"
    );
}

#[test]
fn existing_artifact_is_never_overwritten() {
    let tree = TempTree::new();
    let triplet = publish_triplet(&tree, SOURCE_RELATIVE);
    let artifact = tree.path().join("immutable.bin");
    fs::write(&artifact, b"pre-existing evidence").expect("seed output file");

    let output = compiler_triplet(&triplet.sens, &artifact);
    assert!(!output.status.success());
    assert_eq!(
        fs::read(&artifact).expect("original artifact remains"),
        b"pre-existing evidence"
    );
}

#[cfg(unix)]
#[test]
fn symlinked_physical_t5_is_rejected() {
    use std::os::unix::fs::symlink;

    let tree = TempTree::new();
    let triplet = publish_triplet(&tree, SOURCE_RELATIVE);
    let alias = tree.path().join("symlink-alias");
    let lisp = alias.with_extension("lisp");
    let sens = alias.with_extension("sens");
    let view = alias.with_extension("");
    fs::copy(&triplet.lisp, &lisp).expect("copy source projection");
    fs::copy(&triplet.view, &view).expect("copy bit-view projection");
    symlink(&triplet.sens, &sens).expect("create physical T5 symlink");
    let artifact = tree.path().join("must-not-exist.bin");

    let output = compiler_triplet(&sens, &artifact);
    assert!(!output.status.success());
    assert!(
        !artifact.exists(),
        "symlinked T5 input must not publish compiler evidence"
    );
}
