//! Independent, capability-free core of the my-lisp language.
//! Nezalezhne yadro movy my-lisp bez dostupu do mozhlyvostei operatsiinoi systemy.
//! Unabhängiger Sprachkern von my-lisp ohne Zugriff auf Betriebssystemfunktionen.
//!
//! The crate physically contains no OS access: no filesystem, no processes,
//! no sockets. Host capabilities live in the `my-lisp-host` crate and are
//! installed into this core's registry at startup by whichever embedder
//! wants them (the CLI does; WASM does not). See eval/capabilities.rs.

pub mod layout;

mod bignum;
mod environment;
mod error;
pub(crate) mod eval;
/// Compiler IR v0 (GitHub issue #68) — provenance-bearing lowering data.
/// See docs/COMPILER-IR-V0.md. Not part of the public API yet (no
/// execution backend exists); kept `pub(crate)` until a consumer needs it
/// exposed, per rule 7 (minimize change surface).
pub(crate) mod ir;
mod language_items;
mod parser;
mod presentation;
mod semantic_registry;
/// Deliberately thin, crate-external view onto `semantic_registry` — exposes
/// exactly the (namespace, spelling) pairs a consumer like the CML semantic
/// export needs, without making the internal parsing/index machinery public.
/// See docs/cml-semantic-export-v1-design.md.
pub mod semantic_registry_export {
    /// One admitted (namespace, spelling) pair for a semantic ID — e.g.
    /// `SurfaceRow { namespace: "uk", name: "як-є" }` for `quote`'s Ukrainian
    /// surface.
    pub struct SurfaceRow {
        pub namespace: &'static str,
        pub name: &'static str,
    }

    /// Stable and compatibility-only spellings admitted for `semantic_id`,
    /// each tagged with which namespace (en/uk/sa/sym/...) it belongs to.
    pub fn admitted_surfaces_for_semantic_id(semantic_id: u8) -> Vec<SurfaceRow> {
        super::semantic_registry::admitted_surfaces_with_namespace_for_semantic_id(semantic_id)
            .into_iter()
            .map(|(namespace, name)| SurfaceRow { namespace, name })
            .collect()
    }

    /// Повертає opaque semantic ID для stable або compatibility-only surface.
    /// Значення операції лишається у мовному контракті, не в цій проєкції.
    pub fn semantic_id_for_admitted_surface(name: &str) -> Option<u8> {
        super::semantic_registry::admitted_semantic_id_for_surface(name)
    }

    /// Canonical 8-bit textual serialization for provenance/export.
    pub fn semantic_id_bits(semantic_id: u8) -> String {
        super::semantic_registry::semantic_id_bits(semantic_id)
    }
}
pub mod syntax;
mod value;

pub use environment::{Environment, Session};
pub use error::{Classification, ErrorKind, LanguageError};
pub use language_items::{language_items, Arity, LanguageItem, LanguageItemKind};

pub use eval::exact_arity;
pub use eval::parse_json;
pub use eval::{
    capability_installed, installed_capabilities, register_capability, unregister_capability,
};
pub use eval::{
    eval_parsed_expressions, eval_parsed_expressions_incremental, eval_program,
    eval_program_incremental, evaluate as eval_expr, EvalResult,
};
pub use parser::parse;
pub use presentation::{
    present_system_message, render_error_for_presentation, render_value_for_presentation,
    PresentationLanguage,
};
pub use syntax::fasl::{
    decode_program as fasl_decode_program, encode_program as fasl_encode_program,
};

/// Language-owned macro constructor. Its only host-side bootstrap dependency
/// is the narrow first-class `make-macro` binding that materializes
/// Closure -> Macro. The source returns one Macro value and deliberately binds
/// no human surface name; `load_macro_library` installs peer spellings onto
/// that same value after evaluation.
pub const MACRO_LIBRARY_SOURCE: &str = include_str!("../../../lib/macro.lisp");
const DEFMACRO_SEMANTIC_ID: u8 = 10;
const LAMBDA_SEMANTIC_ID: u8 = 8;

/// The ordinary my-lisp bootstrap library, evaluated after the macro layer.
pub const CORE_LIBRARY_SOURCE: &str = include_str!("../../../lib/core.lisp");

/// Generated runtime projection of admitted surface spellings to opaque numeric
/// semantic IDs. semantic-registry.lisp remains the only spelling authority.
pub const META_SEMANTIC_REGISTRY_SOURCE: &str =
    include_str!("../../../lib/generated/meta-semantic-registry.lisp");

/// Metacircular evaluator source. Surface names are supplied by the generated
/// semantic registry projection rather than duplicated in this file.
pub const META_EVAL_LIBRARY_SOURCE: &str = include_str!("../../../lib/meta-eval.lisp");

/// Language-owned time semantics. Host clocks expose raw observations such as
/// `mono-ns` and `unix-time-now`; this library derives coarser clocks,
/// calendar interpretation, UTC structure, and deadline arithmetic.
pub const TIME_LIBRARY_SOURCE: &str = include_str!("../../../lib/time.lisp");

