//! Independent, capability-free core of the sens language.
//! Nezalezhne yadro movy sens bez dostupu do mozhlyvostei operatsiinoi systemy.
//! Unabhängiger Sprachkern von sens ohne Zugriff auf Betriebssystemfunktionen.
//!
//! The crate physically contains no OS access: no filesystem, no processes,
//! no sockets. Host capabilities live in the `sens-host` crate and are
//! installed into this core's registry at startup by whichever embedder
//! wants them (the CLI does; WASM does not). See eval/capabilities.rs.


mod bignum;
mod bit9;
mod binary_number;
mod bits;
mod canonical_reader;
mod program_data;
mod compiler_role;
mod compiler_bootstrap;
mod compiler_language;
mod domain_words;
mod domain_identity;
pub mod domain_ladder;
#[allow(dead_code)]
mod domain_owner_generated;
mod packed_bits;
mod outer_envelope;
mod binary_framing;
mod gpu_execution_packet;
mod environment;
mod error;
pub(crate) mod eval;
mod language_items;
mod parser;
mod mixed_source;
mod presentation;
mod semantic_registry;
mod source_words;
mod source_packing;
mod ternary_transport;
mod binary_execution;
#[cfg(test)]
mod bootstrap_measurement;
pub mod sens;
mod sid;
/// Deliberately thin, crate-external view onto `semantic_registry` — exposes
/// exactly the (namespace, spelling) pairs a consumer like the CML semantic
/// export needs, without making the internal parsing/index machinery public.
/// See docs/cml-semantic-export-v1-design.md.
pub mod semantic_registry_export {
    /// One admitted (namespace, spelling) pair for a semantic ID — e.g.
    /// `SurfaceRow { namespace: "ук", name: "як-є" }` for `quote`'s Ukrainian
    /// surface.
    pub struct SurfaceRow {
        pub namespace: &'static str,
        pub name: &'static str,
    }

    /// Mechanical input accepted by the external projection boundary.
    ///
    /// Runtime/source semantics use `Sens8`. The `u8` implementation exists
    /// only so the pre-#1098 CML export can remain byte-for-byte unchanged in
    /// this first vertical slice; it must not be used as a SID constructor.
    #[doc(hidden)]
    pub trait ProjectionSidInput {
        #[doc(hidden)]
        fn into_projection_sid(self) -> super::Sens8;
    }

    impl ProjectionSidInput for super::Sens8 {
        fn into_projection_sid(self) -> super::Sens8 {
            self
        }
    }

    impl ProjectionSidInput for u8 {
        fn into_projection_sid(self) -> super::Sens8 {
            super::Sens8::from_packed_byte(self)
        }
    }

    /// Stable and compatibility-only spellings admitted for `semantic_id`,
    /// each tagged with which namespace (en/uk/sa/sym/...) it belongs to.
    pub fn admitted_surfaces_for_semantic_id(
        semantic_id: impl ProjectionSidInput,
    ) -> Vec<SurfaceRow> {
        super::semantic_registry::admitted_surfaces_with_namespace_for_semantic_id(
            semantic_id.into_projection_sid(),
        )
        .into_iter()
        .map(|(namespace, name)| SurfaceRow { namespace, name })
        .collect()
    }

    /// Повертає opaque semantic ID для stable або compatibility-only surface.
    /// Значення операції лишається у мовному контракті, не в цій проєкції.
    pub fn semantic_id_for_admitted_surface(name: &str) -> Option<super::Sens8> {
        super::semantic_registry::admitted_semantic_id_for_surface(name)
    }

    /// Current ratified Ukrainian CALL-head projection (exact domain width),
    /// not a historical eight-bit identity. Source editors must preserve
    /// these forms in authored .lisp; the mixed parser already lowers them to
    /// exact DomainIdentity only in legitimate executable head positions.
    ///
    /// In particular, the legacy sens-to-sens compatibility migrator must
    /// NEVER rewrite a valid current Ukrainian head into an old SID8 token.
    pub fn exact_uk_callable_for_source_head(name: &str) -> Option<super::DomainIdentity> {
        super::semantic_registry::exact_uk_callable_for_source_head(name)
    }


