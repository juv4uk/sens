//! CLI-level physical T5 execution of already Lisp-owned Core4 mechanisms.
//!
//! D4 LIST/APPEND are already ratified pure exact-domain mechanisms;
//! compare direct physical eval against the explicitly bootstrapped Core4
//! mode without claiming a new resident or historical binary migration.
use std::{
    fs,
    path::PathBuf,
    process::{Command, Output},
    sync::atomic::{AtomicU64, Ordering},
};
static UNIQUE: AtomicU64 = AtomicU64::new(0);

struct PhysicalT5 {
    path: PathBuf,
    bytes: Vec<u8>,
}
impl PhysicalT5 {
    fn from_exact(words: &str) -> Self {
        let bytes = sens::encode_binary_projection_ternary(words).expect("canonical T5");
        assert_eq!(sens::open_ternary_program(&bytes).unwrap(), words);
        assert_eq!(sens::encode_binary_projection_ternary(words).unwrap(), bytes);
        let suffix = UNIQUE.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "sens-core4-sequence-{}-{suffix}.sens", std::process::id(),
        ));
        assert!(!path.exists(), "must never overwrite another test artifact");
        fs::write(&path, &bytes).expect("physical T5 test file");
        Self { path, bytes }
    }
    fn cli(&self, mode: &str) -> Output {
        Command::new(env!("CARGO_BIN_EXE_sens-trit"))
            .arg(mode).arg(&self.path).output()
            .expect("spawn public SENS T5 CLI")
    }
}
impl Drop for PhysicalT5 {
    fn drop(&mut self) {
        let current = fs::read(&self.path).expect("test T5 still exists");
        assert_eq!(current, self.bytes, "CLI must not mutate physical source");
        fs::remove_file(&self.path).expect("clean isolated temp input");
    }
}
fn observed(output: &Output) -> String {
    String::from_utf8(output.stdout.clone()).expect("UTF-8 CLI stdout")
}
fn error(output: &Output) -> String {
    String::from_utf8(output.stderr.clone()).expect("UTF-8 CLI stderr")
}

#[test]
fn public_ratified_d4_list_runs_from_pure_physical_t5_without_core4_bootstrap() {
    // D4:1110 LIST(D3:001 QUOTE(D3:000 EMPTY)).
    let physical = PhysicalT5::from_exact("10 1110 00 10 001 00 000 01 01");
    let opened = physical.cli("open");
    assert!(opened.status.success(), "{}", error(&opened));
    assert_eq!(observed(&opened).trim(), "10 1110 00 10 001 00 000 01 01");

    let bare = physical.cli("eval");
    assert!(bare.status.success(), "ratified D4:1110 LIST is a pure exact-domain mechanism: {}", error(&bare));
    assert_eq!(observed(&bare).trim(), "(())");

    // Optional Core4 bootstrap may supply additional language closures, but
    // may not rewrite the already-ratified D4 LIST identity or its result.
    let bootstrapped = physical.cli("eval-core4");
    assert!(bootstrapped.status.success(), "{}", error(&bootstrapped));
    assert_eq!(observed(&bootstrapped).trim(), "(())");
}

#[test]
fn public_core4_append_uses_existing_lisp_owned_sequence_law() {
    // APPEND (LIST (QUOTE ())) (LIST (QUOTE ()))
    let exact =
        "10 1111 00 10 1110 00 10 001 00 000 01 01 00 10 1110 00 10 001 00 000 01 01 01";
    let physical = PhysicalT5::from_exact(exact);
    let bare = physical.cli("eval");
    assert!(bare.status.success(), "ratified D4:1111 APPEND must execute without host bootstrap: {}", error(&bare));
    assert_eq!(observed(&bare).trim(), "(() ())");
    let current = physical.cli("eval-core4");
    assert!(current.status.success(), "{}", error(&current));
    assert_eq!(observed(&current).trim(), "(() ())");
    let id = PhysicalT5::from_exact(
        "10 1111 00 10 001 00 000 01 00 10 1110 00 10 001 00 000 01 01 01",
    );
    let answer = id.cli("eval-core4");
    assert!(answer.status.success(), "{}", error(&answer));
    assert_eq!(observed(&answer).trim(), "(())");
}

#[test]
fn corrupt_physical_t5_is_rejected_even_under_opt_in_core4() {
    let suffix = UNIQUE.fetch_add(1, Ordering::Relaxed);
    let path = std::env::temp_dir().join(format!(
        "sens-invalid-core4-{}-{suffix}.sens", std::process::id(),
    ));
    assert!(!path.exists());
    fs::write(&path, [0xf3u8]).unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
        .arg("eval-core4").arg(&path).output().unwrap();
    fs::remove_file(&path).unwrap();
    assert!(!output.status.success(), "corrupt T5 cannot reach bootstrap");
}