/// Exact UTF-8 validation and byte-to-Unicode interpretation owned by Lisp.
pub const UTF8_LIBRARY_SOURCE: &str = include_str!("../../../lib/utf8.lisp");

/// Process-result interpretation owned by Lisp. The host contributes only the
/// `process-run-raw` capability; this layer decides how captured bytes become
/// text and how decoding failures are represented.
pub const PROCESS_LIBRARY_SOURCE: &str = include_str!("../../../lib/process.lisp");

/// TCP text interpretation owned by Lisp. The host contributes only the raw
/// socket-read bytes through `tcp-read-raw`; this layer defines public
/// `tcp-read` by applying the shared UTF-8 semantics.
pub const TCP_LIBRARY_SOURCE: &str = include_str!("../../../lib/tcp.lisp");

/// File text interpretation owned by Lisp. The host contributes only raw
/// bytes through `read-file-bytes`/`write-file-bytes`; this layer defines
/// public `read-file`/`write-file` by applying the shared UTF-8 semantics.
pub const FS_LIBRARY_SOURCE: &str = include_str!("../../../lib/fs.lisp");

/// Install the one primitive macro-construction mechanism required by the
/// language-owned macro layer, evaluate the Lisp derivation exactly once, and
/// bind every stable or compatibility-only spelling admitted for semantic
/// identity 0012 directly to the resulting Macro value.
///
/// The loader owns only binding mechanics. Macro-definition behavior remains
/// in `lib/macro.lisp`; there is still no evaluator head-name fallback for any
/// human macro-definition spelling. Surface admission belongs to the numeric
/// semantic registry, not to this Rust loader.
///
/// Embedders that deliberately construct a custom/bare `Environment` must use
/// this function before evaluating source that depends on the macro-definition
/// surface. `Environment::root()` therefore remains the minimal kernel.
pub fn load_macro_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    eval::install_macro_substrate(&session.environment);
    let result = eval_program(MACRO_LIBRARY_SOURCE, session)?;

    if !matches!(&result.value, Value::Macro(_)) {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "macro library must evaluate to one Macro value",
            Span { start: 0, end: 0 },
        ));
    }

    let admitted = semantic_registry::admitted_surfaces_for_semantic_id(DEFMACRO_SEMANTIC_ID);
    if admitted.is_empty() {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "semantic registry must admit at least one macro-definition surface for SID 10",
            Span { start: 0, end: 0 },
        ));
    }
    for name in admitted {
        session.environment.define(name, result.value.clone());
    }

    Ok(result)
}

/// Bind stable peer spellings for values that already exist in the current
/// bootstrap environment. The semantic registry owns which names share an ID;
/// this function owns only the one-time binding mechanism.
///
/// Existing bindings are never overwritten. That matters for ordinary
/// shadowable operations: peers begin with the same value, but shadowing one
/// name later must not retarget the others. Canon identities are skipped here
/// because their resolver already owns surface routing independently of the
/// lexical environment.
fn bind_missing_stable_surface_peers(environment: &Environment) {
    let snapshot = environment.snapshot();
    let mut values_by_semantic_id = std::collections::BTreeMap::new();

    for (name, value) in snapshot {
        if eval::canon::identity_for_surface(&name).is_some() {
            continue;
        }
        if let Some(semantic_id) = semantic_registry::semantic_id_for_surface(&name) {
            values_by_semantic_id.entry(semantic_id).or_insert(value);
        }
    }

    for (semantic_id, value) in values_by_semantic_id {
        for peer in semantic_registry::stable_surfaces_for_semantic_id(semantic_id) {
            if environment.get(peer).is_none() {
                environment.define(peer, value.clone());
            }
        }
    }
}

/// Install the narrow macro substrate, then load the language-owned macro
/// layer and finally the ordinary core library. Once the Lisp-owned values
/// exist, install every missing stable peer spelling from the semantic
/// registry onto the same initial value; no human-language alias table is
/// duplicated here.
///
/// This is the canonical bootstrap order for embedders that start from a bare
/// `Environment::root()`: the root itself stays smaller, while the bootstrap
/// explicitly gains `make-macro` before evaluating `lib/macro.lisp`.
pub fn load_core_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    load_macro_library(session)?;
    let result = eval_program(CORE_LIBRARY_SOURCE, session)?;
    bind_missing_stable_surface_peers(&session.environment);
    Ok(result)
}

/// Load the explicit metacircular self-hosting witness after the ordinary core.
/// Rust owns bootstrap mechanics; surface admission stays registry-owned.
pub fn load_meta_evaluator_library(
    session: &mut Session,
) -> Result<EvalResult, LanguageError> {
    eval_program(META_SEMANTIC_REGISTRY_SOURCE, session)?;
    eval_program(META_EVAL_LIBRARY_SOURCE, session)
}