    /// Legacy packed-byte export for external projection consumers.
    ///
    /// Runtime/source semantics use opaque `Sens8`; this function deliberately
    /// preserves the pre-#1098 projection ABI so untouched observers do not
    /// become semantic participants merely because the runtime identity type
    /// changed.
    pub fn admitted_semantic_ids() -> Vec<u8> {
        super::semantic_registry::admitted_semantic_ids()
            .into_iter()
            .map(super::Sens8::packed_byte)
            .collect()
    }

    /// Роль функції таблиці за кодом — з таблиці функцій, не з рукописного
    /// списку: `syntax` (особлива форма або макрос), `primitive` (примітив
    /// за кодом), `library` (визначена мовою). `None` — коду нема в таблиці
    /// метаданих (lib/surface/function-signatures.lisp).
    pub fn function_role(semantic_id: impl ProjectionSidInput) -> Option<&'static str> {
        let sid = semantic_id.into_projection_sid();
        match super::language_items::signature_kind(sid)? {
            super::LanguageItemKind::SyntaxForm | super::LanguageItemKind::Macro => Some("syntax"),
            super::LanguageItemKind::Builtin if super::eval::canon::has_primitive(sid) => {
                Some("primitive")
            }
            super::LanguageItemKind::Builtin => Some("library"),
        }
    }

    /// Canonical 8-bit textual serialization for provenance/export.
    pub fn semantic_id_bits(semantic_id: impl ProjectionSidInput) -> String {
        super::semantic_registry::semantic_id_bits(semantic_id.into_projection_sid())
    }
}
pub mod syntax;
mod text7;
mod text7_projection;
mod text7_projection_generated;
mod value;

pub use binary_number::{BinaryNumber, BinaryNumberError};
pub use bit9::Bit9;
pub use bits::{Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8, Bits};
pub use canonical_reader::{parse_canonical_binary, parse_canonical_packed_words, parse_canonical_word_sequence};
pub use mixed_source::parse_mixed_exact_domain;
pub use compiler_role::{compiler_execution_role, CompilerExecutionRole, CompilerLoweringRole};
pub use compiler_bootstrap::{
    canonical_value_sha256_mechanism, compiler_evidence_canonical_bytes,
    compiler_evidence_from_canonical_bytes, domain_identity_shape_mechanism,
    domain_identity_shape_or_empty_mechanism,
};
pub use compiler_language::{
    compiler_execution_role_from_sens, compiler_lowering_role_from_sens,
    compiler_program_artifact_from_sens, compiler_program_bootstrap_bundle,
    compiler_program_requests_from_sens, compiler_semantic_input_from_sens,
    verify_compiler_program_artifact_from_sens, CompilerProgramBootstrapBundle,
    CompilerSemanticInput, VerifiedCompilerProgramArtifact, VerifiedCompilerProgramRequest,
};
pub use domain_identity::{CoreDomainIdentity, DomainIdentity};
pub use domain_words::{Bija3, CoreD4, CoreD5, CoreD6, SoundD7, CoreD8, CoreD9, PredicateBit, Racana2};
pub use packed_bits::{BitPacker, PackedBitstream};
pub use outer_envelope::{encode_outer_records, OuterEnvelope, OuterEnvelopeError, OuterRecord};
pub use binary_framing::{
    decode_binary_frame, decode_binary_program, encode_binary_frame, encode_binary_program,
    BinaryFrame, BinaryFrameError,
};
pub use gpu_execution_packet::{
    GpuExecutionPacketError, GpuExecutionPacketV1, GpuOutputRequest,
};
pub use environment::{CoreProfile, Environment, Session};
pub use error::{Classification, ErrorKind, LanguageError};
pub use language_items::{language_items, Arity, LanguageItem, LanguageItemKind};
#[allow(deprecated)]
pub use sid::Sid8;
pub use sens::{Sens, Sens8};
pub use source_words::{
    parse_binary_source_words, BinarySourceToken, BinarySourceWord, CANONICAL_SOURCE_EXTENSION,
};
pub use ternary_transport::{
    decode_ternary_program, decode_ternary_words, encode_binary_projection_ternary,
    encode_ternary_words, open_ternary_program, render_ternary_words_spaced,
    render_ternary_words_vertical, ternary_transport_accounting,
    TernaryTransportAccounting, TernaryTransportError,
};
pub use source_packing::{
    append_binary_source_word, pack_binary_source_tokens, pack_binary_source_words,
    packed_transport_accounting, semantic_source_bits, unpack_binary_source_words,
    PackedTransportAccounting,
};
pub use text7::{Text7, Text7CellError, Text7W7Error, Text7WireError, Text7WordError};
pub use text7_projection::{
    encode_text7, render_text7, Text7Layout, Text7ProjectionError, TEXT7_LAYOUT_SHA256,
    TEXT7_TABLE_SHA256, TEXT7_UPSTREAM_REVISION,
};

