//! guard_knowledge.rs — Guard explanation/guidance/evidence for the IDE,
//! sourced from the canonical WSM files themselves, never duplicated in
//! Rust strings.
//!
//! Guard knowledge lives in two authoritative files under the workspace
//! root: `knowledge/guard-reference.lisp` (the reference bureau: each topic
//! points at authority, the canonical how-to and the verification evidence)
//! and `lib/guard.lisp` (the shared guard-finding functions). This module
//! reads both at runtime, parses them with the SAME canonical reader the
//! evaluator uses (`sens::parse`), and walks the parsed AST. No string
//! copy of any summary/authority/how-to/verify text exists here — if the
//! WSM files change, what the IDE shows follows, because the IDE serves the
//! live parse.
//!
//! If either file is absent (a workspace that is not the sens repo), the
//! knowledge is simply empty and the LSP behaves exactly as before: no
//! guard hover, no guard arity diagnostics.

use sens::{Arity, Expr, ExprKind, LanguageItemKind, Span};
use std::collections::HashMap;
use std::path::PathBuf;
use std::path::Path;

/// One entry of the reference bureau directory.
#[derive(Clone, Debug)]
pub struct GuardReference {
    pub topic: String,
    pub summary: String,
    pub authority: Vec<String>,
    pub how_to: Vec<String>,
    pub verify: Vec<String>,
    pub lifecycle: String,
    pub provenance: String,
    pub unknown_route: String,
}

/// One function defined in lib/guard.lisp, with its lambda arity and the
/// spans needed to render the canonical defining form on hover.
#[derive(Clone, Debug)]
pub struct GuardFunction {
    pub name: String,
    pub name_span: Span,
    pub form_span: Span,
    pub arity: usize,
}

/// A loaded guard-knowledge snapshot. Default = empty (nothing found).
///
/// Load is deliberately split: the function map comes from `lib/guard.lisp`
/// and is cheap (~ms, so arity diagnostics publish it eagerly), while the
/// reference directory (`knowledge/guard-reference.lisp`) is only parsed on
/// first need via `ensure_topics` — the canonical parser takes ~3.4s
/// (release) on that 47KB file today, so a session that never hovers a
/// guard topic must never pay for it.
#[derive(Clone, Debug, Default)]
pub struct GuardKnowledge {
    pub topics: HashMap<String, GuardReference>,
    pub functions: HashMap<String, GuardFunction>,
    /// Where the reference directory lives (for lazy topic parsing).
    pub reference_file_uri: Option<String>,
    /// Where the knowledge was loaded from (for source rendering).
    pub guard_file_uri: Option<String>,
    /// Full text of lib/guard.lisp as loaded (for span→text rendering).
    pub guard_file_text: Option<String>,
    reference_path: PathBuf,
    reference_loaded: bool,
}

impl GuardKnowledge {
    /// Cheap snapshot used at `initialize`: only `lib/guard.lisp` is read
    /// and parsed. Missing files produce an empty snapshot — this is
    /// graceful, not a failure (a workspace that is not the sens repo
    /// simply gets no guard knowledge).
    pub fn load_functions(root: &Path) -> Self {
        let reference_path = root.join("knowledge/guard-reference.lisp");
        let guard_path = root.join("lib/guard.lisp");

        let guard_text = std::fs::read_to_string(&guard_path).unwrap_or_default();
        let functions = parse_functions(&guard_text);
        let reference_file_uri = Some(crate::workspace::path_to_uri(&reference_path));
        let guard_file_uri = if guard_path.exists() {
            Some(crate::workspace::path_to_uri(&guard_path))
        } else {
            None
        };
        let guard_file_text = if guard_path.exists() {
            Some(guard_text)
        } else {
            None
        };

        GuardKnowledge {
            topics: HashMap::new(),
            functions,
            reference_file_uri,
            guard_file_uri,
            guard_file_text,
            reference_path,
            reference_loaded: false,
        }
    }

    /// Full snapshot: functions plus the reference directory. Used for
    /// explicit evidence/CLI paths; the LSP uses `load_functions` +
    /// `ensure_topics` instead so the slow parse is deferred.
    pub fn load(root: &Path) -> Self {
        let mut knowledge = Self::load_functions(root);
        knowledge.ensure_topics();
        knowledge
    }

