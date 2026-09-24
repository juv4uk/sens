//! workspace.rs — cross-file definition index (LSP M1).
//!
//! Scans the workspace root for source files once on `initialize`, then
//! refreshes individual documents on open/change. Definitions are still
//! proven ONLY by the canonical parser (`analysis::analyze`) — this module
//! just remembers them per-file so go-to-definition can cross document
//! boundaries. No grep-based detection, no invented semantics.
//!
//! Recognized extensions include `.sens` as the canonical project-name surface,
//! plus the existing `.wsm`, `.my`, and `.lisp` source aliases, and
//! the equal-standing Ukrainian Cyrillic spellings `.всм`/`.мій`/`.лісп`
//! (issue #62, 2026-09-10 owner decision: file-naming surface policy, not
//! a new semantic authority — a `.мій` file means exactly what a `.my`
//! file means).
//!
//! Memory model: every scanned/opened file's full text is kept so spans
//! can be rendered as LSP ranges without re-reading disk. Reasonable for
//! source workspaces; revisit only if real projects outgrow RAM.

use crate::analysis;
use my_lisp::Span;
use std::collections::HashMap;
use std::path::{Path, PathBuf};

/// A definition proven in some workspace file.
#[derive(Clone, Debug)]
pub struct WorkspaceDef {
    pub name: String,
    pub uri: String,
    pub kind: String,
    pub name_span: Span,
    pub form_span: Span,
}

/// Files larger than this are skipped during scanning: the index must not
/// stall startup on generated artifacts. Open documents bypass the cap.
const SCAN_MAX_BYTES: u64 = 4 * 1024 * 1024;

#[derive(Default)]
pub struct WorkspaceIndex {
    root: Option<PathBuf>,
    /// name -> definitions across all known files (last wins per file).
    by_name: HashMap<String, Vec<WorkspaceDef>>,
    /// uri -> full text of every indexed/opened file.
    texts: HashMap<String, String>,
}

impl WorkspaceIndex {
    pub fn new() -> Self {
        Self::default()
    }

    /// Set the workspace root and scan it. A previous index is replaced —
    /// initialize happens once per session.
    pub fn set_root(&mut self, root: PathBuf) {
        let mut by_name: HashMap<String, Vec<WorkspaceDef>> = HashMap::new();
        let mut texts = HashMap::new();
        let mut stack = vec![root.clone()];
        while let Some(dir) = stack.pop() {
            let Ok(entries) = std::fs::read_dir(&dir) else {
                continue;
            };
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_dir() {
                    // Hidden dirs (.git, .obsidian, target…) are never sources.
                    if !entry.file_name().to_string_lossy().starts_with('.') {
                        stack.push(path);
                    }
                    continue;
                }
                let is_source = matches!(
                    path.extension().and_then(|e| e.to_str()),
                    Some("sens") | Some("wsm") | Some("my") | Some("lisp")
                        | Some("всм") | Some("мій") | Some("лісп")
                );
                if !is_source {
                    continue;
                }
                let Ok(meta) = entry.metadata() else { continue };
                if meta.len() > SCAN_MAX_BYTES {
                    continue;
                }
                let Ok(text) = std::fs::read_to_string(&path) else {
                    continue;
                };
                let uri = path_to_uri(&path);
                collect_into(&mut by_name, &mut texts, &uri, &text);
            }
        }
        self.root = Some(root);
        self.by_name = by_name;
        self.texts = texts;
    }

    pub fn root(&self) -> Option<&Path> {
        self.root.as_deref()
    }

    /// Refresh one document's contributions after open/change. The text is
    /// kept even when parsing fails (spans of other files stay correct;
    /// this file simply contributes no definitions until it parses again).
    pub fn update_document(&mut self, uri: &str, text: &str) {
        self.texts.insert(uri.to_string(), text.to_string());
        // Remove this uri's previous contributions.
        for defs in self.by_name.values_mut() {
            defs.retain(|d| d.uri != uri);
        }
        self.by_name.retain(|_, defs| !defs.is_empty());
        collect_into(&mut self.by_name, &mut self.texts, uri, text);
    }

    pub fn lookup(&self, name: &str) -> &[WorkspaceDef] {
        match self.by_name.get(name) {
            Some(defs) => defs,
            None => &[],
        }
    }

    /// URIs of every known document.
    pub fn all_texts(&self) -> Vec<String> {
        self.texts.keys().cloned().collect()
    }

    /// Full text of an indexed or opened document (for span→range math).
    pub fn text_of(&self, uri: &str) -> Option<&str> {
        self.texts.get(uri).map(String::as_str)
    }
}

