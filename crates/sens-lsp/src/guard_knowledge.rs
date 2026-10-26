//! guard_knowledge.rs — Guard explanation/guidance/evidence for the IDE,
//! sourced from the canonical WSM files themselves, never duplicated in
//! Rust strings.
//!
//! Guard knowledge lives in two authoritative files under the workspace
//! root: `knowledge/guard-reference.lisp` (the reference bureau: each topic
//! points at authority, the canonical how-to and the verification evidence)
//! and `lib/guard.lisp` (the shared guard-finding functions). This module
//! reads both at runtime through the exact-domain mixed reader used for
//! admitted D3/D4 source heads, and walks the parsed AST. No string
//! copy of any summary/authority/how-to/verify text exists here — if the
//! WSM files change, what the IDE shows follows, because the IDE serves the
//! live parse.
//!
//! If either file is absent (a workspace that is not the sens repo), the
//! knowledge is simply empty and the LSP behaves exactly as before: no
//! guard hover, no guard arity diagnostics.

use sens::{Arity, Expr, ExprKind, LanguageItemKind, Span};
use std::collections::HashMap;
use std::path::Path;
use std::path::PathBuf;

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

const D3_QUOTE: (usize, u16) = (3, 0b001);
const D4_LAMBDA: (usize, u16) = (4, 0b0010);
const D4_DEFINE: (usize, u16) = (4, 0b0011);

/// Tooling projection from an admitted human surface to its already-known
/// domain identity. This consumes `LanguageItem.domain_identity`; it never
/// reconstructs a domain from the legacy registry byte.
fn surface_domain_coordinate(surface: &str) -> Option<(usize, u16)> {
    sens::language_items()
        .into_iter()
        .find(|item| item.name == surface)
        .and_then(|item| item.domain_identity)
        .map(|identity| (identity.width(), identity.packed_bits()))
}

/// Доменний заголовок визначається шириною та точними бітами.
///
/// Вісім бітів історичного Sens8 не можуть підтверджувати закон D3/D4.
/// Дозволені людські написання лише проєктують уже відому координату.
fn head_has_exact_domain(expr: &Expr, domain: (usize, u16)) -> bool {
    match &expr.kind {
        ExprKind::DomainIdentity(identity) => (identity.width(), identity.packed_bits()) == domain,
        ExprKind::Symbol(surface) => surface_domain_coordinate(surface) == Some(domain),
        _ => false,
    }
}

fn is_quote_head(expr: &Expr) -> bool {
    head_has_exact_domain(expr, D3_QUOTE)
}

fn is_define_head(expr: &Expr) -> bool {
    head_has_exact_domain(expr, D4_DEFINE)
        || as_symbol(expr).is_some_and(sens::is_define_surface_name)
}

fn is_lambda_head(expr: &Expr) -> bool {
    head_has_exact_domain(expr, D4_LAMBDA)
        || as_symbol(expr).is_some_and(sens::is_lambda_surface_name)
}

fn as_list(expr: &Expr) -> Option<&[Expr]> {
    match &expr.kind {
        ExprKind::List(items) => Some(items),
        _ => None,
    }
}

/// Read `(field value...)` pairs from a list of expressions.
fn read_fields<'a>(items: &'a [Expr]) -> impl Iterator<Item = (&'a str, Vec<&'a Expr>)> + 'a {
    items.iter().filter_map(|item| {
        let list = as_list(item)?;
        let field = as_symbol(list.first()?)?;
        Some((field, list[1..].iter().collect()))
    })
}

