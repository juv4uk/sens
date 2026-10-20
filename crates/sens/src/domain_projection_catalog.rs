//! Read-only, source-derived projection lookup. A projection row does not grant
//! residency, callability, meaning, or physical encoding behavior.

/// Незалежний простір джерела: однакові назви колонок не зливають різні таблиці.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProjectionSource {
    /// Людиночитані таблиці `lib/domains/d1.lisp` … `d11.lisp`.
    DomainTable,
    /// Окрема ратифікована клавіатурна проєкція D7 версії 2.
    D7KeyboardV2,
    /// Окремий ратифікований словник тестової лексики D11.
    D11RatifiedVocabulary,
}

/// Точна форма клітинки: символ, рядок або явний порожній список `()`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProjectionValue {
    Symbol(&'static str),
    Text(&'static str),
    EmptyList,
}

pub(super) struct Entry {
    source: ProjectionSource,
    domain: u16,
    bits: &'static str,
    column: &'static str,
    value: ProjectionValue,
}

include!(concat!(env!("OUT_DIR"), "/domain_projection_catalog.rs"));

/// Exact lookup in an explicitly selected source namespace.
///
/// `domain` means the named SENS domain D1–D11, not a width-derived semantic
/// classification. Unknown domains, malformed/inexact bits, and missing cells
/// return `None`; D24+ remains governed by the existing numeric implementation.
pub fn lookup(
    source: ProjectionSource,
    domain: u16,
    bits: &str,
    column: &str,
) -> Option<ProjectionValue> {
    if bits.len() != usize::from(domain) || !bits.bytes().all(|bit| matches!(bit, b'0' | b'1')) {
        return None;
    }
    ENTRIES
        .iter()
        .find(|entry| {
            entry.source == source
                && entry.domain == domain
                && entry.bits == bits
                && entry.column == column
        })
        .map(|entry| entry.value)
}

/// Number of generated source cells, useful for consumers that need inventory.
pub fn entry_count() -> usize {
    ENTRIES.len()
}
