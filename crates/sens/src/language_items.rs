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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::Value;

    #[test]
    fn every_primitive_code_has_tooling_metadata() {
        // Після #1477 вбудовані функції — примітиви за кодом, без прив'язки за
        // назвою; метадані мають знаходитися за кодом для кожного з них.
        for byte in 0..=u8::MAX {
            let sid = Sens8::from_packed_byte(byte);
            if crate::eval::canon::has_primitive(sid) {
                assert!(
                    generated::FUNCTION_SIGNATURES.iter().any(|row| row.semantic_id == byte),
                    "primitive {sid} needs tooling metadata"
                );
            }
        }
        let items = language_items();
        for name in ["string-append", "print", "vector-ref", "json-parse", "string<?"] {
            assert!(items.iter().any(|item| item.name == name), "missing tooling item {name}");
        }
    }

    #[test]
    fn add_peer_spellings_share_one_metadata_source() {
        let items = language_items();
        let find = |name: &str| {
            items
                .iter()
                .find(|item| item.kind == LanguageItemKind::Builtin && item.name == name)
                .unwrap_or_else(|| panic!("missing tooling binding {name}"))
        };

        let uk = find("додати");
        let en = find("+");
        let sa = find("yoga");
        assert_eq!(uk.signature, en.signature);
        assert_eq!(en.signature, sa.signature);
        assert_eq!(uk.documentation, en.documentation);
        assert_eq!(en.documentation, sa.documentation);
        assert_eq!(uk.arity, en.arity);
        assert_eq!(en.arity, sa.arity);
    }

    #[test]
    fn tooling_metadata_has_one_row_per_code() {
        let mut seen = std::collections::HashSet::new();
        for row in generated::FUNCTION_SIGNATURES {
            assert!(seen.insert(row.semantic_id), "duplicate tooling row {:08b}", row.semantic_id);
        }
    }

    #[test]
    fn registry_mutation_changes_discovered_surface_without_changing_metadata_key() {
        let discover = |sid8_surface: &'static str| {
            semantic_language_items_with(
                |semantic_id| {
                    if semantic_id == crate::sens!(00001000) {
                        vec![sid8_surface]
                    } else {
                        vec![]
                    }
                },
                |semantic_id| {
                    if semantic_id == crate::sens!(00001000) {
                        vec![sid8_surface]
                    } else {
                        vec![]
                    }
                },
            )
        };
        let before = discover("comet");
        let after = discover("meteor");
        assert!(before.iter().any(|item| {
            item.name == "comet" && item.legacy_registry_id == crate::sens!(00001000)
        }));
        assert!(!before.iter().any(|item| item.name == "meteor"));
        assert!(after.iter().any(|item| {
            item.name == "meteor" && item.legacy_registry_id == crate::sens!(00001000)
        }));
        assert!(!after.iter().any(|item| item.name == "comet"));
    }

    #[test]
    fn necessary_form_peers_share_sid8_tooling_identity() {
        let items = language_items();
        let find = |name: &str| {
            items
                .iter()
                .find(|item| item.name == name)
                .unwrap_or_else(|| panic!("missing tooling item {name}"))
        };
        for pair in [["lambda", "функція"], ["define", "визначити"]] {
            let left = find(pair[0]);
            let right = find(pair[1]);
            assert_eq!(left.domain_identity, right.domain_identity);
            assert_eq!(left.legacy_registry_id, right.legacy_registry_id);
            assert_eq!(left.signature, right.signature);
            assert_eq!(left.documentation, right.documentation);
            assert_eq!(left.arity, right.arity);
            assert_eq!(left.kind, LanguageItemKind::SyntaxForm);
            assert_eq!(right.kind, LanguageItemKind::SyntaxForm);
        }
        let lambda = find("lambda");
        let define = find("define");
        assert_eq!(lambda.legacy_registry_id, crate::sens!(00001000));
        assert_eq!(define.legacy_registry_id, crate::sens!(00001001));
        assert_eq!(lambda.domain_identity.map(CoreDomainIdentity::width), Some(4));
        assert_eq!(lambda.domain_identity.map(CoreDomainIdentity::packed_bits), Some(0b0010));
        assert_eq!(define.domain_identity.map(CoreDomainIdentity::width), Some(4));
        assert_eq!(define.domain_identity.map(CoreDomainIdentity::packed_bits), Some(0b0011));
    }

    #[test]
    fn d3_tooling_uses_canonical_domain_identity() {
        let items = language_items();
        let find = |name: &str| items.iter().find(|item| item.name == name).unwrap();

        let cond = find("cond").domain_identity.unwrap();
        let eq = find("eq").domain_identity.unwrap();
        assert_eq!((cond.width(), cond.packed_bits()), (3, 0b011));
        assert_eq!((eq.width(), eq.packed_bits()), (3, 0b111));
    }

    #[test]
    fn defmacro_tooling_matches_runtime_macro_identity() {
        let items = language_items();
        for name in ["defmacro", "визначити-макрос"] {
            let item = items
                .iter()
                .find(|item| item.name == name)
                .unwrap_or_else(|| panic!("missing macro tooling item {name}"));
            assert_eq!(item.legacy_registry_id, crate::sens!(00001010));
            assert_eq!(item.kind, LanguageItemKind::Macro);
        }

        let session = crate::Session::default();
        for name in ["defmacro", "визначити-макрос"] {
            assert!(
                matches!(session.environment.get(name), Some(Value::Macro(_))),
                "runtime binding {name} must be Value::Macro"
            );
        }
    }

    #[test]
    fn def_is_a_present_status_free_registry_surface() {
        let items = language_items();
        let def = items
            .iter()
            .find(|item| item.name == "def")
            .expect("def tooling item");
        assert_eq!(def.legacy_registry_id, crate::sens!(00001011));
        assert_eq!(def.kind, LanguageItemKind::SyntaxForm);
        assert_eq!(
            semantic_registry::stable_surfaces_for_semantic_id(crate::sens!(00001011)),
            vec!["def"]
        );
        assert_eq!(
            semantic_registry::admitted_surfaces_for_semantic_id(crate::sens!(00001011)),
            vec!["def"]
        );
    }

}
