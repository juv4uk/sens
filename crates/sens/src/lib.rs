//! Independent, capability-free core of the sens language.
//! Nezalezhne yadro movy sens bez dostupu do mozhlyvostei operatsiinoi systemy.
//! Unabhängiger Sprachkern von sens ohne Zugriff auf Betriebssystemfunktionen.
//!
//! The crate physically contains no OS access: no filesystem, no processes,
//! no sockets. Host capabilities live in the `sens-host` crate and are
//! installed into this core's registry at startup by whichever embedder
//! wants them (the CLI does; WASM does not). See eval/capabilities.rs.

/// Максимальна глибина рекурсії читачів фізичних D2-рамок.
/// Енкодери мають звіряти з нею синтетичні D2-обгортки.
pub const MAX_EXACT_D2_READER_DEPTH: usize = 128;

mod arena;
mod bignum;
mod binary_number;
mod bit9;
mod bits;
mod canonical_reader;
pub mod d7_keyboard;
mod d7_projection;
mod domain_numeric;
pub mod frame3_domain;
pub mod frame3_grammar;
pub mod frame3_micro;
pub mod frame3_micro_enumerator;
pub mod frame3_micro_v5;
pub mod frame3_micro_v5_lambda;
pub mod frame3_micro_v5_lambda_app;
pub mod frame3_semantic;
// Rust F3 лишається лише test/reference реалізацією; для окремого benchmark
// його треба явно opt-in ввімкнути. Production-коридор F3C — Zig.
#[cfg(any(test, feature = "rust-f3-reference"))]
pub mod frame3_small;
pub mod machine_math;
pub mod universal_frame3;

/// Public names for the self-contained, metadata-heavy transport experiments.
///
/// These are deliberately called Envelope E1/E2/E3 so they cannot be confused
/// with compact Frame3/F3.  The historical module paths remain available for
/// source compatibility, but new code and documentation should use these names.
pub mod envelope_e1 {
    pub use crate::universal_frame3::{
        decode, encode, Frame3Decoder as Decoder, Frame3Error as Error,
    };
}

/// Envelope E2: E1 plus the bounded grammar-rank block mode.
/// Historical wire/research name: S3/v2.
pub mod envelope_e2 {
    pub use crate::universal_frame3::{
        decode_v2 as decode, encode_v2 as encode, Frame3Error as Error, Frame3V2Decoder as Decoder,
    };
}

/// Envelope E3: domain-aware self-contained carrier, including explicit D24+.
/// Historical wire/research name: S3/v3.
pub mod envelope_e3 {
    pub use crate::frame3_domain::{decode, encode, Error, Word};
}
mod compiler_bootstrap;
mod compiler_language;
mod compiler_role;
mod domain_identity;
pub mod domain_ladder;
mod domain_words;
mod program_data;
pub use domain_ladder::DomainD10;
mod binary_bootstrap;
mod binary_execution;
mod binary_framing;
#[cfg(test)]
mod bootstrap_measurement;
#[allow(dead_code)]
mod domain_owner_generated;
pub mod domain_projection_catalog;
mod environment;
mod error;
pub(crate) mod eval;
mod gpu_execution_packet;
mod language_items;
mod mixed_source;
// Legacy Rust bit-packer retained only as a unit-test reference. Production
// SENS exposes no Rust OuterEnvelope carrier; physical packing belongs to the
// sterile Zig corridor.
#[cfg(test)]
mod outer_envelope;
mod packed_bits;
mod parser;
mod presentation;
mod semantic_registry;
pub mod sens;
mod source_packing;
mod source_words;
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
    /// Runtime/source semantics use `CoreDomainIdentity`. The `u8` implementation exists
    /// only so the pre-#1098 CML export can remain byte-for-byte unchanged in
    /// this first vertical slice; it must not be used as a SID constructor.
    #[doc(hidden)]
    pub trait ProjectionSidInput {
        #[doc(hidden)]
        fn into_projection_sid(self) -> Option<super::CoreDomainIdentity>;
    }

    impl ProjectionSidInput for super::CoreDomainIdentity {
        fn into_projection_sid(self) -> Option<super::CoreDomainIdentity> {
            Some(self)
        }
    }

    impl ProjectionSidInput for u8 {
        fn into_projection_sid(self) -> Option<super::CoreDomainIdentity> {
            super::semantic_registry::exact_identity_for_legacy_registry_slot(self)
        }
    }

    /// Stable and compatibility-only spellings admitted for `semantic_id`,
    /// each tagged with which namespace (en/uk/sa/sym/...) it belongs to.
    pub fn admitted_surfaces_for_semantic_id(
        semantic_id: impl ProjectionSidInput,
    ) -> Vec<SurfaceRow> {
        semantic_id
            .into_projection_sid()
            .map(super::semantic_registry::admitted_surfaces_with_namespace_for_semantic_id)
            .unwrap_or_default()
            .into_iter()
            .map(|(namespace, name)| SurfaceRow { namespace, name })
            .collect()
    }

    /// Повертає opaque semantic ID для stable або compatibility-only surface.
    /// Значення операції лишається у мовному контракті, не в цій проєкції.
    pub fn semantic_id_for_admitted_surface(name: &str) -> Option<super::CoreDomainIdentity> {
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

    /// Whether an exact current D6/D9/D10 identity may be an explicit D4
    /// DEFINE target. D6 targets must appear in the generated definition map
    /// and must not already be a Core operation. Evaluation still requires a
    /// concrete callable and an empty root slot.
    pub fn is_admitted_exact_definition_target(identity: super::DomainIdentity) -> bool {
        super::semantic_registry::is_admitted_exact_definition_target(identity)
    }

    /// Current domain-ladder lookup for admitted callable surfaces.
    ///
    /// Unlike historical CoreDomainIdentity, this returns the exact D3/D4/D5/D6/D8
    /// identity; an equal packed payload from another domain cannot alias it.
    /// Unadmitted or ambiguous surfaces fail closed.
    pub fn admitted_core_domain_for_surface(name: &str) -> Option<super::CoreDomainIdentity> {
        super::semantic_registry::domain_identity_for_surface(name)
    }

    /// Чинні допущені тотожності зберігають точну ширину домену.
    ///
    /// Не стискати різні D3/D4/D5/D6/D8 до одного u8: бітовий payload
    /// без домену не є семантичною тотожністю. Історичний байтовий CML ABI
    /// лишається окремою явно кваліфікованою межею експорту.
    pub fn admitted_semantic_ids() -> Vec<super::CoreDomainIdentity> {
        super::semantic_registry::admitted_semantic_ids()
    }

    /// Роль функції таблиці за кодом — з таблиці функцій, не з рукописного
    /// списку: `syntax` (особлива форма або макрос), `primitive` (примітив
    /// за кодом), `library` (визначена мовою). `None` — коду нема в таблиці
    /// метаданих (lib/surface/function-signatures.lisp).
    pub fn function_role(semantic_id: impl ProjectionSidInput) -> Option<&'static str> {
        let sid = semantic_id.into_projection_sid()?;
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
        semantic_id
            .into_projection_sid()
            .map(super::semantic_registry::semantic_id_bits)
            .unwrap_or_else(|| "UNQUALIFIED-LEGACY-SLOT".to_string())
    }
}
pub mod source_projection;
pub mod syntax;
mod text7;
mod text7_projection;
mod value;

