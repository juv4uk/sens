//! server.rs — LSP dispatch. Maps decoded JSON-RPC requests onto the
//! language analysis (`analysis.rs`, which itself is only the canonical
//! sens parser) and emits protocol responses. Holds per-document state
//! for full-text sync.
//!
//! The handler set is exactly M0: initialize, didOpen, didChange,
//! publishDiagnostics (pushed on sync), documentSymbol, hover,
//! definition, plus shutdown/exit lifecycle. Anything else answers
//! MethodNotFound rather than pretending.

use crate::analysis::{self, span_text};
use crate::jsonout::str_lit;
use crate::protocol::{
    self, as_array, as_i64, as_str, decode, get, publish_diagnostics, response, span_to_range,
};
use crate::workspace::WorkspaceIndex;
use sens::{LanguageItemKind, Value};
use std::collections::HashMap;

const PARSE_ERROR: i64 = -32700;
const INVALID_REQUEST: i64 = -32600;
const METHOD_NOT_FOUND: i64 = -32601;

#[derive(Default)]
pub struct Server {
    documents: HashMap<String, String>,
    workspace: WorkspaceIndex,
    /// Guard knowledge loaded from the workspace root when it is the
    /// sens repo; empty otherwise. Functions load eagerly (cheap),
    /// topics lazily on first guard-topic hover.
    guard: crate::guard_knowledge::GuardKnowledge,
}

impl Server {
    pub fn new() -> Self {
        Self::default()
    }

    /// Process one raw JSON-RPC message; returns every outgoing message
    /// (responses and pushed notifications) in order, unframed. Never
    /// panics on malformed input — that is acceptance requirement 9.
    pub fn handle_message(&mut self, text: &str) -> Vec<String> {
        let incoming = match decode(text) {
            Ok(incoming) => incoming,
            Err(message) => {
                return vec![response(
                    &None,
                    None,
                    Some((PARSE_ERROR, format!("parse error: {message}"))),
                )];
            }
        };
        // A notification carries no id and expects no response, but a
        // message with an id AND no method is a malformed request.
        let Some(method) = incoming.method.clone() else {
            if incoming.id.is_some() {
                return vec![response(
                    &incoming.id,
                    None,
                    Some((INVALID_REQUEST, "missing method".into())),
                )];
            }
            return vec![];
        };
        match method.as_str() {
            "initialize" => vec![self.initialize(&incoming)],
            "initialized" | "$/cancelRequest" => vec![],
            "shutdown" => vec![response(&incoming.id, Some("null".to_string()), None)],
            "exit" => vec![], // the stdio loop stops via wants_exit()
            "textDocument/didOpen" => self.did_open(&incoming),
            "textDocument/didChange" => self.did_change(&incoming),
            "textDocument/documentSymbol" => vec![self.document_symbols(&incoming)],
            "textDocument/hover" => vec![self.hover(&incoming)],
            "textDocument/definition" => vec![self.definition(&incoming)],
            "textDocument/completion" => vec![self.completion(&incoming)],
            "textDocument/references" => vec![self.references(&incoming)],
            "textDocument/rename" => vec![self.rename(&incoming)],
            _ => {
                if incoming.id.is_some() {
                    vec![response(
                        &incoming.id,
                        None,
                        Some((METHOD_NOT_FOUND, format!("method not found: {method}"))),
                    )]
                } else {
                    vec![]
                }
            }
        }
    }

    /// Whether this raw message is the `exit` notification.
    pub fn wants_exit(text: &str) -> bool {
        matches!(decode(text), Ok(incoming) if incoming.method.as_deref() == Some("exit"))
    }

