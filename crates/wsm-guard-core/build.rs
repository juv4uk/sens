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
    // Explicit compatibility builds may compile the host but cannot load
    // SENS Guard sources. The Rust adapter below fails closed in that mode.
    if env::var_os("CARGO_FEATURE_ZIG_SOURCE").is_none() {
        return;
    }
    let root = PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR"))
        .join("../..");
    let compiler = env::var_os("ZIG").unwrap_or_else(|| "zig".into());
    let compiler_label = PathBuf::from(&compiler).display().to_string();
    let pinned = include_str!("../../.zig-version").trim();
    let probe = Command::new(&compiler)
        .arg("version")
        .output()
        .unwrap_or_else(|error| {
            panic!(
                concat!(
                    "Guard exact-source transport requires pinned Zig {0}; cannot execute ",
                    "{1}: {2}. On Windows run ",
                    "`.\\scripts\\with-pinned-zig.ps1 cargo build` from the repository root, ",
                    "or set ZIG to the pinned zig.exe."
                ),
                pinned,
                compiler_label,
                error
            )
        });
    assert!(probe.status.success(), "Guard Zig version probe failed");
    let actual = std::str::from_utf8(&probe.stdout)
        .expect("Zig version is not UTF-8")
        .trim();
    assert_eq!(actual, pinned, "Guard source transport Zig version mismatch");

    let out = PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR"));
    let target_env = env::var("CARGO_CFG_TARGET_ENV").unwrap_or_default();
    let target_os = env::var("CARGO_CFG_TARGET_OS").unwrap_or_default();
    let target_arch = env::var("CARGO_CFG_TARGET_ARCH").expect("CARGO_CFG_TARGET_ARCH");
    // rustc resolves `static=sens_zig_guard_sources` to this MSVC archive name.
    // MinGW/Unix linkers use the conventional lib-prefixed .a archive.
    let archive_name = if target_env == "msvc" {
        "sens_zig_guard_sources.lib"
    } else {
        "libsens_zig_guard_sources.a"
    };
    let archive = out.join(archive_name);
    let mut command = Command::new(&compiler);
    command
        .current_dir(root)
        .arg("build-lib")
        .arg("guard_source_root.zig")
        .arg("-O")
        .arg("ReleaseSafe")
        .arg("-fcompiler-rt")
        .arg("-lc");
    if target_env == "msvc" {
        command
            .arg("-target")
            .arg(format!("{target_arch}-windows-msvc"));
    }
    if target_os != "windows" {
        command.arg("-fPIC");
    }
    let result = command
        .arg(format!("-femit-bin={}", archive.display()))
        .status()
        .expect("Cannot execute Zig Guard source compiler");
    assert!(result.success(), "Zig Guard source compilation failed");
    println!("cargo:rustc-link-search=native={}", out.display());
    println!("cargo:rustc-link-lib=static=sens_zig_guard_sources");
}