pub use binary_number::{BinaryNumber, BinaryNumberError};
/// Canonical constructor for an existing domain-qualified exact rational.
/// Do not use this to mint a language identity: it only preserves the admitted Dn
/// identity carried by the numerator and denominator.
pub use domain_numeric::{
    canonical_parts as exact_domain_fraction_parts, DomainNumericComposition,
};

/// Host embedding adapter for already-ratified exact same-Dn + - * /
/// Value operations. Does not introduce any SENS callable identity, opcode,
/// human literal or physical T5 grammar. Operands must be admitted Dn Values.
pub fn domain_numeric_value(operator: &str, lhs: &Value, rhs: &Value) -> Option<Value> {
    domain_numeric::compute(operator, lhs, rhs)
}

pub use binary_framing::{
    decode_binary_frame, decode_binary_program, decode_numeric_value_frame,
    decode_packed_numeric_value, encode_binary_frame, encode_binary_program,
    encode_numeric_value_frame, encode_packed_numeric_value, BinaryFrame, BinaryFrameError,
};
pub use bit9::Bit9;
pub use bits::{Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8, Bits};
pub use canonical_reader::{
    parse_canonical_binary, parse_canonical_packed_words, parse_canonical_word_sequence,
};
pub use compiler_bootstrap::{
    canonical_value_sha256_mechanism, compiler_evidence_canonical_bytes,
    compiler_evidence_from_canonical_bytes, domain_identity_shape_mechanism,
    domain_identity_shape_or_empty_mechanism,
};
pub use compiler_language::{
    compiler_execution_role_from_sens, compiler_lowering_role_from_sens,
    compiler_program_artifact_from_sens, compiler_program_bootstrap_bundle,
    compiler_program_requests_from_sens, compiler_semantic_input_from_sens,
    compiler_semantic_input_from_sens_with_sources, verify_compiler_program_artifact_from_sens,
    CompilerLanguageSources, CompilerProgramBootstrapBundle, CompilerSemanticInput,
    VerifiedCompilerProgramArtifact, VerifiedCompilerProgramRequest,
};
pub use compiler_role::{compiler_execution_role, CompilerExecutionRole, CompilerLoweringRole};
pub use d7_projection::{decode_d7_uk_words, encode_d7_uk_words, D7ProjectionError};
pub use domain_identity::{CoreDomainIdentity, DomainIdentity};
pub use domain_words::{
    Bija3, CoreD4, CoreD5, CoreD6, CoreD8, CoreD9, D7DataWord, PredicateBit, Racana2,
};
pub use environment::{CoreProfile, Environment, Session};
pub use error::{Classification, ErrorKind, LanguageError};
pub use gpu_execution_packet::{GpuExecutionPacketError, GpuExecutionPacketV1, GpuOutputRequest};
pub use language_items::{language_items, Arity, LanguageItem, LanguageItemKind};
pub use mixed_source::{
    parse_mixed_exact_domain, parse_mixed_exact_domain_core_source,
    parse_mixed_exact_domain_fs_fixture_source, parse_mixed_exact_domain_fs_source,
    parse_mixed_exact_domain_guard_reference_source, parse_mixed_exact_domain_machine_source,
    parse_mixed_exact_domain_process_tcp_source, parse_mixed_exact_domain_reasoning_source,
    parse_mixed_exact_domain_time_source, parse_mixed_exact_domain_utf8_source,
};
pub use packed_bits::{BitPacker, PackedBitstream};
pub use source_packing::{
    append_binary_source_word, pack_binary_source_tokens, pack_binary_source_words,
    pack_domain_coordinates, packed_transport_accounting, semantic_source_bits,
    unpack_binary_source_words, unpack_domain_coordinates, PackedTransportAccounting,
};
pub use source_words::{
    parse_binary_source_words, parse_domain_ladder_source_words, render_binary_words_spaced,
    BinarySourceToken, BinarySourceWord, DomainLadderSourceToken, CANONICAL_SOURCE_EXTENSION,
};
pub use text7::{Text7, Text7CellError, Text7W7Error, Text7WireError, Text7WordError};
pub use text7_projection::{encode_text7, render_text7, Text7Layout, Text7ProjectionError};

pub use binary_execution::{eval_e1_program, E1ExecutionError, ExactDomainWord, PhysicalT5Program};

pub use eval::lower::lower_program;
pub use eval::parse_json;
pub use eval::{
    capability_installed, installed_capabilities, register_capability,
    register_evaluated_capability, register_sens_capability, unregister_capability,
    unregister_sens_capability,
};
pub use eval::{
    eval_exact_domain_program, eval_lowered_expressions, eval_parsed_expressions,
    eval_parsed_expressions_incremental, eval_program, evaluate as eval_expr, EvalResult,
};
pub use eval::{exact_arity, read_single_quoted_datum};
pub(crate) use parser::parse_canonical_value_wire;
pub use parser::{parse, parse_exact_domain_source};
pub use presentation::{
    ast_nodes, present_system_message, render_ast, render_ast_node, render_error_for_presentation,
    render_error_summary_for_presentation, render_value_for_presentation, AstLine, AstNode,
    AstNodeKind, PresentationLanguage,
};
pub use program_data::{expr_to_exact_program_data, lowered_program_to_exact_data};
pub use syntax::fasl::{
    decode_program as fasl_decode_program, encode_program as fasl_encode_program,
};
pub use syntax::wire::{
    decode_program as wire_decode_program, encode_program as wire_encode_program,
};

/// The current Core4 sens bootstrap library, evaluated after the macro layer.
#[cfg(test)]
pub const CORE_LIBRARY_SOURCE: &str = include_str!("../../../lib/core4.lisp");

/// Parse-output кеш для точного вбудованого Core4 source. Це лише bootstrap-
/// оптимізація: hash source перевіряється перед використанням, а stale/invalid
/// bytes переходять на parsing CORE_LIBRARY_SOURCE.
#[cfg(test)]
const CORE_LIBRARY_FASL: &[u8] = include_bytes!("../../../lib/core4.lisp.fasl");

