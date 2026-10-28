//! Runtime projection of the Lisp-owned semantic registry.
//!
//! The canonical authority is lib/surface/semantic-registry.lisp and its
//! Lisp-owned reader/API. This module contains no parser for canonical source
//! text. The generated table is emitted by
//! scripts/generate-rust-semantic-registry.lisp and is only a mechanical
//! runtime projection for fast lookup.
//
//! Generated rows may carry a packed byte as substrate representation of an
//! already understood Lisp Binary identity. This wrapper converts that byte to
//! opaque CoreDomainIdentity immediately; runtime registry APIs never expose decimal IDs.

use std::{collections::HashMap, sync::OnceLock};

use crate::{
    BinarySourceWord, Bit1, Bit3, Bit4, Bit5, Bit6, Bit9, CoreD5, CoreD6, CoreD9,
    CoreDomainIdentity, DomainIdentity,
};

mod generated {
    include!("semantic_registry_generated.rs");
}

mod domain_surface_generated {
    include!("domain_surface_registry_generated.rs");
}

mod d7_display_generated {
    include!("d7_display_registry_generated.rs");
}

mod d5_definition_bindings_generated {
    include!("d5_definition_bindings_generated.rs");
}

mod d6_definition_bindings_generated {
    include!("d6_definition_bindings_generated.rs");
}

mod d9_definition_bindings_generated {
    include!("d9_definition_bindings_generated.rs");
}

mod d10_definition_bindings_generated {
    include!("d10_definition_bindings_generated.rs");
}

use d10_definition_bindings_generated::D10_DEFINITION_BINDINGS;
use d5_definition_bindings_generated::D5_DEFINITION_BINDINGS;
use d6_definition_bindings_generated::D6_DEFINITION_BINDINGS;
use d7_display_generated::D7_DISPLAY_ROWS;
use d9_definition_bindings_generated::D9_DEFINITION_BINDINGS;
use domain_surface_generated::{DomainSurfaceRow, DOMAIN_SURFACE_ROWS};
use generated::{SemanticRow, SEMANTIC_ROWS};

/// Only the historical W8 surface-table slot. Although the carrier type can
/// also represent exact admitted D9 operations, this registry lane must stay
/// W8-only and never reinterpret a D9 identity as a historical slot.
pub(crate) type LegacyRegistrySlot = CoreDomainIdentity;

/// A historical surface row cannot supply the width of a modern domain.
/// Resolve only through non-ambiguous, ratified exact surface records.
fn exact_identity_for_row(row: &SemanticRow) -> Option<CoreDomainIdentity> {
    let mut admitted = None;
    for surface in row.surfaces {
        let Some(current) = direct_domain_identity_for_surface(surface.name)
            .filter(|identity| identity.width() <= 8)
        else {
            continue;
        };
        if admitted.is_some_and(|previous| previous != current) {
            return None;
        }
        admitted = Some(current);
    }
    admitted
}

pub(crate) fn exact_identity_for_legacy_registry_slot(slot: u8) -> Option<CoreDomainIdentity> {
    SEMANTIC_ROWS
        .get(usize::from(slot))
        .filter(|row| row.semantic_id == slot)
        .and_then(exact_identity_for_row)
}

pub(crate) fn legacy_slot_for_exact_identity(identity: CoreDomainIdentity) -> Option<u8> {
    if identity.width() > 8 {
        return None;
    }
    let mut matched = None;
    for row in SEMANTIC_ROWS {
        if exact_identity_for_row(row) == Some(identity) {
            if matched.is_some() {
                return None;
            }
            matched = Some(row.semantic_id);
        }
    }
    matched
}