    /// Parse the reference directory on first need (a hover over a guard
    /// topic). Idempotent; the parse is cached for the session duration.
    pub fn ensure_topics(&mut self) {
        if self.reference_loaded {
            return;
        }
        self.reference_loaded = true;
        let text = std::fs::read_to_string(&self.reference_path).unwrap_or_default();
        self.topics = parse_topics(&text);
    }

    /// The canonical source text of a guard function's defining form, if
    /// the snapshot holds lib/guard.lisp.
    pub fn source_of(&self, function: &GuardFunction) -> Option<String> {
        let text = self.guard_file_text.as_ref()?;
        Some(crate::analysis::span_text(text, function.form_span).to_string())
    }

    /// Extra callables for arity diagnostics: guard functions behave like
    /// runtime builtins for the shadow rule — a local `def` of the same
    /// name suppresses the diagnostic, quoted data stays data.
    pub fn arity_items(&self) -> Vec<(String, LanguageItemKind, Arity)> {
        self.functions
            .values()
            .map(|function| {
                (
                    function.name.clone(),
                    LanguageItemKind::Builtin,
                    Arity::Exact(function.arity),
                )
            })
            .collect()
    }

    /// Reference entry for a topic name, if present.
    pub fn topic(&self, name: &str) -> Option<&GuardReference> {
        self.topics.get(name)
    }

    /// Function definition for a name, if present.
    pub fn function(&self, name: &str) -> Option<&GuardFunction> {
        self.functions.get(name)
    }
}

// ---------------------------------------------------------------------------
// Extraction. Everything below walks the canonical parse tree; the field
// extractor is a tiny generic (field -> value) reader over `(field v ...)`.
// ---------------------------------------------------------------------------

fn as_symbol(expr: &Expr) -> Option<&str> {
    match &expr.kind {
        ExprKind::Symbol(name) => Some(name.as_ref()),
        ExprKind::String(name) => Some(name.as_ref()),
        _ => None,
    }
}

fn is_d3_quote_identity(identity: sens::CoreDomainIdentity) -> bool {
    matches!(
        identity,
        sens::CoreDomainIdentity::D3(word) if word.word().packed_bits() == 0b001
    )
}

fn is_d4_define_identity(identity: sens::CoreDomainIdentity) -> bool {
    matches!(
        identity,
        sens::CoreDomainIdentity::D4(word) if word.word().packed_bits() == 0b0011
    )
}

fn is_quote_head(expr: &Expr) -> bool {
    match &expr.kind {
        ExprKind::DomainIdentity(identity) => is_d3_quote_identity(*identity),
        ExprKind::Sid(code) => *code == sens::sens!(00000001),
        ExprKind::Symbol(surface) => {
            sens::semantic_registry_export::domain_identity_for_admitted_surface(surface)
                .is_some_and(is_d3_quote_identity)
        }
        _ => false,
    }
}

/// Canonical DEFINE is Core.D4:0011. Historical exact-eight DEFINE/DEF tokens
/// remain accepted only as explicit compatibility input.
fn is_define_head(expr: &Expr) -> bool {
    match &expr.kind {
        ExprKind::DomainIdentity(identity) => is_d4_define_identity(*identity),
        ExprKind::Sid(code) => {
            *code == sens::sens!(00001001) || *code == sens::sens!(00001011)
        }
        _ => as_symbol(expr).is_some_and(sens::is_define_surface_name),
    }
}

fn as_list(expr: &Expr) -> Option<&[Expr]> {
    match &expr.kind {
        ExprKind::List(items) => Some(items),
        _ => None,
    }
}

/// Read `(field value...)` pairs from a list of expressions.
fn read_fields<'a>(
    items: &'a [Expr],
) -> impl Iterator<Item = (&'a str, Vec<&'a Expr>)> + 'a {
    items.iter().filter_map(|item| {
        let list = as_list(item)?;
        let field = as_symbol(list.first()?)?;
        Some((field, list[1..].iter().collect()))
    })
}

