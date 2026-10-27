//! analysis.rs — the language half of the adapter. Protocol-free by
//! design: everything here speaks in byte offsets, `Span`s and plain
//! structs, so no LSP shapes can leak into language reasoning and no
//! sens semantics can leak into protocol glue.
//!
//! Everything is derived from the canonical parser (`sens::parse`)
//! operating on the canonical source representation. There is no second
//! parser and no textual/grep-based definition detection: a definition
//! exists only where the parse tree structurally proves one — a top-level
//! `(def name ...)` or `(defmacro name ...)` list whose second element is
//! a symbol. Ordinary symbol text inside strings, comments or quoted data
//! is never classified as a definition because it never appears as a
//! top-level def-form in the AST.

use sens::{Arity, Expr, ExprKind, LanguageError, LanguageItemKind, Span};
use std::collections::{HashMap, HashSet};
use std::rc::Rc;

/// A definition the language can structurally prove.
#[derive(Clone, Debug)]
pub struct DefInfo {
    pub name: String,
    /// "def" or "defmacro" — exactly as written in the defining form.
    pub kind: String,
    /// Span of just the defined name (LSP selectionRange).
    pub name_span: Span,
    /// Span of the whole defining form (LSP range).
    pub form_span: Span,
}

/// One document's structural analysis, recomputed on every sync.
#[derive(Debug, Default)]
pub struct Analysis {
    pub defs: Vec<DefInfo>,
}

/// Parse with the canonical parser and collect what M0 needs.
/// A parse failure is returned untouched — inventing recovery here would
/// mean inventing semantics.
pub fn analyze(source: &str) -> Result<Analysis, LanguageError> {
    let expressions = sens::parse(source)?;
    Ok(Analysis {
        defs: collect_defs(&expressions),
    })
}

fn collect_defs(expressions: &[Expr]) -> Vec<DefInfo> {
    let mut defs = Vec::new();
    for expr in expressions {
        let ExprKind::List(items) = &expr.kind else {
            continue;
        };
        let Some(head) = items.first() else { continue };
        let ExprKind::Symbol(head_name) = &head.kind else {
            continue;
        };
        if !sens::is_define_surface_name(head_name) && !sens::is_defmacro_surface_name(head_name) {
            continue;
        }
        // Structural proof requires the second element to be a symbol;
        // `(def (f a) ...)` or `(def "x" 1)` is not a provable named
        // definition, so it produces none rather than guessing one.
        let Some(second) = items.get(1) else { continue };
        let ExprKind::Symbol(name) = &second.kind else {
            continue;
        };
        defs.push(DefInfo {
            name: name.to_string(),
            kind: head_name.to_string(),
            name_span: second.span,
            form_span: expr.span,
        });
    }
    defs
}