    fn initialize(&mut self, incoming: &protocol::Incoming) -> String {
        // M1: a workspace root turns on the cross-file index.
        if let Some(root_uri) = incoming
            .params
            .as_ref()
            .and_then(|p| get(p, "rootUri"))
            .and_then(|u| as_str(Some(u)))
            .and_then(crate::workspace::uri_to_path)
        {
            self.workspace.set_root(root_uri.clone());
            self.guard = crate::guard_knowledge::GuardKnowledge::load_functions(&root_uri);
        }
        // Capabilities list exactly what is implemented — nothing more.
        let capabilities = concat!(
            "{\"textDocumentSync\":1,", // 1 = Full: simplest correct sync for M0
            "\"documentSymbolProvider\":true,",
            "\"hoverProvider\":true,",
            "\"definitionProvider\":true,",
            "\"completionProvider\":{\"resolveProvider\":false},",
            "\"referencesProvider\":true,",
            "\"renameProvider\":true}"
        );
        let result = format!(
            "{{\"capabilities\":{capabilities},\"serverInfo\":{{\"name\":\"sens-lsp\",\"version\":\"0.1.0\"}}}}"
        );
        response(&incoming.id, Some(result), None)
    }

    fn text_document<'a>(params: &'a Option<Value>, key: &'a str) -> Option<&'a Value> {
        get(params.as_ref()?, key)
    }

    fn uri_and_text(
        params: &Option<Value>,
        documents: &HashMap<String, String>,
    ) -> Option<(String, String)> {
        let td = Self::text_document(params, "textDocument")?;
        let uri = as_str(get(td, "uri"))?.to_string();
        let text = documents.get(&uri)?.clone();
        Some((uri, text))
    }

    fn did_open(&mut self, incoming: &protocol::Incoming) -> Vec<String> {
        let Some(uri) = Self::text_document(&incoming.params, "textDocument")
            .and_then(|td| as_str(get(td, "uri")).map(str::to_string))
        else {
            return vec![];
        };
        let Some(text) = Self::text_document(&incoming.params, "textDocument")
            .and_then(|td| as_str(get(td, "text")).map(str::to_string))
        else {
            return vec![];
        };
        self.documents.insert(uri.clone(), text.clone());
        self.workspace.update_document(&uri, &text);
        vec![self.publish(&uri)]
    }

    fn did_change(&mut self, incoming: &protocol::Incoming) -> Vec<String> {
        let Some(uri) = Self::text_document(&incoming.params, "textDocument")
            .and_then(|td| as_str(get(td, "uri")).map(str::to_string))
        else {
            return vec![];
        };
        // Full sync: the LAST content change carries the whole document.
        let changes = as_array(
            incoming
                .params
                .as_ref()
                .and_then(|p| get(p, "contentChanges")),
        );
        let Some(&last) = changes.last() else {
            return vec![];
        };
        let Some(text) = as_str(get(last, "text")).map(str::to_string) else {
            return vec![];
        };
        self.documents.insert(uri.clone(), text.clone());
        self.workspace.update_document(&uri, &text);
        vec![self.publish(&uri)]
    }

    /// Recompute diagnostics from the canonical parser and canonical
    /// language-item arities. Dynamic/unknown calls are never guessed.
    fn publish(&self, uri: &str) -> String {
        let diagnostics = match self.documents.get(uri) {
            Some(text) => match analysis::analyze(text) {
                Ok(_) => match analysis::arity_diagnostics_with_items(text, &self.guard.arity_items()) {
                    Ok(diagnostics) => diagnostics
                        .into_iter()
                        .map(|diagnostic| {
                            protocol::diagnostic(
                                text,
                                &diagnostic.message,
                                diagnostic.span.start,
                                diagnostic.span.end,
                            )
                        })
                        .collect(),
                    Err(err) => vec![protocol::diagnostic(
                        text,
                        &err.message,
                        err.span.start,
                        err.span.end,
                    )],
                },
                Err(err) => vec![protocol::diagnostic(
                    text,
                    &err.message,
                    err.span.start,
                    err.span.end,
                )],
            },
            None => vec![],
        };
        publish_diagnostics(uri, &diagnostics)
    }

