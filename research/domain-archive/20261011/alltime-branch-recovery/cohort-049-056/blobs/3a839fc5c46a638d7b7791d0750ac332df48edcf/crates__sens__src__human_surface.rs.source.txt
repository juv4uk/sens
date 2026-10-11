//! Human-language projections over exact domain identity.
//!
//! Authority for spelling projection: `knowledge/domain-surface-registry.lisp`.
//! Semantic authority remains the ratified domain laws.  The generated table
//! contains exact width + exact bits + surface spellings and no historical
//! historical flat-byte semantic identity.
//!
//! This first vertical slice admits the seven surfaced D3 residents.

use crate::{Bija3, Bit3, CoreDomainIdentity};

mod generated {
    include!("domain_surface_registry_generated.rs");
}

use generated::DOMAIN_SURFACE_ROWS;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SurfaceLanguage {
    Ukrainian,
    Sanskrit,
}

fn identity_for_row(width: u8, bits: u8) -> Option<CoreDomainIdentity> {
    match width {
        0b11 => Bit3::new(bits)
            .map(Bija3::from_word)
            .map(CoreDomainIdentity::D3),
        _ => None,
    }
}

/// Resolve one admitted human/symbolic spelling directly to exact domain identity.
///
/// There is no English semantic middleman and no legacy byte round-trip here.
/// Unknown spellings remain unresolved so ordinary lexical identifiers keep
/// their normal path.
pub fn resolve_human_surface(name: &str) -> Option<CoreDomainIdentity> {
    DOMAIN_SURFACE_ROWS.iter().find_map(|row| {
        let identity = identity_for_row(row.width, row.bits)?;
        row.surfaces
            .iter()
            .any(|surface| surface.name == name)
            .then_some(identity)
    })
}

/// Render an admitted Ukrainian or Sanskrit spelling from exact identity.
///
/// This is presentation only; rendering never changes the canonical identity.
pub fn render_human_surface(
    language: SurfaceLanguage,
    identity: CoreDomainIdentity,
) -> Option<&'static str> {
    let namespace = match language {
        SurfaceLanguage::Ukrainian => "ук",
        SurfaceLanguage::Sanskrit => "sa",
    };

    DOMAIN_SURFACE_ROWS.iter().find_map(|row| {
        if identity_for_row(row.width, row.bits) != Some(identity) {
            return None;
        }
        row.surfaces
            .iter()
            .find_map(|surface| (surface.namespace == namespace).then_some(surface.name))
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeMap;

    fn bits(identity: CoreDomainIdentity) -> (usize, u8) {
        (identity.width(), identity.packed_bits())
    }

    #[test]
    fn uk_and_sa_resolve_directly_to_the_same_exact_d3_identity() {
        let cases = [
            ("як-є", "svarūpa", 0b001),
            ("атом?", "aṇu", 0b010),
            ("за-умовою", "anukrama", 0b011),
            ("сполучити", "saṃyuj", 0b100),
            ("перше", "ādi", 0b101),
            ("решта", "śeṣa", 0b110),
            ("тотожне?", "abheda", 0b111),
        ];
        for (uk, sa, expected) in cases {
            let uk_id = resolve_human_surface(uk).expect("UK D3 spelling resolves");
            let sa_id = resolve_human_surface(sa).expect("SA D3 spelling resolves");
            assert_eq!(bits(uk_id), (3, expected));
            assert_eq!(uk_id, sa_id);
        }
    }

    #[test]
    fn domain_identity_round_trips_through_each_current_surface() {
        for row in DOMAIN_SURFACE_ROWS {
            let identity =
                identity_for_row(row.width, row.bits).expect("current row has exact identity");
            for language in [SurfaceLanguage::Ukrainian, SurfaceLanguage::Sanskrit] {
                let spelling =
                    render_human_surface(language, identity).expect("D3 spelling renders");
                assert_eq!(resolve_human_surface(spelling), Some(identity));
            }
        }
    }

    #[test]
    fn current_d3_spellings_are_collision_free_and_unknowns_fail_closed() {
        let mut seen = BTreeMap::new();
        for row in DOMAIN_SURFACE_ROWS {
            let identity =
                identity_for_row(row.width, row.bits).expect("current row has exact identity");
            for surface in row.surfaces {
                if let Some(previous) = seen.insert(surface.name, identity) {
                    assert_eq!(
                        previous, identity,
                        "surface spelling maps to two exact identities: {}",
                        surface.name
                    );
                }
            }
        }
        assert_eq!(resolve_human_surface("невідоме"), None);
        assert_eq!(resolve_human_surface("unknown"), None);
        assert_eq!(resolve_human_surface("krama"), None);
    }

    #[test]
    fn binary_uk_and_sa_sources_lower_to_byte_identical_domain_wire() {
        const BINARY: &str = "10 111 00 10 001 00 000 01 00 10 001 00 000 01 01";
        const UK: &str = "(тотожне? (як-є ()) (як-є ()))";
        const SA: &str = "(abheda (svarūpa ()) (svarūpa ()))";

        let binary =
            crate::lower_program(&crate::parse_canonical_binary(BINARY).expect("binary parses"));
        let uk = crate::lower_program(&crate::parse(UK).expect("UK surface parses"));
        let sa = crate::lower_program(&crate::parse(SA).expect("SA surface parses"));

        let binary_wire = crate::wire_encode_program(&binary);
        assert_eq!(crate::wire_encode_program(&uk), binary_wire);
        assert_eq!(crate::wire_encode_program(&sa), binary_wire);

        for spelling in ["тотожне?", "як-є", "abheda", "svarūpa"] {
            assert!(
                !binary_wire
                    .windows(spelling.len())
                    .any(|window| window == spelling.as_bytes()),
                "human surface spelling leaked into canonical wire: {spelling}"
            );
        }
    }
}
