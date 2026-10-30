use std::{
    collections::HashSet,
    env, fs,
    path::{Path, PathBuf},
    process::Command,
};

#[path = "build_support/projection_transfer.rs"]
mod projection_transfer;
use projection_transfer::projection_sources;

#[derive(Debug, Clone)]
enum Expr {
    Symbol(String),
    Text(String),
    List(Vec<Expr>),
}

#[derive(Debug, Clone, PartialEq)]
enum Token {
    Open,
    Close,
    Atom(String),
    Text(String),
}

fn tokenize(source: &str, label: &str) -> Vec<Token> {
    let mut chars = source.chars().peekable();
    let mut result = Vec::new();
    while let Some(ch) = chars.next() {
        match ch {
            ';' => while chars.next().is_some_and(|next| next != '\n') {},
            '(' => result.push(Token::Open),
            ')' => result.push(Token::Close),
            '"' => {
                let mut value = String::new();
                let mut closed = false;
                while let Some(next) = chars.next() {
                    match next {
                        '"' => {
                            closed = true;
                            break;
                        }
                        '\\' => {
                            let escaped = chars
                                .next()
                                .unwrap_or_else(|| panic!("{label}: dangling escape in string"));
                            value.push(match escaped {
                                'n' => '\n',
                                'r' => '\r',
                                't' => '\t',
                                '0' => '\0',
                                other => other,
                            });
                        }
                        other => value.push(other),
                    }
                }
                assert!(closed, "{label}: unterminated string");
                result.push(Token::Text(value));
            }
            ch if ch.is_whitespace() => {}
            first => {
                let mut atom = String::from(first);
                while chars.peek().is_some_and(|next| {
                    !next.is_whitespace() && *next != '(' && *next != ')' && *next != ';'
                }) {
                    atom.push(chars.next().expect("peeked character"));
                }
                result.push(Token::Atom(atom));
            }
        }
    }
    result
}

fn parse_expr(tokens: &[Token], cursor: &mut usize, label: &str) -> Expr {
    let token = tokens
        .get(*cursor)
        .unwrap_or_else(|| panic!("{label}: unexpected EOF"));
    *cursor += 1;
    match token {
        Token::Atom(value) => Expr::Symbol(value.clone()),
        Token::Text(value) => Expr::Text(value.clone()),
        Token::Open => {
            let mut values = Vec::new();
            while tokens.get(*cursor) != Some(&Token::Close) {
                assert!(*cursor < tokens.len(), "{label}: unterminated list");
                values.push(parse_expr(tokens, cursor, label));
            }
            *cursor += 1;
            Expr::List(values)
        }
        Token::Close => panic!("{label}: unexpected close parenthesis"),
    }
}

fn parse_all(source: &str, label: &str) -> Vec<Expr> {
    let tokens = tokenize(source, label);
    let mut cursor = 0;
    let mut forms = Vec::new();
    while cursor < tokens.len() {
        forms.push(parse_expr(&tokens, &mut cursor, label));
    }
    forms
}

fn symbol<'a>(expr: &'a Expr, label: &str) -> &'a str {
    match expr {
        Expr::Symbol(value) => value,
        _ => panic!("{label}: expected symbol, got {expr:?}"),
    }
}

fn rust_str(value: &str) -> String {
    format!("{:?}", value)
}

fn add_entry(
    out: &mut String,
    source: &str,
    domain: u16,
    bits: &str,
    column: &str,
    value: &Expr,
    label: &str,
) {
    let (kind, text) = match value {
        Expr::Symbol(value) => ("Symbol", value.as_str()),
        Expr::Text(value) => ("Text", value.as_str()),
        Expr::List(items) if items.is_empty() => {
            out.push_str(&format!("    Entry {{ source: ProjectionSource::{source}, domain: {domain}, bits: {}, column: {}, value: ProjectionValue::EmptyList }},\n", rust_str(bits), rust_str(column)));
            return;
        }
        Expr::List(_) => panic!("{label}: nested list is not a projection value: {value:?}"),
    };
    out.push_str(&format!("    Entry {{ source: ProjectionSource::{source}, domain: {domain}, bits: {}, column: {}, value: ProjectionValue::{kind}({}) }},\n", rust_str(bits), rust_str(column), rust_str(text)));
}

