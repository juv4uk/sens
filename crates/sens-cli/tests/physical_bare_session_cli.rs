//! CLI boundary checks for current T5M and the Ukrainian source surface.
//! Assert the current T5M open path and real CLI behavior, not merely
//! unit-level identity or successful exit.
use std::{
    fs,
    path::{Path, PathBuf},
    process::{Command, Output},
    sync::atomic::{AtomicU64, Ordering},
};
static NONCE: AtomicU64 = AtomicU64::new(0);

const DEFAULT_T5M_OPEN_FIXTURES: &[&str] = &[
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
fn trit_open(path: &Path) -> Output {
    Command::new(env!("CARGO_BIN_EXE_sens-trit"))
        .arg("open")
        .arg(path)
        .output()
        .expect("execute default-T5M read-only open")
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
fn sens_trit_open_reads_default_t5m_fixtures_without_execution_or_mutation() {
    for relative in DEFAULT_T5M_OPEN_FIXTURES {
        let file = repo_path(relative);
        let original = fs::read(&file).expect("real tracked physical fixture");
        let words = sens_cli::zig_transport::decode_t5m_words(&original)
            .unwrap_or_else(|error| panic!("{relative}: Zig/T5M exact-width reference decode: {error}"));
        let expected = format!("{}\n", sens::render_binary_words_spaced(&words));
        let opened = trit_open(&file);
        assert!(
            opened.status.success(),
            "{relative}: {}",
            String::from_utf8_lossy(&opened.stderr)
        );
        assert_eq!(
            opened.stdout,
            expected.as_bytes(),
            "{relative}: default T5M projection"
        );
        assert!(
            opened.stderr.is_empty(),
            "{relative}: open must not execute or warn"
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

