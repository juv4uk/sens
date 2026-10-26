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

#[test]
fn part_ii_exact_carrier_preserves_value_across_ukrainian_projection() {
    // Конкретна Part II: ратифіковане слово -> Zig T5M -> бінарний SENS,
    // і незалежна українська поверхня -> той самий виконавець SENS.
    // Д1:0 і Д3:000 — різні значення, хоч обоє мають нульовий payload.
    for (bits, ukrainian, expected) in [
        ("1", "(атом? (як-є ()))\n", "1\n"),
        ("0", "(хибне? (атом? (як-є ())))\n", "0\n"),
        ("000", "(як-є ())\n", "()\n"),
    ] {
        let words = sens::parse_binary_source_words(bits)
            .unwrap_or_else(|error| {
                panic!("test_id=part-ii layer=reader bits={bits} error={error}")
            })
            .into_iter()
            .map(|token| token.word)
            .collect::<Vec<_>>();
        let bytes = sens_cli::zig_transport::encode_t5m_direct(&words)
            .expect("test_id=part-ii layer=Zig-T5M-encode");
        let recovered = sens_cli::zig_transport::decode_t5m_words(&bytes)
            .expect("test_id=part-ii layer=Zig-T5M-inverse");
        assert_eq!(
            recovered, words,
            "test_id=part-ii layer=carrier bits={bits}"
        );

        let binary = TempPhysical::write(&bytes, "sens");
        let opened = trit_open(&binary.path);
        assert!(
            opened.status.success(),
            "test_id=part-ii layer=open bits={bits}"
        );
        assert_eq!(
            opened.stdout,
            format!("{bits}\n").as_bytes(),
            "test_id=part-ii layer=exact-width bits={bits}"
        );

        let physical = physical_sens(&binary.path);
        assert!(
            physical.status.success(),
            "test_id=part-ii layer=binary-SENS bits={bits} error={}",
            String::from_utf8_lossy(&physical.stderr)
        );
        let source = TempPhysical::write(ukrainian.as_bytes(), "lisp");
        let projected = Command::new(env!("CARGO_BIN_EXE_sens"))
            .arg(&source.path)
            .output()
            .expect("test_id=part-ii layer=Ukrainian-SENS");
        assert!(
            projected.status.success(),
            "test_id=part-ii layer=Ukrainian-SENS bits={bits} error={}",
            String::from_utf8_lossy(&projected.stderr)
        );
        assert_eq!(
            physical.stdout,
            expected.as_bytes(),
            "test_id=part-ii layer=binary-result bits={bits}"
        );
        assert_eq!(
            projected.stdout, physical.stdout,
            "test_id=part-ii layer=projection-parity bits={bits}"
        );

        let explicit = full_macro_baseline(&binary.path);
        assert!(
            explicit.status.success(),
            "test_id=part-ii layer=Zig-eval bits={bits}"
        );
        assert_eq!(
            explicit.stdout, physical.stdout,
            "test_id=part-ii layer=execution-paths bits={bits}"
        );
    }

    // Відмінність доменів є семантичною, не лише друкарською:
    // COND приймає Д1:1, але відхиляє Д3:000 як предикат.
    for (canonical, allowed) in [
        ("10 110 00 10 1 00 1 01 01", true),
        ("10 110 00 10 000 00 1 01 01", false),
    ] {
        let words = sens::parse_binary_source_words(canonical)
            .expect("test_id=part-ii layer=D2-framed-reader")
            .into_iter()
            .map(|token| token.word)
            .collect::<Vec<_>>();
        let bytes = sens_cli::zig_transport::encode_t5m_direct(&words)
            .expect("test_id=part-ii layer=D2-Zig-mint");
        assert_eq!(
            sens_cli::zig_transport::decode_t5m_words(&bytes).unwrap(),
            words,
            "test_id=part-ii layer=D2-inverse"
        );
        let file = TempPhysical::write(&bytes, "sens");
        let result = physical_sens(&file.path);
        assert_eq!(
            result.status.success(),
            allowed,
            "test_id=part-ii layer=D1-only-cond input={canonical} stdout={} stderr={}",
            String::from_utf8_lossy(&result.stdout),
            String::from_utf8_lossy(&result.stderr)
        );
        if allowed {
            assert_eq!(result.stdout, b"1\n", "test_id=part-ii layer=COND-D1:1");
        } else {
            assert!(
                result.stdout.is_empty(),
                "test_id=part-ii layer=fail-closed"
            );
        }
    }
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