fn domain_tables(root: &Path, compiler: &std::ffi::OsStr, out: &mut String) {
    let transferred = Command::new(compiler)
        .current_dir(root)
        .args([
            "run",
            "bootstrap_t5m.zig",
            "-O",
            "ReleaseSafe",
            "--",
            "--projection-tables",
        ])
        .output()
        .expect("receive domain projection bytes through pinned Zig");
    assert!(
        transferred.status.success(),
        "Zig projection transfer rejected: {}",
        String::from_utf8_lossy(&transferred.stderr)
    );
    let sources = projection_sources(&transferred.stdout)
        .expect("Zig returned invalid domain projection frames");
    for domain in 1..=10u16 {
        let relative = format!("lib/domains/d{domain}.lisp");
        let path = root.join(&relative);
        println!("cargo:rerun-if-changed={}", path.display());
        let forms = parse_all(sources[usize::from(domain) - 1], &relative);
        assert_eq!(forms.len(), 1, "{relative}: expected one root form");
        let Expr::List(root_form) = &forms[0] else {
            panic!("{relative}: expected root list")
        };
        assert_eq!(
            symbol(&root_form[0], &relative),
            "domain-table-1",
            "{relative}: unsupported table schema"
        );
        let mut count = 0usize;
        let mut coordinates = HashSet::new();
        for row in &root_form[1..] {
            let Expr::List(fields) = row else {
                panic!("{relative}: malformed row {row:?}")
            };
            assert_eq!(
                fields.len(),
                7,
                "{relative}: row must contain bits and six projections"
            );
            let bits = symbol(&fields[0], &relative);
            assert_eq!(
                bits.len(),
                usize::from(domain),
                "{relative}: wrong exact coordinate width {bits}"
            );
            assert!(
                bits.bytes().all(|bit| matches!(bit, b'0' | b'1')),
                "{relative}: non-binary coordinate {bits}"
            );
            assert!(
                coordinates.insert(bits.to_owned()),
                "{relative}: duplicate coordinate {bits}"
            );
            let mut columns = HashSet::new();
            for field in &fields[1..] {
                let Expr::List(pair) = field else {
                    panic!("{relative}: malformed projection {field:?}")
                };
                assert_eq!(
                    pair.len(),
                    2,
                    "{relative}: malformed projection pair {pair:?}"
                );
                let column = symbol(&pair[0], &relative);
                assert!(
                    columns.insert(column),
                    "{relative}: duplicate {column} projection at {bits}"
                );
                add_entry(
                    out,
                    "DomainTable",
                    domain,
                    bits,
                    column,
                    &pair[1],
                    &relative,
                );
            }
            assert_eq!(
                columns.len(),
                6,
                "{relative}: a row must include all six projections"
            );
            count += 1;
        }
        let expected = 1usize << domain;
        assert_eq!(
            count, expected,
            "{relative}: unexpected domain table occupancy"
        );
    }
}

fn binary_bootstrap_words(root: &Path, output: &Path, compiler: &std::ffi::OsStr) {
    for path in [
        ".zig-version",
        "bootstrap_t5m.zig",
        "domain_projection_assets.zig",
        "lib/domains/d11.lisp",
        "lib/macro.sens",
        "lib/core3.sens",
        "lib/core4.sens",
        "lib/compiler-nucleus.sens",
        "lib/time.sens",
        "lib/utf8.sens",
        "lib/process.sens",
        "lib/tcp.sens",
        "lib/fs.sens",
        "language-contract.lisp",
        "contracts/bija3-l1-l5-ratification.lisp",
        "contracts/d4-bootstrap-ratification.lisp",
        "research/zig-codecs/t5m.zig",
        "research/zig-codecs/domain_ladder.zig",
        "research/zig-codecs/numeric_domains.zig",
        "research/zig-codecs/t5/t5.zig",
        "research/zig-codecs/transport/fields.zig",
    ] {
        println!("cargo:rerun-if-changed={}", root.join(path).display());
    }
    // Zig 0.16 may reuse an `@embedFile` run result after Cargo reruns this
    // build script for a changed physical library. Give this small bootstrap
    // decoder a private cache and clear it on every invocation so generated
    // words always correspond to the exact current .sens files.
    let cache = output.join("bootstrap-t5m-zig-cache");
    if cache.exists() {
        fs::remove_dir_all(&cache).expect("clear stale Zig T5M bootstrap cache");
    }
    // Генератор Zig отримує фізичний носій, а Rust — лише точні слова.
    // Жодного читання Lisp або запасного Rust-декодера.
    let restored = Command::new(compiler)
        .current_dir(root)
        .arg("run")
        .arg("--cache-dir")
        .arg(&cache)
        .args(["bootstrap_t5m.zig", "-O", "ReleaseSafe"])
        .output()
        .expect("run pinned Zig T5M bootstrap decoder");
    assert!(
        restored.status.success(),
        "Zig T5M binary bootstrap rejected: {}",
        String::from_utf8_lossy(&restored.stderr)
    );
    assert!(
        !restored.stdout.is_empty(),
        "Zig returned no binary bootstrap words"
    );
    fs::write(output.join("binary_bootstrap_words.rs"), restored.stdout)
        .expect("write Zig-restored exact binary bootstrap words");
}