/// Process-result interpretation owned by Lisp. The host contributes only the
/// `process-run-raw` capability; this layer decides how captured bytes become
/// text and how decoding failures are represented.
#[cfg(test)]
pub const PROCESS_LIBRARY_SOURCE: &str = include_str!("../../../lib/process.lisp");

/// TCP text interpretation owned by Lisp. The host contributes only the raw
/// socket-read bytes through `tcp-read-raw`; this layer defines public
/// `tcp-read` by applying the shared UTF-8 semantics.
#[cfg(test)]
pub const TCP_LIBRARY_SOURCE: &str = include_str!("../../../lib/tcp.lisp");

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
/// Увімкнути лише ратифікований механізм D5:00011 MACRO.
/// Не завантажує текстові бібліотеки, Core4 чи сторонні можливості.
/// Потрібний самодостатній фізичній програмі SENS, яка визначає макроси.
pub fn install_ratified_d5_macro_mechanism(session: &Session) {
    eval::install_macro_substrate(&session.environment);
}

/// Виконує точні слова макробібліотеки, відновлені Zig із Т5М під час збірки.
/// D5 створює Macro; людські назви прив'язуються до того самого значення нижче.
pub fn load_macro_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    eval::install_macro_substrate(&session.environment);
    let result = binary_bootstrap::macro_program()?.execute(session)?;

    if !matches!(&result.value, Value::Macro(_)) {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "macro library must evaluate to one Macro value",
            Span { start: 0, end: 0 },
        ));
    }

    // The macro itself was constructed by lib/macro.lisp using admitted
    // exact-domain forms. Its human spellings are lexical projections only;
    // the obsolete W8 registry row MUST NOT mint a callable domain/code slot.
    let admitted = semantic_registry::lexical_peer_spellings_for_documented_name("defmacro");
    if admitted.is_empty() {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "language-defined defmacro has no unambiguous documented surface",
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
/// name later must not retarget the others. SID-routed syntax/value slots are skipped here because their resolver already
/// owns source/UI routing independently of the lexical environment.
fn bind_missing_stable_surface_peers(environment: &Environment) {
    let snapshot = environment.snapshot();
    // HashMap, not BTreeMap: CoreDomainIdentity is deliberately not Ord (identity
    // comparison/hashing only, no ordering).
    // Iteration order here is irrelevant; this is a lookup table.
    let mut values_by_semantic_id = std::collections::HashMap::new();

    for (name, value) in snapshot {
        if eval::canon::is_reserved_surface(&name) {
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
            eval::canon::is_reserved_surface(peer)
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
/// explicitly installs the D5 `макрос` mechanism before evaluating `lib/macro.lisp`.
/// Per-thread cache of the *mechanical* Core4 binary decode and lowering.
/// This is not a shared Environment, evaluated Value, macro, or Lisp semantic
/// snapshot. Every caller still performs the full language-owned bootstrap.
/// Canonical Core4 FASL is determined by the path-bound exact-domain reader,
/// never by a source hash alone. Cache only this mechanical reference encoding
/// per thread, independently of the decoded/lowered bootstrap cache.
#[cfg(test)]
fn canonical_core4_fasl_bytes() -> Option<std::rc::Rc<[u8]>> {
    thread_local! {
        static EXPECTED: std::cell::OnceCell<Option<std::rc::Rc<[u8]>>> =
            const { std::cell::OnceCell::new() };
    }
    EXPECTED.with(|slot| {
        slot.get_or_init(|| {
            let expressions =
                parse_mixed_exact_domain_core_source("lib/core4.lisp", CORE_LIBRARY_SOURCE).ok()?;
            let hash = sha256_source(CORE_LIBRARY_SOURCE.as_bytes());
            Some(std::rc::Rc::<[u8]>::from(fasl_encode(&expressions, &hash)))
        })
        .clone()
    })
}

/// A forged or incorrectly parsed FASL may carry the correct source hash but
/// represent short D3/D4 callable heads as Numbers. Admit only the exact
/// canonical path-bound Core4 encoding; otherwise fall back to source.
#[cfg(test)]
fn decode_verified_core4_fasl(fasl: &[u8]) -> Option<Vec<Expr>> {
    let expected = canonical_core4_fasl_bytes()?;
    if fasl != expected.as_ref() {
        return None;
    }
    fasl_decode_program(fasl).map(|(expressions, _)| expressions)
}

#[cfg(test)]
fn current_core_verified_lowered() -> Option<std::rc::Rc<[Expr]>> {
    thread_local! {
        static LOWERED: std::cell::OnceCell<Option<std::rc::Rc<[Expr]>>> =
            const { std::cell::OnceCell::new() };
    }
    LOWERED.with(|slot| {
        slot.get_or_init(|| {
            let expressions = decode_verified_core4_fasl(CORE_LIBRARY_FASL)?;
            let lowered = eval::lower::lower_program(&expressions);
            Some(std::rc::Rc::<[Expr]>::from(lowered))
        })
        .clone()
    })
}

/// Core4's source fallback must use the same path-bound exact-domain reader as
/// the canonical FASL generator. The general parser intentionally keeps short
/// bit spellings such as `100` numeric outside this exact source context;
/// parsing Core4 that way leaves executable CAR heads as Numbers whenever the
/// checked-in FASL is stale. Other libraries retain their ordinary reader.
#[cfg(test)]
fn eval_core4_source_fallback(session: &mut Session) -> Result<EvalResult, LanguageError> {
    let expressions = parse_mixed_exact_domain_core_source("lib/core4.lisp", CORE_LIBRARY_SOURCE)?;
    eval_parsed_expressions(&expressions, session)
}

#[cfg(test)]
fn load_core_library_with_fasl_mode(
    session: &mut Session,
    core_fasl: &[u8],
    use_verified_cache: bool,
) -> Result<EvalResult, LanguageError> {
    // `Session::default()` already installs the same language-owned macro
    // layer. Its exact D5 mechanism slot is bind-once, so bootstrapping Core4
    // must not install the identical layer a second time.
    let macro_identity = semantic_registry::domain_identity_for_surface("макрос");
    if macro_identity
        .and_then(|identity| session.environment.domain_code_slot(identity))
        .is_none()
    {
        load_macro_library(session)?;
    }

    // Cache only the exact embedded FASL. Arbitrary caller-supplied FASL
    // (including invalid/stale fixtures) retains the original decode/fallback
    // behavior and can never borrow this cached program by matching bytes.
    let exact_embedded = core_fasl.len() == CORE_LIBRARY_FASL.len()
        && std::ptr::eq(core_fasl.as_ptr(), CORE_LIBRARY_FASL.as_ptr());
    let result = if exact_embedded && use_verified_cache {
        match current_core_verified_lowered() {
            Some(lowered) => eval_lowered_expressions(&lowered, session)?,
            None => eval_core4_source_fallback(session)?,
        }
    } else {
        match decode_verified_core4_fasl(core_fasl) {
            Some(expressions) => eval_parsed_expressions(&expressions, session)?,
            None => eval_core4_source_fallback(session)?,
        }
    };

    bind_core_runtime_mechanisms(&session.environment);
    bind_missing_stable_surface_peers(&session.environment);
    bind_existing_d5_language_mechanisms(&session.environment);
    bind_existing_d6_language_mechanisms(&session.environment);
    bind_existing_d9_language_mechanisms(&session.environment);
    session.environment.select_core_profile(CoreProfile::Core4);
    Ok(result)
}

/// Явне допущення механізму для ратифікованого D10-монотонного годинника.
/// Джерело identity: `lib/domains/d10.lisp`, точне слово `0011110110`.
/// Це один іменований механізм, а не загальна викличність D10 за резидентністю.
fn bind_core_runtime_mechanisms(environment: &Environment) {
    // The D8 ladder identifies MOD at exactly 00101100. Core4 supplies its
    // executable Lisp closure; Rust only places that existing closure in the
    // exact domain slot. If Core4 did not define it, there is no fallback or
    // host implementation and invocation remains unavailable.
    const D8_MODULO: u8 = 0b00101100;
    let modulo_identity = DomainIdentity::D8(crate::CoreD8::from_word(
        crate::Bit8::new(D8_MODULO).expect("the D8 MOD resident has eight bits"),
    ));
    if environment.domain_code_slot(modulo_identity).is_none() {
        // Lisp DEFINE stores Ukrainian D7 names under their canonical Text7
        // wire token, not their Unicode display spelling.
        if let Ok(surface) = encode_text7("модульна-остача", Text7Layout::Uk) {
            if let Some(implementation) = environment
                .get(&surface.to_canonical_wire_token())
                .filter(|value| matches!(value, Value::Closure(_) | Value::Builtin(_)))
            {
                let _ = environment.bind_domain_code_slot_once(modulo_identity, implementation);
            }
        }
    }

    const MONOTONIC_NANOSECONDS_D10: u16 = 0b0011110110;
    const SURFACE: &str = "монотонний-наносекунди";
    let identity = DomainIdentity::D10(
        DomainD10::new(MONOTONIC_NANOSECONDS_D10)
            .expect("the exact D10 monotonic-nanoseconds coordinate is ten bits"),
    );
    let candidate = eval::d10_monotonic_nanoseconds_builtin();
    if environment.domain_code_slot(identity).is_none() {
        let _ = environment.bind_domain_code_slot_once(identity, candidate.clone());
    }
    let mechanism = environment.domain_code_slot(identity).unwrap_or(candidate);
    if environment.get(SURFACE).is_none() {
        environment.define(SURFACE, mechanism);
    }

    // D8:11110100 is already an explicitly admitted value-to-text primitive.
    // Materialize its Ukrainian and compatibility names as one callable value.
    let write_to_string = eval::d8_write_to_string_builtin();
    for surface in ["значення-у-текст", "write-to-string"] {
        if environment.get(surface).is_none() {
            environment.define(surface, write_to_string.clone());
        }
    }

    // D8:11101101 уже має точний примітив і Type-перевірку в SENS.
    // Фізичне виконання за кодом працює; звичайний український Lisp
    // потребує того самого механізму за лексичною D7-проєкцією.
    // Не встановлюємо нової семантики або нератифікованого коду.
    let string_to_symbol = eval::d8_string_to_symbol_builtin();
    for surface in ["текст-у-символ", "string->symbol"] {
        if environment.get(surface).is_none() {
            environment.define(surface, string_to_symbol.clone());
        }
    }
}

/// Механічне зв'язування вже обчислених замикань SENS з точними D5.
/// Самі визначення лишаються в lib/core4.lisp, а словник дозволених адрес
/// — в lib/surface/d5-definition-bindings.lisp. Відсутній closure не
/// створюється; невідома координата ніколи не отримує викличність.
fn bind_existing_d5_language_mechanisms(environment: &Environment) {
    for name in semantic_registry::d5_lisp_definition_names() {
        let Some(identity) = semantic_registry::d5_binding_identity_for_definition(name) else {
            continue;
        };
        if environment.domain_code_slot(identity).is_some() {
            continue;
        }
        let Some(value) = encode_text7(name, Text7Layout::Uk)
            .ok()
            .and_then(|surface| environment.get(&surface.to_canonical_wire_token()))
            .or_else(|| environment.get(name))
        else {
            continue;
        };
        if matches!(value, Value::Closure(_) | Value::Builtin(_)) {
            let _ = environment.bind_domain_code_slot_once(identity, value);
        }
    }
}

/// Механічне зв'язування вже обчислених замикань SENS з точними D6.
/// Дзеркало D5-нету. Фізичний Core4 (`lib/core4.sens`) відновлює український
/// зв'язувач DEFINE як канонічне D7-слово, а не як Unicode-текст, тому шлях
/// `bind_language_definition` не бачить Unicode-імені таблиці; тут шукаємо
/// вже створене замикання за обома формами. Сам перелік не надає нового
/// допуску: похідні D6 без власного Rust-механізму отримують слот лише тоді,
/// коли справжнє Lisp-визначення вже існує. Відсутній closure не створюється.
fn bind_existing_d6_language_mechanisms(environment: &Environment) {
    for name in semantic_registry::d6_lisp_definition_names() {
        let Some(identity) = semantic_registry::d6_binding_identity_for_definition(name) else {
            continue;
        };
        // ADD1/SUB1/NEG/INTEGERP мають ратифікований Rust-механізм; їхній
        // точний слот не замінюємо Lisp-замиканням.
        if identity.core_operation().is_some() {
            continue;
        }
        if environment.domain_code_slot(identity).is_some() {
            continue;
        }
        let Some(value) = encode_text7(name, Text7Layout::Uk)
            .ok()
            .and_then(|surface| environment.get(&surface.to_canonical_wire_token()))
            .or_else(|| environment.get(name))
        else {
            continue;
        };
        // LET/LET* are SENS-owned macros: they carry source AST, not eager values.
        // Transfer only the already-executed root binding to the exact D6 slot.
        // This grants no code/residency a callable mechanism by itself.
        if matches!(
            value,
            Value::Closure(_) | Value::Builtin(_) | Value::Macro(_)
        ) {
            let _ = environment.bind_domain_code_slot_once(identity, value);
        }
    }
}

/// Attach only already-existing callable values to their ratified D9 identities.
/// This is a mechanism migration bridge, never a width-based callability grant.
fn bind_existing_d9_language_mechanisms(environment: &Environment) {
    for (name, value) in environment.snapshot() {
        if !matches!(
            value,
            Value::Builtin(_) | Value::Closure(_) | Value::Macro(_)
        ) {
            continue;
        }
        let Some(identity) = semantic_registry::d9_binding_identity_for_definition(name.as_ref())
        else {
            continue;
        };
        if environment.domain_code_slot(identity).is_none() {
            let _ = environment.bind_domain_code_slot_once(identity, value.clone());
        }
        // A language-defined D9 macro may also carry owner-ratified
        // compatibility spellings — e.g. the symbolic `->`/`->>` of
        // THREAD-FIRST/THREAD-LAST — recorded as lexical peers of its
        // documented name. Mirror load_macro_library: bind only the missing
        // peers of the already-evaluated macro value. No new law is added and
        // no existing binding is overwritten.
        if matches!(value, Value::Macro(_)) {
            for definition_name in semantic_registry::d9_definition_names(identity)
                .iter()
                .copied()
            {
                for peer in
                    semantic_registry::lexical_peer_spellings_for_documented_name(definition_name)
                {
                    if environment.get(peer).is_none()
                        && eval::canon::ensure_bindable(peer, Span::default()).is_ok()
                    {
                        environment.define(peer, value.clone());
                    }
                }
            }
        }
    }
}

/// Production always uses the owner-verified binary decode/lowering cache.
/// An internal-only switch exists solely to compare identical full Core4
/// bootstrap paths with and without cached transport on the *same* CPU.
#[cfg(test)]
fn load_core_library_with_fasl(
    session: &mut Session,
    core_fasl: &[u8],
) -> Result<EvalResult, LanguageError> {
    load_core_library_with_fasl_mode(session, core_fasl, true)
}

pub fn load_core_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    let macro_identity = semantic_registry::domain_identity_for_surface("макрос");
    if macro_identity
        .and_then(|identity| session.environment.domain_code_slot(identity))
        .is_none()
    {
        load_macro_library(session)?;
    }

    let result = binary_bootstrap::with_core4_program(|program| program.execute(session))??;
    bind_core_runtime_mechanisms(&session.environment);
    bind_missing_stable_surface_peers(&session.environment);
    bind_existing_d5_language_mechanisms(&session.environment);
    bind_existing_d6_language_mechanisms(&session.environment);
    bind_existing_d9_language_mechanisms(&session.environment);
    session.environment.select_core_profile(CoreProfile::Core4);
    Ok(result)
}

/// Read-only діагностика для embedder-а: чи відповідає Core4 FASL точному
/// вбудованому source. Не вибирає profile і не змінює bootstrap.
#[cfg(test)]
pub fn core_library_fasl_is_current() -> bool {
    decode_verified_core4_fasl(CORE_LIBRARY_FASL).is_some()
}

/// Activate the frozen Core2/Contract-6 compatibility profile.
///
/// This loader deliberately does not install the current Core4 macro layer:
/// Core2 is a historical compatibility profile, not Core4 plus legacy answers.
/// All profiles now use D3's exact-D1 conditional mechanism; selecting a
/// historical profile changes provenance, not the language's truth model.
pub fn load_core2_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    session.environment.select_core_profile(CoreProfile::Core2);
    bind_missing_stable_surface_peers(&session.environment);
    // `lib/core2.lisp` is a comments-only profile description (zero forms),
    // so loading it has no language effect and needs no embedded source bytes.
    Ok(EvalResult {
        value: Value::Nil,
        output: session.environment.output_snapshot(),
    })
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
    let result = binary_bootstrap::core3_program()?.execute(session)?;
    session.environment.select_core_profile(CoreProfile::Core3);
    Ok(result)
}

/// Завантажити caller-supplied MetaEval source через той самий загальний
/// exact-domain reader, який використовує інший SENS Lisp source.
pub fn load_meta_evaluator_library_from_source(
    session: &mut Session,
    meta_eval_source: &str,
) -> Result<EvalResult, LanguageError> {
    let forms = parse_mixed_exact_domain(meta_eval_source)?;
    eval_parsed_expressions(&forms, session)
}

/// Load language-owned time semantics into a session that already has the
/// ordinary core library. Keeping this separate from `load_core_library`
/// preserves the closed language core while giving embedders one canonical
/// time-layer loader instead of ad-hoc `include_str!` calls.
pub fn load_time_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    if session
        .environment
        .has_domain_code_slot(binary_bootstrap::TIME_DEFINITION)
    {
        return Ok(EvalResult {
            value: Value::Nil,
            output: Vec::new(),
        });
    }
    binary_bootstrap::time_program()?.execute(session)
}

/// Завантажити UTF-8 бібліотеку як точні слова Zig/T5M.
/// Джерело Lisp тут не читається і не проєктується Rust-ом.
pub fn load_utf8_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    bind_existing_d9_language_mechanisms(&session.environment);
    bind_process_tcp_lisp_owned_macros(session)?;
    if session.environment.get("codepoint->string").is_none() {
        session.environment.define(
            "codepoint->string",
            Value::host_function(std::rc::Rc::new(eval::runtime_codepoint_to_string)),
        );
    }
    // D10-слот є першокласною мовною функцією, а не повторно
    // переписуваною назвою. FS, TCP і process можуть звернутися до
    // спільного UTF-8 після першого завантаження; другий DEFINE
    // того самого доменного коду порушує незмінність SENS.
    // D10:0010111011 is the exact, owner-ratified `укр` coordinate in
    // lib/domains/d10.lisp. The generic D10 definition-binding projection
    // includes concrete Core4 definitions only; UTF-8 is loaded separately
    // and must not be guessed from that narrower table (or from SID8/W8).
    // This identity locates an existing SENS-defined closure, not a host
    // implementation or blanket admission of a D10 resident.
    if utf8_library_is_loaded(session) {
        let value = session
            .environment
            .completed_bootstrap_result(binary_bootstrap::UTF8_DEFINITION)
            .ok_or_else(|| {
                LanguageError::new(
                    ErrorKind::InvalidForm,
                    "UTF8_BOOTSTRAP_INCOMPLETE: Д10 функція вже існує, але завершений запуск бібліотеки не зареєстрований",
                    Span::default(),
                )
            })?;
        bind_missing_stable_surface_peers(&session.environment);
        return Ok(EvalResult {
            value,
            output: session.environment.output_snapshot(),
        });
    }
    let result = binary_bootstrap::utf8_program()?.execute(session)?;
    session
        .environment
        .complete_bootstrap(binary_bootstrap::UTF8_DEFINITION, result.value.clone());
    bind_missing_stable_surface_peers(&session.environment);
    Ok(result)
}

