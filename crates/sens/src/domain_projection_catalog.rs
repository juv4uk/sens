//! Read-only, source-derived projection lookup. A projection row does not grant
//! residency, callability, meaning, or physical encoding behavior.

/// Незалежний простір джерела: однакові назви колонок не зливають різні таблиці.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProjectionSource {
    /// Людиночитані таблиці `lib/domains/d1.lisp` … `d10.lisp`.
    DomainTable,
    /// Окрема D7 клавіатурна проєкція з нативних таблиць Rust.
    D7KeyboardV2,
}

/// Точна форма клітинки: доменний символ, Unicode-символ, рядок або `()`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProjectionValue {
    Symbol(&'static str),
    Text(&'static str),
    Character(char),
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
/// `domain` means the named SENS domain D1–D10, not a width-derived semantic
/// classification. Unknown domains, malformed/inexact bits, and missing cells
/// return `None`; D11–D24+ remain governed by their current authorities and
/// are not inferred or synthesized by this catalog.
pub fn lookup(
    source: ProjectionSource,
    domain: u16,
    bits: &str,
    column: &str,
) -> Option<ProjectionValue> {
    if bits.len() != usize::from(domain) || !bits.bytes().all(|bit| matches!(bit, b'0' | b'1')) {
        return None;
    }
    if source == ProjectionSource::D7KeyboardV2 {
        if domain != 7 {
            return None;
        }
        let coordinate = bits
            .bytes()
            .fold(0_u8, |value, bit| (value << 1) | u8::from(bit == b'1'));
        return match column {
            "ascii" => Some(ProjectionValue::Character(char::from(coordinate))),
            "uk" => Some(ProjectionValue::Character(
                crate::d7_keyboard::UK[usize::from(coordinate)],
            )),
            "san" => Some(ProjectionValue::Character(
                crate::d7_keyboard::SAN[usize::from(coordinate)],
            )),
            "iast" => {
                let word = crate::BinarySourceWord::W7(crate::Bit7::new(coordinate)?);
                let identity = crate::DomainIdentity::from_source_word(word);
                crate::semantic_registry::surface_for_domain_identity(identity, "sa")
                    .map(ProjectionValue::Text)
            }
            _ => None,
        };
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

/// Кількість клітинок згенерованих Lisp-таблиць D1–D10.
pub fn entry_count() -> usize {
    ENTRIES.len()
}
