use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::time::{SystemTime, UNIX_EPOCH};

const SOURCE_RELATIVE: &str = "examples/migrated/smoke-quote.lisp";

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

fn publish_triplet(tree: &TempTree) -> Triplet {
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
        .arg(SOURCE_RELATIVE)
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

    let lisp = mirror.join(SOURCE_RELATIVE);
    let sens = lisp.with_extension("sens");
    let view = lisp.with_extension("");
    assert!(lisp.is_file(), "publisher must stage canonical .lisp");
    assert!(sens.is_file(), "publisher must stage physical .sens");
    assert!(view.is_file(), "publisher must stage the extensionless bit view");

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
    let triplet = publish_triplet(&tree);
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
fn mismatched_view_is_blocked_without_publishing_an_artifact() {
    let tree = TempTree::new();
    let triplet = publish_triplet(&tree);
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
fn missing_final_lf_is_rejected_as_noncanonical_file_projection() {
    let tree = TempTree::new();
    let triplet = publish_triplet(&tree);
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
    let triplet = publish_triplet(&tree);
    fs::write(&triplet.lisp, b"(атом? ())\n").expect("tamper source projection");
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
    let triplet = publish_triplet(&tree);
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