/// Convert only explicit generated D3–D6 coordinates into resident identity.
///
/// No W8 slot, packed payload, or name may select the width. Higher domains
/// require their own generated coordinate authority (never an implicit lift).
fn exact_domain_resident_from_projection(width: u8, bits: u8) -> Option<DomainIdentity> {
    use crate::BinarySourceWord;
    let source = match width {
        3 => BinarySourceWord::W3(Bit3::new(bits)?),
        4 => BinarySourceWord::W4(Bit4::new(bits)?),
        5 => BinarySourceWord::W5(Bit5::new(bits)?),
        6 => BinarySourceWord::W6(crate::Bit6::new(bits)?),
        _ => return None,
    };
    Some(DomainIdentity::from_source_word(source))
}

/// A stable source name has either exactly one domain-qualified coordinate or
/// none. Conflicts are terminal: a third equal row must not re-admit a name
/// that was already ambiguous between two widths or two bit patterns.
#[derive(Default)]
struct ExactDomainSourceIndex {
    all: HashMap<&'static str, Option<DomainIdentity>>,
    uk: HashMap<&'static str, Option<DomainIdentity>>,
}

fn insert_exact_source(
    index: &mut HashMap<&'static str, Option<DomainIdentity>>,
    name: &'static str,
    identity: Option<DomainIdentity>,
) {
    use std::collections::hash_map::Entry;
    match index.entry(name) {
        Entry::Vacant(slot) => {
            slot.insert(identity);
        }
        Entry::Occupied(mut slot) => {
            // None is a terminal collision/malformed-coordinate state.
            // A later A in A,B,A must never resurrect a callable route.
            if let Some(previous) = *slot.get() {
                if Some(previous) != identity {
                    slot.insert(None);
                }
            }
        }
    }
}

/// Build from the Lisp-owned ratified generated table only.
///
/// A malformed generated coordinate is rejected just like a collision. The
/// Ukrainian exact-source index stays separate from the language projections:
/// historical W8 and the English compatibility registry cannot authorize a
/// new executable source head.
fn build_exact_source_index(rows: &[DomainSurfaceRow]) -> ExactDomainSourceIndex {
    let mut index = ExactDomainSourceIndex::default();
    for row in rows.iter().filter(|row| row.source_routable) {
        let identity = exact_domain_resident_from_projection(row.width, row.bits);
        for surface in row.surfaces.iter() {
            if !matches!(surface.namespace, "uk" | "ukr" | "sa" | "en") {
                continue;
            }
            insert_exact_source(&mut index.all, surface.name, identity);
            if matches!(surface.namespace, "uk" | "ukr") {
                insert_exact_source(&mut index.uk, surface.name, identity);
            }
        }
    }
    index
}

fn exact_source_index() -> &'static ExactDomainSourceIndex {
    static INDEX: OnceLock<ExactDomainSourceIndex> = OnceLock::new();
    INDEX.get_or_init(|| build_exact_source_index(DOMAIN_SURFACE_ROWS))
}

/// Source human names select only the exact D3/D4/D5/D6 projection.
/// A name conflict cannot silently pick the first generated row.
fn direct_domain_identity_for_surface(name: &str) -> Option<CoreDomainIdentity> {
    exact_source_index()
        .all
        .get(name)
        .copied()
        .flatten()?
        .core_operation()
}

/// Сумісний SID лише знаходить рядок surface-реєстру; координату D3
/// встановлює виключно ратифікована доменна таблиця. Немає збігу або
/// кілька різних координат — fail-closed, жодної таблиці SID→роль у Rust.
pub(crate) fn compatibility_d3_route_from_ratified_domains(
    semantic_id: LegacyRegistrySlot,
) -> Option<CoreDomainIdentity> {
    let packed = legacy_slot_for_exact_identity(semantic_id)?;
    let row = SEMANTIC_ROWS.get(usize::from(packed))?;
    if row.semantic_id != packed {
        return None;
    }
    let mut admitted = None;
    for surface in row.surfaces {
        // Лише іменні історичні проєкції підтверджують чинний D3-закон.
        // Байт W8 та символічна мітка не мають права призначати D8/D3.
        if !matches!(surface.namespace, "ук" | "укр" | "sa") {
            continue;
        }
        let Some(identity) = direct_domain_identity_for_surface(surface.name) else {
            continue;
        };
        if !matches!(identity, CoreDomainIdentity::D3(_)) {
            return None;
        }
        if admitted.is_some_and(|previous| previous != identity) {
            return None;
        }
        admitted = Some(identity);
    }
    admitted
}

