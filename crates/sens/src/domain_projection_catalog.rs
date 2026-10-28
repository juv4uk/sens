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

/// Unique Ukrainian D1–D10 projection identity for executable source heads.
///
/// This resolves identity only: evaluator dispatch separately requires an
/// admitted primitive or an explicitly installed code slot. D7 is excluded
/// because its Ukrainian cells are text glyph data, not function names. D24+
/// numeric operands are handled by the numeric source projection instead.
// Допоміжний індекс потрібен лише тестам проєкцій, не двійковому рантайму.
    let index = INDEX.get_or_init(|| {
        let mut names = HashMap::new();
        for entry in ENTRIES.iter().filter(|entry| {
            entry.source == ProjectionSource::DomainTable
                && entry.column == "ук"
                && entry.domain != 7
        }) {
            let ProjectionValue::Symbol(surface) = entry.value else {
                continue;
            };
            let Ok(bits) = u16::from_str_radix(entry.bits, 2) else {
                continue;
            };
            let Some(coordinate) =
                crate::domain_ladder::DomainCoordinate::new(entry.domain as u8, bits)
            else {
                continue;
            };
            let identity = crate::DomainIdentity::from_coordinate(coordinate);
            use std::collections::hash_map::Entry;
            match names.entry(surface) {
                Entry::Vacant(slot) => {
                    slot.insert(Some(identity));
                }
                Entry::Occupied(mut slot) if slot.get().is_some_and(|old| old != identity) => {
                    slot.insert(None);
                }
                Entry::Occupied(_) => {}
            }
        }
        names
    });
    index.get(name).copied().flatten()
}

/// Кількість клітинок згенерованих Lisp-таблиць D1–D10.
pub fn entry_count() -> usize {
    ENTRIES.len()
}


