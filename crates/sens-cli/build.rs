// Zig owns the DEFAULT sens-cli physical transport. The Rust-only CLI is an
// explicit --no-default-features compatibility build, never a silent fallback.
// Standalone SENS core/WASM do not inherit the sens-cli physical backend.
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
    println!("cargo:rerun-if-changed=../../research/zig-codecs/t5/t5.zig");
    println!("cargo:rerun-if-changed=../../research/zig-codecs/t5m.zig");
    println!("cargo:rerun-if-changed=../../research/zig-codecs/t5m3.zig");
    println!("cargo:rerun-if-changed=../../research/zig-codecs/f3c/f3c.zig");
    println!("cargo:rerun-if-changed=../../research/zig-codecs/transport_abi.zig");
    // Cargo's directory dependency watch is recursive (Cargo Book).
    // Future Zig 0.16 codec imports MUST invalidate the Rust-linked archive,
    // not only today's hand-listed leaf files. Source bits stay Zig-owned.
    println!("cargo:rerun-if-changed=../../research/zig-codecs");
    println!("cargo:rerun-if-changed=../../zig_transport_root.zig");
    println!("cargo:rerun-if-changed=../../domain_projection_assets.zig");
    // Zig @embedFile holds the linter's physical T5M pair: never serve a stale asset.
    println!("cargo:rerun-if-changed=../../lib/linter.sens");
    println!("cargo:rerun-if-changed=../../lib/unify.lisp");
    println!("cargo:rerun-if-changed=../../lib/unify.sens");
    println!("cargo:rerun-if-changed=../../lib/reason.lisp");
    println!("cargo:rerun-if-changed=../../lib/reason.sens");
    println!("cargo:rerun-if-changed=../../lib/forward.lisp");
    println!("cargo:rerun-if-changed=../../lib/forward.sens");
    println!("cargo:rerun-if-changed=../../lib/knowledge.lisp");
    println!("cargo:rerun-if-changed=../../lib/knowledge.sens");
    println!("cargo:rerun-if-changed=../../lib/persistent-map.lisp");
    println!("cargo:rerun-if-changed=../../lib/persistent-map.sens");
    println!("cargo:rerun-if-changed=../../lib/world.lisp");
    println!("cargo:rerun-if-changed=../../lib/world.sens");
    println!("cargo:rerun-if-changed=../../lib/content-store.lisp");
    println!("cargo:rerun-if-changed=../../lib/content-store.sens");
    println!("cargo:rerun-if-changed=../../lib/lisp-fs.lisp");
    println!("cargo:rerun-if-changed=../../lib/lisp-fs.sens");
    println!("cargo:rerun-if-changed=../../tests/fixtures/wsm-fs-record-producer.lisp");
    println!("cargo:rerun-if-changed=../../tests/fixtures/wsm-fs-record-producer.sens");
    println!("cargo:rerun-if-changed=../../lib/persistent-vector.sens");
    println!("cargo:rerun-if-changed=../../lib/time.lisp");
    println!("cargo:rerun-if-changed=../../tests/semantic/d9-string-append-physical.lisp");
    println!("cargo:rerun-if-changed=../../lib/epistemic.sens");
    println!("cargo:rerun-if-changed=../../lib/meta-eval.sens");
    println!("cargo:rerun-if-changed=../../lib/repl-core.sens");
    println!("cargo:rerun-if-changed=../../language-contract.lisp");
    println!("cargo:rerun-if-changed=../../lib/surface/sa.lisp");
    println!("cargo:rerun-if-changed=../../lib/surface/ukr.lisp");
    println!("cargo:rerun-if-changed=../../lib/surface/uk.lisp");
    println!("cargo:rerun-if-changed=../../lib/surface/uk-docs.lisp");
    println!("cargo:rerun-if-changed=../../lib/domains");
    println!("cargo:rerun-if-changed=../../lib/compiler-nucleus.lisp");
    println!("cargo:rerun-if-changed=../../contracts/compiler-nucleus-identity-corpus-v1.tsv");
    println!("cargo:rerun-if-changed=../../contracts/bija3-l1-l5-ratification.lisp");
    println!("cargo:rerun-if-changed=../../contracts/d4-bootstrap-ratification.lisp");
    println!("cargo:rerun-if-changed=../../knowledge/bija3-l1-l5-structure-projection.json");
    println!(
        "cargo:rerun-if-changed=../../knowledge/d4-bootstrap-compiler-structure-projection.json"
    );
    // Zig embeds this release artifact into the linked archive; a manifest
    // change must invalidate Cargo's previous Zig build before packaging.
    println!("cargo:rerun-if-changed=../../packaging/islands-manifest-v1.json");
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
    println!("cargo:rerun-if-env-changed=LOCALAPPDATA");
    println!("cargo:rerun-if-env-changed=SENS_ZIG_PORTABLE_LINUX");
    if env::var_os("CARGO_FEATURE_ZIG_TRANSPORT").is_none() {
        return;
    }
    let root =
        PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR")).join("../..");
    let out = PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR"));
    let target_env = env::var("CARGO_CFG_TARGET_ENV").unwrap_or_default();
    let target_os = env::var("CARGO_CFG_TARGET_OS").unwrap_or_default();
    let target_arch = env::var("CARGO_CFG_TARGET_ARCH").expect("CARGO_CFG_TARGET_ARCH");
    let portable_linux = env::var("SENS_ZIG_PORTABLE_LINUX").unwrap_or_default() == "1";
    let archive_name = if target_env == "msvc" {
        "sens_zig_transport.lib"
    } else {
        "libsens_zig_transport.a"
    };
    let archive = out.join(archive_name);
    // Toolchain identity is not SENS semantic authority. Refuse version drift.
    let pinned = include_str!("../../.zig-version").trim();
    let compiler = pinned_zig_compiler(pinned);
    let version = Command::new(&compiler)
        .arg("version")
        .output()
        .expect("zig-transport requires the pinned Zig compiler");
    assert!(
        version.status.success(),
        "zig-transport: Zig version probe failed"
    );
    let actual = std::str::from_utf8(&version.stdout)
        .expect("zig-transport: Zig version output is not UTF-8")
        .trim();
    assert_eq!(
        actual, pinned,
        "zig-transport: wrong Zig version, expected repository .zig-version"
    );
    let mut command = Command::new(&compiler);
    command
        .current_dir(&root)
        .arg("build-lib")
        .arg("zig_transport_root.zig")
        .arg("-O")
        // Zig ABI reads caller-owned physical bytes: keep optimization AND
        // runtime safety checks at the default Rust-to-Zig ingress.
        .arg("ReleaseSafe")
        // Zig 0.16 static archives do not bundle compiler-rt by default.
        // Preserve ReleaseSafe stack probes: provide __zig_probe_stack through
        // Zig compiler-rt instead of disabling stack checks or inventing a stub.
        .arg("-fcompiler-rt")
        .arg("-lc");
    if portable_linux {
        assert_eq!(target_os, "linux", "portable Linux Zig target requested for non-Linux build");
        assert_eq!(target_arch, "x86_64", "portable Linux Zig target is x86-64 only");
        assert_eq!(target_env, "gnu", "portable Linux Zig target requires the GNU ABI");
        // The Linux release asset must not inherit the hosted runner CPU or glibc.
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
        .expect("zig-transport requested: Zig compiler unavailable");
    assert!(
        result.success(),
        "zig-transport requested: Zig C ABI compile failed"
    );
    println!("cargo:rustc-link-search=native={}", out.display());
    println!("cargo:rustc-link-lib=static=sens_zig_transport");
}