/// Exact Ukrainian spellings for the explicitly implemented D8 mechanisms.
/// Residency alone is not enough: this small owner-pinned list names only
/// routes with a concrete mechanism in eval/canon.rs. Keep it shared with the
/// mixed-source lift so direct and Lisp→T5M source do not disagree.
pub(crate) fn admitted_d8_uk_callable_bits(spelling: &str) -> Option<&'static str> {
    match spelling {
        "символ-за-кодом" => Some("00000000"),
        "модульна-остача" => Some("00101100"),
        "код-символу" => Some("11100000"),
        "прочитати" => Some("11101010"),
        "текст-у-символ" => Some("11101101"),
        "символ-у-текст" => Some("11101110"),
        "значення-у-текст" => Some("11110100"),
        "однакові?" => Some("11110111"),
        _ => None,
    }
}

/// Canonical Ukrainian *source-head* projection, before evaluation.
///
/// Only owner-ratified source-routable uk/ukr peer rows are eligible, together
/// with the small explicit D8 mechanism list above. This is NOT the legacy SID
/// compatibility index: no en alias, old W8, D2 structure, or unratified D7
/// binder can become a callable head via this API.
pub(crate) fn exact_uk_callable_for_source_head(name: &str) -> Option<crate::DomainIdentity> {
    if let Some(identity) = exact_source_index().uk.get(name).copied().flatten() {
        return Some(identity);
    }
    if let Some(bits) = admitted_d8_uk_callable_bits(name) {
        let word = crate::parse_binary_source_words(bits)
            .ok()?
            .into_iter()
            .next()?
            .word;
        return Some(DomainIdentity::from_source_word(word));
    }
    higher_selector_uk_index()
        .get(name)
        .copied()
        .or_else(|| d8_selector_uk_index().get(name).copied())
}

/// Lazily cache only the mathematical selector subfamily from the
/// current owner tables. Unrelated D9/D10 residents remain non-callable.
/// No linear table scan is performed for each SENS source expression.
fn higher_selector_uk_index() -> &'static HashMap<&'static str, DomainIdentity> {
    static INDEX: OnceLock<HashMap<&'static str, DomainIdentity>> = OnceLock::new();
    INDEX.get_or_init(|| {
        let mut names = HashMap::new();
        for row in D9_DEFINITION_BINDINGS {
            if matches!(row.bits >> 6, 0b011 | 0b100) && row.names.len() == 5 {
                let id = DomainIdentity::D9(CoreD9::from_word(Bit9::new(row.bits).unwrap()));
                for name in &row.names[..2] {
                    names.insert(*name, id);
                }
            }
        }
        for row in D10_DEFINITION_BINDINGS {
            if matches!(row.bits >> 7, 0b011 | 0b100) && row.names.len() == 5 {
                let id = DomainIdentity::D10(crate::DomainD10::new(row.bits).unwrap());
                for name in &row.names[..2] {
                    names.insert(*name, id);
                }
            }
        }
        names
    })
}

