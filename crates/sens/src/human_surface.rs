//! Current human-language surfaces over exact D1-D8 domain identity.
//!
//! This first vertical slice admits the ratified D3 foundation directly:
//!
//! human spelling -> CoreDomainIdentity::D3
//!
//! No historical SID8/SENS8/Function8 value is constructed.  Human spellings
//! are projections only; canonical serialization continues to carry the exact
//! domain-qualified identity.

use crate::{Bija3, Bit3, CoreDomainIdentity};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SurfaceLanguage {
    Ukrainian,
    Sanskrit,
}

#[derive(Clone, Copy)]
struct D3SurfaceRow {
    bits: u8,
    uk: &'static str,
    sa: &'static str,
}

// Vocabulary donors are the already-audited surface documents.  The table owns
// spelling projection only; D3 semantics/occupancy remain owned by the language
// contract and DomainIdentity.
const D3_SURFACES: [D3SurfaceRow; 7] = [
    D3SurfaceRow { bits: 0b001, uk: "як-є",       sa: "svarūpa" },
    D3SurfaceRow { bits: 0b010, uk: "атом?",      sa: "aṇu" },
    D3SurfaceRow { bits: 0b011, uk: "за-умовою",  sa: "anukrama" },
    D3SurfaceRow { bits: 0b100, uk: "сполучити",  sa: "saṃyuj" },
    D3SurfaceRow { bits: 0b101, uk: "перше",      sa: "ādi" },
    D3SurfaceRow { bits: 0b110, uk: "решта",      sa: "śeṣa" },
    D3SurfaceRow { bits: 0b111, uk: "тотожне?",   sa: "abheda" },
];

fn d3_identity(bits: u8) -> CoreDomainIdentity {
    let word = Bit3::new(bits).expect("D3 surface table contains exact three-bit payloads");
    CoreDomainIdentity::D3(Bija3::from_word(word))
}

/// Resolve a current human spelling directly into exact Core domain identity.
///
/// This table intentionally contains no English middleman and no legacy byte
/// identity.  Unknown spellings stay unresolved so ordinary identifiers keep
/// their normal lexical path.
pub fn resolve_human_surface(name: &str) -> Option<CoreDomainIdentity> {
    D3_SURFACES
        .iter()
        .find(|row| row.uk == name || row.sa == name)
        .map(|row| d3_identity(row.bits))
}

/// Render one admitted current surface from exact domain identity.
///
/// Only the first current-native D3 slice is admitted here.  Other domains
/// return None until their residents receive explicit human-surface rows.
pub fn render_human_surface(
    language: SurfaceLanguage,
    identity: CoreDomainIdentity,
) -> Option<&'static str> {
    let CoreDomainIdentity::D3(word) = identity else {
        return None;
    };
    let bits = word.word().packed_bits();
    D3_SURFACES
        .iter()
        .find(|row| row.bits == bits)
        .map(|row| match language {
            SurfaceLanguage::Ukrainian => row.uk,
            SurfaceLanguage::Sanskrit => row.sa,
        })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeSet;

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
        for row in D3_SURFACES {
            let identity = d3_identity(row.bits);
            for language in [SurfaceLanguage::Ukrainian, SurfaceLanguage::Sanskrit] {
                let spelling =
                    render_human_surface(language, identity).expect("D3 spelling renders");
                assert_eq!(resolve_human_surface(spelling), Some(identity));
            }
        }
    }

    #[test]
    fn current_d3_spellings_are_collision_free_and_unknowns_fail_closed() {
        let mut seen = BTreeSet::new();
        for row in D3_SURFACES {
            assert!(seen.insert(row.uk), "duplicate UK/SA spelling {}", row.uk);
            assert!(seen.insert(row.sa), "duplicate UK/SA spelling {}", row.sa);
        }
        assert_eq!(resolve_human_surface("невідоме"), None);
        assert_eq!(resolve_human_surface("unknown"), None);
        // Older donor spelling remains outside the current-native table until
        // it is explicitly admitted as a compatibility alias.
        assert_eq!(resolve_human_surface("krama"), None);
    }

    #[test]
    fn binary_uk_and_sa_sources_lower_to_byte_identical_domain_wire() {
        const BINARY: &str =
            "10 111 00 10 001 00 000 01 00 10 001 00 000 01 01";
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
                    .windows(spelling.as_bytes().len())
                    .any(|window| window == spelling.as_bytes()),
                "human surface spelling leaked into canonical wire: {spelling}"
            );
        }
    }
}
