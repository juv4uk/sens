//! Canonical exact-domain occupancy and callability.
//!
//! Authority is the ratified exact-width corpus and its referenced laws.
//! This module deliberately contains no legacy Sens8/Sid8/Function8 lookup,
//! no human surface names, and no byte-to-domain inference.

use crate::CoreDomainIdentity;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum DomainStatus {
    Admitted,
    Generated,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum DomainRole {
    Foundation,
    SelectorRoot,
    Bootstrap,
    Selector,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct DomainEntry {
    pub identity: CoreDomainIdentity,
    pub status: DomainStatus,
    pub role: DomainRole,
    pub family: &'static str,
    pub authority_ref: &'static str,
    callable: bool,
}

impl DomainEntry {
    pub const fn callable(self) -> bool {
        self.callable
    }
}

const fn entry(
    identity: CoreDomainIdentity,
    status: DomainStatus,
    role: DomainRole,
    family: &'static str,
    authority_ref: &'static str,
    callable: bool,
) -> DomainEntry {
    DomainEntry {
        identity,
        status,
        role,
        family,
        authority_ref,
        callable,
    }
}

/// Resolve one canonical Core identity through exact-domain law only.
///
/// Presence here means occupied by the current ratified/generated corpus.
/// It does not imply that an execution mechanism is currently installed.
pub(crate) fn lookup(identity: CoreDomainIdentity) -> Option<DomainEntry> {
    match identity {
        CoreDomainIdentity::D3(word) => {
            let bits = word.word().packed_bits();
            let (role, family, callable) = match bits {
                0b000 => (DomainRole::Foundation, "foundation", false),
                0b101 | 0b110 => (DomainRole::SelectorRoot, "selector", true),
                0b001 | 0b010 | 0b011 | 0b100 | 0b111 => {
                    (DomainRole::Foundation, "foundation", true)
                }
                _ => return None,
            };
            Some(entry(
                identity,
                DomainStatus::Admitted,
                role,
                family,
                "#2151/#2170",
                callable,
            ))
        }
        CoreDomainIdentity::D4(word) => {
            let bits = word.word().packed_bits();
            match bits {
                0b0000 | 0b0001 | 0b0010 | 0b0011 | 0b0100 | 0b0110 | 0b0111
                | 0b1000 | 0b1110 | 0b1111 => Some(entry(
                    identity,
                    DomainStatus::Admitted,
                    DomainRole::Bootstrap,
                    "bootstrap",
                    "#2151/#2170",
                    true,
                )),
                0b1010 | 0b1011 | 0b1100 | 0b1101 => Some(entry(
                    identity,
                    DomainStatus::Generated,
                    DomainRole::Selector,
                    "selector",
                    "#2151/#2170 + #1968/#2329",
                    true,
                )),
                0b0101 | 0b1001 => None,
                _ => None,
            }
        }
        CoreDomainIdentity::D5(word) => {
            let bits = word.word().packed_bits();
            if (0b10100..=0b11011).contains(&bits) {
                Some(entry(
                    identity,
                    DomainStatus::Generated,
                    DomainRole::Selector,
                    "selector",
                    "#2175/#2329 + #1968/#2329",
                    true,
                ))
            } else {
                None
            }
        }
        CoreDomainIdentity::D6(_) => None,
    }
}

pub(crate) fn is_occupied(identity: CoreDomainIdentity) -> bool {
    lookup(identity).is_some()
}

pub(crate) fn is_callable(identity: CoreDomainIdentity) -> bool {
    lookup(identity).is_some_and(DomainEntry::callable)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bija3, Bit3, Bit4, Bit5, Bit6, CoreD4, CoreD5, CoreD6};

    fn d3(bits: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(bits).unwrap()))
    }

    fn d4(bits: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(bits).unwrap()))
    }

    fn d5(bits: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(bits).unwrap()))
    }

    fn d6(bits: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D6(CoreD6::from_word(Bit6::new(bits).unwrap()))
    }

    #[test]
    fn d3_occupancy_is_complete_but_empty_structure_is_not_callable() {
        for bits in 0..=0b111 {
            assert!(is_occupied(d3(bits)), "D3 {bits:03b}");
        }
        assert!(!is_callable(d3(0b000)));
        for bits in 1..=0b111 {
            assert!(is_callable(d3(bits)), "D3 {bits:03b}");
        }
    }

    #[test]
    fn d4_occupancy_matches_ratified_14_of_16_map() {
        for bits in 0..=0b1111 {
            let expected = !matches!(bits, 0b0101 | 0b1001);
            assert_eq!(is_occupied(d4(bits)), expected, "D4 {bits:04b}");
            assert_eq!(is_callable(d4(bits)), expected, "D4 {bits:04b}");
        }
    }

    #[test]
    fn d5_contains_only_the_generated_selector_family() {
        for bits in 0..=0b1_1111 {
            let expected = (0b10100..=0b11011).contains(&bits);
            assert_eq!(is_occupied(d5(bits)), expected, "D5 {bits:05b}");
            assert_eq!(is_callable(d5(bits)), expected, "D5 {bits:05b}");
        }
    }

    #[test]
    fn d6_has_no_occupied_cells_in_the_current_exact_width_corpus() {
        for bits in 0..=0b11_1111 {
            assert!(!is_occupied(d6(bits)), "D6 {bits:06b}");
            assert!(!is_callable(d6(bits)), "D6 {bits:06b}");
        }
    }

    #[test]
    fn equal_payloads_in_different_domains_do_not_share_occupancy() {
        assert!(is_occupied(d3(0b001)));
        assert!(is_occupied(d4(0b0001)));
        assert!(!is_occupied(d5(0b00001)));
        assert!(!is_occupied(d6(0b000001)));
    }
}