/// Check the exact ratified D10 resident that the UTF-8 bootstrap defines.
/// This is only an installation sentinel; the D10 identity does not gain a
/// call route from this check. Reusing the already-loaded dependency prevents
/// a second DEFINE from conflicting when process/TCP and FS are composed.
fn utf8_library_is_loaded(session: &Session) -> bool {
    session
        .environment
        .has_domain_code_slot(binary_bootstrap::UTF8_DEFINITION)
}

fn load_utf8_dependency(session: &mut Session) -> Result<(), LanguageError> {
    if !utf8_library_is_loaded(session)
        || session
            .environment
            .completed_bootstrap_result(binary_bootstrap::UTF8_DEFINITION)
            .is_none()
    {
        load_utf8_library(session)?;
    }
    Ok(())
}

/// Load caller-supplied time source through the SAME owner-pinned exact-width
/// reader used by the original loader. Zig transports bytes; SENS interprets.
pub fn load_time_library_from_source(
    session: &mut Session,
    source: &str,
) -> Result<EvalResult, LanguageError> {
    // Short D3 heads are domain words, not ordinary Lisp numeric literals.
    let expressions = parse_mixed_exact_domain_time_source("lib/time.lisp", source)?;
    let result = eval_parsed_expressions(&expressions, session)?;
    bind_missing_stable_surface_peers(&session.environment);
    Ok(result)
}