/// Parse knowledge/guard-reference.lisp into topic entries.
///
/// Канонічні заголовки D3/D4 та допущені проєкції. Історичні W8
/// байти не можуть виступати доказом D3/D4-семантики.
/// where each `(reference ...)` is a series of `(field value)` pairs.
fn parse_topics(source: &str) -> HashMap<String, GuardReference> {
    let mut out = HashMap::new();
    let Ok(expressions) = sens::parse_mixed_exact_domain(source) else {
        return out;
    };
    for expression in &expressions {
        let list = match as_list(expression) {
            Some(list) => list,
            None => continue,
        };
        if !list.first().is_some_and(is_define_head) {
            continue;
        }
        if list.get(1).and_then(as_symbol) != Some("*guard-reference-directory*") {
            continue;
        }
        let Some(value) = list.get(2) else { continue };
        // value = (quote ((reference ...) ...))
        let Some(value_list) = as_list(value) else {
            continue;
        };
        if !value_list.first().is_some_and(is_quote_head) {
            continue;
        }
        let Some(data) = value_list.get(1).and_then(as_list) else {
            continue;
        };
        for entry in data {
            let Some(fields) = as_list(entry) else {
                continue;
            };
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
    let Ok(expressions) = sens::parse_mixed_exact_domain(source) else {
        return out;
    };
    for expression in &expressions {
        let head = match &expression.kind {
            ExprKind::List(items) => items,
            _ => continue,
        };
        if !head.first().is_some_and(is_define_head) {
            continue;
        }
        let Some(Expr {
            kind: ExprKind::Symbol(name),
            ..
        }) = head.get(1)
        else {
            continue;
        };
        let Some(lambda) = head.get(2).and_then(as_list) else {
            continue;
        };
        if !lambda.first().is_some_and(is_lambda_head) {
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

    const SAMPLE_REFERENCE: &str = r#"(0011 *guard-reference-directory*
  (001
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
    fn exact_guard_reference_quote_keeps_d3_identity_distinct_from_w8() {
        // Позитивний свідок: D4 DEFINE містить D3 QUOTE і лише дані.
        let exact = "(0011 *guard-reference-directory* (001 ((reference (topic точний-домен) (summary \"дані\")))))";
        let topics = parse_topics(exact);
        assert!(
            topics.contains_key("точний-домен"),
            "D3:001 має зберегти цитований довідник"
        );

        // Негативний свідок: рівний payload W8 не є D3 QUOTE.
        let legacy = exact.replacen("(001 ((", "(00000001 ((", 1);
        assert!(
            parse_topics(&legacy).is_empty(),
            "W8:00000001 не може підміняти D3:001"
        );

        let exact_define = "(0011 точна-функція (0010 (x) x))";
        let functions = parse_functions(exact_define);
        assert_eq!(functions.get("точна-функція").map(|f| f.arity), Some(1));

        // Так само D4:0011/0010 не тотожні W8:00000011/00000010.
        let wrong_width_define = "(00000011 точна-функція (00000010 (x) x))";
        assert!(
            parse_functions(wrong_width_define).is_empty(),
            "ширина D4 є частиною ідентичності"
        );
    }

    #[test]
    fn live_guard_getter_quotes_keep_exact_d3_and_reject_w8_alias() {
        // Лише структурна перевірка джерела; семантичну істину визначає SENS.
        let source = include_str!("../../../knowledge/guard-reference.lisp");
        for (getter, field) in [
            ("guard-explain", "summary"),
            ("guard-how-to", "how-to"),
            ("guard-authority", "authority"),
            ("guard-verify", "verify"),
        ] {
            let marker = format!("(0011 {getter}\n");
            let start = source.find(&marker).expect("missing admitted D4 getter");
            let form = source[start..].split("\n\n").next().unwrap();
            let head_bits = |code: &str| {
                let tree = sens::parse_mixed_exact_domain(code).expect("exact D3/D4 source");
                let ExprKind::List(definition) = &tree[0].kind else {
                    panic!("DEFINE list")
                };
                let ExprKind::List(lambda) = &definition[2].kind else {
                    panic!("LAMBDA list")
                };
                let ExprKind::List(call) = &lambda[2].kind else {
                    panic!("field call")
                };
                let ExprKind::List(quoted) = &call[1].kind else {
                    panic!("QUOTE list")
                };
                assert!(
                    matches!(&quoted[1].kind, ExprKind::Symbol(name) if name.as_ref() == field),
                    "{getter} changed its literal field name"
                );
                matches!(&quoted[0].kind, ExprKind::DomainIdentity(id)
                    if id.width() == 3 && id.packed_bits() == 0b001)
            };
            assert!(head_bits(form), "{getter}: D3:001 QUOTE required");
            let mutant =
                form.replacen(&format!("(001 {field})"), &format!("(00000001 {field})"), 1);
            assert_ne!(mutant, form, "{getter}: missing mutation site");
            assert!(!head_bits(&mutant), "{getter}: W8 cannot alias D3:001");
        }
    }

    #[test]
    fn guard_evidence_status_uses_exact_d3_data_without_w8_alias() {
        // Структурний тест reader, а не другий Rust-оракул семантики.
        // Історичні W8-контейнери лишаються відокремленими від D3.
        let whole = include_str!("../../../knowledge/guard-reference.lisp");
        let start = whole
            .find("(0011 guard-reference-evidence-status\n")
            .expect("guard-reference-evidence-status missing");
        let rest = &whole[start..];
        let end = rest
            .find("\n(0011 guard-evidence-status-strength")
            .expect("next exact D4 function missing");
        let section = &rest[..end];

        fn count_d3_quote(section: &str) -> usize {
            fn visit(node: &Expr) -> usize {
                let ExprKind::List(items) = &node.kind else {
                    return 0;
                };
                let this = usize::from(matches!(
                    items.first(),
                    Some(Expr { kind: ExprKind::DomainIdentity(id), .. })
                        if id.width() == 3 && id.packed_bits() == 0b001
                ));
                this + items.iter().map(visit).sum::<usize>()
            }
            sens::parse_mixed_exact_domain_guard_reference_source(
                "knowledge/guard-reference.lisp",
                section,
            )
            .expect("Guard source must parse by its pinned exact-domain reader")
            .iter()
            .map(visit)
            .sum()
        }

        assert_eq!(count_d3_quote(section), 2, "D3:001 field and fallback");
        for field in ["evidence-status", "unresolved"] {
            let from = format!("(001 {field})");
            assert_eq!(
                section.matches(&from).count(),
                1,
                "unique source site: {field}"
            );
            let wrong_width = section.replacen(&from, &format!("(00000001 {field})"), 1);
            assert_eq!(
                count_d3_quote(&wrong_width),
                1,
                "{field}: W8 QUOTE must not acquire D3 identity"
            );
        }
    }

    #[test]
    fn guard_topics_preserves_three_exact_d3_quotes_and_rejects_w8_mutants() {
        // Це перевірка AST-ширини носієм Rust. Семантичний оракул — тільки SENS.
        let full = include_str!("../../../knowledge/guard-reference.lisp");
        let start = full
            .find("(0011 guard-topics\n")
            .expect("missing D4:0011 guard-topics definition");
        let rest = &full[start..];
        let end = rest
            .find("\n; One canonical entry point for a cold agent:")
            .expect("missing end of guard-topics section");
        let form = rest[..end].trim();

        fn d3_quotes(code: &str) -> usize {
            fn visit(expr: &Expr) -> usize {
                match &expr.kind {
                    ExprKind::List(items) => {
                        usize::from(matches!(
                            items.first(),
                            Some(Expr { kind: ExprKind::DomainIdentity(id), .. })
                                if id.width() == 3 && id.packed_bits() == 0b001
                        )) + items.iter().map(visit).sum::<usize>()
                    }
                    _ => 0,
                }
            }
            sens::parse_mixed_exact_domain_guard_reference_source(
                "knowledge/guard-reference.lisp",
                code,
            )
            .expect("guard-topics exact-domain parse")
            .iter()
            .map(visit)
            .sum()
        }

        assert_eq!(
            form.matches("(001 ())").count(),
            2,
            "two explicit nil quotations"
        );
        assert_eq!(
            form.matches("(001 topic)").count(),
            1,
            "one field-name quotation"
        );
        assert_eq!(d3_quotes(form), 3, "all three quotes must retain D3 width");

        let mut mutant_count = 0;
        for (exact, legacy) in [
            ("(001 ())", "(00000001 ())"),
            ("(001 topic)", "(00000001 topic)"),
        ] {
            for (at, _) in form.match_indices(exact) {
                let mut mutant = form.to_owned();
                mutant.replace_range(at..at + exact.len(), legacy);
                assert_eq!(
                    d3_quotes(&mutant),
                    2,
                    "W8 != D3 for {exact}, byte offset {at}"
                );
                mutant_count += 1;
            }
        }
        assert_eq!(
            mutant_count, 3,
            "both nil sites and field-name site checked"
        );
    }

    #[test]
    fn guard_script_ten_data_quotes_keep_d3_identity_against_w8_mutants() {
        // AST-only witness: semantic decisions still belong to native SENS.
        let full = include_str!("../../../knowledge/guard-reference.lisp");
        let start = full
            .find("(0011 guard-script\n")
            .expect("missing exact Guard script definition");
        let rest = &full[start..];
        let end = rest
            .find("\n(0011 guard-scripts")
            .expect("missing next Guard definition");
        let form = rest[..end].trim();

        fn exact_quote_heads(form: &str) -> usize {
            fn visit(expr: &Expr) -> usize {
                match &expr.kind {
                    ExprKind::List(items) => {
                        usize::from(matches!(
                            items.first(),
                            Some(Expr { kind: ExprKind::DomainIdentity(id), .. })
                                if id.width() == 3 && id.packed_bits() == 0b001
                        )) + items.iter().map(visit).sum::<usize>()
                    }
                    _ => 0,
                }
            }
            sens::parse_mixed_exact_domain_guard_reference_source(
                "knowledge/guard-reference.lisp",
                form,
            )
            .expect("pinned Guard source reader")
            .iter()
            .map(visit)
            .sum()
        }

        let expected = [
            ("tool-missing", 2_usize),
            ("name", 2),
            ("decision", 2),
            ("unknown", 2),
            ("unknown-routes", 2),
        ];
        assert_eq!(exact_quote_heads(form), 10, "ten exact D3:001 data quotes");
        let mut mutations = 0;
        for (symbol, multiplicity) in expected {
            let from = format!("(001 {symbol})");
            let to = format!("(00000001 {symbol})");
            let sites: Vec<_> = form.match_indices(&from).map(|(index, _)| index).collect();
            assert_eq!(sites.len(), multiplicity, "quoted field changed: {symbol}");
            for site in sites {
                let mut mutant = form.to_owned();
                mutant.replace_range(site..site + from.len(), &to);
                assert_eq!(
                    exact_quote_heads(&mutant),
                    9,
                    "W8 must not alias D3:001 at {symbol}, offset {site}"
                );
                mutations += 1;
            }
        }
        assert_eq!(mutations, 10, "all ten single-width mutations exercised");
    }

    #[test]
    fn guard_reference_missing_evidence_has_22_exact_d3_quote_heads_not_w8() {
        // Structural width protection only. Native SENS is the semantic authority.
        let full = include_str!("../../../knowledge/guard-reference.lisp");
        let start = full
            .find("(0011 guard-reference\n")
            .expect("guard-reference D4 definition missing");
        let rest = &full[start..];
        let end = rest
            .find("\n(0011 guard-explain")
            .expect("guard-reference delimiter missing");
        let form = rest[..end].trim();

        fn exact_quote_count(code: &str) -> usize {
            fn visit(expr: &Expr) -> usize {
                match &expr.kind {
                    ExprKind::List(items) => {
                        usize::from(matches!(
                            items.first(),
                            Some(Expr { kind: ExprKind::DomainIdentity(id), .. })
                                if id.width() == 3 && id.packed_bits() == 0b001
                        )) + items.iter().map(visit).sum::<usize>()
                    }
                    _ => 0,
                }
            }
            sens::parse_mixed_exact_domain_guard_reference_source(
                "knowledge/guard-reference.lisp",
                code,
            )
            .expect("canonical pinned Guard reader")
            .iter()
            .map(visit)
            .sum()
        }

        assert_eq!(
            exact_quote_count(form),
            22,
            "eleven field/value atoms in two branches"
        );

        let quoted_symbols = [
            "reference-missing",
            "schema",
            "guard-reference-1",
            "topic",
            "decision",
            "unknown",
            "evidence-status",
            "unresolved",
            "guidance",
            "choose-unknown-route",
            "unknown-routes",
        ];
        let mut mutants = 0;
        for symbol in quoted_symbols {
            let correct = format!("(001 {symbol})");
            let historical = format!("(00000001 {symbol})");
            let sites: Vec<_> = form.match_indices(&correct).map(|(at, _)| at).collect();
            assert_eq!(sites.len(), 2, "expected two quoted records for {symbol}");
            for at in sites {
                let mut mutant = form.to_owned();
                mutant.replace_range(at..at + correct.len(), &historical);
                assert_eq!(
                    exact_quote_count(&mutant),
                    21,
                    "W8:00000001 must never alias D3:001 at {symbol}, byte {at}"
                );
                mutants += 1;
            }
        }
        assert_eq!(
            mutants, 22,
            "all 22 single-site width mutants were exercised"
        );
    }

    #[test]
    fn guard_ask_preserves_all_48_d3_quote_heads_against_w8_mutants() {
        // Rust checks exact width in AST; SENS alone defines the semantics.
        let full = include_str!("../../../knowledge/guard-reference.lisp");
        let at = full.find("(0011 guard-ask\n").expect("guard-ask missing");
        let form = full[at..].trim();

        fn exact_quote_count(source: &str) -> usize {
            fn visit(expr: &Expr) -> usize {
                match &expr.kind {
                    ExprKind::List(items) => {
                        usize::from(matches!(
                            items.first(),
                            Some(Expr { kind: ExprKind::DomainIdentity(id), .. })
                                if id.width() == 3 && id.packed_bits() == 0b001
                        )) + items.iter().map(visit).sum::<usize>()
                    }
                    _ => 0,
                }
            }
            sens::parse_mixed_exact_domain_guard_reference_source(
                "knowledge/guard-reference.lisp",
                source,
            )
            .expect("pinned Guard exact-domain reader")
            .iter()
            .map(visit)
            .sum()
        }

        let quote_sites: Vec<_> = form.match_indices("(001 ").map(|(at, _)| at).collect();
        assert_eq!(quote_sites.len(), 48, "guard-ask D3 quote sites");
        assert_eq!(
            exact_quote_count(form),
            48,
            "all 48 exact D3:001 identities"
        );
        let mut seen = std::collections::BTreeMap::new();
        for at in quote_sites {
            // Each quoted value here is a bare atom, never a nested form.
            let after_head = at + "(001 ".len();
            let atom_end = form[after_head..]
                .find(')')
                .expect("quoted atom terminator")
                + after_head;
            let atom = &form[after_head..atom_end];
            assert!(!atom.is_empty(), "quoted atom must be non-empty");
            assert!(!atom.contains('('), "quoted datum is a bare atom: {atom}");
            *seen.entry(atom.to_owned()).or_insert(0usize) += 1;
            let mut mutant = form.to_owned();
            mutant.replace_range(at..after_head, "(00000001 ");
            assert_eq!(
                exact_quote_count(&mutant),
                47,
                "W8 QUOTE must remain distinct from D3 at {atom}, offset {at}"
            );
        }
        for atom in [
            "not-found",
            "query",
            "decision",
            "unknown",
            "unknown-routes",
            "result",
            "type",
            "reference-topic",
            "source",
            "entry",
            "knowledge/guard-reference.lisp",
            "tool",
            "guard-script-directory",
            "ambiguous",
        ] {
            assert!(
                seen.contains_key(atom),
                "missing Guard response field: {atom}"
            );
        }
        assert_eq!(
            seen.values().sum::<usize>(),
            48,
            "all data symbols accounted for"
        );
    }

    #[test]
    fn guard_topics_exact_d3_list_ops_reject_three_independent_w8_mutants() {
        // Exact-domain AST transport check. Native SENS, not Rust, owns semantics.
        let full = include_str!("../../../knowledge/guard-reference.lisp");
        let start = full
            .find("(0011 guard-topics\n")
            .expect("D4 guard-topics definition missing");
        let rest = &full[start..];
        let end = rest
            .find("\n; One canonical entry point for a cold agent:")
            .expect("guard-topics section terminator missing");
        let form = rest[..end].trim();

        fn exact_list_ops(code: &str) -> [usize; 3] {
            fn visit(expr: &Expr, tally: &mut [usize; 3]) {
                if let ExprKind::List(items) = &expr.kind {
                    if let Some(Expr {
                        kind: ExprKind::DomainIdentity(id),
                        ..
                    }) = items.first()
                    {
                        if id.width() == 3 {
                            let expected = match id.packed_bits() {
                                0b111 => Some((0, 3)), // CONS plus two operands
                                0b100 => Some((1, 2)), // CAR plus one operand
                                0b011 => Some((2, 2)), // CDR plus one operand
                                _ => None,
                            };
                            if let Some((index, arity)) = expected {
                                assert_eq!(items.len(), arity, "D3 list-op arity differs");
                                tally[index] += 1;
                            }
                        }
                    }
                    for child in items.iter() {
                        visit(child, tally);
                    }
                }
            }
            let trees = sens::parse_mixed_exact_domain_guard_reference_source(
                "knowledge/guard-reference.lisp",
                code,
            )
            .expect("pinned Guard exact-domain reader");
            let mut tally = [0; 3];
            for expr in &trees {
                visit(expr, &mut tally);
            }
            tally
        }

        assert_eq!(exact_list_ops(form), [1, 1, 1], "one D3 CONS, CAR, CDR");
        let mutations = [
            ("(111\n", "(00000100\n", [0, 1, 1]),
            ("(100 references)", "(00000101 references)", [1, 0, 1]),
            ("(011 references)", "(00000110 references)", [1, 1, 0]),
        ];
        for (exact, historical, expected) in mutations {
            assert_eq!(form.matches(exact).count(), 1, "unique head {exact}");
            let mutant = form.replacen(exact, historical, 1);
            assert_eq!(
                exact_list_ops(&mutant),
                expected,
                "eight source bits cannot impersonate exact D3 {exact}"
            );
        }
    }

    #[test]
    fn guard_reference_stronger_definition_has_exact_d4_width_not_w8() {
        // Mechanical AST proof only; SENS owns the actual definition law.
        let full = include_str!("../../../knowledge/guard-reference.lisp");
        let begin = full
            .find("(0011 guard-reference-stronger\n")
            .expect("exact D4 stronger definition missing");
        let rest = &full[begin..];
        let end = rest
            .find("\n(0011 guard-reference-all")
            .expect("following D4 function missing");
        let form = rest[..end].trim();

        fn definition_head_is_d4(code: &str) -> bool {
            let parsed = sens::parse_mixed_exact_domain_guard_reference_source(
                "knowledge/guard-reference.lisp",
                code,
            )
            .expect("pinned Guard exact-domain reader");
            assert_eq!(parsed.len(), 1, "one definition");
            let ExprKind::List(def) = &parsed[0].kind else {
                panic!("definition list expected");
            };
            assert_eq!(def.len(), 3, "DEFINE target and one value expression");
            assert!(matches!(&def[1].kind, ExprKind::Symbol(name)
                if name.as_ref() == "guard-reference-stronger"));
            let ExprKind::List(lambda) = &def[2].kind else {
                panic!("value must remain a lambda form");
            };
            assert!(
                matches!(lambda.first(),
                    Some(Expr { kind: ExprKind::DomainIdentity(id), .. })
                        if id.width() == 4 && id.packed_bits() == 0b0010
                ),
                "lambda retains exact D4:0010 identity"
            );
            matches!(def.first(),
                Some(Expr { kind: ExprKind::DomainIdentity(id), .. })
                    if id.width() == 4 && id.packed_bits() == 0b0011
            )
        }

        assert!(
            definition_head_is_d4(form),
            "ratified exact D4:0011 required"
        );
        let mutant = form.replacen(
            "(0011 guard-reference-stronger",
            "(00001011 guard-reference-stronger",
            1,
        );
        assert_ne!(mutant, form, "mutation must change exactly one head");
        assert!(
            !definition_head_is_d4(&mutant),
            "historical W8 must never impersonate D4:0011"
        );
    }

    #[test]
    fn guard_last_two_define_heads_use_exact_d4_and_reject_w8_width() {
        // Structural readback, never a replacement for native SENS evaluation.
        let source = include_str!("../../../knowledge/guard-reference.lisp");
        let cases = [
            ("guard-script", "\n(0011 guard-scripts"),
            (
                "guard-reference-evidence-status",
                "\n(0011 guard-evidence-status-strength",
            ),
        ];

        fn has_exact_d4_define_and_lambda(code: &str, name: &str) -> bool {
            let trees = sens::parse_mixed_exact_domain_guard_reference_source(
                "knowledge/guard-reference.lisp",
                code,
            )
            .expect("pinned Guard reader must parse this source");
            assert_eq!(trees.len(), 1, "exactly one top-level definition: {name}");
            let ExprKind::List(def) = &trees[0].kind else {
                panic!("expected one definition form: {name}");
            };
            assert_eq!(def.len(), 3, "DEFINE target and value: {name}");
            assert!(
                matches!(&def[1].kind, ExprKind::Symbol(symbol)
                if symbol.as_ref() == name),
                "must not rename definition target"
            );
            let ExprKind::List(lambda) = &def[2].kind else {
                panic!("lambda body must be retained for {name}");
            };
            assert!(
                matches!(lambda.first(),
                    Some(Expr { kind: ExprKind::DomainIdentity(id), .. })
                        if id.width() == 4 && id.packed_bits() == 0b0010
                ),
                "D4:0010 lambda must remain exact for {name}"
            );
            matches!(def.first(),
                Some(Expr { kind: ExprKind::DomainIdentity(id), .. })
                    if id.width() == 4 && id.packed_bits() == 0b0011
            )
        }

        for (name, next_marker) in cases {
            let exact = format!("(0011 {name}\n");
            let historical = format!("(00001011 {name}\n");
            assert_eq!(source.matches(&exact).count(), 1, "{name} must be unique");
            assert!(
                !source.contains(&historical),
                "{name} must have no historical DEFINE"
            );
            let from = source
                .find(&exact)
                .expect("ratified Guard definition present");
            let next = source[from..]
                .find(next_marker)
                .expect("following Guard definition present")
                + from;
            let form = source[from..next].trim();
            assert!(has_exact_d4_define_and_lambda(form, name), "{name} uses D4");
            let mutant = form.replacen(&exact, &historical, 1);
            assert_ne!(mutant, form, "{name} one-head mutation applied");
            assert!(
                !has_exact_d4_define_and_lambda(&mutant, name),
                "historical W8 must never be admitted as D4:0011 for {name}"
            );
        }
    }

    #[test]
    fn all_sixteen_guard_definitions_are_exact_d4_and_reject_historical_w8() {
        // AST-width witness only: native binary SENS owns semantics.
        let source = include_str!("../../../knowledge/guard-reference.lisp");
        let names = [
            "guard-script-find",
            "guard-script",
            "guard-scripts",
            "guard-reference-evidence-status",
            "guard-evidence-status-strength",
            "guard-reference-stronger",
            "guard-reference-all",
            "guard-reference-find-strongest",
            "guard-reference-find",
            "guard-reference",
            "guard-explain",
            "guard-how-to",
            "guard-authority",
            "guard-verify",
            "guard-topics",
            "guard-ask",
        ];

        fn is_exact_d4_definition(source: &str, name: &str) -> bool {
            let parsed = sens::parse_mixed_exact_domain_guard_reference_source(
                "knowledge/guard-reference.lisp",
                source,
            )
            .expect("the pinned Guard reader must parse each function");
            assert_eq!(parsed.len(), 1, "single Guard definition: {name}");
            let ExprKind::List(def) = &parsed[0].kind else {
                panic!("definition must be a list: {name}");
            };
            assert_eq!(def.len(), 3, "DEFINE must have two operands: {name}");
            assert!(
                matches!(&def[1].kind, ExprKind::Symbol(symbol)
                if symbol.as_ref() == name),
                "definition name changed: {name}"
            );
            let ExprKind::List(lambda) = &def[2].kind else {
                panic!("LAMBDA missing from definition: {name}");
            };
            assert!(
                matches!(lambda.first(),
                    Some(Expr { kind: ExprKind::DomainIdentity(id), .. })
                        if id.width() == 4 && id.packed_bits() == 0b0010
                ),
                "exact D4:0010 LAMBDA required for {name}"
            );
            matches!(def.first(),
                Some(Expr { kind: ExprKind::DomainIdentity(id), .. })
                    if id.width() == 4 && id.packed_bits() == 0b0011
            )
        }

        let mut covered = 0;
        for (i, name) in names.iter().enumerate() {
            let exact = format!("(0011 {name}\n");
            let historical = format!("(00001011 {name}\n");
            assert_eq!(
                source.matches(&exact).count(),
                1,
                "one D4 definition: {name}"
            );
            assert!(
                !source.contains(&historical),
                "historical W8 DEFINE remains: {name}"
            );
            let begin = source.find(&exact).expect("existing Guard definition");
            let end = match names.get(i + 1) {
                Some(next_name) => {
                    let next = format!("(0011 {next_name}\n");
                    begin
                        + exact.len()
                        + source[begin + exact.len()..]
                            .find(&next)
                            .expect("next exact Guard definition")
                }
                None => source.len(),
            };
            let form = source[begin..end].trim();
            assert!(
                is_exact_d4_definition(form, name),
                "{name} must have D4 identity"
            );
            let mutant = form.replacen(&exact, &historical, 1);
            assert_ne!(mutant, form, "{name} width mutation changed source");
            assert!(
                !is_exact_d4_definition(&mutant, name),
                "historical W8 must not alias D4 DEFINE for {name}"
            );
            covered += 1;
        }
        assert_eq!(covered, 16, "all Guard entrypoints and W8 mutants covered");
    }

    #[test]
    fn admitted_surfaces_resolve_to_exact_domain_coordinates() {
        assert_eq!(surface_domain_coordinate("як-є"), Some(D3_QUOTE));
        assert_eq!(surface_domain_coordinate("функція"), Some(D4_LAMBDA));
        assert_eq!(surface_domain_coordinate("визначити"), Some(D4_DEFINE));
        assert_eq!(surface_domain_coordinate("+"), None);
    }

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
        assert_eq!(
            semantics.how_to,
            vec!["read-contract", "run-conformance-fixtures"]
        );
        assert_eq!(
            semantics.verify,
            vec!["cargo-test-workspace", "evidence/README.md"]
        );
        assert_eq!(semantics.lifecycle, "current-contract");
        assert_eq!(semantics.unknown_route, "ask-agent");
    }

    #[test]
    fn ignores_entries_without_topic() {
        let broken = SAMPLE_REFERENCE.replace("(topic language-semantics)", "(topic )");
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
            .join("..")
            .join("..");
        let knowledge = GuardKnowledge::load_functions(&root);
        assert!(
            knowledge.functions.contains_key("guard-unknown"),
            "guard-unknown function missing"
        );
        assert!(
            knowledge.functions.contains_key("make-guard-finding"),
            "make-guard-finding function missing"
        );
        assert!(knowledge
            .source_of(&knowledge.functions["guard-unknown"])
            .is_some());
    }

    #[test]
    #[ignore = "parses knowledge/guard-reference.lisp (~47KB): ~3.4s in release, ~65s in debug. Run explicitly for live evidence."]
    fn live_reference_topics_parse() {
        // The guard topic and the swarm-coordination topic must be present
        // in the live canonical directory. Slower than a normal unit test,
        // so it stays explicit rather than slowing every `cargo test`.
        let root = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("..")
            .join("..");
        let knowledge = GuardKnowledge::load(&root);
        assert!(
            knowledge.topics.contains_key("guard"),
            "guard topic missing"
        );
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