/// D8 has 64 proved selector addresses. Their human names are projected
/// from the CAR/CDR path, not stored as manually written functions.
fn d8_selector_uk_index() -> &'static HashMap<String, DomainIdentity> {
    static INDEX: OnceLock<HashMap<String, DomainIdentity>> = OnceLock::new();
    INDEX.get_or_init(|| {
        let mut names = HashMap::new();
        for (root, initial, full) in [(0b011u8, "р", "решта"), (0b100u8, "п", "перше")]
        {
            for suffix in 0..(1u8 << 5) {
                let bits = (root << 5) | suffix;
                let id =
                    DomainIdentity::D8(crate::CoreD8::from_word(crate::Bit8::new(bits).unwrap()));
                let mut short = initial.to_owned();
                let mut long = full.to_owned();
                for shift in (0..5).rev() {
                    let rest = (suffix >> shift) & 1 == 1;
                    short.push('-');
                    short.push(if rest { 'р' } else { 'п' });
                    long.push_str(if rest {
                        "-від-решта"
                    } else {
                        "-від-перше"
                    });
                }
                names.insert(short, id);
                names.insert(long, id);
            }
        }
        names
    })
}

/// Точне D5-зв'язування наявних Lisp-визначень.
/// Таблиця може надати механізм лише identity, уже ратифікованій контрактом
/// SENS; вона не надає нового допуску до виклику.
pub(crate) fn d5_lisp_definition_names() -> impl Iterator<Item = &'static str> {
    D5_DEFINITION_BINDINGS.iter().map(|row| row.name)
}

/// Імена вже ратифікованих похідних Lisp-визначень D6.
/// Ця проєкція не надає нового допуску до виклику.
pub(crate) fn d6_lisp_definition_names() -> impl Iterator<Item = &'static str> {
    D6_DEFINITION_BINDINGS
        .iter()
        .flat_map(|row| row.names.iter().copied())
}

pub(crate) fn d5_binding_identity_for_definition(name: &str) -> Option<CoreDomainIdentity> {
    D5_DEFINITION_BINDINGS
        .iter()
        .find(|row| row.name == name)
        .map(|row| CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(row.bits).unwrap())))
}

/// Знаходить ратифіковане українське написання визначення D6.
/// Цей пошук метаданих не надає написанню права бути головою джерела.
pub(crate) fn d6_uk_source_identity(name: &str) -> Option<DomainIdentity> {
    D6_DEFINITION_BINDINGS
        .iter()
        .find(|row| {
            row.names.first().copied() == Some(name)
                // Five-name rows carry distinct uk and ukr projections;
                // the second name is still Ukrainian, unlike Sanskrit/English
                // peers which follow it. Keep both UI surfaces on one D6 word.
                || (row.names.len() == 5 && row.names.get(1).copied() == Some(name))
        })
        .map(|row| {
            DomainIdentity::D6(CoreD6::from_word(
                Bit6::new(row.bits).expect("generated D6 source word is exactly six bits"),
            ))
        })
}

/// True when a spelling appears only in a non-Ukrainian peer column of a D6 row.
/// Five-name rows have two distinct Ukrainian projections (`ук`, `укр`);
/// the four-name rows expose only the first Ukrainian spelling.
pub(crate) fn d6_non_uk_peer_source_name(name: &str) -> bool {
    D6_DEFINITION_BINDINGS.iter().any(|row| {
        let ukrainian_names = if row.names.len() == 5 { 2 } else { 1 };
        row.names
            .iter()
            .skip(ukrainian_names)
            .any(|peer| *peer == name)
    })
}

/// Binding-only D6 lookup for an already-evaluated Lisp definition.
///
/// A matching name does not make D6 callable. The caller may populate an
/// exact mechanism slot only when a real root callable value exists.
pub(crate) fn d6_binding_identity_for_definition(name: &str) -> Option<DomainIdentity> {
    D6_DEFINITION_BINDINGS
        .iter()
        .find(|row| row.names.contains(&name))
        .map(|row| {
            DomainIdentity::D6(CoreD6::from_word(
                Bit6::new(row.bits).expect("generated D6 binding is exactly six bits"),
            ))
        })
}

/// Binding-only D9 lookup for language-owned Lisp definitions.
/// D9 residency remains separate from callability: only a concrete evaluated
/// definition can populate the exact mechanism slot.
pub(crate) fn d9_binding_identity_for_definition(name: &str) -> Option<DomainIdentity> {
    D9_DEFINITION_BINDINGS
        .iter()
        .find(|row| row.names.contains(&name))
        .map(|row| {
            DomainIdentity::D9(CoreD9::from_word(
                Bit9::new(row.bits).expect("generated D9 binding is exactly nine bits"),
            ))
        })
}

