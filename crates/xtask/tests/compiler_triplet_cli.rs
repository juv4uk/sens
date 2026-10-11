use sens::encode_binary_projection_ternary;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::time::{SystemTime, UNIX_EPOCH};

const CANONICAL_SOURCE: &[u8] = "(як-є ())\n".as_bytes();
const CANONICAL_VIEW: &[u8] = b"10 001 00 000 01\n";

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

fn write_triplet(root: &Path, stem: &str, source: &[u8], view: &[u8]) -> PathBuf {
    let sens = root.join(format!("{stem}.sens"));
    let lisp = root.join(format!("{stem}.lisp"));
    let view_path = root.join(stem);
    let visible = std::str::from_utf8(view).expect("triplet view is UTF-8/ASCII");
    let physical = encode_binary_projection_ternary(visible)
        .expect("fixture view encodes using the canonical SENS T5 codec");

    fs::write(&lisp, source).expect("write Lisp projection");
    fs::write(&view_path, view).expect("write extensionless word view");
    fs::write(&sens, physical).expect("write physical T5 projection");
    sens
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
fn canonical_three_file_projection_reaches_the_sens_compiler() {
    let tree = TempTree::new();
    let sens = write_triplet(tree.path(), "program", CANONICAL_SOURCE, CANONICAL_VIEW);
    let artifact = tree.path().join("artifact.bin");

    let output = compiler_triplet(&sens, &artifact);
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
    let mismatched_view = b"10 100 00 000 01\n";
    let sens = write_triplet(tree.path(), "mismatch-view", CANONICAL_SOURCE, mismatched_view);
    let artifact = tree.path().join("must-not-exist.bin");

    let output = compiler_triplet(&sens, &artifact);
    assert!(!output.status.success());
    assert!(
        !artifact.exists(),
        "a projection mismatch must not publish compiler evidence"
    );
}

#[test]
fn missing_final_lf_is_rejected_as_noncanonical_file_projection() {
    let tree = TempTree::new();
    let sens = write_triplet(
        tree.path(),
        "missing-lf",
        CANONICAL_SOURCE,
        b"10 001 00 000 01",
    );
    let artifact = tree.path().join("must-not-exist.bin");

    let output = compiler_triplet(&sens, &artifact);
    assert!(!output.status.success());
    assert!(
        !artifact.exists(),
        "a noncanonical view must not publish compiler evidence"
    );
}

#[test]
fn source_and_machine_view_must_lower_to_the_same_exact_program() {
    let tree = TempTree::new();
    let sens = write_triplet(
        tree.path(),
        "mismatch-source",
        b"(інакше ())\n",
        CANONICAL_VIEW,
    );
    let artifact = tree.path().join("must-not-exist.bin");

    let output = compiler_triplet(&sens, &artifact);
    assert!(!output.status.success());
    assert!(
        !artifact.exists(),
        "source/view identity mismatch must not publish compiler evidence"
    );
}

#[test]
fn sw1_and_triplet_modes_cannot_be_selected_together() {
    let tree = TempTree::new();
    let sens = write_triplet(tree.path(), "program", CANONICAL_SOURCE, CANONICAL_VIEW);
    let sw1 = tree.path().join("input.sw1");
    fs::write(&sw1, b"not a SW1 stream").expect("write negative SW1 control");
    let artifact = tree.path().join("must-not-exist.bin");

    let repo_root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    let output = Command::new(env!("CARGO_BIN_EXE_xtask"))
        .current_dir(repo_root)
        .args(["compiler-compile", "--input"])
        .arg(sw1)
        .arg("--triplet")
        .arg(sens)
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
