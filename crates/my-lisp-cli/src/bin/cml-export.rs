//! Producer for `mylisp-cml-export.wsm` — the versioned semantic export
//! CML consumes so it stops manually duplicating or inventing my-lisp's
//! own language rules. Design fixed before this code:
//! docs/cml-semantic-export-v1-design.md.
//!
//! my-lisp owns producing this file. my-lisp does not touch cml's own
//! repository or code — per docs/agent-doctrine.md rule 4, a neighboring
//! repo is an external authority, not a file this repo edits.

use my_lisp::semantic_registry_export::{admitted_surfaces_for_semantic_id, semantic_id_bits, SurfaceRow};

/// Slice 1 (2026-09-10, unchanged): exactly the semantic IDs
/// `tests/fixtures/conformance.my`'s fixture #69 (named def + recursion,
/// `count-down`) exercises.
///
/// Slice 2 (2026-09-11, per cml's own real need, not speculative --
/// cml#9 found `semantic.rs`'s `is_reserved_canon_surface` hand-transcribing
/// the full Canon 0+7 surface list instead of reading it from this export,
/// because slice 1 never covered atom/cons/car/cdr/defmacro in the first
/// place): adds the remaining Canon 0 identities (atom/cons/car/cdr) and
/// defmacro (SID 00001010), so a consumer's own "which surfaces are Canon-reserved"
/// table can be derived entirely from this file instead of staying a
/// second hand-typed list that silently drifts if the registry changes.
const EXPORTED_FORMS: &[(u8, Role, bool)] = &[
    (1, Role::Syntax, false),    // quote
    (2, Role::Primitive, true),  // atom
    (3, Role::Primitive, true),  // eq
    (4, Role::Primitive, true),  // cons
    (5, Role::Primitive, true),  // car
    (6, Role::Primitive, true),  // cdr
    (7, Role::Syntax, false),    // cond
    (8, Role::Syntax, false),    // lambda
    (9, Role::Syntax, false),    // define
    (10, Role::Syntax, false),    // defmacro
    (13, Role::Library, true),    // subtraction
];

#[derive(Clone, Copy)]
enum Role {
    Syntax,
    Primitive,
    Library,
}

impl Role {
    fn as_str(self) -> &'static str {
        match self {
            Role::Syntax => "syntax",
            Role::Primitive => "primitive",
            Role::Library => "library",
        }
    }
}

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
/// character parses fine inside `lib/surface/semantic-registry.wsm`
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
    for &(id, role, callable) in EXPORTED_FORMS {
        let surfaces = admitted_surfaces_for_semantic_id(id);
        let id_bits = semantic_id_bits(id);
        lines.push(format!(
            "    (\\\"{id_bits}\\\" (surfaces {}) (role {}) (callable {}))",
            render_surfaces(&surfaces),
            role.as_str(),
            if callable { "t" } else { "nil" }
        ));
    }
    lines.join("\n")
}

fn render_export() -> String {
    let forms_block = render_forms_block();
    let digest = fnv1a_hex(forms_block.as_bytes());

    format!(
        "(cml-export/1\n  (contract (major 6) (minor 0))\n  (digest \"{digest}\")\n  (forms\n{forms_block}))\n"
    )
}

fn main() {
    print!("{}", render_export());
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Issue juv4uk/my-lisp#51, acceptance criterion "repeat export gives
    /// byte-identical output": guards this in CI, not just by manual `diff`
    /// between two ad hoc runs.
    #[test]
    fn repeated_export_is_byte_identical() {
        assert_eq!(render_export(), render_export());
    }

    /// The committed `mylisp-cml-export.wsm` at the repo root must be
    /// exactly what this producer emits right now -- if this fails, the
    /// committed artifact has drifted from the producer and needs
    /// regenerating (`cargo run --bin cml-export > mylisp-cml-export.wsm`),
    /// not hand-editing.
    #[test]
    fn committed_artifact_matches_producer_output() {
        let committed = std::fs::read_to_string(
            concat!(env!("CARGO_MANIFEST_DIR"), "/../../mylisp-cml-export.lisp"),
        )
        .expect("mylisp-cml-export.wsm must exist at the repo root");
        assert_eq!(committed, render_export());
    }
}