fn collect_into(
    by_name: &mut HashMap<String, Vec<WorkspaceDef>>,
    texts: &mut HashMap<String, String>,
    uri: &str,
    text: &str,
) {
    texts.insert(uri.to_string(), text.to_string());
    if let Ok(analysis) = analysis::analyze(text) {
        for def in analysis.defs {
            by_name
                .entry(def.name.clone())
                .or_default()
                .push(WorkspaceDef {
                    name: def.name,
                    uri: uri.to_string(),
                    kind: def.kind,
                    name_span: def.name_span,
                    form_span: def.form_span,
                });
        }
    }
}

// ---------------------------------------------------------------------------
// file:// URI <-> path conversion (minimal, no external crates)
// ---------------------------------------------------------------------------

pub fn path_to_uri(path: &Path) -> String {
    let path = path.canonicalize().unwrap_or_else(|_| path.to_path_buf());
    let mut out = String::from("file://");
    for component in path.to_string_lossy().bytes() {
        match component {
            b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' | b'/' => {
                out.push(component as char)
            }
            _ => out.push_str(&format!("%{component:02X}")),
        }
    }
    out
}

pub fn uri_to_path(uri: &str) -> Option<PathBuf> {
    let rest = uri.strip_prefix("file://")?;
    let mut bytes = Vec::new();
    let raw = rest.as_bytes();
    let mut i = 0;
    while i < raw.len() {
        if raw[i] == b'%' && i + 2 < raw.len() {
            let hex = std::str::from_utf8(&raw[i + 1..i + 3]).ok()?;
            bytes.push(u8::from_str_radix(hex, 16).ok()?);
            i += 3;
        } else {
            bytes.push(raw[i]);
            i += 1;
        }
    }
    Some(PathBuf::from(String::from_utf8(bytes).ok()?))
}

impl WorkspaceIndex {
    /// All definitions in the index, in insertion order.
    pub fn lookup_all(&self) -> Vec<WorkspaceDef> {
        self.by_name.values().flatten().cloned().collect()
    }
}

#[cfg(test)]
mod sens_extension_tests {
    use super::*;

    #[test]
    fn scan_root_recognizes_sens_extension_without_widening_filter() {
        let dir = std::env::temp_dir().join(format!(
            "sens-lsp-extension-test-{}",
            std::process::id()
        ));
        std::fs::create_dir_all(&dir).expect("create temp workspace dir");

        std::fs::write(dir.join("example.sens"), "(def sens-example 42)")
            .expect("write .sens fixture");
        std::fs::write(dir.join("ignored.txt"), "(def ignored-example 0)")
            .expect("write non-source control file");

        let mut index = WorkspaceIndex::new();
        index.set_root(dir.clone());

        assert!(
            !index.lookup("sens-example").is_empty(),
            ".sens file was not scanned"
        );
        assert!(
            index.lookup("ignored-example").is_empty(),
            ".txt file must remain outside the source allowlist"
        );

        let _ = std::fs::remove_dir_all(&dir);
    }
}

#[cfg(test)]
mod cyrillic_extension_tests {
    //! Issue #62 (2026-09-10 owner decision): `.мій`/`.всм`/`.лісп` are
    //! equal-standing Ukrainian spellings of `.my`/`.wsm`/`.lisp`. Proves
    //! the workspace scanner recognizes them on a real temp directory, not
    //! just via a `matches!` arm read in isolation.
    use super::*;

    #[test]
    fn scan_root_recognizes_all_three_cyrillic_extensions() {
        let dir = std::env::temp_dir().join(format!(
            "my-lisp-lsp-cyrillic-ext-test-{}",
            std::process::id()
        ));
        std::fs::create_dir_all(&dir).expect("create temp workspace dir");

        std::fs::write(dir.join("визначення.мій"), "(def приклад 42)")
            .expect("write .мій fixture");
        std::fs::write(dir.join("контракт.всм"), "(def інший 7)").expect("write .всм fixture");
        std::fs::write(dir.join("програма.лісп"), "(def третій 1)")
            .expect("write .лісп fixture");
        // A non-source extension must still be ignored, exactly as for the
        // Latin extensions — this proves the addition didn't accidentally
        // widen the filter to "everything."
        std::fs::write(dir.join("нотатка.txt"), "(def четвертий 0)")
            .expect("write non-source control file");

        let mut index = WorkspaceIndex::new();
        index.set_root(dir.clone());

        assert!(
            !index.lookup("приклад").is_empty(),
            ".мій file was not scanned"
        );
        assert!(
            !index.lookup("інший").is_empty(),
            ".всм file was not scanned"
        );
        assert!(
            !index.lookup("третій").is_empty(),
            ".лісп file was not scanned"
        );
        assert!(
            index.lookup("четвертий").is_empty(),
            ".txt file must still be ignored — the Cyrillic extensions must \
             not widen the filter beyond the intended six spellings"
        );

        let _ = std::fs::remove_dir_all(&dir);
    }
}
