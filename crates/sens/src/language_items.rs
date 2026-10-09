//! Discoverable language items for tooling.
//!
//! Runtime builtin names come from the same root environment used by the
//! evaluator. Tooling therefore cannot silently retain a stale copy when a
//! first-class builtin is added. Syntax-dispatched forms remain explicit
//! because they are not ordinary environment bindings.
//!
//! ADR-007 peer spellings may bind the same `Value::Builtin` under several
//! human names. Metadata follows the shared builtin value, not the spelling by
//! which that value was found, so adding a peer name does not invent another
//! operation signature.

use crate::{semantic_registry, CoreDomainIdentity, Sens8};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LanguageItemKind {
    Builtin,
    Macro,
    SyntaxForm,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Arity {
    Exact(usize),
    AtLeast(usize),
    Between { min: usize, max: usize },
}

impl Arity {
    pub fn accepts(self, received: usize) -> bool {
        match self {
            Self::Exact(expected) => received == expected,
            Self::AtLeast(minimum) => received >= minimum,
            Self::Between { min, max } => (min..=max).contains(&received),
        }
    }

    pub fn expected(self) -> String {
        match self {
            Self::Exact(expected) => expected.to_string(),
            Self::AtLeast(minimum) => format!("at least {minimum}"),
            Self::Between { min, max } => format!("between {min} and {max}"),
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LanguageItem {
    pub name: String,
    /// Canonical domain-qualified identity when this registry row has migrated.
    pub domain_identity: Option<CoreDomainIdentity>,
    /// Explicit compatibility-only registry identity for still-byte-shaped generated metadata.
    pub legacy_registry_id: Sens8,
    pub signature: &'static str,
    pub documentation: &'static str,
    pub kind: LanguageItemKind,
    pub arity: Arity,
}

mod generated {
    include!("function_signatures_generated.rs");
}

/// Метадані для інструментів (LSP, довідка REPL) — лише за кодом СЕНС, зі
/// згенерованої проєкції lib/surface/function-signatures.lisp. Назви дає
/// таблиця функцій; Rust не тримає власної копії назв чи описів.
fn semantic_language_items_with(
    stable_surfaces: impl Fn(Sens8) -> Vec<&'static str>,
    admitted_surfaces: impl Fn(Sens8) -> Vec<&'static str>,
) -> Vec<LanguageItem> {
    let mut items = Vec::new();
    for row in generated::FUNCTION_SIGNATURES {
        let semantic_id = Sens8::from_packed_byte(row.semantic_id);
        let surfaces = if row.admitted_surfaces {
            admitted_surfaces(semantic_id)
        } else {
            stable_surfaces(semantic_id)
        };
        items.extend(surfaces.into_iter().map(|name| LanguageItem {
            name: name.to_string(),
            domain_identity: semantic_registry::domain_identity_for_surface(name),
            legacy_registry_id: semantic_id,
            signature: row.signature,
            documentation: row.documentation,
            kind: row.kind,
            arity: row.arity,
        }));
    }
    items
}

/// Вид функції таблиці за кодом (з lib/surface/function-signatures.lisp).
pub(crate) fn signature_kind(semantic_id: Sens8) -> Option<LanguageItemKind> {
    generated::FUNCTION_SIGNATURES
        .iter()
        .find(|row| row.semantic_id == semantic_id.packed_byte())
        .map(|row| row.kind)
}

pub fn language_items() -> Vec<LanguageItem> {
    semantic_language_items_with(
        semantic_registry::stable_surfaces_for_semantic_id,
        semantic_registry::admitted_surfaces_for_semantic_id,
    )
}