/// Execute only a specifically pinned reasoning library through the exact
/// domain-width reader. The caller supplies the identity-checked repository
/// path; ordinary eval_program continues to mean ordinary Lisp, not inference
/// from unknown three-bit tokens. No W8 -> D8 conversion occurs here.
pub fn eval_pinned_reasoning_source(
    path: &str,
    source: &str,
    session: &mut Session,
) -> Result<EvalResult, LanguageError> {
    let expressions = parse_mixed_exact_domain_reasoning_source(path, source)?;
    eval_parsed_expressions(&expressions, session)
}

/// Evaluate precisely one filesystem regression fixture through its
/// pinned D3/D4 source reader, after the caller loads the Lisp libraries.
pub fn eval_pinned_fs_fixture_source(
    path: &str,
    source: &str,
    session: &mut Session,
) -> Result<EvalResult, LanguageError> {
    let expressions = parse_mixed_exact_domain_fs_fixture_source(path, source)?;
    eval_parsed_expressions(&expressions, session)
}

/// Evaluate the current human-readable Core library through SENS's common
/// reader. The reader and evaluator own every identity and language rule.
pub fn eval_core_library_source(
    source: &str,
    session: &mut Session,
) -> Result<EvalResult, LanguageError> {
    let expressions = parse_mixed_exact_domain(source)?;
    eval_parsed_expressions(&expressions, session)
}