/// Every owner-ratified name spelling of one exact D9 definition row.
///
/// The list is projection-only: it identifies the spellings that share the
/// coordinate, never a new admission. Callers may bind the already-evaluated
/// value under these names, mirroring the documented-peer step of the macro
/// library. An unknown or non-D9 identity yields an empty slice.
pub(crate) fn d9_definition_names(identity: DomainIdentity) -> &'static [&'static str] {
    let DomainIdentity::D9(word) = identity else {
        return &[];
    };
    D9_DEFINITION_BINDINGS
        .iter()
        .find(|row| row.bits == word.word().packed_bits())
        .map(|row| row.names)
        .unwrap_or(&[])
}

/// Resolve an owner-ratified **Ukrainian source head** from the D9 ladder.
/// Unlike binding-only aliases, only the first (укр/ук) spelling is eligible
/// for this executable-source path; the evaluator must still require a
/// separately admitted concrete D9 mechanism before dispatch. No W8 lookup.
pub(crate) fn d9_uk_source_identity(name: &str) -> Option<DomainIdentity> {
    D9_DEFINITION_BINDINGS
        .iter()
        .find(|row| row.names.first().copied() == Some(name))
        .map(|row| {
            DomainIdentity::D9(CoreD9::from_word(
                Bit9::new(row.bits).expect("ratified D9 source word has exactly nine bits"),
            ))
        })
}

/// Binding-only D10 lookup. A domain-table name maps to an exact coordinate,
/// but only evaluation of a concrete root callable populates its runtime slot.
pub(crate) fn d10_binding_identity_for_definition(name: &str) -> Option<DomainIdentity> {
    // lib/knowledge.lisp defines this concrete SENS closure, whose exact D10
    // word is ratified in lib/domains/d10.lisp. The generated Core4/epistemic
    // binding inventory does not cover that library. Bind its exact identity
    // only after the SENS DEFINE has actually evaluated; an arbitrary D10
    // resident still has no mechanism or callable slot.
    if name == "перетворити-клаузи-на-події-повідомлення" {
        return Some(DomainIdentity::D10(
            crate::DomainD10::new(0b0010000001).expect("ratified D10 knowledge closure"),
        ));
    }
    D10_DEFINITION_BINDINGS
        .iter()
        .find(|row| row.names.contains(&name))
        .map(|row| {
            DomainIdentity::D10(
                crate::DomainD10::new(row.bits).expect("generated D10 binding is exactly ten bits"),
            )
        })
}

/// Exact D6 definitions recorded by the generated binding table, plus current
/// D9/D10 identities, may be explicit D4 DEFINE targets. The target identity
/// alone does not grant callability: DEFINE still requires a concrete
/// closure/builtin, a root frame, and an empty exact runtime slot. D6 Core
/// operations are excluded from redefinition.
pub(crate) fn is_admitted_exact_definition_target(identity: DomainIdentity) -> bool {
    match identity {
        DomainIdentity::D6(_) if identity.core_operation().is_none() => D6_DEFINITION_BINDINGS
            .iter()
            .any(|binding| u16::from(binding.bits) == identity.packed_bits()),
        DomainIdentity::D9(_) | DomainIdentity::D10(_) => true,
        _ => false,
    }
}

/// Канонічний surface → domain маршрут читає тільки ратифіковану
/// exact-width проєкцію. Історичний SID/байт не визначає домен.
pub(crate) fn domain_identity_for_surface(name: &str) -> Option<CoreDomainIdentity> {
    direct_domain_identity_for_surface(name)
}