/// Parse knowledge/guard-reference.lisp into topic entries.
///
/// Structure: `(00001001 *guard-reference-directory* (00000001 ((reference ...) ...)))`
/// (surface names `def`/`quote` are accepted too).
/// where each `(reference ...)` is a series of `(field value)` pairs.
fn parse_topics(source: &str) -> HashMap<String, GuardReference> {
    let mut out = HashMap::new();
    let Ok(expressions) = sens::parse(source) else {
        return out;
    };
    for expression in &expressions {
        let list = match as_list(expression) {
            Some(list) => list,
            None => continue,
        };
        if !is_define_head(&list[0]) {
            continue;
        }
        if as_symbol(&list[1]) != Some("*guard-reference-directory*") {
            continue;
        }
        let Some(value) = list.get(2) else { continue };
        // value = (quote ((reference ...) ...))
        let Some(value_list) = as_list(value) else {
            continue;
        };
        if !is_quote_head(&value_list[0]) {
            continue;
        }
        let Some(data) = value_list.get(1).and_then(as_list) else {
            continue;
        };
        for entry in data {
            let Some(fields) = as_list(entry) else { continue };
            if fields.first().and_then(as_symbol) != Some("reference") {
                continue;
            }
            let mut reference = GuardReference::default_filled();
            for (field, values) in read_fields(&fields[1..]) {
                match field {
                    "topic" => {
                        if let Some(v) = values.first().copied().and_then(as_symbol) {
                            reference.topic = v.to_string();
                        }
                    }
                    "summary" => {
                        if let Some(v) = values.first().copied().and_then(as_symbol) {
                            reference.summary = v.to_string();
                        }
                    }
                    "authority" | "how-to" | "verify" => {
                        let collected: Vec<String> = values
                            .iter()
                            .flat_map(|v| as_list(v).unwrap_or(&[]).iter())
                            .filter_map(as_symbol)
                            .map(str::to_string)
                            .collect();
                        match field {
                            "authority" => reference.authority = collected,
                            "how-to" => reference.how_to = collected,
                            _ => reference.verify = collected,
                        }
                    }
                    "lifecycle" => {
                        if let Some(v) = values.first().copied().and_then(as_symbol) {
                            reference.lifecycle = v.to_string();
                        }
                    }
                    "provenance" => {
                        if let Some(v) = values.first().copied().and_then(as_symbol) {
                            reference.provenance = v.to_string();
                        }
                    }
                    "unknown-route" => {
                        if let Some(v) = values.first().copied().and_then(as_symbol) {
                            reference.unknown_route = v.to_string();
                        }
                    }
                    _ => {}
                }
            }
            if reference.topic.is_empty() {
                continue;
            }
            out.insert(reference.topic.clone(), reference);
        }
    }
    out
}

impl GuardReference {
    fn default_filled() -> Self {
        GuardReference {
            topic: String::new(),
            summary: String::new(),
            authority: Vec::new(),
            how_to: Vec::new(),
            verify: Vec::new(),
            lifecycle: String::new(),
            provenance: String::new(),
            unknown_route: String::new(),
        }
    }
}

