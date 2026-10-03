//! Canonical callable-domain registry.
//!
//! Generated migration snapshot from the ratified exact-width D3/D4 corpus and
//! the full D5/D6 owner maps. Historical 8-bit registry rows are consulted only
//! to project already-existing surface spellings and temporary backend mechanisms.
//! They do not define domain identity or occupancy.

use crate::{Bija3, Bit3, Bit4, Bit5, Bit6, CoreD4, CoreD5, CoreD6, CoreDomainIdentity};

#[derive(Clone, Copy, Debug)]
pub(crate) struct DomainOwnerRow {
    pub width: u8,
    pub bits: u8,
    pub legacy_mechanism: Option<u8>,
    pub surfaces: &'static [&'static str],
}

pub(crate) const DOMAIN_OWNER_ROWS: &[DomainOwnerRow] = &[
    DomainOwnerRow { width: 3, bits: 0b001, legacy_mechanism: Some(0b00000001), surfaces: &["quote", "як-є", "як-є", "svarūpa", "'"] },
    DomainOwnerRow { width: 3, bits: 0b010, legacy_mechanism: Some(0b00000010), surfaces: &["atom?", "атом?", "атом?", "aṇu", ".?"] },
    DomainOwnerRow { width: 3, bits: 0b011, legacy_mechanism: Some(0b00000111), surfaces: &["cond", "за-умовою", "за-умовою", "anukrama", "?:"] },
    DomainOwnerRow { width: 3, bits: 0b100, legacy_mechanism: Some(0b00000100), surfaces: &["cons", "сполучити", "сполучити", "saṃyuj"] },
    DomainOwnerRow { width: 3, bits: 0b101, legacy_mechanism: Some(0b00000101), surfaces: &["car", "перше", "перше", "ādi", ":п"] },
    DomainOwnerRow { width: 3, bits: 0b110, legacy_mechanism: Some(0b00000110), surfaces: &["cdr", "решта", "решта", "śeṣa", ":р"] },
    DomainOwnerRow { width: 3, bits: 0b111, legacy_mechanism: Some(0b00000011), surfaces: &["eq?", "тотожне?", "тотожне?", "abheda", "=?"] },
    DomainOwnerRow { width: 4, bits: 0b0000, legacy_mechanism: Some(0b10101111), surfaces: &["apply", "застосувати", "застосувати"] },
    DomainOwnerRow { width: 4, bits: 0b0001, legacy_mechanism: Some(0b01001101), surfaces: &["eval", "обчислити", "обчислити", "vicāraṇa"] },
    DomainOwnerRow { width: 4, bits: 0b0010, legacy_mechanism: Some(0b00001000), surfaces: &["lambda", "функція", "функція"] },
    DomainOwnerRow { width: 4, bits: 0b0011, legacy_mechanism: Some(0b00001001), surfaces: &["define", "визначити", "визначити"] },
    DomainOwnerRow { width: 4, bits: 0b0100, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 4, bits: 0b0110, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 4, bits: 0b0111, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 4, bits: 0b1000, legacy_mechanism: Some(0b00100111), surfaces: &["list", "список", "список", "śreṇī"] },
    DomainOwnerRow { width: 4, bits: 0b1010, legacy_mechanism: Some(0b00110011), surfaces: &["caar", "перше-від-першого"] },
    DomainOwnerRow { width: 4, bits: 0b1011, legacy_mechanism: Some(0b00110100), surfaces: &["cadr", "перше-від-решти"] },
    DomainOwnerRow { width: 4, bits: 0b1100, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 4, bits: 0b1101, legacy_mechanism: Some(0b00110101), surfaces: &["cddr", "решта-від-решти"] },
    DomainOwnerRow { width: 4, bits: 0b1110, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 4, bits: 0b1111, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b00000, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b00001, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b00010, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b00011, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b00100, legacy_mechanism: Some(0b10101010), surfaces: &["label", "мітка", "мітка"] },
    DomainOwnerRow { width: 5, bits: 0b00101, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b00110, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b00111, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b01000, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b01001, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b01010, legacy_mechanism: Some(0b00001100), surfaces: &["plus", "додати", "додати", "yoga", "+"] },
    DomainOwnerRow { width: 5, bits: 0b01011, legacy_mechanism: Some(0b00001101), surfaces: &["difference", "відняти", "відняти", "viyoga", "-"] },
    DomainOwnerRow { width: 5, bits: 0b01100, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b01101, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b01110, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b01111, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b10000, legacy_mechanism: Some(0b00101001), surfaces: &["append", "приєднати", "приєднати", "saṅkalana"] },
    DomainOwnerRow { width: 5, bits: 0b10001, legacy_mechanism: Some(0b00101010), surfaces: &["reverse", "зворот", "зворот", "viloma"] },
    DomainOwnerRow { width: 5, bits: 0b10010, legacy_mechanism: Some(0b00001110), surfaces: &["times", "помножити", "помножити", "guṇana", "*"] },
    DomainOwnerRow { width: 5, bits: 0b10011, legacy_mechanism: Some(0b00010100), surfaces: &["quotient", "частка", "частка", "bhāga"] },
    DomainOwnerRow { width: 5, bits: 0b10100, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b10101, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b10110, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b10111, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b11000, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b11001, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b11010, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b11011, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b11100, legacy_mechanism: Some(0b00101101), surfaces: &["assoc", "знайти-за-ключем", "знайти-за-ключем", "saṃbandha"] },
    DomainOwnerRow { width: 5, bits: 0b11101, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b11110, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b11111, legacy_mechanism: Some(0b10101100), surfaces: &["subst", "замінити", "замінити"] },
    DomainOwnerRow { width: 6, bits: 0b000000, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b000001, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b000010, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b000011, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b000100, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b000101, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b000110, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b000111, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b001000, legacy_mechanism: Some(0b10011100), surfaces: &["let", "нехай", "нехай"] },
    DomainOwnerRow { width: 6, bits: 0b001001, legacy_mechanism: Some(0b10011101), surfaces: &["let*", "нехай*", "нехай-послідовно"] },
    DomainOwnerRow { width: 6, bits: 0b001010, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b001011, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b001100, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b001101, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b001110, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b001111, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b010000, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b010001, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b010010, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b010011, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b010100, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b010101, legacy_mechanism: Some(0b00010000), surfaces: &["abs", "модуль", "модуль", "rūpa"] },
    DomainOwnerRow { width: 6, bits: 0b010110, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b010111, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b011000, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b011001, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b011010, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b011011, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b011100, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b011101, legacy_mechanism: Some(0b00010001), surfaces: &["min", "найменше", "найменше", "alpatara"] },
    DomainOwnerRow { width: 6, bits: 0b011110, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b011111, legacy_mechanism: Some(0b00010010), surfaces: &["max", "найбільше", "найбільше", "brhattara"] },
    DomainOwnerRow { width: 6, bits: 0b100000, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b100001, legacy_mechanism: Some(0b00101000), surfaces: &["length", "довжина", "довжина", "pramāṇa"] },
    DomainOwnerRow { width: 6, bits: 0b100010, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b100011, legacy_mechanism: Some(0b00101011), surfaces: &["nth", "елемент-списку-за-індексом", "елемент-списку-за-індексом", "kramāṅka"] },
    DomainOwnerRow { width: 6, bits: 0b100100, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b100101, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b100110, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b100111, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101000, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101001, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101010, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101011, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101100, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101101, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101110, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101111, legacy_mechanism: Some(0b00110110), surfaces: &["cadddr", "перше-після-трьох-решт"] },
    DomainOwnerRow { width: 6, bits: 0b110000, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b110001, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b110010, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b110011, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b110100, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b110101, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b110110, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b110111, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b111000, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b111001, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b111010, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b111011, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b111100, legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b111101, legacy_mechanism: Some(0b10101110), surfaces: &["maplist", "відобразити-залишки", "відобразити-залишки"] },
    DomainOwnerRow { width: 6, bits: 0b111110, legacy_mechanism: Some(0b10101101), surfaces: &["sublis", "підставити-пари", "підставити-пари"] },
    DomainOwnerRow { width: 6, bits: 0b111111, legacy_mechanism: None, surfaces: &[] },
];