/// Bind the already-evaluated Lisp-owned LET* macro to the exact D6 identity
/// from the ratified Ukrainian source registry. The parser preserves the D6
/// head; dispatch then finds this code-slot and expands the macro before its
/// binding-list arguments are evaluated. No D6 law or Rust implementation is
/// added here, and an existing non-macro slot is a hard error.
fn bind_process_tcp_lisp_owned_macros(session: &mut Session) -> Result<(), LanguageError> {
    for (uk_surface, full_ukr_surface, expected_bits) in [
        ("нехай", "нехай", 0b001000u16),
        ("нехай*", "нехай-послідовно", 0b001001u16),
    ] {
        let identity = semantic_registry::exact_uk_callable_for_source_head(uk_surface)
            .filter(|identity| identity.width() == 6 && identity.packed_bits() == expected_bits)
            .ok_or_else(|| {
                LanguageError::new(
                    ErrorKind::InvalidForm,
                    format!("D6 {uk_surface} source identity is not admitted by the exact domain registry"),
                    Span::default(),
                )
            })?;

        // Точний D6-слот є владою виклику: Core4 міг уже встановити
        // виконуваний Lisp-макрос без окремого lexical spelling. У такому
        // разі додатковий lookup за текстовою назвою не є передумовою.
        // Важливо: зайнятий НЕ-макросом слот — справжня помилка.
        match session.environment.domain_code_slot(identity) {
            Some(Value::Macro(_)) => continue,
            Some(_) => {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    format!("D6 {uk_surface} mechanism slot is occupied by a non-macro"),
                    Span::default(),
                ));
            }
            None => {}
        }

        // Лише коли точного слота немає, переносимо вже існуюче
        // SENS-визначення, а не вигадуємо Rust-реалізацію або SID8.
        // З фізичного T5M Core4 український зв'язувач може бути збережений
        // як канонічне D7-слово, а не як текстовий ключ середовища.
        // Шукаємо тільки вже створений SENS-макрос; Rust не визначає закон LET.
        let implementation = [full_ukr_surface, uk_surface]
            .into_iter()
            .find_map(|name| {
                session.environment.get(name).or_else(|| {
                    crate::encode_text7(name, crate::Text7Layout::Uk)
                        .ok()
                        .and_then(|word| session.environment.get(&word.to_canonical_wire_token()))
                })
            })
            .filter(|value| matches!(value, Value::Macro(_)))
            .ok_or_else(|| {
                LanguageError::new(
                    ErrorKind::InvalidForm,
                    format!("Lisp-owned {full_ukr_surface} macro is not installed"),
                    Span::default(),
                )
            })?;

        if !session
            .environment
            .bind_domain_code_slot_once(identity, implementation)
        {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                format!("could not bind Lisp-owned {full_ukr_surface} to exact D6"),
                Span::default(),
            ));
        }
    }
    Ok(())
}

/// Load the shared byte/text adapters used by process and TCP boundaries.
/// `load_process_library` remains the compatibility entry point already used
/// by native embedders, so it now installs both language-owned text adapters:
/// public `process-run` over `process-run-raw`, and public `tcp-read` over
/// `tcp-read-raw`. Neither raw capability is required merely to define them.
pub fn load_process_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    load_utf8_dependency(session)?;
    binary_bootstrap::process_program()?.execute(session)?;
    let result = binary_bootstrap::tcp_program()?.execute(session)?;
    bind_missing_stable_surface_peers(&session.environment);
    Ok(result)
}

