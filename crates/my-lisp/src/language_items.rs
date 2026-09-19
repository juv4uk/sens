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

use crate::{semantic_registry, Environment, Value};

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
    /// Numeric semantic identity when the item is governed by the surface registry.
    /// Runtime-only host capabilities may legitimately have no registry identity yet.
    pub semantic_id: Option<u8>,
    pub signature: &'static str,
    pub documentation: &'static str,
    pub kind: LanguageItemKind,
    pub arity: Arity,
}

#[derive(Clone, Copy)]
enum SurfacePolicy {
    Stable,
    Admitted,
}

#[derive(Clone, Copy)]
struct SemanticToolingMetadata {
    semantic_id: u8,
    signature: &'static str,
    documentation: &'static str,
    kind: LanguageItemKind,
    arity: Arity,
    surface_policy: SurfacePolicy,
}

// Tooling meaning is keyed only by opaque numeric semantic identity.
// Human spellings are projected from semantic-registry.wsm at discovery time.
const SEMANTIC_TOOLING: &[SemanticToolingMetadata] = &[
    SemanticToolingMetadata {
        semantic_id: 1,
        signature: "(quote value)",
        documentation: "Return value unevaluated",
        kind: LanguageItemKind::SyntaxForm,
        arity: Arity::Exact(1),
        surface_policy: SurfacePolicy::Stable,
    },
    SemanticToolingMetadata {
        semantic_id: 7,
        signature: "(cond (test result) ...)",
        documentation: "Evaluate the first matching clause",
        kind: LanguageItemKind::SyntaxForm,
        arity: Arity::AtLeast(0),
        surface_policy: SurfacePolicy::Stable,
    },
    SemanticToolingMetadata {
        semantic_id: 8,
        signature: "(lambda (params) body ...)",
        documentation: "Create an anonymous function",
        kind: LanguageItemKind::SyntaxForm,
        arity: Arity::AtLeast(2),
        surface_policy: SurfacePolicy::Stable,
    },
    SemanticToolingMetadata {
        semantic_id: 9,
        signature: "(define name value)",
        documentation: "Bind name in the current scope",
        kind: LanguageItemKind::SyntaxForm,
        arity: Arity::Exact(2),
        surface_policy: SurfacePolicy::Stable,
    },
    SemanticToolingMetadata {
        semantic_id: 10,
        signature: "(defmacro name (params) body ...)",
        documentation: "Bind a language-owned macro",
        kind: LanguageItemKind::Macro,
        arity: Arity::AtLeast(3),
        surface_policy: SurfacePolicy::Admitted,
    },
    SemanticToolingMetadata {
        semantic_id: 11,
        signature: "(def name value)",
        documentation: "Compatibility-only binding form",
        kind: LanguageItemKind::SyntaxForm,
        arity: Arity::Exact(2),
        surface_policy: SurfacePolicy::Admitted,
    },
];

fn semantic_language_items_with(
    stable_surfaces: impl Fn(u8) -> Vec<&'static str>,
    admitted_surfaces: impl Fn(u8) -> Vec<&'static str>,
) -> Vec<LanguageItem> {
    let mut items = Vec::new();
    for metadata in SEMANTIC_TOOLING {
        let surfaces = match metadata.surface_policy {
            SurfacePolicy::Stable => stable_surfaces(metadata.semantic_id),
            SurfacePolicy::Admitted => admitted_surfaces(metadata.semantic_id),
        };
        items.extend(surfaces.into_iter().map(|name| LanguageItem {
            name: name.to_string(),
            semantic_id: Some(metadata.semantic_id),
            signature: metadata.signature,
            documentation: metadata.documentation,
            kind: metadata.kind,
            arity: metadata.arity,
        }));
    }
    items
}

fn semantic_language_items() -> Vec<LanguageItem> {
    semantic_language_items_with(
        semantic_registry::stable_surfaces_for_semantic_id,
        semantic_registry::admitted_surfaces_for_semantic_id,
    )
}