    fn document_symbols(&self, incoming: &protocol::Incoming) -> String {
        let Some((_uri, text)) = Self::uri_and_text(&incoming.params, &self.documents) else {
            return response(&incoming.id, Some("null".to_string()), None);
        };
        let Ok(analysis) = analysis::analyze(&text) else {
            // A broken document has no provable symbols; empty array, not
            // an error — diagnostics already reported why.
            return response(&incoming.id, Some("[]".to_string()), None);
        };
        let symbols: Vec<String> = analysis
            .defs
            .iter()
            .map(|def| {
                // SymbolKind 12 = Function; LSP has no Macro kind, so the
                // exact defining keyword travels in `detail`.
                format!(
                    "{{\"name\":{},\"detail\":{},\"kind\":12,\"range\":{},\"selectionRange\":{},\"children\":[]}}",
                    str_lit(&def.name),
                    str_lit(&def.kind),
                    span_to_range(&text, def.form_span.start, def.form_span.end),
                    span_to_range(&text, def.name_span.start, def.name_span.end),
                )
            })
            .collect();
        response(&incoming.id, Some(format!("[{}]", symbols.join(","))), None)
    }

    fn hover(&mut self, incoming: &protocol::Incoming) -> String {
        let Some((_, text)) = Self::uri_and_text(&incoming.params, &self.documents) else {
            return response(&incoming.id, Some("null".to_string()), None);
        };
        let offset = Self::cursor_offset(&incoming.params, &text);
        let Ok(analysis) = analysis::analyze(&text) else {
            return response(&incoming.id, Some("null".to_string()), None);
        };
        let Some((symbol, sym_span)) = analysis.symbol_at(&text, offset) else {
            return response(&incoming.id, Some("null".to_string()), None);
        };
        if let Some(def) = analysis.lookup(&symbol) {
            let value = format!(
                "**{}** `{}`\n\nDefined locally at bytes {}..{}\n\n```sens\n{}\n```",
                def.kind,
                def.name,
                def.name_span.start,
                def.name_span.end,
                span_text(&text, def.form_span)
            );
            let result = format!(
                "{{\"contents\":{{\"kind\":\"markdown\",\"value\":{}}},\"range\":{}}}",
                str_lit(&value),
                span_to_range(&text, sym_span.start, sym_span.end)
            );
            return response(&incoming.id, Some(result), None);
        }
        if let Some(item) = sens::language_items()
            .into_iter()
            .find(|item| item.name == symbol)
        {
            let kind = match item.kind {
                LanguageItemKind::Builtin => "builtin",
                LanguageItemKind::Macro => "macro",
                LanguageItemKind::SyntaxForm => "syntax-dispatched form",
            };
            let value = format!(
                "**{}** `{}`\n\n```sens\n{}\n```\n\n{}",
                kind, symbol, item.signature, item.documentation
            );
            let result = format!(
                "{{\"contents\":{{\"kind\":\"markdown\",\"value\":{}}},\"range\":{}}}",
                str_lit(&value),
                span_to_range(&text, sym_span.start, sym_span.end)
            );
            return response(&incoming.id, Some(result), None);
        }
        // Guard knowledge from the live canonical WSM files (G3): a guard
        // function shows its defining form from lib/guard.wsm; a guard
        // topic shows its reference-bureau entry. The source of truth is
        // the workspace files themselves, never a Rust copy.
        if let Some(function) = self.guard.function(&symbol) {
            if let Some(source) = self.guard.source_of(function) {
                let value = format!(
                    "**guard function** `{}`\n\n```sens\n{}\n```\n\nDefined in lib/guard.lisp (live file, not duplicated in the IDE).",
                    function.name, source
                );
                let result = format!(
                    "{{\"contents\":{{\"kind\":\"markdown\",\"value\":{}}},\"range\":{}}}",
                    str_lit(&value),
                    span_to_range(&text, sym_span.start, sym_span.end)
                );
                return response(&incoming.id, Some(result), None);
            }
        }
        self.guard.ensure_topics();
        if let Some(reference) = self.guard.topic(&symbol) {
            let value = format!(
                "**guard topic** `{}`\n\n{}\n\n**authority:** {}\n\n**how-to:** {}\n\n**verify:** {}\n\n**lifecycle:** {}\n\n**provenance:** {}\n\n**unknown route:** {}",
                reference.topic,
                reference.summary,
                reference.authority.join(", "),
                reference.how_to.join(", "),
                reference.verify.join(", "),
                reference.lifecycle,
                reference.provenance,
                reference.unknown_route
            );
            let result = format!(
                "{{\"contents\":{{\"kind\":\"markdown\",\"value\":{}}},\"range\":{}}}",
                str_lit(&value),
                span_to_range(&text, sym_span.start, sym_span.end)
            );
            return response(&incoming.id, Some(result), None);
        }
        // Eval-on-hover: if the cursor is on a complete top-level form,
        // evaluate it in a fresh session and show the result alongside docs.
        if let Some(form_span) = analysis.top_level_at(&text, offset) {
            let form_text = crate::analysis::span_text(&text, form_span);
            let mut session = sens::Session::default();
            match sens::eval_program(form_text, &mut session) {
                Ok(result) => {
                    let value = format!(
                        "**result:** `{}`\n\n```sens\n{}\n```",
                        result.value, form_text
                    );
                    let result_json = format!(
                        "{{\"contents\":{{\"kind\":\"markdown\",\"value\":{}}},\"range\":{}}}",
                        str_lit(&value),
                        span_to_range(&text, form_span.start, form_span.end)
                    );
                    return response(&incoming.id, Some(result_json), None);
                }
                Err(err) => {
                    let value = format!("**error:** {}", err.message);
                    let result_json = format!(
                        "{{\"contents\":{{\"kind\":\"markdown\",\"value\":{}}},\"range\":{}}}",
                        str_lit(&value),
                        span_to_range(&text, form_span.start, form_span.end)
                    );
                    return response(&incoming.id, Some(result_json), None);
                }
            }
        }
        response(&incoming.id, Some("null".to_string()), None)
    }

