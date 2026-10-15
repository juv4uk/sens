// Compile the exact-byte Zig adapter, not a Rust copy of SENS source.
// The Guard runner intentionally fails closed if the pinned Zig toolchain
// or any source-file byte carrier is unavailable.
use std::{env, path::PathBuf, process::Command};

fn main() {
    for path in [
        "../../.zig-version",
        "../../guard_source_root.zig",
        "../../lib/core.lisp",
        "../../lib/unify.lisp",
        "../../lib/guard.lisp",
    ] {
        println!("cargo:rerun-if-changed={path}");
    }
    println!("cargo:rerun-if-env-changed=ZIG");
    println!("cargo:rerun-if-env-changed=PATH");
    let root = PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR"))
        .join("../..");
    let compiler = env::var_os("ZIG").unwrap_or_else(|| "zig".into());
    let pinned = include_str!("../../.zig-version").trim();
    let probe = Command::new(&compiler)
        .arg("version")
        .output()
        .expect("Guard exact-source transport requires pinned Zig");
    assert!(probe.status.success(), "Guard Zig version probe failed");
    let actual = std::str::from_utf8(&probe.stdout)
        .expect("Zig version is not UTF-8")
        .trim();
    assert_eq!(actual, pinned, "Guard source transport Zig version mismatch");

    let out = PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR"));
    let archive = out.join("libsens_zig_guard_sources.a");
    let result = Command::new(&compiler)
        .current_dir(root)
        .arg("build-lib")
        .arg("guard_source_root.zig")
        .arg("-O")
        .arg("ReleaseSafe")
        .arg("-fcompiler-rt")
        .arg("-lc")
        .arg("-fPIC")
        .arg(format!("-femit-bin={}", archive.display()))
        .status()
        .expect("Cannot execute Zig Guard source compiler");
    assert!(result.success(), "Zig Guard source compilation failed");
    println!("cargo:rustc-link-search=native={}", out.display());
    println!("cargo:rustc-link-lib=static=sens_zig_guard_sources");
}