pub use binary_execution::{eval_t5_program, T5ExecutionError};

pub use eval::exact_arity;
pub use eval::parse_json;
pub use eval::{
    capability_installed, installed_capabilities, register_capability,
    register_evaluated_capability, register_sens_capability, unregister_capability,
    unregister_sens_capability,
};
pub use eval::{
    eval_lowered_expressions, eval_parsed_expressions, eval_parsed_expressions_incremental,
    eval_program, evaluate as eval_expr, EvalResult,
};
pub use eval::lower::lower_program;
pub use parser::parse;
pub use program_data::{expr_to_exact_program_data, lowered_program_to_exact_data};
pub use presentation::{
    present_system_message, render_error_for_presentation, render_value_for_presentation,
    PresentationLanguage,
};
pub use syntax::fasl::{
    decode_program as fasl_decode_program, encode_program as fasl_encode_program,
};
pub use syntax::wire::{
    decode_program as wire_decode_program, encode_program as wire_encode_program,
};

/// Language-owned macro constructor. Its only host-side bootstrap dependency
/// is the narrow first-class `make-macro` binding that materializes
/// Closure -> Macro. The source returns one Macro value and deliberately binds
/// no human surface name; `load_macro_library` installs peer spellings onto
/// that same value after evaluation.
pub const MACRO_LIBRARY_SOURCE: &str = include_str!("../../../lib/macro.lisp");

/// Frozen Contract-6 compatibility profile.
pub const CORE2_LIBRARY_SOURCE: &str = include_str!("../../../lib/core2.lisp");

/// Core3 experimental kernel-laboratory profile layered over the current
/// shared bootstrap substrate. Mechanism selection is loaded separately by
/// the execution layer because the current selector reads SENS-owned files and
/// therefore does not belong in this capability-free core crate.
pub const CORE3_LIBRARY_SOURCE: &str = include_str!("../../../lib/core3.lisp");

/// The current Core4 sens bootstrap library, evaluated after the macro layer.
pub const CORE_LIBRARY_SOURCE: &str = include_str!("../../../lib/core4.lisp");

/// Parse-output кеш для точного вбудованого Core4 source. Це лише bootstrap-
/// оптимізація: hash source перевіряється перед використанням, а stale/invalid
/// bytes переходять на parsing CORE_LIBRARY_SOURCE.
const CORE_LIBRARY_FASL: &[u8] = include_bytes!("../../../lib/core4.lisp.fasl");

/// Generated runtime projection of admitted surface spellings to opaque Sens8
/// identities. semantic-registry.lisp remains the only spelling authority.
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
/// bind every admitted peer spelling for the registry identity selected by
/// the canonical `defmacro` surface directly to the resulting Macro value.
///
/// The loader owns only binding mechanics. Macro-definition behavior remains
/// in `lib/macro.lisp`; there is still no evaluator head-name fallback for any
/// human macro-definition spelling. Surface admission belongs to the Lisp-owned
/// semantic registry projection, not to this Rust loader.
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

    let defmacro_semantic_id = semantic_registry::admitted_semantic_id_for_surface("defmacro")
        .ok_or_else(|| {
            LanguageError::new(
                ErrorKind::InvalidForm,
                "semantic registry must admit the canonical defmacro surface",
                Span { start: 0, end: 0 },
            )
        })?;
    let admitted = semantic_registry::admitted_surfaces_for_semantic_id(defmacro_semantic_id);
    if admitted.is_empty() {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "semantic registry identity selected by defmacro must admit at least one surface",
            Span { start: 0, end: 0 },
        ));
    }
    for name in admitted {
        session.environment.define(name, result.value.clone());
    }
    // #1460: сам `defmacro` теж прив'язаний до свого коду СЕНС (00001010),
    // тож `(00001010 назва параметри тіло)` працює так само, як назва.
    session
        .environment
        .bind_code_slot_once(defmacro_semantic_id, result.value.clone());

    Ok(result)
}