    fn definition(&self, incoming: &protocol::Incoming) -> String {
        let Some((uri, text)) = Self::uri_and_text(&incoming.params, &self.documents) else {
            return response(&incoming.id, Some("null".to_string()), None);
        };
        let offset = Self::cursor_offset(&incoming.params, &text);
        let Ok(analysis) = analysis::analyze(&text) else {
            return response(&incoming.id, Some("null".to_string()), None);
        };
        let Some((symbol, _span)) = analysis.symbol_at(&text, offset) else {
            return response(&incoming.id, Some("null".to_string()), None);
        };
        // Same-document first (M0 path), then the workspace index (M1).
        if let Some(def) = analysis.lookup(&symbol) {
            let result = format!(
                "{{\"uri\":{},\"range\":{}}}",
                str_lit(&uri),
                span_to_range(&text, def.name_span.start, def.name_span.end)
            );
            return response(&incoming.id, Some(result), None);
        }
        if let Some(def) = self.workspace.lookup(&symbol).first() {
            // The defining file's own text provides span→range arithmetic;
            // using it keeps ranges correct even when line lengths differ.
            if let Some(def_text) = self.workspace.text_of(&def.uri) {
                let result = format!(
                    "{{\"uri\":{},\"range\":{}}}",
                    str_lit(&def.uri),
                    span_to_range(def_text, def.name_span.start, def.name_span.end)
                );
                return response(&incoming.id, Some(result), None);
            }
        }
        response(&incoming.id, Some("null".to_string()), None)
    }