/// Load language-owned TCP text semantics explicitly when an embedder does
/// not otherwise need the process adapter.
pub fn load_tcp_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    load_utf8_dependency(session)?;
    let result = binary_bootstrap::tcp_program()?.execute(session)?;
    bind_missing_stable_surface_peers(&session.environment);
    Ok(result)
}

/// Load language-owned file text semantics: public `read-file`/`write-file`
/// composed entirely on the existing `read-file-bytes`/`записати-байти-файла` raw
/// host capabilities plus the shared UTF-8 layer. No new host capability is
/// introduced for this migration.
pub fn load_fs_library(session: &mut Session) -> Result<EvalResult, LanguageError> {
    load_utf8_dependency(session)?;
    let result = binary_bootstrap::fs_program()?.execute(session)?;
    bind_missing_stable_surface_peers(&session.environment);
    Ok(result)
}

/// Public mechanical routing hook for tooling and embedders.
/// It answers only whether a source/UI surface belongs to a currently reserved
/// SID-routed evaluator slot; no named function identity is materialized.
pub fn is_reserved_surface_name(name: &str) -> bool {
    eval::canon::is_reserved_surface(name)
}

/// Перевірити точну доменну тотожність поверхневої назви.
/// Збіг бітів без збігу домену не створює еквівалентності.
pub fn surface_has_domain_identity(name: &str, identity: CoreDomainIdentity) -> bool {
    semantic_registry::domain_identity_for_surface(name) == Some(identity)
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
pub use value::{Closure, NumericBuffer, PairNode, Rational, Value};

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

    // Механічний тест завантажувача, а не оракул семантики LET/LET*.
    // Core4 уже повинен надати виконувані D6 макроси; повторне
    // зв'язування не має вимагати дубльованих текстових назв.
    #[test]
    fn d6_macro_mechanism_rebinding_is_idempotent_after_core4() {
        let mut session = Session::bare();
        load_core_library(&mut session).expect("живий Core4 через Zig T5M");
        bind_process_tcp_lisp_owned_macros(&mut session)
            .expect("вже встановлені мовні D6 механізми допускають повторний прохід");
        bind_process_tcp_lisp_owned_macros(&mut session)
            .expect("повторний прохід не вимагає другого DEFINE");
        for (surface, bits) in [("нехай", 0b001000u16), ("нехай*", 0b001001u16)] {
            let identity = semantic_registry::exact_uk_callable_for_source_head(surface)
                .expect("збережено ратифіковану D6 тотожність");
            assert_eq!(identity.width(), 6);
            assert_eq!(identity.packed_bits(), bits);
            assert!(
                matches!(
                    session.environment.domain_code_slot(identity),
                    Some(Value::Macro(_))
                ),
                "D6 {surface} завантажено тільки як реальний Lisp-макрос"
            );
        }
    }

    // Перевіряється лише видимість уже ратифікованого D8 механізму:
    // закони розпізнавання символу перевіряє сам Lisp/SENS через Zig/T5M.
    #[test]
    fn d8_string_to_symbol_projection_is_installed_after_core4() {
        let mut session = Session::bare();
        load_core_library(&mut session).expect("чинний Core4 завантажується фізично");
        // Таблиця драбини є джерелом координати; реєстр викличності
        // навмисно не містить автоматично кожну ратифіковану поверхню.
        assert_eq!(
            domain_projection_catalog::lookup(
                domain_projection_catalog::ProjectionSource::DomainTable,
                8,
                "11101101",
                "ук",
            ),
            Some(domain_projection_catalog::ProjectionValue::Symbol(
                "текст-у-символ"
            ))
        );
        assert!(
            matches!(
                session.environment.get("текст-у-символ"),
                Some(Value::Builtin(_))
            ),
            "вже реалізований D8 механізм має бути доступним звичайному Lisp"
        );
    }

    #[test]
    fn core4_t5m_bootstrap_contains_executable_forms() {
        let form_count = binary_bootstrap::with_core4_program(PhysicalT5Program::form_count)
            .expect("Zig-restored Core4 T5M program");
        assert!(form_count > 0);

        let mut binary_session = Session::bare();
        let binary_result = load_core_library(&mut binary_session)
            .expect("production Core4 bootstrap executes Zig-restored T5M");
        assert_eq!(
            binary_session.environment.selected_core_profile(),
            Some(CoreProfile::Core4)
        );

        let mut source_session = Session::bare();
        let source_result =
            load_core_library_with_fasl_mode(&mut source_session, b"source-oracle", false)
                .expect("source Core4 oracle remains available to tests");
        assert_eq!(
            binary_result.value.to_string(),
            source_result.value.to_string()
        );

        for session in [&mut binary_session, &mut source_session] {
            let result = eval_program("(додати-1 число-один)", session)
                .expect("Core4 D6 operation is callable after bootstrap");
            assert_eq!(result.value.to_string(), "2");
        }
    }

    #[test]
    fn core2_profile_selection_does_not_load_comment_only_source() {
        let mut session = Session::bare();
        let result = load_core2_library(&mut session).expect("Core2 profile selection");
        assert_eq!(
            session.environment.selected_core_profile(),
            Some(CoreProfile::Core2)
        );
        assert!(matches!(result.value, Value::Nil));
        assert!(result.output.is_empty());
    }

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

        let exact_d3 =
            parse_canonical_binary("10 001 00 000 01").expect("ratified D2/D3 quoted empty");
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
        let expressions =
            parse_mixed_exact_domain_core_source("lib/core4.lisp", CORE_LIBRARY_SOURCE)
                .expect("current Core4 parses with exact-domain call heads");
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
    fn d10_monotonic_nanoseconds_loads_and_invokes_exact_surface() {
        let mut session = Session::default();
        load_core_library(&mut session).expect("Core4 bootstrap");
        load_time_library(&mut session).expect("time library bootstrap");

        let result = eval_program("(монотонний-наносекунди)", &mut session)
            .expect("exact D10 monotonic-nanoseconds mechanism is callable");
        let nanoseconds = result
            .value
            .to_string()
            .parse::<i128>()
            .expect("monotonic clock result is an exact integer");
        assert!(nanoseconds >= 0);

        let identity = semantic_registry::d9_binding_identity_for_definition("створити-символ")
            .expect("ratified D9 identity for fresh-symbol operation");
        let argument = Value::String(std::rc::Rc::from("probe-"));
        let first = eval::invoke_value(
            &Value::DomainIdentity(identity),
            std::slice::from_ref(&argument),
            &session.environment,
            Span::default(),
        )
        .expect("exact D9 mechanism calls the Lisp-owned symbol constructor");
        let second = eval::invoke_value(
            &Value::DomainIdentity(identity),
            &[argument],
            &session.environment,
            Span::default(),
        )
        .expect("exact D9 mechanism returns another fresh symbol");
        assert!(matches!(first, Value::Symbol(_)));
        assert!(matches!(second, Value::Symbol(_)));
        assert_ne!(first, second);

        let unrelated = DomainIdentity::D10(
            DomainD10::new(0b0000000010).expect("valid unrelated D10 resident"),
        );
        assert!(
            eval::invoke_value(
                &Value::DomainIdentity(unrelated),
                &[],
                &session.environment,
                Span::default(),
            )
            .is_err(),
            "one explicit D10 mechanism must not make other D10 residents callable"
        );
    }

    #[test]
    fn time_library_loader_is_idempotent_across_child_surface_frames() {
        let mut root = Session::default();
        load_core_library(&mut root).expect("Core4 bootstrap");
        load_time_library(&mut root).expect("install exact D10 mechanisms in root");

        let mut child = Session {
            environment: root.environment.child(),
        };
        load_time_library(&mut child)
            .expect("inherited time mechanisms are not redefined in a child frame");
    }

    #[test]
    fn utf8_partial_bootstrap_is_not_reported_as_complete() {
        let mut session = Session::default();
        load_core_library(&mut session).expect("Core4 bootstrap");
        assert!(session
            .environment
            .bind_domain_code_slot_once(binary_bootstrap::UTF8_DEFINITION, Value::Nil,));
        let error = load_utf8_dependency(&mut session)
            .expect_err("наявність одного слота не доводить завершення бібліотеки");
        assert_eq!(error.kind, ErrorKind::InvalidForm);
        assert!(error.message.starts_with("UTF8_BOOTSTRAP_INCOMPLETE:"));
    }

    #[test]
    fn same_hash_ordinary_reader_fasl_cannot_reinterpret_d3_heads_as_numbers() {
        // A matching source hash does NOT prove that callable D3-D6 heads
        // survived reading; the generic parser reads bare 100 as a Number.
        let expressions = parse(CORE_LIBRARY_SOURCE).expect("ordinary reader can parse Core4");
        let hash = sha256_source(CORE_LIBRARY_SOURCE.as_bytes());
        let wrong_fasl = fasl_encode(&expressions, &hash);
        assert!(
            decode_verified_core4_fasl(&wrong_fasl).is_none(),
            "source hash must not authorize FASL built by the wrong reader"
        );

        let mut session = Session::default();
        load_core_library_with_fasl(&mut session, &wrong_fasl)
            .expect("incorrect-reader FASL must fall back to exact-domain Core4 source");
        assert_eq!(
            session.environment.selected_core_profile(),
            Some(CoreProfile::Core4)
        );
        let result = eval_program("(нехай-послідовно ((x 7) (y x)) y)", &mut session)
            .expect("D6 let* remains callable after rejected FASL");
        assert_eq!(result.value.to_string(), "7");
    }

    #[test]
    fn stale_or_invalid_fasl_falls_back_to_exact_domain_core4_source() {
        let mut session = Session::default();

        load_core_library_with_fasl(&mut session, b"not-a-current-fasl")
            .expect("exact-domain source fallback Core4 bootstrap");

        assert_eq!(
            session.environment.selected_core_profile(),
            Some(CoreProfile::Core4)
        );
        load_process_library(&mut session)
            .expect("process library must bind its current Ukrainian D6 macros");

        // Core4's Lisp-owned Ukrainian surface must remain executable after
        // the source fallback; no retired English binding is needed.
        let result = eval_core_library_source("(нехай ((значення 7)) значення)", &mut session)
            .expect("fallback must execute the Ukrainian D6 parallel-binding macro");
        assert_eq!(result.value.to_string(), "7");

        // Cover the sequential macro's empty base case and dependent
        // expansion without changing any quantity laws.
        let empty_sequential = eval_core_library_source("(нехай-послідовно () 11)", &mut session)
            .expect("empty sequential bindings must return their body");
        assert_eq!(empty_sequential.value.to_string(), "11");

        let dependent_sequential = eval_core_library_source(
            "(нехай-послідовно ((перший 7) (другий перший)) другий)",
            &mut session,
        )
        .expect("sequential bindings must see previous values");
        assert_eq!(dependent_sequential.value.to_string(), "7");
    }
}