/// Resolve Ukrainian D1 predicate literals as values, never callable heads.
/// The bit and spelling come from the generated projection of `d1.lisp`;
/// keeping `source_routable = false` still prevents D1 from gaining a call route.
pub(crate) fn d1_value_for_uk_surface(name: &str) -> Option<DomainIdentity> {
    let mut matches = DOMAIN_SURFACE_ROWS.iter().filter(|row| {
        row.width == 1
            && row
                .surfaces
                .iter()
                .any(|surface| surface.namespace == "uk" && surface.name == name)
    });
    let row = matches.next()?;
    if matches.next().is_some() {
        return None;
    }
    let word = Bit1::new(row.bits)?;
    Some(DomainIdentity::from_source_word(BinarySourceWord::W1(word)))
}

/// D7 Ukrainian keyboard projection for the physical T5 text boundary.
/// No semantic role is inferred from equal bits in D2/another width.
pub(crate) fn d7_uk_keyboard_glyph(cell: u8) -> Option<&'static str> {
    D7_DISPLAY_ROWS
        .iter()
        .find(|row| row.bits == cell)
        .and_then(|row| row.uk)
}

pub(crate) fn d7_uk_keyboard_cell(glyph: &str) -> Option<u8> {
    D7_DISPLAY_ROWS
        .iter()
        .find(|row| row.uk == Some(glyph))
        .map(|row| row.bits)
}

pub(crate) fn surface_for_domain_identity(
    identity: DomainIdentity,
    namespace: &str,
) -> Option<&'static str> {
    // D7 is a sound/text *display* projection only. Its exact W7 coordinate
    // is already known; no reverse name lookup or callable status is inferred.
    if matches!(identity, DomainIdentity::D7(_)) {
        let row = D7_DISPLAY_ROWS
            .iter()
            .find(|row| u16::from(row.bits) == identity.packed_bits())?;
        return match namespace {
            "uk" => row.uk,
            "sa" => row.sa,
            "en" => row.en,
            "en-ipa" => row.en_ipa,
            _ => None,
        };
    }

    // Драбина Д8–Д10 має окремі ратифіковані таблиці. Не повертатися
    // до 256 комірок історичного SID8, коли просять повну «укр».
    // Це тільки проєкція значення: запис у binding не допускає виклик.
    if namespace == "ukr" {
        match identity {
            DomainIdentity::D8(_) => {
                // Лише 64 доведені селектори: їхні повні імена вже
                // побудовано за шляхом CAR/CDR, і вони точно відповідають Д8.
                return d8_selector_uk_index().iter().find_map(|(name, current)| {
                    (*current == identity && name.contains("-від-")).then_some(name.as_str())
                });
            }
            DomainIdentity::D9(word) => {
                return D9_DEFINITION_BINDINGS
                    .iter()
                    .find(|row| row.bits == word.word().packed_bits())
                    .and_then(|row| {
                        // Генератор згортає лише однакові ук/укр:
                        // 5 імен => окреме повне укр, інакше перше вже повне.
                        row.names
                            .get(if row.names.len() == 5 { 1 } else { 0 })
                            .copied()
                    });
            }
            DomainIdentity::D10(word) => {
                return D10_DEFINITION_BINDINGS
                    .iter()
                    .find(|row| row.bits == word.packed_bits())
                    .and_then(|row| {
                        row.names
                            .get(if row.names.len() == 5 { 1 } else { 0 })
                            .copied()
                    });
            }
            _ => {}
        }
    }

    DOMAIN_SURFACE_ROWS
        .iter()
        .find(|row| {
            usize::from(row.width) == identity.width()
                && u16::from(row.bits) == identity.packed_bits()
        })?
        .surfaces
        .iter()
        .find_map(|surface| (surface.namespace == namespace).then_some(surface.name))
}
pub(crate) fn semantic_id_bits(semantic_id: LegacyRegistrySlot) -> String {
    semantic_id.to_string()
}

fn live_rows() -> &'static [SemanticRow] {
    SEMANTIC_ROWS
}