    /// M1: completion = runtime builtins + syntax-dispatched head forms +
    /// workspace/local defs, filtered by the symbol prefix at the cursor.
    /// Runtime names come from the canonical root environment, so adding a
    /// first-class builtin cannot silently leave LSP completion stale.
    fn completion(&self, incoming: &protocol::Incoming) -> String {
        let Some((_, text)) = Self::uri_and_text(&incoming.params, &self.documents) else {
            return response(&incoming.id, Some("[]".to_string()), None);
        };
        let offset = Self::cursor_offset(&incoming.params, &text);
        let prefix: String = {
            let bytes = text.as_bytes();
            let mut start = offset.min(bytes.len());
            while start > 0 && is_symbol_byte(bytes[start - 1]) {
                start -= 1;
            }
            text[start..offset.min(text.len())].to_string()
        };

        // label -> (detail, kind). Insertion order preserves lexical
        // shadowing: local definitions win over core items with the same name.
        let mut items: Vec<(String, String, u8)> = Vec::new();
        let mut seen = std::collections::HashSet::new();
        let consider = |label: &str,
                        detail: &str,
                        kind: u8,
                        seen: &mut std::collections::HashSet<String>,
                        items: &mut Vec<(String, String, u8)>| {
            if !prefix.is_empty() && !label.starts_with(prefix.as_str()) {
                return;
            }
            if seen.insert(label.to_string()) {
                items.push((label.to_string(), detail.to_string(), kind));
            }
        };

        if let Ok(analysis) = analysis::analyze(&text) {
            for def in &analysis.defs {
                consider(
                    &def.name,
                    &format!("local {}", def.kind),
                    3,
                    &mut seen,
                    &mut items,
                );
            }
        }
        for item in sens::language_items() {
            let kind = match item.kind {
                LanguageItemKind::Builtin => "builtin",
                LanguageItemKind::Macro => "macro",
                LanguageItemKind::SyntaxForm => "syntax-dispatched form",
            };
            let detail = format!("{kind} · {}", item.signature);
            consider(&item.name, &detail, 3, &mut seen, &mut items);
        }
        for def in self.workspace.lookup_all() {
            let file = def.uri.rsplit('/').next().unwrap_or("");
            consider(
                &def.name,
                &format!("{} ({})", def.kind, file),
                3,
                &mut seen,
                &mut items,
            );
        }

        let rendered: Vec<String> = items
            .into_iter()
            .map(|(label, detail, kind)| {
                format!(
                    "{{\"label\":{},\"kind\":{},\"detail\":{}}}",
                    str_lit(&label),
                    kind,
                    str_lit(&detail)
                )
            })
            .collect();
        response(
            &incoming.id,
            Some(format!(
                "{{\"isIncomplete\":false,\"items\":[{}]}}",
                rendered.join(",")
            )),
            None,
        )
    }

    /// M2: all code references of the symbol at the cursor, across open +
    /// indexed workspace documents. Quoted data is skipped (see
    /// analysis::symbol_occurrences). includeDeclaration controls whether
    /// the defining name span counts as a reference.
    fn references(&self, incoming: &protocol::Incoming) -> String {
        let Some((uri, text)) = Self::uri_and_text(&incoming.params, &self.documents) else {
            return response(&incoming.id, Some("[]".to_string()), None);
        };
        let offset = Self::cursor_offset(&incoming.params, &text);
        let Ok(analysis) = analysis::analyze(&text) else {
            return response(&incoming.id, Some("[]".to_string()), None);
        };
        let Some((symbol, _)) = analysis.symbol_at(&text, offset) else {
            return response(&incoming.id, Some("[]".to_string()), None);
        };
        let include_decl = incoming
            .params
            .as_ref()
            .and_then(|p| get(p, "context"))
            .and_then(|c| get(c, "includeDeclaration"))
            .map(|v| match v {
                Value::Bool(b) => *b,
                Value::Symbol(n) => n.as_ref() == "true",
                _ => false,
            })
            .unwrap_or(false);

        let mut locations: Vec<String> = Vec::new();
        let mut seen_spans: std::collections::HashSet<(String, usize)> =
            std::collections::HashSet::new();

        // Def-name spans of this symbol anywhere in this document are its
        // declarations; without includeDeclaration they are not references.
        let decl_spans: Vec<usize> = analysis
            .defs
            .iter()
            .filter(|d| d.name == symbol)
            .map(|d| d.name_span.start)
            .collect();

        // Declarations live wherever their def-form is; exclusion applies
        // per-document, not just to the file the cursor sits in.
        let _ = decl_spans;
        let mut collect = |doc_uri: &str, doc_text: &str| {
            if let Ok(occurrences) = analysis::symbol_occurrences(doc_text) {
                let decl_here: Vec<usize> = if include_decl {
                    vec![]
                } else {
                    analysis::analyze(doc_text)
                        .map(|a| {
                            a.defs
                                .iter()
                                .filter(|d| d.name == symbol)
                                .map(|d| d.name_span.start)
                                .collect()
                        })
                        .unwrap_or_default()
                };
                for occ in occurrences {
                    if occ.name != symbol {
                        continue;
                    }
                    if !include_decl && decl_here.contains(&occ.span.start) {
                        continue;
                    }
                    if seen_spans.insert((doc_uri.to_string(), occ.span.start)) {
                        locations.push(format!(
                            "{{\"uri\":{},\"range\":{}}}",
                            str_lit(doc_uri),
                            span_to_range(doc_text, occ.span.start, occ.span.end)
                        ));
                    }
                }
            }
        };

        collect(&uri, &text);
        for doc_uri in self.workspace.all_texts() {
            if doc_uri == uri {
                continue;
            }
            if let Some(t) = self.workspace.text_of(&doc_uri) {
                collect(&doc_uri, t);
            }
        }
        response(
            &incoming.id,
            Some(format!("[{}]", locations.join(","))),
            None,
        )
    }

