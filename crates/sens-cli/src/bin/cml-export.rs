//! Producer for `mylisp-cml-export.wsm` — the versioned semantic export
//! CML consumes so it stops manually duplicating or inventing sens's
//! own language rules. Design fixed before this code:
//! docs/cml-semantic-export-v1-design.md.
//!
//! sens owns producing this file. sens does not touch cml's own
//! repository or code — per docs/agent-doctrine.md rule 4, a neighboring
//! repo is an external authority, not a file this repo edits.

use sens::semantic_registry_export::{
    admitted_surfaces_for_semantic_id, function_role, semantic_id_bits, SurfaceRow,
};
use sens::{fasl_encode, parse, sha256_source};
use std::{fs, process};

/// Exact single identities that CML export v1 can represent.
/// `defmacro` is deliberately absent: it is a derived surface over the
/// current D5 MACRO and D4 DEFINE identities, not one standalone identity
/// that this legacy single-slot format can truthfully encode.
/// Ролі й викликність беремо з таблиці функцій, а не визначаємо тут.
const EXPORTED_CODES: &[u8] = &[1, 2, 3, 4, 5, 6, 7, 8, 9, 13];

/// FNV-1a (64-bit) — not cryptographic, a drift-detection digest between
/// trusted collaborators. See the design doc for why this is deliberate,
/// not an oversight.
fn fnv1a_hex(bytes: &[u8]) -> String {
    let mut hash: u64 = 0xcbf29ce484222325;
    for &byte in bytes {
        hash ^= byte as u64;
        hash = hash.wrapping_mul(0x100000001b3);
    }
    format!("{hash:016x}")
}

/// Surface names are rendered as string literals, not bare symbols.
/// Real bug found extending this export to slice 2 (cml#9): the bare
/// symbol `'` (quote's own `sym` surface, byte SID 00000001) fails to
/// parse when it is the last token before a closing paren -- verified
/// directly with the real reader (`--oracle-check`): `(a ')` errors
/// with `unexpected-closing-parenthesis`, even though the identical
/// character parses fine inside `lib/surface/semantic-registry.lisp`
/// itself, where it is always followed by more content (` stable)`)
/// before any closing paren. Quote-sugar's removal (contract 2.0) left
/// a bare `'` still requiring a following token in the reader. Rather
/// than special-case this one surface, every surface name is quoted as
/// a string here, which has no such reader ambiguity for any admitted
/// spelling, present or future.
fn render_surfaces(surfaces: &[SurfaceRow]) -> String {
    surfaces
        .iter()
        .map(|s| format!("({} \"{}\")", s.namespace, s.name))
        .collect::<Vec<_>>()
        .join(" ")
}

fn render_forms_block() -> String {
    let mut lines = Vec::new();
    for &id in EXPORTED_CODES {
        let surfaces = admitted_surfaces_for_semantic_id(id);
        let id_bits = semantic_id_bits(id);
        let role = function_role(id).expect("exported code must have function-table metadata");
        let callable = role != "syntax";
        lines.push(format!(
            "    (\"{id_bits}\" (surfaces {}) (role {}) (callable {}))",
            render_surfaces(&surfaces),
            role,
            if callable { "t" } else { "nil" }
        ));
    }
    lines.join("\n")
}

fn render_export() -> String {
    let forms_block = render_forms_block();
    let digest = fnv1a_hex(forms_block.as_bytes());

    format!(
        "(cml-export-1\n  (contract (major 6) (minor 0))\n  (digest \"{digest}\")\n  (forms\n{forms_block}))\n"
    )
}

/// Binary program transport for CML. Unlike the default semantic-metadata
/// export, this path preserves exact parsed SENS identities and typed buffers;
/// it never resolves function identities back to human surface names.
fn program_fasl(source: &[u8]) -> Result<Vec<u8>, String> {
    let text = std::str::from_utf8(source).map_err(|error| format!("UTF-8: {error}"))?;
    let expressions = parse(text).map_err(|error| format!("parse: {error}"))?;
    Ok(fasl_encode(&expressions, &sha256_source(source)))
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match args.as_slice() {
        [] => print!("{}", render_export()),
        [mode, source, output] if mode == "--program-fasl" => {
            let source_bytes = fs::read(source).unwrap_or_else(|error| {
                eprintln!("cml-export: cannot read {source}: {error}");
                process::exit(1);
            });
            let encoded = program_fasl(&source_bytes).unwrap_or_else(|error| {
                eprintln!("cml-export: {source}: {error}");
                process::exit(1);
            });
            fs::write(output, encoded).unwrap_or_else(|error| {
                eprintln!("cml-export: cannot write {output}: {error}");
                process::exit(1);
            });
        }
        _ => {
            eprintln!("usage: cml-export [--program-fasl <source.lisp> <output.fasl>]");
            process::exit(2);
        }
    }
}