pub(crate) fn admitted_semantic_ids() -> Vec<LegacyRegistrySlot> {
    live_rows()
        .iter()
        .filter_map(exact_identity_for_row)
        .collect()
}

fn insert_surface_mapping(
    index: &mut HashMap<&'static str, LegacyRegistrySlot>,
    surface: &'static str,
    semantic_id: LegacyRegistrySlot,
) {
    if let Some(previous) = index.insert(surface, semantic_id) {
        if previous != semantic_id {
            panic!(
                "generated semantic registry surface must be unique: {surface} maps to both {} and {}",
                semantic_id_bits(previous),
                semantic_id_bits(semantic_id)
            );
        }
    }
}

fn surface_index() -> &'static HashMap<&'static str, LegacyRegistrySlot> {
    static INDEX: OnceLock<HashMap<&'static str, LegacyRegistrySlot>> = OnceLock::new();
    INDEX.get_or_init(|| {
        let mut index = HashMap::new();
        for row in live_rows() {
            for surface in row.surfaces {
                if let Some(identity) = exact_identity_for_row(row) {
                    insert_surface_mapping(&mut index, surface.name, identity);
                }
            }
        }
        index
    })
}

pub(crate) fn admitted_semantic_id_for_surface(name: &str) -> Option<LegacyRegistrySlot> {
    surface_index().get(name).copied()
}

/// Human-facing lexical aliases of a language-defined macro. A historical
/// documentation row may identify spellings, never a modern domain coordinate.
/// Ambiguous aliases fail closed; neither the byte nor a row becomes callable.
pub(crate) fn lexical_peer_spellings_for_documented_name(name: &str) -> Vec<&'static str> {
    let mut matched: Option<&SemanticRow> = None;
    for row in SEMANTIC_ROWS {
        if row.surfaces.iter().any(|surface| surface.name == name) {
            if matched.is_some() {
                return Vec::new();
            }
            matched = Some(row);
        }
    }
    let Some(row) = matched else {
        return Vec::new();
    };
    let mut names: Vec<_> = row.surfaces.iter().map(|surface| surface.name).collect();
    names.sort_unstable();
    names.dedup();
    names
}

fn stable_surfaces_from_index(
    index: &HashMap<&'static str, LegacyRegistrySlot>,
    semantic_id: LegacyRegistrySlot,
) -> Vec<&'static str> {
    let mut surfaces = index
        .iter()
        .filter_map(|(surface, mapped_id)| (*mapped_id == semantic_id).then_some(*surface))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces
}

fn admitted_surfaces_from_rows(
    rows: &[SemanticRow],
    semantic_id: LegacyRegistrySlot,
) -> Vec<&'static str> {
    let mut surfaces = rows
        .iter()
        .find(|row| exact_identity_for_row(row) == Some(semantic_id))
        .into_iter()
        .flat_map(|row| row.surfaces.iter().map(|surface| surface.name))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces
}

pub(crate) fn semantic_id_for_surface(name: &str) -> Option<LegacyRegistrySlot> {
    admitted_semantic_id_for_surface(name)
}

pub(crate) fn stable_surfaces_for_semantic_id(
    semantic_id: LegacyRegistrySlot,
) -> Vec<&'static str> {
    stable_surfaces_from_index(surface_index(), semantic_id)
}

pub(crate) fn admitted_surfaces_for_semantic_id(
    semantic_id: LegacyRegistrySlot,
) -> Vec<&'static str> {
    admitted_surfaces_from_rows(live_rows(), semantic_id)
}

pub(crate) fn admitted_surfaces_with_namespace_for_semantic_id(
    semantic_id: LegacyRegistrySlot,
) -> Vec<(&'static str, &'static str)> {
    let mut surfaces = live_rows()
        .iter()
        .find(|row| exact_identity_for_row(row) == Some(semantic_id))
        .into_iter()
        .flat_map(|row| row.surfaces.iter().map(|s| (s.namespace, s.name)))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces
}
