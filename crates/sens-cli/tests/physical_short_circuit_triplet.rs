//! Перевірка фізичного короткого замикання: семантика SENS, пакування Zig/T5M.
use std::{fs, path::PathBuf, process::Command};

#[test]
fn ukr_cond_skips_unsafe_branch_and_preserves_exact_t5m_triplet() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let stem = root.join("examples/migrated/коротке-замикання");
    let source = stem.with_extension("lisp");
    let physical = stem.with_extension("sens");
    let view = fs::read_to_string(&stem).expect("точний бітовий перегляд");
    assert_eq!(view, format!("{}\n", view.trim_end()), "канонічний LF");

    let opened = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
        .arg("open").arg(&physical).output().expect("Zig/T5M open");
    assert!(opened.status.success(), "{:?}", opened.stderr);
    assert_eq!(opened.stdout, view.as_bytes(), "обернений точний перегляд");

    let paired = Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg("--t5m-pair").arg(&source).arg(&physical).output()
        .expect("SENS: українська проєкція ↔ фізична програма");
    assert!(paired.status.success(), "{:?}", paired.stderr);
    assert_eq!(String::from_utf8_lossy(&paired.stdout).trim(), "1");

    let direct = Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg(&physical).output().expect("нативне виконання SENS");
    assert!(direct.status.success(), "{:?}", direct.stderr);
    assert_eq!(direct.stdout, paired.stdout, "семантика не залежить від проєкції");
}
