//! Explicit bridges from ratified exact-width domain roles to remaining
//! legacy evaluator mechanisms.
//!
//! This module is intentionally role-aware. It is not a numeric widening
//! layer: D3 011 is COND and therefore maps to legacy 00000111, while D3 111
//! is EQ and maps to legacy 00000011. Blind zero-padding is forbidden.

use crate::{Bija3, Bit3, DomainWord, SemanticRef, Sens8};

fn d3(bits: u8) -> Bija3 {
    Bija3::from_word(Bit3::new(bits).expect("D3 coordinate must fit three bits"))
}

/// Canonical D3 role corresponding to an admitted historical mechanism.
pub(crate) fn d3_role_for_legacy(sid: Sens8) -> Option<Bija3> {
    let bits = match sid.packed_byte() {
        0b0000_0001 => 0b001, // QUOTE
        0b0000_0010 => 0b010, // ATOM
        0b0000_0011 => 0b111, // EQ
        0b0000_0100 => 0b100, // CONS
        0b0000_0101 => 0b101, // CAR
        0b0000_0110 => 0b110, // CDR
        0b0000_0111 => 0b011, // COND
        _ => return None,
    };
    Some(d3(bits))
}

/// Convert a historical role reference to the canonical exact-width identity
/// where D3 has already been ratified. Other legacy mechanisms remain explicit
/// Legacy8 until their owning domains receive an equally explicit bridge.
pub(crate) fn canonical_role_for_legacy(sid: Sens8) -> SemanticRef {
    match d3_role_for_legacy(sid) {
        Some(word) => SemanticRef::domain(DomainWord::D3(word)),
        None => SemanticRef::legacy8(sid),
    }
}

/// Select a remaining historical evaluator mechanism for a canonical identity.
///
/// This is a semantic role table, not a bit-width conversion. D1/D2 and D4+
/// deliberately fail closed here until their own execution bridge is ratified.
pub(crate) fn legacy_mechanism_for(identity: SemanticRef) -> Option<Sens8> {
    match identity {
        SemanticRef::Legacy8(sid) => Some(sid),
        SemanticRef::Domain(DomainWord::D3(word)) => {
            let byte = match word.word().packed_bits() {
                0b001 => 0b0000_0001, // QUOTE
                0b010 => 0b0000_0010, // ATOM
                0b011 => 0b0000_0111, // COND
                0b100 => 0b0000_0100, // CONS
                0b101 => 0b0000_0101, // CAR
                0b110 => 0b0000_0110, // CDR
                0b111 => 0b0000_0011, // EQ
                0b000 => return None,  // ground/NIL has no Function8 mechanism
                _ => unreachable!("Bija3 cannot exceed three bits"),
            };
            Some(Sens8::from_packed_byte(byte))
        }
        SemanticRef::Domain(_) => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn d3_bridge_is_role_aware_not_zero_padding() {
        let cond = SemanticRef::domain(DomainWord::D3(d3(0b011)));
        let eq = SemanticRef::domain(DomainWord::D3(d3(0b111)));

        assert_eq!(
            legacy_mechanism_for(cond),
            Some(Sens8::from_packed_byte(0b0000_0111))
        );
        assert_eq!(
            legacy_mechanism_for(eq),
            Some(Sens8::from_packed_byte(0b0000_0011))
        );
        assert_ne!(
            legacy_mechanism_for(cond),
            Some(Sens8::from_packed_byte(0b0000_0011)),
            "COND must never be inferred by zero-padding 011"
        );
        assert_ne!(
            legacy_mechanism_for(eq),
            Some(Sens8::from_packed_byte(0b0000_0111)),
            "EQ must never be inferred by zero-padding 111"
        );
    }

    #[test]
    fn d3_ground_has_no_callable_legacy_projection() {
        let ground = SemanticRef::domain(DomainWord::D3(d3(0)));
        assert_eq!(legacy_mechanism_for(ground), None);
    }

    #[test]
    fn legacy_d3_roles_canonicalize_to_exact_width() {
        for (legacy, d3_bits) in [
            (0b0000_0001, 0b001),
            (0b0000_0010, 0b010),
            (0b0000_0011, 0b111),
            (0b0000_0100, 0b100),
            (0b0000_0101, 0b101),
            (0b0000_0110, 0b110),
            (0b0000_0111, 0b011),
        ] {
            let identity = canonical_role_for_legacy(Sens8::from_packed_byte(legacy));
            assert_eq!(identity.exact_width(), 3);
            assert_eq!(identity.packed_bits(), d3_bits);
            assert_eq!(
                legacy_mechanism_for(identity),
                Some(Sens8::from_packed_byte(legacy))
            );
        }
    }

    #[test]
    fn unrelated_legacy_mechanism_stays_legacy8() {
        let sid = Sens8::from_packed_byte(0b0000_1100);
        assert_eq!(canonical_role_for_legacy(sid), SemanticRef::legacy8(sid));
    }
}