    /// M2: rename the symbol at the cursor across open + indexed documents.
    /// newName must be a valid sens symbol (charset enforced by the same
    /// predicate completion uses); quoted data is never touched.
    fn rename(&self, incoming: &protocol::Incoming) -> String {
        let Some(new_name) = incoming
            .params
            .as_ref()
            .and_then(|p| get(p, "newName"))
            .and_then(|v| as_str(Some(v)))
            .map(str::to_string)
        else {
            return response(
                &incoming.id,
                None,
                Some((-32602, "rename requires newName".into())),
            );
        };
        if !is_valid_symbol_name(&new_name) {
            return response(
                &incoming.id,
                None,
                Some((-32602, format!("invalid symbol name: {new_name}"))),
            );
        }

        let Some((uri, text)) = Self::uri_and_text(&incoming.params, &self.documents) else {
            return response(&incoming.id, Some("null".to_string()), None);
        };
        let offset = Self::cursor_offset(&incoming.params, &text);
        let Ok(analysis) = analysis::analyze(&text) else {
            return response(&incoming.id, Some("null".to_string()), None);
        };
        let Some((symbol, _)) = analysis.symbol_at(&text, offset) else {
            return response(&incoming.id, Some("null".to_string()), None);
        };

        let mut changes: Vec<(String, Vec<String>)> = Vec::new();
        let mut collect_edits = |doc_uri: &str, doc_text: &str| {
            if let Ok(occurrences) = analysis::symbol_occurrences(doc_text) {
                let edits: Vec<String> = occurrences
                    .iter()
                    .filter(|occ| occ.name == symbol)
                    .map(|occ| {
                        format!(
                            "{{\"range\":{},\"newText\":{}}}",
                            span_to_range(doc_text, occ.span.start, occ.span.end),
                            str_lit(&new_name)
                        )
                    })
                    .collect();
                if !edits.is_empty() {
                    changes.push((doc_uri.to_string(), edits));
                }
            }
        };

        collect_edits(&uri, &text);
        for doc_uri in self.workspace.all_texts() {
            if doc_uri == uri {
                continue;
            }
            if let Some(t) = self.workspace.text_of(&doc_uri) {
                collect_edits(&doc_uri, t);
            }
        }

        let rendered: Vec<String> = changes
            .into_iter()
            .map(|(u, edits)| format!("{}:[{}]", str_lit(&u), edits.join(",")))
            .collect();
        response(
            &incoming.id,
            Some(format!("{{\"changes\":{{{}}}}}", rendered.join(","))),
            None,
        )
    }

    /// params.position.{line,character} → byte offset into the doc text.
    fn cursor_offset(params: &Option<Value>, text: &str) -> usize {
        let Some(position) = params.as_ref().and_then(|p| get(p, "position")) else {
            return usize::MAX;
        };
        let line = as_i64(get(position, "line")).unwrap_or(0).max(0) as u32;
        let character = as_i64(get(position, "character")).unwrap_or(0).max(0) as u32;
        analysis::position_to_offset(text, line, character)
    }
}

fn is_valid_symbol_name(name: &str) -> bool {
    !name.is_empty()
        && name.bytes().all(is_symbol_byte)
        && !name.bytes().next().unwrap().is_ascii_digit()
}

fn is_symbol_byte(b: u8) -> bool {
    b.is_ascii_alphanumeric()
        || matches!(
            b,
            b'-' | b'_' | b'<' | b'>' | b'?' | b'!' | b'+' | b'*' | b'/' | b'=' | b'.'
        )
}