/// Bind stable peer spellings for values that already exist in the current
/// bootstrap environment. The semantic registry owns which names share an ID;
/// this function owns only the one-time binding mechanism.
///
/// Existing bindings are never overwritten. That matters for ordinary
/// shadowable operations: peers begin with the same value, but shadowing one
/// name later must not retarget the others. SID-routed syntax/value slots are skipped here because their resolver already
/// owns source/UI routing independently of the lexical environment.
fn bind_missing_stable_surface_peers(environment: &Environment) {
    let snapshot = environment.snapshot();
    // HashMap, not BTreeMap: Sens8 is deliberately not Ord (identity
    // comparison/hashing only, no ordering -- see sid.rs's own header).
    // Iteration order here is irrelevant; this is a lookup table.
    let mut values_by_semantic_id = std::collections::HashMap::new();

    for (name, value) in snapshot {
        if eval::canon::routed_sid_for_surface(&name).is_some() {
            continue;
        }
        if let Some(semantic_id) = semantic_registry::semantic_id_for_surface(&name) {
            values_by_semantic_id.entry(semantic_id).or_insert(value);
        }
    }

    // Реєстр лишається єдиною владою surface/SENS навіть без lexical binding:
    // evaluator може знайти точну функцію без placeholder у середовищі.
    // Stable peer копіюємо лише тоді, коли реальне значення вже існує; інакше
    // Value::Sid зайняв би ім'я і заблокував пізніший Lisp-owned closure.
    for semantic_id in semantic_registry::admitted_semantic_ids() {
        let peers = semantic_registry::stable_surfaces_for_semantic_id(semantic_id);

        // Special/necessary forms мають власний routing і тут не стають
        // першокласними lexical values.
        if peers.iter().any(|peer| {
            eval::canon::routed_sid_for_surface(peer).is_some()
                || eval::necessary_forms::identity_for_symbol(peer).is_some()
        }) {
            continue;
        }

        let Some(value) = values_by_semantic_id.get(&semantic_id).cloned() else {
            continue;
        };

        for peer in peers {
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
/// Per-thread cache of the *mechanical* Core4 binary decode and lowering.
/// This is not a shared Environment, evaluated Value, macro, or Lisp semantic
/// snapshot. Every caller still performs the full language-owned bootstrap.
fn current_core_verified_lowered() -> Option<std::rc::Rc<[Expr]>> {
    thread_local! {
        static LOWERED: std::cell::OnceCell<Option<std::rc::Rc<[Expr]>>> =
            const { std::cell::OnceCell::new() };
    }
    LOWERED.with(|slot| {
        slot.get_or_init(|| {
            let (expressions, source_hash) = fasl_decode_program(CORE_LIBRARY_FASL)?;
            if source_hash != sha256_source(CORE_LIBRARY_SOURCE.as_bytes()) {
                return None;
            }
            let lowered = eval::lower::lower_program(&expressions);
            Some(std::rc::Rc::<[Expr]>::from(lowered))
        })
        .clone()
    })
}

fn load_core_library_with_fasl_mode(
    session: &mut Session,
    core_fasl: &[u8],
    use_verified_cache: bool,
) -> Result<EvalResult, LanguageError> {
    session.environment.select_core_profile(CoreProfile::Core4);
    load_macro_library(session)?;

    // Cache only the exact embedded FASL. Arbitrary caller-supplied FASL
    // (including invalid/stale fixtures) retains the original decode/fallback
    // behavior and can never borrow this cached program by matching bytes.
    let exact_embedded = core_fasl.len() == CORE_LIBRARY_FASL.len()
        && std::ptr::eq(core_fasl.as_ptr(), CORE_LIBRARY_FASL.as_ptr());
    let result = if exact_embedded && use_verified_cache {
        match current_core_verified_lowered() {
            Some(lowered) => eval_lowered_expressions(&lowered, session)?,
            None => eval_program(CORE_LIBRARY_SOURCE, session)?,
        }
    } else {
        match fasl_decode_program(core_fasl) {
            Some((expressions, source_hash))
                if source_hash == sha256_source(CORE_LIBRARY_SOURCE.as_bytes()) =>
            {
                eval_parsed_expressions(&expressions, session)?
            }
            _ => eval_program(CORE_LIBRARY_SOURCE, session)?,
        }
    };

    bind_missing_stable_surface_peers(&session.environment);
    Ok(result)
}

/// Production always uses the owner-verified binary decode/lowering cache.
/// An internal-only switch exists solely to compare identical full Core4
/// bootstrap paths with and without cached transport on the *same* CPU.
fn load_core_library_with_fasl(
    session: &mut Session,
    core_fasl: &[u8],
) -> Result<EvalResult, LanguageError> {
    load_core_library_with_fasl_mode(session, core_fasl, true)
}

pub fn load_core_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    load_core_library_with_fasl(session, CORE_LIBRARY_FASL)
}

/// Read-only діагностика для embedder-а: чи відповідає Core4 FASL точному
/// вбудованому source. Не вибирає profile і не змінює bootstrap.
pub fn core_library_fasl_is_current() -> bool {
    fasl_decode_program(CORE_LIBRARY_FASL)
        .map(|(_, source_hash)| source_hash == sha256_source(CORE_LIBRARY_SOURCE.as_bytes()))
        .unwrap_or(false)
}

/// Activate the frozen Core2/Contract-6 compatibility profile.
///
/// This loader deliberately does not install the current Core4 macro layer:
/// Core2 is a historical compatibility profile, not Core4 plus legacy answers.
/// All profiles now use D3's exact-D1 conditional mechanism; selecting a
/// historical profile changes provenance, not the language's truth model.
pub fn load_core2_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    session.environment.select_core_profile(CoreProfile::Core2);
    let result = eval_program(CORE2_LIBRARY_SOURCE, session)?;
    bind_missing_stable_surface_peers(&session.environment);
    Ok(result)
}

/// Activate the Core3 experimental kernel-laboratory profile.
///
/// Core3 currently reuses the Core4 bootstrap as a shared execution substrate.
/// The temporary Core4 selection performed by `load_core_library` is substrate
/// setup only: Core3 becomes the mechanically selected profile only after its
/// thin profile layer loads successfully.
///
/// The SENS-owned mechanism selector is deliberately NOT loaded here. Its
/// current implementation reads authority files through the filesystem, while
/// this crate is capability-free. #1411 owns the later admitted execution path.
///
/// This loader carries only the selected-profile fact. Core3 laws, result
/// domains, and mechanism admission remain owned by SENS contracts/Lisp.
pub fn load_core3_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    load_core_library(session)?;
    let result = eval_program(CORE3_LIBRARY_SOURCE, session)?;
    session.environment.select_core_profile(CoreProfile::Core3);
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
    let result = eval_program(TIME_LIBRARY_SOURCE, session)?;
    bind_missing_stable_surface_peers(&session.environment);
    Ok(result)
}