fn pinned_zig() -> std::ffi::OsString {
    println!("cargo:rerun-if-env-changed=ZIG");
    println!("cargo:rerun-if-env-changed=PATH");
    println!("cargo:rerun-if-env-changed=LOCALAPPDATA");
    let pinned = include_str!("../../.zig-version").trim();
    let compiler = env::var_os("ZIG").unwrap_or_else(|| {
        #[cfg(windows)]
        if let Some(local_app_data) = env::var_os("LOCALAPPDATA") {
            let cached = PathBuf::from(local_app_data)
                .join("SENS/zig")
                .join(format!("zig-x86_64-windows-{pinned}"))
                .join("zig.exe");
            if cached.is_file() {
                return cached.into_os_string();
            }
        }
        "zig".into()
    });
    let version = Command::new(&compiler)
        .arg("version")
        .output()
        .expect("binary bootstrap requires pinned Zig; use ./guix/run dev or set ZIG");
    assert!(
        version.status.success(),
        "binary bootstrap: Zig version probe failed"
    );
    assert_eq!(
        std::str::from_utf8(&version.stdout)
            .expect("Zig version UTF-8")
            .trim(),
        pinned,
        "binary bootstrap requires the repository Zig pin"
    );
    compiler
}

fn build_zig_transport(root: &Path, output: &Path, compiler: &std::ffi::OsStr) {
    println!("cargo:rerun-if-env-changed=CARGO_CFG_TARGET_ENV");
    println!("cargo:rerun-if-env-changed=CARGO_CFG_TARGET_OS");
    println!("cargo:rerun-if-env-changed=CARGO_CFG_TARGET_ARCH");
    println!("cargo:rerun-if-env-changed=SENS_ZIG_PORTABLE_LINUX");

    // Zig @embedFile dependencies are opaque to Cargo. Watch every embedded
    // source/physical asset explicitly: remint can update a .sens file after
    // the first build in this job, and tests must relink the archive against
    // those exact new bytes rather than retain an old T5M image.
    for path in [
        "crates/sens/src/eval/special_forms/io.rs",
        "crates/sens/src/lib.rs",
        "crates/sens/build.rs",
        "lib/repl-core.sens",
        "lib/meta-eval.sens",
        "lib/unify.sens",
        "lib/reason.sens",
        "lib/forward.sens",
        "lib/knowledge.sens",
        "lib/world.sens",
        "lib/content-store.sens",
        "lib/lisp-fs.sens",
        "tests/fixtures/wsm-fs-record-producer.sens",
        "lib/linter.sens",
        "language-contract.lisp",
        "lib/surface/sa.lisp",
        "lib/surface/ukr.lisp",
        "lib/surface/uk.lisp",
        "lib/surface/uk-docs.lisp",
        "lib/unify.lisp",
        "lib/reason.lisp",
        "lib/forward.lisp",
        "lib/knowledge.lisp",
        "packaging/islands-manifest-v1.json",
        "lib/persistent-map.lisp",
        "lib/persistent-map.sens",
        "lib/world.lisp",
        "lib/content-store.lisp",
        "lib/persistent-vector.sens",
        "tests/semantic/d9-string-append-physical.lisp",
        "lib/epistemic.sens",
        "lib/lisp-fs.lisp",
        "lib/compiler-nucleus.lisp",
        "contracts/compiler-nucleus-identity-corpus-v1.tsv",
        "knowledge/bija3-l1-l5-structure-projection.json",
        "contracts/bija3-l1-l5-ratification.lisp",
        "knowledge/d4-bootstrap-compiler-structure-projection.json",
        "contracts/d4-bootstrap-ratification.lisp",
    ] {
        println!("cargo:rerun-if-changed={}", root.join(path).display());
    }

    for path in [
        ".zig-version",
        "zig_transport_root.zig",
        "zig_bitpack_root.zig",
        "research/zig-codecs/transport_abi.zig",
        "research/zig-codecs/transport/raw_bitpack.zig",
        "research/zig-codecs/transport/fields.zig",
        "research/zig-codecs/t5m.zig",
        "research/zig-codecs/t5/t5.zig",
        "research/zig-codecs/f3c/f3c.zig",
        "domain_projection_assets.zig",
    ] {
        println!("cargo:rerun-if-changed={}", root.join(path).display());
    }

    let target_env = env::var("CARGO_CFG_TARGET_ENV").unwrap_or_default();
    let target_os = env::var("CARGO_CFG_TARGET_OS").unwrap_or_default();
    let target_arch = env::var("CARGO_CFG_TARGET_ARCH").expect("CARGO_CFG_TARGET_ARCH");
    let wasm = target_arch == "wasm32";
    let portable_linux = env::var("SENS_ZIG_PORTABLE_LINUX").unwrap_or_default() == "1";
    let archive_name = if target_env == "msvc" {
        "sens_zig_transport.lib"
    } else {
        "libsens_zig_transport.a"
    };
    let archive = output.join(archive_name);
    let mut command = Command::new(compiler);
    command.current_dir(root)
        .arg("build-lib")
        .arg(if wasm { "zig_bitpack_root.zig" } else { "zig_transport_root.zig" })
        .arg("-O").arg("ReleaseSafe");
    if wasm {
        // Match the rustc wasm32-unknown-unknown profile; no host libc or PIC.
        command.arg("-fcompiler-rt").arg("-target").arg("wasm32-freestanding");
    } else {
        command.arg("-lc");
        if portable_linux {
            assert_eq!(target_os, "linux", "portable Linux Zig target requested for non-Linux build");
            assert_eq!(target_arch, "x86_64", "portable Linux Zig target is x86-64 only");
            assert_eq!(target_env, "gnu", "portable Linux Zig target requires the GNU ABI");
            // The core archive must share the release target/CPU of sens-cli's Zig archive.
            command
                .arg("-target")
                .arg("x86_64-linux-gnu.2.35")
                .arg("-mcpu")
                .arg("baseline");
        } else if target_env == "msvc" {
            command.arg("-target").arg(format!("{target_arch}-windows-msvc"));
        }
        if target_os != "windows" {
            command.arg("-fPIC");
        }
    }
    let result = command.arg(format!("-femit-bin={}", archive.display()))
        .status()
        .expect("sens core requires the pinned Zig physical packer");
    assert!(result.success(), "sens core: Zig transport archive build failed");
    println!("cargo:rustc-link-search=native={}", output.display());
    println!("cargo:rustc-link-lib=static=sens_zig_transport");

    if !wasm {
        // Роздільні архіви зберігають compiler-rt stack probes без LLD-конфлікту з -lc.
        println!("cargo:rerun-if-changed={}", root.join("zig_compiler_rt_anchor.zig").display());
        let runtime_name = if target_env == "msvc" {
            "sens_zig_compiler_rt.lib"
        } else {
            "libsens_zig_compiler_rt.a"
        };
        let runtime_archive = output.join(runtime_name);
        let mut runtime = Command::new(compiler);
        runtime.current_dir(root)
            .arg("build-lib")
            .arg("zig_compiler_rt_anchor.zig")
            .arg("-O").arg("ReleaseSafe")
            .arg("-fcompiler-rt");
        if portable_linux {
            runtime.arg("-target").arg("x86_64-linux-gnu.2.35")
                .arg("-mcpu").arg("baseline");
        } else if target_env == "msvc" {
            runtime.arg("-target").arg(format!("{target_arch}-windows-msvc"));
        }
        if target_os != "windows" {
            runtime.arg("-fPIC");
        }
        let runtime_result = runtime.arg(format!("-femit-bin={}", runtime_archive.display()))
            .status()
            .expect("sens core requires the pinned Zig compiler-rt");
        assert!(runtime_result.success(), "sens core: Zig compiler-rt archive build failed");
        println!("cargo:rustc-link-lib=static=sens_zig_compiler_rt");
        if target_env != "msvc" {
            println!("cargo:rustc-link-lib=c");
        }
    }
}

fn main() {
    let root =
        PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").expect("manifest dir")).join("../..");
    let output = PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR"));
    let compiler = pinned_zig();
    build_zig_transport(&root, &output, &compiler);
    binary_bootstrap_words(&root, &output, &compiler);
    let mut generated = String::from("pub(super) static ENTRIES: &[Entry] = &[\n");
    domain_tables(&root, &compiler, &mut generated);
    generated.push_str("];\n");
    let destination = output.join("domain_projection_catalog.rs");
    fs::write(destination, generated).expect("write generated projection catalog");
}