/// Load language-owned time semantics into a session that already has the
/// ordinary core library. Keeping this separate from `load_core_library`
/// preserves the closed language core while giving embedders one canonical
/// time-layer loader instead of ad-hoc `include_str!` calls.
pub fn load_time_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    eval_program(TIME_LIBRARY_SOURCE, session)
}

/// Load the shared byte/text adapters used by process and TCP boundaries.
/// `load_process_library` remains the compatibility entry point already used
/// by native embedders, so it now installs both language-owned text adapters:
/// public `process-run` over `process-run-raw`, and public `tcp-read` over
/// `tcp-read-raw`. Neither raw capability is required merely to define them.
pub fn load_process_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    eval_program(UTF8_LIBRARY_SOURCE, session)?;
    eval_program(PROCESS_LIBRARY_SOURCE, session)?;
    eval_program(TCP_LIBRARY_SOURCE, session)
}

/// Load language-owned TCP text semantics explicitly when an embedder does
/// not otherwise need the process adapter.
pub fn load_tcp_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    eval_program(UTF8_LIBRARY_SOURCE, session)?;
    eval_program(TCP_LIBRARY_SOURCE, session)
}

/// Load language-owned file text semantics: public `read-file`/`write-file`
/// composed entirely on the existing `read-file-bytes`/`write-file-bytes` raw
/// host capabilities plus the shared UTF-8 layer. No new host capability is
/// introduced for this migration.
pub fn load_fs_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    eval_program(UTF8_LIBRARY_SOURCE, session)?;
    eval_program(FS_LIBRARY_SOURCE, session)
}

/// Public Contract 6.0 classification hook for tooling and embedders.
///
/// This does not expose or mutate the Canon registry. It only answers whether
/// a source spelling belongs to the finite reserved Canon 0+7 name set, so
/// LSPs/linters can follow the same binder rule as the evaluator without
/// duplicating EN/UK/SA tables.
pub fn is_canonical_surface_name(name: &str) -> bool {
    eval::canon::is_reserved_surface(name)
}

/// Public hook for tooling that must recognize `quote`'s specific identity
/// (byte SID 1) across every admitted surface (`quote`/`як-є`/
/// `svarūpa`/`'`), not just the English spelling. Added after a real bug
/// was found in `crates/my-lisp-lsp/src/analysis.rs`'s own quoted-data
/// detection: it matched only the literal ASCII string `"quote"`, so a
/// program written `(як-є (a b c))` would have its quoted symbols
/// mis-treated as live code references by go-to-definition/rename —
/// silently breaking exactly the multilingual guarantee this ecosystem's
/// Canon 0 routing exists to provide. Mirrors `is_canonical_surface_name`'s
/// minimal-surface-area pattern rather than exposing the whole
/// `CanonicalIdentity` enum.
pub fn is_quote_surface_name(name: &str) -> bool {
    eval::canon::is_quote_identity(name)
}

/// True for any admitted surface of `define`/`def` (byte SIDs 9 and 11).
pub fn is_define_surface_name(name: &str) -> bool {
    matches!(
        semantic_registry::admitted_semantic_id_for_surface(name),
        Some(crate::eval::necessary_forms::DEFINE_SEMANTIC_ID
            | crate::eval::necessary_forms::DEF_COMPATIBILITY_SEMANTIC_ID)
    )
}

/// True for any admitted surface of `defmacro` (semantic ID `0012`).
pub fn is_defmacro_surface_name(name: &str) -> bool {
    semantic_registry::admitted_semantic_id_for_surface(name) == Some(DEFMACRO_SEMANTIC_ID)
}

/// True for any admitted surface of `lambda` (semantic ID `0010`).
pub fn is_lambda_surface_name(name: &str) -> bool {
    semantic_registry::admitted_semantic_id_for_surface(name) == Some(LAMBDA_SEMANTIC_ID)
}

/// Convenience: FASL-encode already-parsed expressions bound to a source hash.
pub fn fasl_encode(expressions: &[Expr], source_hash: &[u8; 32]) -> Vec<u8> {
    syntax::fasl::encode_program(expressions, source_hash)
}

/// Source-hash helper for FASL producers (sha256 over raw source bytes).
pub fn sha256_source(input: &[u8]) -> [u8; 32] {
    eval::digest_sha256(input)
}
pub use syntax::{Exactness, Expr, ExprKind, Span};
pub use value::{Closure, NumericBuffer, Rational, Value};

/// Return a half-open, Unicode-scalar-indexed substring with clamped bounds.
///
/// This is the shared implementation behind the language primitive and
/// direct host bindings, so adapters cannot silently drift from language
/// semantics. Argument validation remains the caller's responsibility.
pub fn string_slice_text(text: &str, start: usize, end: usize) -> String {
    let chars: Vec<char> = text.chars().collect();
    let start = start.min(chars.len());
    let end = end.min(chars.len()).max(start);
    chars[start..end].iter().collect()
}
