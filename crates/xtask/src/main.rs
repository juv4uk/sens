//! xtask — генератори машинних доказів (external oracle, Intel XED).
//! Перевірки документації й політик (колишній
//! `cargo xtask verify`) перенесено в мову: `scripts/verify-repo.lisp`.
//!
//! xtask — machine-evidence generators only; repository policy checks
//! (formerly `cargo xtask verify`) now live in `scripts/verify-repo.lisp`.

pub mod compiler_export;
pub mod external_oracle;
pub mod xed_import;

use std::process::ExitCode;

fn main() -> ExitCode {
    let mut args = std::env::args().skip(1);
    match args.next().as_deref() {
        Some("compiler-export") => run_compiler_export(args),
        Some("external-oracle") => run_external_oracle(args),
        Some("import-xed-evidence") => run_import_xed_evidence(args),
        Some(other) => {
            eprintln!("unknown xtask subcommand: {other}");
            print_usage();
            ExitCode::FAILURE
        }
        None => {
            print_usage();
            ExitCode::FAILURE
        }
    }
}

fn run_compiler_export(mut args: impl Iterator<Item = String>) -> ExitCode {
    let repo_root = locate_repo_root();
    let mut fixture: Option<String> = None;
    let mut artifact = false;
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--artifact" => {
                artifact = true;
            }
            "--fixture" => {
                let Some(value) = args.next() else {
                    eprintln!("--fixture requires a compiler corpus fixture name");
                    return ExitCode::FAILURE;
                };
                fixture = Some(value);
            }
            other => {
                eprintln!("unknown compiler-export option: {other}");
                eprintln!("  available: --artifact, --fixture <name>");
                return ExitCode::FAILURE;
            }
        }
    }

    match compiler_export::run(
        &repo_root,
        compiler_export::ExportOptions { fixture, artifact },
    ) {
        Ok(rendered) => {
            print!("{rendered}");
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("compiler export failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn print_usage() {
    eprintln!(
        "usage: cargo xtask <compiler-export [--artifact] [--fixture NAME]|external-oracle <export|render> [--fixture F-...]|import-xed-evidence [--check] [--vendor-root DIR] [--out FILE]>"
    );
}

const XED_PINNED_COMMIT: &str = "0bcb6237345c5066726dcc08b3d87928df3b5b26";

fn run_import_xed_evidence(args: impl Iterator<Item = String>) -> ExitCode {
    let repo_root = locate_repo_root();
    let mut vendor_root = std::path::PathBuf::from(&repo_root).join("lib/machine/xed/vendor");
    let mut out_path = std::path::PathBuf::from(&repo_root)
        .join("lib/machine/xed/generated/machine-evidence.lisp");
    let mut check = false;

    let remaining: Vec<String> = args.collect();
    let mut i = 0;
    while i < remaining.len() {
        match remaining[i].as_str() {
            "--check" => {
                check = true;
                i += 1;
            }
            "--vendor-root" => {
                let Some(value) = remaining.get(i + 1) else {
                    eprintln!("--vendor-root requires a path argument");
                    return ExitCode::FAILURE;
                };
                vendor_root = std::path::PathBuf::from(value);
                i += 2;
            }
            "--out" => {
                let Some(value) = remaining.get(i + 1) else {
                    eprintln!("--out requires a path argument");
                    return ExitCode::FAILURE;
                };
                out_path = std::path::PathBuf::from(value);
                i += 2;
            }
            other => {
                eprintln!("unknown option: {other}");
                return ExitCode::FAILURE;
            }
        }
    }

    xed_import::run(xed_import::RunOptions {
        vendor_root,
        out_path,
        pinned_commit: XED_PINNED_COMMIT.to_string(),
        check,
    })
}


/// Handle `cargo xtask external-oracle <subcommand> [args]`
///
/// Subcommands:
///   export  [--fixture F-<id>]  — print request s-expression(s)
///   render  [--fixture F-<id>]  — alias for export (human-readable label)
fn run_external_oracle(mut args: impl Iterator<Item = String>) -> ExitCode {
    // Locate repo root: CARGO_MANIFEST_DIR is crates/xtask, go up two levels.
    // At runtime we use the binary's own manifest path via environment.
    let repo_root = locate_repo_root();

    let subcmd = match args.next().as_deref() {
        Some("export") | Some("render") => "export",
        Some(other) => {
            eprintln!("unknown external-oracle subcommand: {other}");
            eprintln!("  available: export, render");
            return ExitCode::FAILURE;
        }
        None => {
            eprintln!("external-oracle requires a subcommand: export");
            return ExitCode::FAILURE;
        }
    };

    // Parse --fixture F-... option
    let mut fixture_filter: Option<String> = None;
    let remaining: Vec<String> = args.collect();
    let mut i = 0;
    while i < remaining.len() {
        if remaining[i] == "--fixture" {
            if let Some(id) = remaining.get(i + 1) {
                fixture_filter = Some(id.clone());
                i += 2;
            } else {
                eprintln!("--fixture requires an argument (F-<id>)");
                return ExitCode::FAILURE;
            }
        } else {
            eprintln!("unknown option: {}", remaining[i]);
            return ExitCode::FAILURE;
        }
    }

    let _ = subcmd; // "export" is the only one; future subcommands extend here

    let corpus = match external_oracle::load_corpus(&repo_root) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("corpus load failed: {e}");
            return ExitCode::FAILURE;
        }
    };

    // Filter to requested fixture(s)
    let ids_to_export: Vec<String> = if let Some(ref fid) = fixture_filter {
        vec![fid.clone()]
    } else {
        // All S1 fixtures with expected values
        corpus
            .iter()
            .filter(|f| f.is_s1 && f.expected.is_some())
            .map(|f| f.id.clone())
            .collect()
    };

    let mut any_failed = false;
    for id in &ids_to_export {
        let outcome = external_oracle::export_fixture(&corpus, id);
        let rendered = external_oracle::render_request(&outcome, (6, 0));
        println!("{rendered}");
        println!();
        if matches!(outcome, external_oracle::ExportOutcome::Unsupported { .. }) {
            any_failed = true;
        }
    }

    if any_failed {
        ExitCode::FAILURE
    } else {
        ExitCode::SUCCESS
    }
}

fn locate_repo_root() -> String {
    // Try CARGO_MANIFEST_DIR from env (set when running via `cargo xtask`)
    if let Ok(manifest) = std::env::var("CARGO_MANIFEST_DIR") {
        // crates/xtask → go up two levels
        let path = std::path::Path::new(&manifest);
        if let Some(repo) = path.parent().and_then(|p| p.parent()) {
            return repo.to_string_lossy().into_owned();
        }
    }
    // Fallback: current working directory (useful when binary is run directly)
    std::env::current_dir()
        .map(|p| p.to_string_lossy().into_owned())
        .unwrap_or_else(|_| ".".into())
}
