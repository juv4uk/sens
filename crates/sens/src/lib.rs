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
pub mod compilation_artifact;
pub mod compilation_artifact_producer;
pub mod conformance_oracle;
pub mod fixpoint_checkpoint;
pub mod gpu_admission;
pub mod gpu_oracle;
pub mod gpu_oracle_conformance;
pub mod program_compiler;
mod program_data;
mod compiler_role;
mod compiler_bootstrap;
mod compiler_language;
pub mod selfhost_lineage;
mod domain_words;
mod domain_identity;
mod packed_bits;
mod binary_framing;
mod gpu_execution_packet;
mod environment;
mod error;
pub(crate) mod eval;
mod language_items;
mod parser;
mod presentation;
mod semantic_registry;
mod source_words;
mod source_packing;
mod ternary_transport;
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
pub use canonical_reader::parse_canonical_binary;
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
pub use gpu_admission::{GpuAdmission, GpuAdmissionInventory};
pub use domain_identity::{CoreDomainIdentity, DomainIdentity};
pub use domain_words::{Bija3, CoreD4, CoreD5, CoreD6, SoundD7, CoreD8, CoreD9, PredicateBit, Racana2};
pub use packed_bits::{BitPacker, PackedBitstream};
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
    append_binary_source_word, pack_binary_source_tokens, packed_transport_accounting,
    semantic_source_bits, unpack_binary_source_words, PackedTransportAccounting,
};
pub use text7::{Text7, Text7CellError, Text7W7Error, Text7WireError, Text7WordError};
pub use text7_projection::{
    encode_text7, render_text7, Text7Layout, Text7ProjectionError, TEXT7_LAYOUT_SHA256,
    TEXT7_TABLE_SHA256, TEXT7_UPSTREAM_REVISION,
};

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