/// One occurrence of a symbol in source code.
#[derive(Clone, Debug)]
pub struct SymbolOccurrence {
    pub name: String,
    pub span: Span,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ArityDiagnostic {
    pub message: String,
    pub span: Span,
}

const D3_QUOTE: (usize, u16) = (3, 0b001);

/// Resolve an admitted human surface through tooling metadata that already
/// carries exact domain identity. No legacy byte is used to infer a domain.
fn surface_domain_coordinate(surface: &str) -> Option<(usize, u16)> {
    sens::language_items()
        .into_iter()
        .find(|item| item.name == surface)
        .and_then(|item| item.domain_identity)
        .map(|identity| (identity.width(), identity.packed_bits()))
}

/// True when an expression is Core.D3 QUOTE.
///
/// Canonical domain AST and admitted surfaces use exact domain identity.
/// Historical exact-eight QUOTE remains only as an explicit compatibility
/// fallback while legacy human-parser output is retired.
fn is_quote_head(expr: &Expr) -> bool {
    match &expr.kind {
        ExprKind::DomainIdentity(identity) => {
            (identity.width(), identity.packed_bits()) == D3_QUOTE
        }
        ExprKind::Sid(identity) => {
            // No historical eight-bit payload can establish D3 QUOTE.
            (identity.width(), identity.packed_bits()) == D3_QUOTE
        }
        ExprKind::Symbol(surface) => surface_domain_coordinate(surface) == Some(D3_QUOTE),
        _ => false,
    }
}

/// Diagnose only calls whose head is a canonical runtime builtin or
/// syntax-dispatched form. Unknown/dynamic heads and locally shadowed
/// first-class builtins remain untouched; quoted subtrees are data.
pub fn arity_diagnostics(source: &str) -> Result<Vec<ArityDiagnostic>, LanguageError> {
    arity_diagnostics_with_items(source, &[])
}

/// Same as [`arity_diagnostics`], with additional known heads folded into
/// the same canonical shape (e.g. live guard functions from
/// `lib/guard.lisp`). Canonical `language_items()` win on name collision —
/// guard files are lower authority than the language itself.
pub fn arity_diagnostics_with_items(
    source: &str,
    extra: &[(String, LanguageItemKind, Arity)],
) -> Result<Vec<ArityDiagnostic>, LanguageError> {
    let expressions = sens::parse(source)?;
    let local_defs = collect_defs(&expressions)
        .into_iter()
        .map(|definition| definition.name)
        .collect::<HashSet<_>>();
    let mut items = sens::language_items()
        .into_iter()
        .map(|item| (item.name, (item.kind, item.arity)))
        .collect::<HashMap<_, _>>();
    for (name, kind, arity) in extra {
        items.entry(name.clone()).or_insert((*kind, *arity));
    }
    let mut diagnostics = Vec::new();
    for expression in &expressions {
        collect_arity_diagnostics(expression, false, &local_defs, &items, &mut diagnostics);
    }
    Ok(diagnostics)
}

fn collect_arity_diagnostics(
    expression: &Expr,
    in_quote: bool,
    local_defs: &HashSet<String>,
    items: &HashMap<String, (LanguageItemKind, Arity)>,
    diagnostics: &mut Vec<ArityDiagnostic>,
) {
    if in_quote {
        return;
    }
    match &expression.kind {
        ExprKind::List(elements) => {
            let head_name = elements.first().and_then(|head| match &head.kind {
                ExprKind::Symbol(name) => Some(name.as_ref()),
                _ => None,
            });
            if let Some(name) = head_name {
                if let Some((kind, arity)) = items.get(name) {
                    let shadowable =
                        matches!(kind, LanguageItemKind::Builtin | LanguageItemKind::Macro);
                    let shadowed = shadowable && local_defs.contains(name);
                    let received = elements.len().saturating_sub(1);
                    if !shadowed && !arity.accepts(received) {
                        diagnostics.push(ArityDiagnostic {
                            message: format!(
                                "arity: {name} expects {}, received {received}",
                                arity.expected()
                            ),
                            span: expression.span,
                        });
                    }
                }
            }
            // QUOTE is a Core.D3 identity. Surface spelling is only a
            // projection, and old exact-eight parser output is compatibility.
            let head_is_quote = elements.first().is_some_and(is_quote_head);
            for (index, element) in elements.iter().enumerate() {
                collect_arity_diagnostics(
                    element,
                    head_is_quote && index > 0,
                    local_defs,
                    items,
                    diagnostics,
                );
            }
        }
        ExprKind::Pair(head, tail) => {
            collect_arity_diagnostics(head, false, local_defs, items, diagnostics);
            collect_arity_diagnostics(tail, false, local_defs, items, diagnostics);
        }
        _ => {}
    }
}

/// Collect every symbol occurrence that represents a *code reference*.
/// Subtrees under `(quote ...)` are data, not code, and are skipped —
/// this is structurally provable from the parse tree plus the fixed set
/// of special forms, so it stays inside the "nothing invented" boundary.
pub fn symbol_occurrences(source: &str) -> Result<Vec<SymbolOccurrence>, LanguageError> {
    let expressions = sens::parse(source)?;
    let mut out = Vec::new();
    for expr in &expressions {
        walk_symbols(expr, false, &mut out);
    }
    Ok(out)
}

fn walk_symbols(expr: &Expr, in_quote: bool, out: &mut Vec<SymbolOccurrence>) {
    match &expr.kind {
        ExprKind::Symbol(name) => {
            if !in_quote {
                out.push(SymbolOccurrence {
                    name: name.to_string(),
                    span: expr.span,
                });
            }
        }
        ExprKind::List(items) => {
            // Core.D3 QUOTE preserves its argument as data. Human spellings
            // resolve through domain-qualified tooling metadata; old exact-8
            // parser output is a compatibility-only fallback.
            let head_is_quote = items.first().is_some_and(is_quote_head);
            for (i, item) in items.iter().enumerate() {
                walk_symbols(item, in_quote || (head_is_quote && i > 0), out);
            }
        }
        ExprKind::Pair(head, tail) => {
            walk_symbols(head, in_quote, out);
            walk_symbols(tail, in_quote, out);
        }
        _ => {}
    }
}

impl Analysis {
    /// Find the top-level expression containing `offset` and return its span.
    /// Used by hover to show evaluation results for complete forms.
    pub fn top_level_at(&self, source: &str, offset: usize) -> Option<Span> {
        let exprs = sens::parse(source).ok()?;
        exprs
            .iter()
            .find(|e| e.span.start <= offset && offset < e.span.end)
            .map(|e| e.span)
    }