/// Parse lib/guard.lisp into function definitions with lambda arities.
///
/// A top-level `(def name (lambda (params) body ...))` contributes name →
/// (name_span, form_span, arity = params.len()). Non-lambda defs (data) and
/// macro definitions are skipped — this module only models callable guard
/// functions, which is exactly what arity diagnostics and hover need.
fn parse_functions(source: &str) -> HashMap<String, GuardFunction> {
    let mut out = HashMap::new();
    let Ok(expressions) = sens::parse(source) else {
        return out;
    };
    for expression in &expressions {
        let head = match &expression.kind {
            ExprKind::List(items) => items,
            _ => continue,
        };
        if !is_define_head(&head[0]) {
            continue;
        }
        let ExprKind::Symbol(name) = &head[1].kind else {
            continue;
        };
        let Some(lambda) = head.get(2).and_then(as_list) else {
            continue;
        };
        if !(head_is_sid(&lambda[0], sens::sens!(00001000))
            || as_symbol(&lambda[0]).is_some_and(sens::is_lambda_surface_name))
        {
            continue;
        }
        let Some(params) = lambda.get(1).and_then(as_list) else {
            continue;
        };
        out.insert(
            name.to_string(),
            GuardFunction {
                name: name.to_string(),
                name_span: head[1].span,
                form_span: expression.span,
                arity: params.len(),
            },
        );
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    const SAMPLE_REFERENCE: &str = r#"(def *guard-reference-directory*
  (quote
    ((reference
       (topic language-semantics)
       (summary "Meaning of WSM programs")
       (authority (language-contract.lisp docs/language-core-axioms.md))
       (how-to (read-contract run-conformance-fixtures))
       (verify (cargo-test-workspace evidence/README.md))
       (lifecycle current-contract)
       (provenance sens commit abc123)
       (unknown-route ask-agent))
     (reference
       (topic second-topic)
       (summary "Another")
       (authority (file.md))
       (how-to (step))
       (verify (check))
       (lifecycle current-design)
       (provenance repo commit def456)
       (unknown-route research-web)))))"#;

    #[test]
    fn parses_reference_topics() {
        let topics = parse_topics(SAMPLE_REFERENCE);
        assert_eq!(topics.len(), 2);
        let semantics = &topics["language-semantics"];
        assert_eq!(semantics.summary, "Meaning of WSM programs");
        assert_eq!(
            semantics.authority,
            vec!["language-contract.lisp", "docs/language-core-axioms.md"]
        );
        assert_eq!(semantics.how_to, vec!["read-contract", "run-conformance-fixtures"]);
        assert_eq!(
            semantics.verify,
            vec!["cargo-test-workspace", "evidence/README.md"]
        );
        assert_eq!(semantics.lifecycle, "current-contract");
        assert_eq!(semantics.unknown_route, "ask-agent");
    }

    #[test]
    fn ignores_entries_without_topic() {
        let broken = SAMPLE_REFERENCE.replace(
            "(topic language-semantics)",
            "(topic )",
        );
        let topics = parse_topics(&broken);
        assert_eq!(topics.len(), 1);
        assert!(topics.contains_key("second-topic"));
    }

    #[test]
    fn unbalanced_file_gives_empty_not_panic() {
        let topics = parse_topics("(def x 1))");
        assert!(topics.is_empty());
    }

    #[test]
    fn parses_lambda_arities() {
        let source = "(def guard-unknown (lambda (subject missing-evidence guidance) x))\n(def make-guard-finding (lambda (a b c d e f g h i) x))\n(def data-thing (quote (1 2)))\n";
        let functions = parse_functions(source);
        assert_eq!(functions.len(), 2);
        assert_eq!(functions["guard-unknown"].arity, 3);
        assert_eq!(functions["make-guard-finding"].arity, 9);
        // data def (no lambda) must not become a callable
        assert!(!functions.contains_key("data-thing"));
    }

    #[test]
    fn load_functions_from_real_repo_sees_live_guard_functions() {
        // Real evidence: the actual repo's lib/guard.lisp must yield the
        // guard functions. This is the cheap half (milliseconds).
        let root = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("..").join("..");
        let knowledge = GuardKnowledge::load_functions(&root);
        assert!(
            knowledge.functions.contains_key("guard-unknown"),
            "guard-unknown function missing"
        );
        assert!(
            knowledge.functions.contains_key("make-guard-finding"),
            "make-guard-finding function missing"
        );
        assert!(knowledge.source_of(&knowledge.functions["guard-unknown"]).is_some());
    }

    #[test]
    #[ignore = "parses knowledge/guard-reference.lisp (~47KB): ~3.4s in release, ~65s in debug. Run explicitly for live evidence."]
    fn live_reference_topics_parse() {
        // The guard topic and the swarm-coordination topic must be present
        // in the live canonical directory. Slower than a normal unit test,
        // so it stays explicit rather than slowing every `cargo test`.
        let root = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("..").join("..");
        let knowledge = GuardKnowledge::load(&root);
        assert!(knowledge.topics.contains_key("guard"), "guard topic missing");
        assert!(
            knowledge.topics.contains_key("swarm-coordination"),
            "swarm-coordination topic missing"
        );
    }

    #[test]
    fn load_functions_is_cheap_for_non_sens_root() {
        // A root without lib/guard.lisp yields an empty snapshot quickly —
        // the LSP must behave exactly as before for other workspaces.
        let root = std::env::temp_dir();
        let knowledge = GuardKnowledge::load_functions(&root);
        assert!(knowledge.functions.is_empty());
        assert!(knowledge.topics.is_empty());
    }
}