pub(crate) fn identity(width: u8, bits: u8) -> Option<CoreDomainIdentity> {
    match width {
        3 => Some(Bija3::from_word(Bit3::new(bits)?).into()),
        4 => Some(CoreD4::from_word(Bit4::new(bits)?).into()),
        5 => Some(CoreD5::from_word(Bit5::new(bits)?).into()),
        6 => Some(CoreD6::from_word(Bit6::new(bits)?).into()),
        _ => None,
    }
}

pub(crate) fn identity_for_surface(surface: &str) -> Option<CoreDomainIdentity> {
    DOMAIN_OWNER_ROWS
        .iter()
        .find(|row| row.surfaces.contains(&surface))
        .and_then(|row| identity(row.width, row.bits))
}

pub(crate) fn row_for_identity(identity_key: CoreDomainIdentity) -> Option<&'static DomainOwnerRow> {
    DOMAIN_OWNER_ROWS.iter().find(|row| {
        identity(row.width, row.bits).is_some_and(|candidate| candidate == identity_key)
    })
}

pub(crate) fn legacy_mechanism_for(identity_key: CoreDomainIdentity) -> Option<u8> {
    row_for_identity(identity_key).and_then(|row| row.legacy_mechanism)
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn all_ratified_callable_owner_coordinates_are_unique() {
        assert_eq!(DOMAIN_OWNER_ROWS.len(), 117);
        let mut seen = std::collections::HashSet::new();
        for row in DOMAIN_OWNER_ROWS {
            assert!(seen.insert((row.width, row.bits)), "duplicate D{} {:b}", row.width, row.bits);
            assert!(identity(row.width, row.bits).is_some());
        }
    }

    #[test]
    fn migrated_surfaces_resolve_domain_first() {
        for surface in ["atom?", "eq?", "car", "lambda", "plus", "+", "let", "maplist"] {
            assert!(identity_for_surface(surface).is_some(), "{surface}");
        }
    }

    #[test]
    fn equal_payloads_in_different_domains_never_alias() {
        let d3 = identity(3, 1).unwrap();
        let d4 = identity(4, 1).unwrap();
        let d5 = identity(5, 1).unwrap();
        let d6 = identity(6, 1).unwrap();
        assert_ne!(d3, d4);
        assert_ne!(d4, d5);
        assert_ne!(d5, d6);
    }
}
