// Compile the exact-byte Zig adapter, not a Rust copy of SENS source.
// The Guard runner intentionally fails closed if the pinned Zig toolchain
// or any source-file byte carrier is unavailable.
use std::{env, path::PathBuf, process::Command};

fn pinned_zig_compiler(_pinned: &str) -> std::ffi::OsString {
    if let Some(compiler) = env::var_os("ZIG") {
        return compiler;
    }
    #[cfg(windows)]
    if let Some(local_app_data) = env::var_os("LOCALAPPDATA") {
        let cached = PathBuf::from(local_app_data)
            .join("SENS")
            .join("zig")
            .join(format!("zig-x86_64-windows-{_pinned}"))
            .join("zig.exe");
        if cached.is_file() {
            return cached.into_os_string();
        }
    }
    "zig".into()
}

fn main() {
    for path in [
        "../../.zig-version",
        "../../guard_source_root.zig",
        "../../lib/core.sens",
        "../../lib/unify.sens",
        "../../lib/guard.sens",
    ] {
        println!("cargo:rerun-if-changed={path}");
    }
    println!("cargo:rerun-if-env-changed=ZIG");
    println!("cargo:rerun-if-env-changed=PATH");
    println!("cargo:rerun-if-env-changed=LOCALAPPDATA");
    println!("cargo:rerun-if-env-changed=SENS_ZIG_PORTABLE_LINUX");
    // Explicit compatibility builds may compile the host but cannot load
    // SENS Guard sources. The Rust adapter below fails closed in that mode.
    if env::var_os("CARGO_FEATURE_ZIG_SOURCE").is_none() {
        return;
    }
    let root =
        PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR")).join("../..");
    let pinned = include_str!("../../.zig-version").trim();
    let compiler = pinned_zig_compiler(pinned);
    let compiler_label = PathBuf::from(&compiler).display().to_string();
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
                pinned, compiler_label, error
            )
        });
    assert!(probe.status.success(), "Guard Zig version probe failed");
    let actual = std::str::from_utf8(&probe.stdout)
        .expect("Zig version is not UTF-8")
        .trim();
    assert_eq!(
        actual, pinned,
        "Guard source transport Zig version mismatch"
    );

    let out = PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR"));
    let target_env = env::var("CARGO_CFG_TARGET_ENV").unwrap_or_default();
    let target_os = env::var("CARGO_CFG_TARGET_OS").unwrap_or_default();
    let target_arch = env::var("CARGO_CFG_TARGET_ARCH").expect("CARGO_CFG_TARGET_ARCH");
    let portable_linux = env::var("SENS_ZIG_PORTABLE_LINUX").unwrap_or_default() == "1";
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
    if portable_linux {
        assert_eq!(target_os, "linux", "portable Linux Zig target requested for non-Linux build");
        assert_eq!(target_arch, "x86_64", "portable Linux Zig target is x86-64 only");
        assert_eq!(target_env, "gnu", "portable Linux Zig target requires the GNU ABI");
        command
            .arg("-target")
            .arg("x86_64-linux-gnu.2.35")
            .arg("-mcpu")
            .arg("baseline");
    } else if target_env == "msvc" {
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
