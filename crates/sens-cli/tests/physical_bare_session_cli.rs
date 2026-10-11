//! Pure physical SENS uses Session::bare; legacy source and explicit macro
//! bootstraps must remain separate. Prove real CLI output parity, not merely
//! unit-level identity or successful exit status.
use std::{
    fs,
    path::{Path, PathBuf},
    process::{Command, Output},
    sync::atomic::{AtomicU64, Ordering},
};
static NONCE: AtomicU64 = AtomicU64::new(0);

const ADMITTED: &[&str] = &[
    "tests/fixtures/migration-quote-cohort-main/quote-legacy.sens",
    "tests/fixtures/migration-multiform-cohort-main/two-forms.sens",
    "tests/fixtures/migration-eq-cond-cohort-main/eq-cond-select.sens",
    "tests/fixtures/migration-eq-cond-cohort-main/eq-cond-skip.sens",
    "tests/fixtures/migration-pair-cohort-main/pair-car-cdr.sens",
];

fn repo_path(relative: &str) -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..").join(relative)
}
fn physical_sens(path: &Path) -> Output {
    Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg(path).output().expect("execute actual physical SENS CLI")
}
fn full_macro_baseline(path: &Path) -> Output {
    Command::new(env!("CARGO_BIN_EXE_sens-trit"))
        .arg("eval").arg(path).output().expect("execute comparison CLI")
}

#[test]
fn every_admitted_physical_program_preserves_default_session_cli_oracle() {
    for relative in ADMITTED {
        let file = repo_path(relative);
        let original = fs::read(&file).expect("real tracked physical fixture");
        assert!(original.iter().all(|byte| *byte < 243));
        let bare = physical_sens(&file);
        let original_default = full_macro_baseline(&file);
        assert_eq!(bare.status, original_default.status, "{relative} exit parity");
        assert!(bare.status.success(), "{relative}: {:?}\n{:?}", bare.stderr, original_default.stderr);
        assert_eq!(bare.stdout, original_default.stdout, "{relative}: exact stdout");
        assert_eq!(bare.stderr, original_default.stderr, "{relative}: exact stderr");
        assert!(!bare.stdout.is_empty(), "{relative}: nonempty result");
        assert_eq!(fs::read(&file).unwrap(), original, "{relative}: no source mutation");
    }
}

struct TempPhysical {
    path: PathBuf,
}
impl TempPhysical {
    fn write(bytes: &[u8], ext: &str) -> Self {
        let n = NONCE.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "sens-bare-t5-{}-{n}.{ext}", std::process::id()
        ));
        let mut file = fs::OpenOptions::new().write(true).create_new(true)
            .open(&path).expect("no duplicate fixture");
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
fn corrupt_transport_and_invalid_d2_still_fail_before_any_execution() {
    for malformed in [
        vec![243u8], // physically impossible base-3 byte
        sens::encode_ternary_words(&sens::parse_binary_source_words("01")
            .unwrap().into_iter().map(|w| w.word).collect::<Vec<_>>()).unwrap(),
    ] {
        let source = TempPhysical::write(&malformed, "sens");
        let actual = physical_sens(&source.path);
        let baseline = full_macro_baseline(&source.path);
        assert!(!actual.status.success(), "bad physical bytes must not execute");
        assert!(!baseline.status.success(), "baseline must reject same input");
        assert!(actual.stdout.is_empty(), "invalid source must not emit a value");
    }
}

#[test]
fn no_implicit_core4_or_legacy_source_reinterpretation() {
    // D4 LIST(QUOTE EMPTY): this is a real D2/T5 program but requires the
    // *explicit* Lisp-owned Core4 bootstrap, not automatic macro injection.
    let bytes = sens::encode_binary_projection_ternary(
        "10 1110 00 10 001 00 000 01 01",
    ).expect("exact typed T5 words");
    let source = TempPhysical::write(&bytes, "sens");
    let bare = physical_sens(&source.path);
    let default = full_macro_baseline(&source.path);
    assert!(!bare.status.success(), "bare physical program cannot admit Core4 LIST");
    assert!(!default.status.success(), "default physical route also cannot admit LIST");
    assert!(bare.stdout.is_empty());
    assert!(String::from_utf8_lossy(&bare.stderr).contains("1110"));

    // Textual compatibility is deliberately NOT routed through bare Session.
    let source_text = TempPhysical::write(b"(+ 1 2)\n", "lisp");
    let canonical = Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg(&source_text.path).output().unwrap();
    let historical = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
        .arg(&source_text.path).output().unwrap();
    assert!(canonical.status.success(), "{:?}", canonical.stderr);
    assert_eq!(canonical.stdout, historical.stdout);
    assert_eq!(canonical.stderr, historical.stderr);
    assert_eq!(canonical.stdout, b"3\n");
}
