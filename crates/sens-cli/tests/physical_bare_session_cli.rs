//! CLI boundary checks for current T5M and the Ukrainian source surface.
//! Preserve fail-closed treatment of historical physical fixtures and assert
//! real CLI behavior, not merely unit-level identity or successful exit.
use std::{
    fs,
    path::{Path, PathBuf},
    process::{Command, Output},
    sync::atomic::{AtomicU64, Ordering},
};
static NONCE: AtomicU64 = AtomicU64::new(0);

const MIGRATION_FIXTURES_NOT_CURRENT_T5M: &[&str] = &[
    "tests/fixtures/migration-quote-cohort-main/quote-legacy.sens",
    "tests/fixtures/migration-multiform-cohort-main/two-forms.sens",
    "tests/fixtures/migration-eq-cond-cohort-main/eq-cond-select.sens",
    "tests/fixtures/migration-eq-cond-cohort-main/eq-cond-skip.sens",
    "tests/fixtures/migration-pair-cohort-main/pair-car-cdr.sens",
];

fn repo_path(relative: &str) -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(relative)
}
fn physical_sens(path: &Path) -> Output {
    Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg(path)
        .output()
        .expect("execute actual physical SENS CLI")
}
fn full_macro_baseline(path: &Path) -> Output {
    Command::new(env!("CARGO_BIN_EXE_sens-trit"))
        .arg("eval")
        .arg(path)
        .output()
        .expect("execute comparison CLI")
}

#[test]
fn migration_fixtures_are_not_admitted_by_current_t5m() {
    for relative in MIGRATION_FIXTURES_NOT_CURRENT_T5M {
        let file = repo_path(relative);
        let original = fs::read(&file).expect("real tracked physical fixture");
        assert!(original.iter().all(|byte| *byte < 243));
        let bare = physical_sens(&file);
        let original_default = full_macro_baseline(&file);
        assert_eq!(
            bare.status, original_default.status,
            "{relative} rejection parity"
        );
        assert!(
            !bare.status.success(),
            "migration fixture {relative} must not enter current T5M execution"
        );
        assert!(
            bare.stdout.is_empty(),
            "{relative}: rejection emitted output"
        );
        assert!(
            String::from_utf8_lossy(&bare.stderr).contains("Zig physical T5M rejected"),
            "{relative}: unexpected native diagnostic: {}",
            String::from_utf8_lossy(&bare.stderr)
        );
        assert!(
            !original_default.status.success(),
            "{relative}: T5M baseline admitted the historical fixture"
        );
        assert_eq!(
            fs::read(&file).unwrap(),
            original,
            "{relative}: no source mutation"
        );
    }
}

struct TempPhysical {
    path: PathBuf,
}
impl TempPhysical {
    fn write(bytes: &[u8], ext: &str) -> Self {
        let n = NONCE.fetch_add(1, Ordering::Relaxed);
        let path =
            std::env::temp_dir().join(format!("sens-bare-t5-{}-{n}.{ext}", std::process::id()));
        let mut file = fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&path)
            .expect("no duplicate fixture");
        use std::io::Write;
        file.write_all(bytes).unwrap();
        Self { path }
    }
}
impl Drop for TempPhysical {
    fn drop(&mut self) {
        fs::remove_file(&self.path).expect("remove test fixture");
    }
}

#[test]
fn corrupt_transport_fails_before_any_execution() {
    // 243 is outside the canonical T5M byte alphabet. Keep this negative
    // transport witness independent of Rust-side physical packing.
    let source = TempPhysical::write(&[243u8], "sens");
    let actual = physical_sens(&source.path);
    let baseline = full_macro_baseline(&source.path);
    assert!(
        !actual.status.success(),
        "bad physical bytes must not execute"
    );
    assert!(
        !baseline.status.success(),
        "baseline must reject same input"
    );
    assert!(
        actual.stdout.is_empty(),
        "invalid source must not emit a value"
    );
}

#[test]
fn current_ukrainian_surface_runs_through_sens() {
    let source_text = TempPhysical::write("(як-є ())\n".as_bytes(), "lisp");
    let current = Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg(&source_text.path)
        .output()
        .unwrap();
    assert!(
        current.status.success(),
        "{}",
        String::from_utf8_lossy(&current.stderr)
    );
    assert_eq!(current.stdout, b"()\n");
}