/// Load the shared byte/text adapters used by process and TCP boundaries.
/// `load_process_library` remains the compatibility entry point already used
/// by native embedders, so it now installs both language-owned text adapters:
/// public `process-run` over `process-run-raw`, and public `tcp-read` over
/// `tcp-read-raw`. Neither raw capability is required merely to define them.
pub fn load_process_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    eval_program(UTF8_LIBRARY_SOURCE, session)?;
    eval_program(PROCESS_LIBRARY_SOURCE, session)?;
    let result = eval_program(TCP_LIBRARY_SOURCE, session)?;
    bind_missing_stable_surface_peers(&session.environment);
    Ok(result)
}

/// Load language-owned TCP text semantics explicitly when an embedder does
/// not otherwise need the process adapter.
pub fn load_tcp_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    eval_program(UTF8_LIBRARY_SOURCE, session)?;
    let result = eval_program(TCP_LIBRARY_SOURCE, session)?;
    bind_missing_stable_surface_peers(&session.environment);
    Ok(result)
}

/// Load language-owned file text semantics: public `read-file`/`write-file`
/// composed entirely on the existing `read-file-bytes`/`write-file-bytes` raw
/// host capabilities plus the shared UTF-8 layer. No new host capability is
/// introduced for this migration.
pub fn load_fs_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    eval_program(UTF8_LIBRARY_SOURCE, session)?;
    let result = eval_program(FS_LIBRARY_SOURCE, session)?;
    bind_missing_stable_surface_peers(&session.environment);
    Ok(result)
}