    pub fn lookup(&self, name: &str) -> Option<&DefInfo> {
        // Last definition wins, matching the evaluator's own shadowing of
        // a repeated `def` in one session/document.
        self.defs.iter().rev().find(|d| d.name == name)
    }

    /// The innermost symbol expression containing `offset`, found by
    /// walking the same parse tree — never by scanning raw text.
    pub fn symbol_at(&self, source: &str, offset: usize) -> Option<(String, Span)> {
        fn walk(expr: &Expr, offset: usize) -> Option<(String, Span)> {
            if !(expr.span.start <= offset && offset < expr.span.end) {
                return None;
            }
            match &expr.kind {
                ExprKind::Symbol(name) => Some((name.to_string(), expr.span)),
                ExprKind::List(items) => items.iter().find_map(|item| walk(item, offset)),
                ExprKind::Pair(head, tail) => walk(head, offset).or_else(|| walk(tail, offset)),
                _ => None,
            }
        }
        // Top-level forms come from parse(); if the offset falls between
        // forms there is simply nothing to find.
        sens::parse(source)
            .ok()?
            .iter()
            .find_map(|e| walk(e, offset))
    }
}

// ---------------------------------------------------------------------------
// Position mapping. LSP positions are line / UTF-16 code units; the
// canonical spans are UTF-8 byte offsets. This conversion is pure adapter
// arithmetic and belongs nowhere near the core.
// ---------------------------------------------------------------------------

/// Byte offset → (line, character-in-UTF-16-units), end-exclusive spans
/// map naturally since LSP ranges are also end-exclusive. Offsets past the
/// end clamp to the end instead of failing — diagnostics must survive
/// truncated sources.
fn floor_char_boundary(source: &str, mut i: usize) -> usize {
    i = i.min(source.len());
    while i > 0 && !source.is_char_boundary(i) {
        i -= 1;
    }
    i
}

fn ceil_char_boundary(source: &str, mut i: usize) -> usize {
    i = i.min(source.len());
    while i < source.len() && !source.is_char_boundary(i) {
        i += 1;
    }
    i
}

pub fn offset_to_position(source: &str, offset: usize) -> (u32, u32) {
    let offset = floor_char_boundary(source, offset);
    let mut line = 0u32;
    let mut character = 0u32;
    for ch in source[..offset].chars() {
        if ch == '\n' {
            line += 1;
            character = 0;
        } else {
            character += ch.len_utf16() as u32;
        }
    }
    (line, character)
}

/// (line, character-in-UTF-16-units) → byte offset. Out-of-range positions
/// clamp to the nearest valid boundary for the same robustness reason.
pub fn position_to_offset(source: &str, line: u32, character: u32) -> usize {
    let mut current_line = 0u32;
    let mut line_start_byte = 0usize;
    if line > 0 {
        for (i, b) in source.bytes().enumerate() {
            if b == b'\n' {
                current_line += 1;
                line_start_byte = i + 1;
                if current_line == line {
                    break;
                }
            }
        }
        if current_line < line {
            return source.len();
        }
    }
    let rest = &source[line_start_byte..];
    let mut utf16_seen = 0u32;
    for (i, ch) in rest.char_indices() {
        if ch == '\n' || utf16_seen >= character {
            return line_start_byte + i;
        }
        utf16_seen += ch.len_utf16() as u32;
        if utf16_seen >= character {
            return line_start_byte + i + ch.len_utf8();
        }
    }
    source.len()
}

/// Render a span back to source text (for hover payload details).
pub fn span_text(source: &str, span: Span) -> &str {
    let start = floor_char_boundary(source, span.start);
    let end = ceil_char_boundary(source, span.end.max(start));
    &source[start..end]
}

// `Rc` is used by ExprKind; keep the import honest even if unused today.
#[allow(unused)]
fn _rc_witness(_: Rc<str>) {}