fn builtin_metadata(name: &str) -> (&'static str, &'static str, Arity) {
    match name {
        "+" => ("(+ number ...)", "Sum all arguments", Arity::AtLeast(0)),
        "-" => ("(- number ...)", "Subtract or negate", Arity::AtLeast(1)),
        "*" => (
            "(* number ...)",
            "Multiply all arguments",
            Arity::AtLeast(0),
        ),
        "/" => (
            "(/ number ...)",
            "Perform exact rational division",
            Arity::AtLeast(1),
        ),
        "<" => (
            "(< number ...)",
            "Less-than chain comparison",
            Arity::AtLeast(1),
        ),
        ">" => (
            "(> number ...)",
            "Greater-than chain comparison",
            Arity::AtLeast(1),
        ),
        "=" => ("(= number ...)", "Numeric equality", Arity::AtLeast(1)),
        "atom" => (
            "(atom value)",
            "Test whether value is not a pair",
            Arity::Exact(1),
        ),
        "car" => (
            "(car pair)",
            "Return the first element of a pair",
            Arity::Exact(1),
        ),
        "cdr" => ("(cdr pair)", "Return the tail of a pair", Arity::Exact(1)),
        "cons" => ("(cons head tail)", "Create a pair", Arity::Exact(2)),
        "eq" => (
            "(eq left right)",
            "Test structural or identity equality",
            Arity::Exact(2),
        ),
        "env" => (
            "(env)",
            "Return visible bindings as an alist",
            Arity::Exact(0),
        ),
        // abs/min/max/min-list/max-list removed 2026-09-11: migrated to
        // lib/core.my (Value::Closure, not Value::Builtin), so this
        // match arm was dead -- this function only ever matches
        // Value::Builtin names (see language_items() below). Matches
        // the same already-accepted gap "list"/"not" (migrated earlier)
        // have always had: Lisp-defined library functions simply don't
        // appear in this Rust-builtin-only tooling metadata table.
        "make-vector" => (
            "(make-vector length)",
            "Create a vector of nil slots",
            Arity::Exact(1),
        ),
        "vector" => (
            "(vector value ...)",
            "Create a vector containing the arguments",
            Arity::AtLeast(0),
        ),
        "vector-length" => (
            "(vector-length vector)",
            "Return the element count",
            Arity::Exact(1),
        ),
        "vector-ref" => (
            "(vector-ref vector index)",
            "Return an element by index",
            Arity::Exact(2),
        ),
        "vector-set!" => (
            "(vector-set! vector index value)",
            "Mutate a vector slot",
            Arity::Exact(3),
        ),
        "mono-ns" => (
            "(mono-ns)",
            "Return a monotonic nanosecond counter as an exact integer",
            Arity::Exact(0),
        ),
        "unix-time-now" => (
            "(unix-time-now)",
            "Observe the host wall clock as raw Unix seconds and nanoseconds",
            Arity::Exact(0),
        ),
        "ntp-query-raw" => (
            "(ntp-query-raw host timeout-ms)",
            "Perform one bounded NTP query and return raw protocol fields",
            Arity::Exact(2),
        ),
        "timezone-declarations-raw" => (
            "(timezone-declarations-raw)",
            "Observe raw TZ and /etc/timezone declaration candidates",
            Arity::Exact(0),
        ),
        "i32-buffer" => (
            "(i32-buffer number ...)",
            "Create a signed 32-bit numeric buffer",
            Arity::AtLeast(0),
        ),
        "f32-buffer" => (
            "(f32-buffer number ...)",
            "Create a binary32 numeric buffer",
            Arity::AtLeast(0),
        ),
        "numeric-buffer?" => (
            "(numeric-buffer? value)",
            "Test for a numeric buffer",
            Arity::Exact(1),
        ),
        "numeric-buffer-type" => (
            "(numeric-buffer-type buffer)",
            "Return i32 or f32",
            Arity::Exact(1),
        ),
        "numeric-buffer-length" => (
            "(numeric-buffer-length buffer)",
            "Return the element count",
            Arity::Exact(1),
        ),
        "numeric-buffer-ref" => (
            "(numeric-buffer-ref buffer index)",
            "Return an element by index",
            Arity::Exact(2),
        ),
        "numeric-buffer-map" => (
            "(numeric-buffer-map function buffer)",
            "Map a function over a numeric buffer",
            Arity::Exact(2),
        ),
        "string-slice" => (
            "(string-slice string start end)",
            "Return a UTF-8-safe substring",
            Arity::Exact(3),
        ),
        "string-append" => (
            "(string-append left right)",
            "Concatenate two strings",
            Arity::Exact(2),
        ),
        "string<?" => (
            "(string<? left right)",
            "Compare strings lexicographically",
            Arity::Exact(2),
        ),
        "string?" => (
            "(string? value)",
            "Return t if value is a string",
            Arity::Exact(1),
        ),
        "symbol->string" => (
            "(symbol->string symbol)",
            "Return the string form of a symbol",
            Arity::Exact(1),
        ),
        "string->symbol" => (
            "(string->symbol string)",
            "Create a symbol from a string",
            Arity::Exact(1),
        ),
        "string-first" => (
            "(string-first string)",
            "Return the first character as a string",
            Arity::Exact(1),
        ),
        "string-rest" => (
            "(string-rest string)",
            "Return the string without its first character",
            Arity::Exact(1),
        ),
        "codepoint->string" => (
            "(codepoint->string scalar)",
            "Materialize one Unicode scalar as a string",
            Arity::Exact(1),
        ),
        "string->codepoint" => (
            "(string->codepoint string)",
            "Return the Unicode scalar value of one-character string",
            Arity::Exact(1),
        ),
        "sha256-hex" => (
            "(sha256-hex string)",
            "Return the SHA-256 hex digest",
            Arity::Exact(1),
        ),
        "json-parse" => (
            "(json-parse string)",
            "Parse JSON into my-lisp values",
            Arity::Exact(1),
        ),
        "print" => (
            "(print value)",
            "Output value followed by newline",
            Arity::Exact(1),
        ),
        "princ" => (
            "(princ value)",
            "Output value without reader quoting",
            Arity::Exact(1),
        ),
        "write-to-string" => (
            "(write-to-string value)",
            "Return a readable string representation",
            Arity::Exact(1),
        ),
        "read" => (
            "(read [source])",
            "Read one s-expression from a string or stdin",
            Arity::Between { min: 0, max: 1 },
        ),
        "read-all" => (
            "(read-all source)",
            "Read all expressions from a string",
            Arity::Exact(1),
        ),
        "eval" => (
            "(eval expression)",
            "Evaluate an expression represented as data",
            Arity::Exact(1),
        ),
        _ => (
            "(builtin ...)",
            "First-class runtime builtin",
            Arity::AtLeast(0),
        ),
    }
}

