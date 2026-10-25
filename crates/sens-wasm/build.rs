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
    println!("cargo:rerun-if-changed=../../.zig-version");
    println!("cargo:rerun-if-changed=../../wasm_source_assets.zig");
    for source in [
        "../../lib/unify.lisp",
        "../../lib/reason.lisp",
        "../../lib/forward.lisp",
        "../../lib/knowledge.lisp",
        "../../lib/persistent-map.lisp",
        "../../lib/persistent-vector.lisp",
        "../../lib/epistemic.lisp",
        "../../lib/surface/uk.lisp",
        "../../lib/surface/ukr.lisp",
        "../../lib/surface/sa.lisp",
    ] {
        println!("cargo:rerun-if-changed={source}");
    }
    for variable in ["ZIG", "PATH", "LOCALAPPDATA"] {
        println!("cargo:rerun-if-env-changed={variable}");
    }

    let manifest_dir = PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").expect("manifest dir"));
    let root = manifest_dir.join("../..");
    let out = PathBuf::from(env::var_os("OUT_DIR").expect("output dir"));
    let target_arch = env::var("CARGO_CFG_TARGET_ARCH").expect("target architecture");
    let target_env = env::var("CARGO_CFG_TARGET_ENV").unwrap_or_default();
    let target_os = env::var("CARGO_CFG_TARGET_OS").unwrap_or_default();
    let is_wasm = target_arch == "wasm32";
    let archive_name = if target_env == "msvc" {
        "sens_wasm_source_assets.lib"
    } else {
        "libsens_wasm_source_assets.a"
    };
    let archive = out.join(archive_name);

    let pinned = include_str!("../../.zig-version").trim();
    let compiler = pinned_zig_compiler(pinned);
    let version = Command::new(&compiler)
        .arg("version")
        .output()
        .expect("sens-wasm source transport requires pinned Zig");
    assert!(version.status.success(), "Zig version probe failed");
    let actual = std::str::from_utf8(&version.stdout)
        .expect("Zig version output is not UTF-8")
        .trim();
    assert_eq!(
        actual, pinned,
        "wrong Zig version for sens-wasm source transport"
    );

    let mut command = Command::new(&compiler);
    command
        .current_dir(&root)
        .arg("build-lib")
        .arg("wasm_source_assets.zig")
        .arg("--name")
        .arg("sens_wasm_source_assets")
        .arg("-O")
        .arg("ReleaseSafe")
        .arg("-fcompiler-rt");
    if is_wasm {
        command.arg("-target").arg("wasm32-freestanding");
    } else {
        command.arg("-lc");
        if target_env == "msvc" {
            command
                .arg("-target")
                .arg(format!("{target_arch}-windows-msvc"));
        }
        if target_os != "windows" {
            command.arg("-fPIC");
        }
    }
    let result = command
        .arg(format!("-femit-bin={}", archive.display()))
        .status()
        .expect("sens-wasm source transport requested: Zig compiler unavailable");
    assert!(
        result.success(),
        "sens-wasm source transport: Zig asset build failed"
    );
    println!("cargo:rustc-link-search=native={}", out.display());
    println!("cargo:rustc-link-lib=static=sens_wasm_source_assets");
}