#[cfg(test)]
mod exact_surface_domain_query_migration_tests {
    use super::*;

    #[test]
    fn surface_query_is_domain_qualified_not_packed_byte() {
        let quote =
            semantic_registry::domain_identity_for_surface("як-є").expect("ратифікована D3 QUOTE");
        let cons = semantic_registry::domain_identity_for_surface("сполучити")
            .expect("ратифікована D3 CONS");
        assert_ne!(quote, cons);
        assert!(surface_has_domain_identity("як-є", quote));
        assert!(!surface_has_domain_identity("як-є", cons));
        assert!(!surface_has_domain_identity("неіснуюча-функція", quote));
    }

    #[test]
    fn bare_cli_session_recovers_lisp_macros_through_d7_and_exact_d6_slots() {
        // CLI використовує голий Environment::root(), НЕ Session::default().
        // Тут Rust перевіряє лише фізичне встановлення механізму; закон макроса —
        // тільки у виконуваних Lisp/SENS-свідках.
        let mut session = Session {
            environment: Environment::root(),
        };
        load_core_library(&mut session).expect("CLI Core4 bootstrap");
        load_utf8_library(&mut session)
            .expect("UTF-8 requires the two Lisp-owned D6 macros from physical Core4");
        for name in ["нехай", "нехай*"] {
            let identity = semantic_registry::exact_uk_callable_for_source_head(name)
                .expect("ратифікований код D6 макроса");
            assert_eq!(identity.width(), 6, "D6 identity for {name}");
            assert!(
                matches!(
                    session.environment.domain_code_slot(identity),
                    Some(Value::Macro(_))
                ),
                "test_id=BARE-CLI-D6-MACRO-INSTALL missing exact macro for {name}"
            );
        }
        load_process_library(&mut session)
            .expect("process/TCP adapters must reuse the installed Lisp macros");
    }

    #[test]
    fn filesystem_library_loads_from_zig_restored_t5m_words() {
        let mut session = Session::default();
        load_core_library(&mut session).expect("Core4 bootstrap");
        load_process_library(&mut session).expect("process and TCP T5M bootstrap");
        load_fs_library(&mut session).expect("filesystem T5M bootstrap executes");
    }
}
