//! #1675: canonical completion gate for the active authored Lisp library.
//!
//! This test intentionally delegates "is this executable surface safely
//! convertible?" to the real `sens-to-sens` tool.  The older repository
//! inventories are conservative lexical ratchets and may still count names in
//! quote/data/shadowing positions.  Migration completion must not be faked by
//! rewriting those positions.

use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repo root")
}

fn tool() -> Command {
    Command::new(env!("CARGO_BIN_EXE_sens-to-sens"))
}

fn is_explicit_non_implementation(rel: &str) -> bool {
    rel.starts_with("lib/generated/")
        || rel.starts_with("lib/surface/")
        || rel == "lib/machine/encoding/coverage.lisp"
}

fn is_language_definition_file(rel: &str) -> bool {
    let Some(name) = rel.strip_prefix("lib/") else {
        return false;
    };
    name.starts_with("core") && name.ends_with(".lisp") && !name.contains('/')
}

fn active_lisp_files() -> Vec<(String, PathBuf)> {
    fn walk(root: &Path, dir: &Path, out: &mut Vec<(String, PathBuf)>) {
        for entry in fs::read_dir(dir).expect("read active lib directory") {
            let entry = entry.expect("read active lib entry");
            let path = entry.path();
            if path.is_dir() {
                walk(root, &path, out);
                continue;
            }
            if path.extension().and_then(|ext| ext.to_str()) != Some("lisp") {
                continue;
            }
            let rel = path
                .strip_prefix(root)
                .expect("active lib path under repo")
                .to_string_lossy()
                .replace('\\', "/");
            if !is_explicit_non_implementation(&rel) {
                out.push((rel, path));
            }
        }
    }

    let root = repo_root();
    let mut files = Vec::new();
    walk(&root, &root.join("lib"), &mut files);
    files.sort_by(|left, right| left.0.cmp(&right.0));
    files
}

fn run_check(files: &[PathBuf], language: bool) -> Output {
    let mut command = tool();
    command.current_dir(repo_root()).arg("--check");
    if language {
        command.arg("--language");
    }
    for file in files {
        command.arg(file);
    }
    command.output().expect("run canonical sens-to-sens check")
}

fn assert_clean(label: &str, files: &[(String, PathBuf)], language: bool) {
    assert!(!files.is_empty(), "{label}: no files selected");

    let paths: Vec<PathBuf> = files.iter().map(|(_, path)| path.clone()).collect();
    let output = run_check(&paths, language);
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    assert!(
        output.status.success(),
        "{label}: canonical sens-to-sens found remaining parser-convertible heads \
         or could not analyze the active library.\nstatus={}\nstdout:\n{}\nstderr:\n{}",
        output.status,
        stdout,
        stderr
    );

    for (rel, _) in files {
        let marker = format!("{rel}: convertible=0");
        assert!(
            stdout.contains(&marker),
            "{label}: missing zero-conversion witness for {rel}\nstdout:\n{stdout}"
        );
    }
}

#[test]
fn active_authored_lib_has_no_parser_convertible_surface_heads() {
    let files = active_lisp_files();
    let (language, ordinary): (Vec<_>, Vec<_>) = files
        .into_iter()
        .partition(|(rel, _)| is_language_definition_file(rel));

    // Core family files define table-owned language functions.  The canonical
    // migration tool must inspect them in --language mode so recursive calls
    // through those first definitions are not hidden as ordinary shadowing.
    assert_clean("language-definition lib", &language, true);

    // Every other active authored library file uses ordinary lexical rules.
    assert_clean("ordinary active lib", &ordinary, false);
}

#[test]
fn completion_gate_exclusions_are_narrow_and_explicit() {
    assert!(is_explicit_non_implementation(
        "lib/machine/encoding/coverage.lisp"
    ));
    assert!(is_explicit_non_implementation(
        "lib/surface/uk-acceptance.lisp"
    ));
    assert!(is_explicit_non_implementation(
        "lib/generated/function-table.lisp"
    ));

    assert!(!is_explicit_non_implementation("lib/meta-eval.lisp"));
    assert!(!is_explicit_non_implementation(
        "lib/machine/dispatch/native-first-coverage.lisp"
    ));
    assert!(!is_explicit_non_implementation("lib/core.lisp"));
}