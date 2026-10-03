//! Canonical Core domain residents.
//!
//! This module is intentionally domain-first.  It does not import Sens8,
//! Sid8, the flat 256-row semantic registry, or any surface spelling.
//!
//! A resident exists because its exact domain and admitted/generated law say
//! that it exists.  Surface names and legacy byte projections are downstream
//! metadata only.

use crate::{Bija3, Bit3, Bit4, CoreD4, CoreDomainIdentity};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum ResidentStatus {
    Admitted,
    Generated,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum ResidentLaw {
    D3Foundation,
    D4Bootstrap,
    SelectorComposition,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum SelectorProjection {
    First,
    Rest,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct SelectorComposition {
    /// Outer/root D3 projection.
    pub root: SelectorProjection,
    /// One generated D4 suffix projection, applied to the input before root.
    pub suffix: SelectorProjection,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct DomainResident {
    pub identity: CoreDomainIdentity,
    pub status: ResidentStatus,
    pub law: ResidentLaw,
}

const fn d3(raw: u8) -> CoreDomainIdentity {
    CoreDomainIdentity::D3(Bija3::from_word(match Bit3::new(raw) {
        Some(word) => word,
        None => panic!("invalid D3 resident"),
    }))
}

const fn d4(raw: u8) -> CoreDomainIdentity {
    CoreDomainIdentity::D4(CoreD4::from_word(match Bit4::new(raw) {
        Some(word) => word,
        None => panic!("invalid D4 resident"),
    }))
}

/// Canonical resident lookup for the first domain-first migration slice.
///
/// D3 is the complete ratified foundation. D4 is complete except its two
/// ratified unallocated holes 0101 and 1001. D5/D6 are deliberately added by
/// their own owner-map/runtime-admission slice rather than reconstructed from
/// the legacy Function8 table here.
pub(crate) const fn resident(identity: CoreDomainIdentity) -> Option<DomainResident> {
    match identity {
        CoreDomainIdentity::D3(_) => Some(DomainResident {
            identity,
            status: ResidentStatus::Admitted,
            law: ResidentLaw::D3Foundation,
        }),
        CoreDomainIdentity::D4(word) => match word.word().packed_bits() {
            0b0101 | 0b1001 => None,
            0b1010 | 0b1011 | 0b1100 | 0b1101 => Some(DomainResident {
                identity,
                status: ResidentStatus::Generated,
                law: ResidentLaw::SelectorComposition,
            }),
            _ => Some(DomainResident {
                identity,
                status: ResidentStatus::Admitted,
                law: ResidentLaw::D4Bootstrap,
            }),
        },
        CoreDomainIdentity::D5(_) | CoreDomainIdentity::D6(_) => None,
    }
}

pub(crate) const fn selector_composition(
    identity: CoreDomainIdentity,
) -> Option<SelectorComposition> {
    let CoreDomainIdentity::D4(word) = identity else {
        return None;
    };
    match word.word().packed_bits() {
        0b1010 => Some(SelectorComposition {
            root: SelectorProjection::First,
            suffix: SelectorProjection::First,
        }),
        0b1011 => Some(SelectorComposition {
            root: SelectorProjection::First,
            suffix: SelectorProjection::Rest,
        }),
        0b1100 => Some(SelectorComposition {
            root: SelectorProjection::Rest,
            suffix: SelectorProjection::First,
        }),
        0b1101 => Some(SelectorComposition {
            root: SelectorProjection::Rest,
            suffix: SelectorProjection::Rest,
        }),
        _ => None,
    }
}

pub(crate) fn d3_d4_residents() -> Vec<DomainResident> {
    let mut out = Vec::with_capacity(22);
    for raw in 0..=0b111 {
        out.push(resident(d3(raw)).expect("every D3 word is resident"));
    }
    for raw in 0..=0b1111 {
        let identity = d4(raw);
        if let Some(row) = resident(identity) {
            out.push(row);
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn d3_is_complete_and_d4_has_only_the_two_ratified_holes() {
        let rows = d3_d4_residents();
        assert_eq!(rows.iter().filter(|row| row.identity.width() == 3).count(), 8);
        assert_eq!(rows.iter().filter(|row| row.identity.width() == 4).count(), 14);

        assert!(resident(d4(0b0101)).is_none());
        assert!(resident(d4(0b1001)).is_none());
    }

    #[test]
    fn d4_selector_descendants_are_generated_by_law_not_flat_slots() {
        for raw in [0b1010, 0b1011, 0b1100, 0b1101] {
            let row = resident(d4(raw)).unwrap();
            assert_eq!(row.status, ResidentStatus::Generated);
            assert_eq!(row.law, ResidentLaw::SelectorComposition);
            assert!(selector_composition(row.identity).is_some());
        }
    }
}