pub fn language_items() -> Vec<LanguageItem> {
    let mut items = Environment::root()
        .snapshot()
        .into_iter()
        .filter_map(|(name, value)| match value {
            Value::Builtin(ref builtin) => {
                let (signature, documentation, arity) = builtin_metadata(builtin.name);
                Some(LanguageItem {
                    semantic_id: semantic_registry::semantic_id_for_surface(name.as_ref()),
                    name: name.to_string(),
                    signature,
                    documentation,
                    kind: LanguageItemKind::Builtin,
                    arity,
                })
            }
            _ => None,
        })
        .collect::<Vec<_>>();

    items.extend(semantic_language_items());
    items
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_root_builtin_binding_is_discoverable_with_operation_metadata() {
        let items = language_items();
        for (name, value) in Environment::root().snapshot() {
            if matches!(value, Value::Builtin(_)) {
                let matches = items
                    .iter()
                    .filter(|item| {
                        item.kind == LanguageItemKind::Builtin
                            && item.name.as_str() == name.as_ref()
                    })
                    .collect::<Vec<_>>();
                assert_eq!(
                    matches.len(),
                    1,
                    "runtime builtin binding {name} must have exactly one tooling item"
                );
                assert_ne!(
                    matches[0].signature, "(builtin ...)",
                    "runtime builtin binding {name} needs operation metadata"
                );
                assert_ne!(
                    matches[0].documentation, "First-class runtime builtin",
                    "runtime builtin binding {name} needs operation metadata"
                );
            }
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
    #[allow(clippy::absurd_extreme_comparisons)]
    fn semantic_tooling_keys_are_byte_identities_only() {
        assert!(SEMANTIC_TOOLING.iter().all(|metadata| {
            metadata.semantic_id <= u8::MAX
        }));
    }

    #[test]
    fn registry_mutation_changes_discovered_surface_without_changing_metadata_key() {
        const BEFORE: &str = "(\"00001000\" (en comet))";
        const AFTER: &str = "(\"00001000\" (en meteor))";
        let discover = |source: &'static str| {
            semantic_language_items_with(
                |semantic_id| {
                    semantic_registry::stable_surfaces_for_semantic_id_from_source(
                        source,
                        semantic_id,
                    )
                },
                |semantic_id| {
                    semantic_registry::admitted_surfaces_for_semantic_id_from_source(
                        source,
                        semantic_id,
                    )
                },
            )
        };
        let before = discover(BEFORE);
        let after = discover(AFTER);
        assert!(before.iter().any(|item| {
            item.name == "comet" && item.semantic_id == Some(8)
        }));
        assert!(!before.iter().any(|item| item.name == "meteor"));
        assert!(after.iter().any(|item| {
            item.name == "meteor" && item.semantic_id == Some(8)
        }));
        assert!(!after.iter().any(|item| item.name == "comet"));
    }

    #[test]
    fn necessary_form_peers_share_numeric_tooling_identity() {
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
            assert_eq!(left.semantic_id, right.semantic_id);
            assert_eq!(left.signature, right.signature);
            assert_eq!(left.documentation, right.documentation);
            assert_eq!(left.arity, right.arity);
            assert_eq!(left.kind, LanguageItemKind::SyntaxForm);
            assert_eq!(right.kind, LanguageItemKind::SyntaxForm);
        }
        assert_eq!(find("lambda").semantic_id, Some(8));
        assert_eq!(find("define").semantic_id, Some(9));
    }

    #[test]
    fn defmacro_tooling_matches_runtime_macro_identity() {
        let items = language_items();
        for name in ["defmacro", "визначити-макрос"] {
            let item = items
                .iter()
                .find(|item| item.name == name)
                .unwrap_or_else(|| panic!("missing macro tooling item {name}"));
            assert_eq!(item.semantic_id, Some(10));
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
    fn def_remains_compatibility_only_in_registry_driven_discovery() {
        let items = language_items();
        let def = items
            .iter()
            .find(|item| item.name == "def")
            .expect("compatibility def tooling item");
        assert_eq!(def.semantic_id, Some(11));
        assert_eq!(def.kind, LanguageItemKind::SyntaxForm);
        assert!(semantic_registry::stable_surfaces_for_semantic_id(11).is_empty());
        assert_eq!(
            semantic_registry::admitted_surfaces_for_semantic_id(11),
            vec!["def"]
        );
    }

}
