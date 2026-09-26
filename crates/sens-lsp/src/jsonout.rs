//! jsonout.rs — the LSP crate's own transport-local JSON *encoder*.
//!
//! Boundary note (2026-08-22): JSON-RPC serialization is a protocol
//! concern of this adapter, NOT sens semantics, so it deliberately
//! does not live in the language core. The core exposes only the decoder
//! (`sens::parse_json`, extracted from its own `json-parse` special
//! form); encoding responses is done here by writing text directly.
//! If some future sens feature independently needs canonical JSON
//! output, that would be the concrete reuse case to promote it — none
//! exists today.

/// Escape a string per RFC 8259 (control chars, quote, backslash).
pub fn escape(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => {
                out.push_str(&format!("\\u{:04x}", c as u32));
            }
            c => out.push(c),
        }
    }
    out
}

pub fn str_lit(s: &str) -> String {
    format!("\"{}\"", escape(s))
}