/// Public mechanical routing hook for tooling and embedders.
/// It answers only whether a source/UI surface belongs to a currently reserved
/// SID-routed evaluator slot; no named function identity is materialized.
pub fn is_reserved_surface_name(name: &str) -> bool {
    eval::canon::is_reserved_surface(name)
}

/// Mechanical source/UI routing query: does this surface resolve to this exact
/// eight-bit function SID?
pub fn surface_has_sid(name: &str, sid: Sens8) -> bool {
    eval::canon::surface_has_sid(name, sid)
}

/// True for any admitted surface whose Lisp-owned evaluator dispatch class is Define.
pub fn is_define_surface_name(name: &str) -> bool {
    matches!(
        crate::eval::necessary_forms::identity_for_symbol(name),
        Some(crate::eval::necessary_forms::NecessaryFormIdentity::Define)
    )
}

/// True when `name` resolves to the same registry identity as the canonical
/// `defmacro` surface. No decimal SID is maintained here.
pub fn is_defmacro_surface_name(name: &str) -> bool {
    match (
        semantic_registry::admitted_semantic_id_for_surface(name),
        semantic_registry::admitted_semantic_id_for_surface("defmacro"),
    ) {
        (Some(candidate), Some(defmacro)) => candidate == defmacro,
        _ => false,
    }
}

