//! Історична матриця #845 — тільки перевірка межі даних.
//! Скасовані твердження про SID8 як семантичну ідентичність тут не виконуються.
//! Чинну поведінку D1/D3/D4 перевіряють відповідні доменні тести.

use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(|path| path.parent())
        .expect("repo root")
        .to_path_buf()
}

#[test]
fn matrix_contract_does_not_copy_axis_payloads() {
    let source = fs::read_to_string(repo_root().join("contracts/semantic-coordinate-matrix-845.lisp"))
        .expect("historical coordinate matrix contract");

    for forbidden in [
        "kernel-entry-status",
        "math-entry-sid",
        "machine-entry-sid",
        "pair-field-load",
        "integer-add",
        "common-lisp",
        "car-cons-left-inverse",
        "x86-lower-",
        "admitted-form",
    ] {
        assert!(
            !source.contains(forbidden),
            "matrix contract must not copy axis payload {forbidden}"
        );
    }
}
