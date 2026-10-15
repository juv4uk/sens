// Zig owns the DEFAULT sens-cli physical transport. The Rust-only CLI is an
// explicit --no-default-features compatibility build, never a silent fallback.
// Standalone SENS core/WASM do not inherit the sens-cli physical backend.
use std::{env, path::PathBuf, process::Command};

fn main() {
    println!("cargo:rerun-if-changed=../../.zig-version");
    println!("cargo:rerun-if-changed=../../research/zig-codecs/t5/t5.zig");
    println!("cargo:rerun-if-changed=../../research/zig-codecs/f3c/f3c.zig");
    println!("cargo:rerun-if-changed=../../research/zig-codecs/transport_abi.zig");
    println!("cargo:rerun-if-changed=../../zig_transport_root.zig");
    // Zig @embedFile holds the linter source: never serve a stale asset in Cargo.
    println!("cargo:rerun-if-changed=../../lib/linter.lisp");
    println!("cargo:rerun-if-changed=../../language-contract.lisp");
    println!("cargo:rerun-if-changed=../../lib/surface/sa.lisp");
    // E1 ABI v2 imports the existing Zig physical reader/writer. Rebuild the
    // static corridor archive when its encoding law or CRC mechanism changes.
    println!("cargo:rerun-if-changed=../../research/zig-codecs/transport/e1.zig");
    println!("cargo:rerun-if-changed=../../research/zig-codecs/transport/e1_writer.zig");
    println!("cargo:rerun-if-changed=../../research/zig-codecs/transport/fields.zig");
    // Zig is resolved from the explicit ZIG override or from PATH.
    // Without these triggers Cargo could silently reuse a stale Zig archive
    // after its compiler selection changes, bypassing the pinned version probe.
    println!("cargo:rerun-if-env-changed=ZIG");
    println!("cargo:rerun-if-env-changed=PATH");
    if env::var_os("CARGO_FEATURE_ZIG_TRANSPORT").is_none() {
        return;
    }
    let root = PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR"))
        .join("../..");
    let out = PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR"));
    let archive = out.join("libsens_zig_transport.a");
    let compiler = env::var_os("ZIG").unwrap_or_else(|| "zig".into());
    // Toolchain identity is not SENS semantic authority. Refuse version drift.
    let pinned = include_str!("../../.zig-version").trim();
    let version = Command::new(&compiler)
        .arg("version")
        .output()
        .expect("zig-transport requires the pinned Zig compiler");
    assert!(version.status.success(), "zig-transport: Zig version probe failed");
    let actual = std::str::from_utf8(&version.stdout)
        .expect("zig-transport: Zig version output is not UTF-8").trim();
    assert_eq!(actual, pinned, "zig-transport: wrong Zig version, expected repository .zig-version");
    let result = Command::new(&compiler)
        .current_dir(&root)
        .arg("build-lib")
        .arg("zig_transport_root.zig")
        .arg("-O")
        .arg("ReleaseFast")
        .arg("-lc")
        .arg("-fPIC")
        .arg(format!("-femit-bin={}", archive.display()))
        .status()
        .expect("zig-transport requested: Zig compiler unavailable");
    assert!(result.success(), "zig-transport requested: Zig C ABI compile failed");
    println!("cargo:rustc-link-search=native={}", out.display());
    println!("cargo:rustc-link-lib=static=sens_zig_transport");
}