/// True when `name` resolves to the same registry identity as the canonical
/// `lambda` surface. No decimal SID is maintained here.
pub fn is_lambda_surface_name(name: &str) -> bool {
    match (
        semantic_registry::admitted_semantic_id_for_surface(name),
        semantic_registry::admitted_semantic_id_for_surface("lambda"),
    ) {
        (Some(candidate), Some(lambda)) => candidate == lambda,
        _ => false,
    }
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


#[cfg(test)]
mod core4_bootstrap_cache_tests {
    use super::*;


    /// Measurement, not a language law. Each sample executes the identical
    /// Lisp-owned macro/Core4 bootstrap in a fresh bare Session; the *only*
    /// variable is cached vs newly verified decoded/lowered binary transport.
    /// An ignored benchmark avoids slowing normal CI correctness checks.
    #[test]
    #[ignore = "performance: run explicitly with --release on GitHub-hosted CPU"]
    fn benchmark_core4_cache_vs_fresh() {
        use std::{hint::black_box, time::Instant};

        fn one_call(use_verified_cache: bool, d3: &[Expr]) {
            let mut session = Session::bare();
            let result = load_core_library_with_fasl_mode(
                &mut session,
                CORE_LIBRARY_FASL,
                use_verified_cache,
            )
            .expect("independent Lisp-owned Core4 bootstrap");
            black_box(result);
            assert_eq!(
                session.environment.selected_core_profile(),
                Some(CoreProfile::Core4)
            );
            let evaluated = eval_parsed_expressions(d3, &mut session)
                .expect("D3 QUOTE evaluates after both Core4 bootstrap paths");
            assert!(matches!(evaluated.value, Value::Nil));
            assert!(evaluated.output.is_empty());
            black_box(session);
        }

        fn median(times: &[f64]) -> f64 {
            let mut sorted = times.to_vec();
            sorted.sort_by(f64::total_cmp);
            sorted[sorted.len() / 2]
        }

        fn measure<F: FnMut()>(iterations: usize, mut task: F) -> f64 {
            let start = Instant::now();
            for _ in 0..iterations {
                task();
            }
            start.elapsed().as_nanos() as f64 / iterations as f64
        }

        let exact_d3 = parse_canonical_binary("10 001 00 000 01")
            .expect("ratified D2/D3 quoted empty");
        assert!(
            core_library_fasl_is_current(),
            "only a verified up-to-date Core4 FASL can be benchmarked"
        );
        // Prime both paths equally; the cached path must have a hot
        // decode/lower projection and the fresh path must remain uncached.
        for _ in 0..3 {
            one_call(false, &exact_d3);
            one_call(true, &exact_d3);
        }
        let samples = 9;
        let iterations = 8;
        let mut cached = Vec::with_capacity(samples);
        let mut uncached = Vec::with_capacity(samples);
        for index in 0..samples {
            if index % 2 == 0 {
                uncached.push(measure(iterations, || one_call(false, &exact_d3)));
                cached.push(measure(iterations, || one_call(true, &exact_d3)));
            } else {
                cached.push(measure(iterations, || one_call(true, &exact_d3)));
                uncached.push(measure(iterations, || one_call(false, &exact_d3)));
            }
        }
        let no_cache_ns = median(&uncached);
        let cache_ns = median(&cached);
        assert!(no_cache_ns.is_finite() && no_cache_ns > 0.0);
        assert!(cache_ns.is_finite() && cache_ns > 0.0);
        println!(
            "SENS_CORE4_CACHE_AB={{\"schema\":\"sens-core4-cache-ab/v1\",\"samples\":{samples},\"iterations_per_sample\":{iterations},\"fresh_decode_lower_median_ns\":{no_cache_ns:.2},\"cached_decode_lower_median_ns\":{cache_ns:.2},\"ratio_fresh_over_cached\":{:.5},\"fresh_samples_ns\":{:?},\"cached_samples_ns\":{:?},\"oracle\":\"full-Lisp-Core4-and-D3-result-parity\",\"scope\":\"warm-process-fresh-sessions\"}}",
            no_cache_ns / cache_ns, uncached, cached,
        );
    }

    #[test]
    fn cached_embedded_core_preserves_independent_sessions_and_domain_result() {
        let program = parse_canonical_binary("10 001 00 000 01").unwrap();
        let mut first = Session::bare();
        let mut second = Session::bare();
        load_core_library(&mut first).expect("first cached Core4 bootstrap");
        load_core_library(&mut second).expect("second cached Core4 bootstrap");
        assert_eq!(
            first.environment.selected_core_profile(),
            Some(CoreProfile::Core4)
        );
        assert_eq!(
            second.environment.selected_core_profile(),
            Some(CoreProfile::Core4)
        );
        let left = eval_parsed_expressions(&program, &mut first).unwrap();
        let right = eval_parsed_expressions(&program, &mut second).unwrap();
        assert!(matches!(left.value, Value::Nil));
        assert_eq!(left, right);
    }

    #[test]
    fn valid_fasl_path_selects_core4_and_evaluates_current_core() {
        let expressions = parse(CORE_LIBRARY_SOURCE).expect("current Core4 parses");
        let hash = sha256_source(CORE_LIBRARY_SOURCE.as_bytes());
        let fasl = fasl_encode(&expressions, &hash);
        let mut session = Session::default();

        load_core_library_with_fasl(&mut session, &fasl).expect("valid FASL Core4 bootstrap");

        assert_eq!(
            session.environment.selected_core_profile(),
            Some(CoreProfile::Core4)
        );
    }

    #[test]
    fn stale_or_invalid_fasl_falls_back_to_text_and_still_selects_core4() {
        let mut session = Session::default();

        load_core_library_with_fasl(&mut session, b"not-a-current-fasl")
            .expect("text fallback Core4 bootstrap");

        assert_eq!(
            session.environment.selected_core_profile(),
            Some(CoreProfile::Core4)
        );
    }
}