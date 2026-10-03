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
    pub name: &'static str,
    pub legacy_mechanism: Option<u8>,
    pub surfaces: &'static [&'static str],
}

pub(crate) const DOMAIN_OWNER_ROWS: &[DomainOwnerRow] = &[
    DomainOwnerRow { width: 3, bits: 0b001, name: "QUOTE", legacy_mechanism: Some(0b00000001), surfaces: &["quote", "як-є", "як-є", "svarūpa", "'"] },
    DomainOwnerRow { width: 3, bits: 0b010, name: "ATOM", legacy_mechanism: Some(0b00000010), surfaces: &["atom?", "атом?", "атом?", "aṇu", ".?"] },
    DomainOwnerRow { width: 3, bits: 0b011, name: "COND", legacy_mechanism: Some(0b00000111), surfaces: &["cond", "за-умовою", "за-умовою", "anukrama", "?:"] },
    DomainOwnerRow { width: 3, bits: 0b100, name: "CONS", legacy_mechanism: Some(0b00000100), surfaces: &["cons", "сполучити", "сполучити", "saṃyuj"] },
    DomainOwnerRow { width: 3, bits: 0b101, name: "CAR", legacy_mechanism: Some(0b00000101), surfaces: &["car", "перше", "перше", "ādi", ":п"] },
    DomainOwnerRow { width: 3, bits: 0b110, name: "CDR", legacy_mechanism: Some(0b00000110), surfaces: &["cdr", "решта", "решта", "śeṣa", ":р"] },
    DomainOwnerRow { width: 3, bits: 0b111, name: "EQ", legacy_mechanism: Some(0b00000011), surfaces: &["eq?", "тотожне?", "тотожне?", "abheda", "=?"] },
    DomainOwnerRow { width: 4, bits: 0b0000, name: "APPLY", legacy_mechanism: Some(0b10101111), surfaces: &["apply", "застосувати", "застосувати"] },
    DomainOwnerRow { width: 4, bits: 0b0001, name: "EVAL", legacy_mechanism: Some(0b01001101), surfaces: &["eval", "обчислити", "обчислити", "vicāraṇa"] },
    DomainOwnerRow { width: 4, bits: 0b0010, name: "LAMBDA", legacy_mechanism: Some(0b00001000), surfaces: &["lambda", "функція", "функція"] },
    DomainOwnerRow { width: 4, bits: 0b0011, name: "DEFINE", legacy_mechanism: Some(0b00001001), surfaces: &["define", "визначити", "визначити"] },
    DomainOwnerRow { width: 4, bits: 0b0100, name: "NOT", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 4, bits: 0b0110, name: "EVCON", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 4, bits: 0b0111, name: "EVLIS", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 4, bits: 0b1000, name: "LIST", legacy_mechanism: Some(0b00100111), surfaces: &["list", "список", "список", "śreṇī"] },
    DomainOwnerRow { width: 4, bits: 0b1010, name: "CAAR", legacy_mechanism: Some(0b00110011), surfaces: &["caar", "перше-від-першого"] },
    DomainOwnerRow { width: 4, bits: 0b1011, name: "CADR", legacy_mechanism: Some(0b00110100), surfaces: &["cadr", "перше-від-решти"] },
    DomainOwnerRow { width: 4, bits: 0b1100, name: "CDAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 4, bits: 0b1101, name: "CDDR", legacy_mechanism: Some(0b00110101), surfaces: &["cddr", "решта-від-решти"] },
    DomainOwnerRow { width: 4, bits: 0b1110, name: "LOOKUP", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 4, bits: 0b1111, name: "BIND", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b00000, name: "EVALQUOTE", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b00001, name: "FUNCTION", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b00010, name: "FEXPR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b00011, name: "MACRO", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b00100, name: "LABEL", legacy_mechanism: Some(0b10101010), surfaces: &["label", "мітка", "мітка"] },
    DomainOwnerRow { width: 5, bits: 0b00101, name: "PROG", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b00110, name: "SET", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b00111, name: "SETQ", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b01000, name: "ZEROP", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b01001, name: "NUMBERP", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b01010, name: "PLUS", legacy_mechanism: Some(0b00001100), surfaces: &["plus", "додати", "додати", "yoga", "+"] },
    DomainOwnerRow { width: 5, bits: 0b01011, name: "DIFFERENCE", legacy_mechanism: Some(0b00001101), surfaces: &["difference", "відняти", "відняти", "viyoga", "-"] },
    DomainOwnerRow { width: 5, bits: 0b01100, name: "GO", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b01101, name: "RETURN", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b01110, name: "LESSP", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b01111, name: "GREATERP", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b10000, name: "APPEND", legacy_mechanism: Some(0b00101001), surfaces: &["append", "приєднати", "приєднати", "saṅkalana"] },
    DomainOwnerRow { width: 5, bits: 0b10001, name: "REVERSE", legacy_mechanism: Some(0b00101010), surfaces: &["reverse", "зворот", "зворот", "viloma"] },
    DomainOwnerRow { width: 5, bits: 0b10010, name: "TIMES", legacy_mechanism: Some(0b00001110), surfaces: &["times", "помножити", "помножити", "guṇana", "*"] },
    DomainOwnerRow { width: 5, bits: 0b10011, name: "QUOTIENT", legacy_mechanism: Some(0b00010100), surfaces: &["quotient", "частка", "частка", "bhāga"] },
    DomainOwnerRow { width: 5, bits: 0b10100, name: "CAAAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b10101, name: "CAADR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b10110, name: "CADAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b10111, name: "CADDR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b11000, name: "CDAAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b11001, name: "CDADR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b11010, name: "CDDAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b11011, name: "CDDDR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b11100, name: "ASSOC", legacy_mechanism: Some(0b00101101), surfaces: &["assoc", "знайти-за-ключем", "знайти-за-ключем", "saṃbandha"] },
    DomainOwnerRow { width: 5, bits: 0b11101, name: "MEMBER", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b11110, name: "PAIRLIS", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 5, bits: 0b11111, name: "SUBST", legacy_mechanism: Some(0b10101100), surfaces: &["subst", "замінити", "замінити"] },
    DomainOwnerRow { width: 6, bits: 0b000000, name: "REPL", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b000001, name: "LOAD", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b000010, name: "CLOSURE", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b000011, name: "CURRY", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b000100, name: "FSUBR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b000101, name: "LEXPR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b000110, name: "MACROEXPAND-1", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b000111, name: "MACROEXPAND", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b001000, name: "LET", legacy_mechanism: Some(0b10011100), surfaces: &["let", "нехай", "нехай"] },
    DomainOwnerRow { width: 6, bits: 0b001001, name: "LET*", legacy_mechanism: Some(0b10011101), surfaces: &["let*", "нехай*", "нехай-послідовно"] },
    DomainOwnerRow { width: 6, bits: 0b001010, name: "DO", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b001011, name: "WHILE", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b001100, name: "RPLACA", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b001101, name: "RPLACD", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b001110, name: "SETF", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b001111, name: "DEFVAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b010000, name: "EVENP", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b010001, name: "ODDP", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b010010, name: "INTEGERP", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b010011, name: "RATIONALP", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b010100, name: "ADD1", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b010101, name: "ABS", legacy_mechanism: Some(0b00010000), surfaces: &["abs", "модуль", "модуль", "rūpa"] },
    DomainOwnerRow { width: 6, bits: 0b010110, name: "SUB1", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b010111, name: "NEG", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b011000, name: "TAGBODY", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b011001, name: "BLOCK", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b011010, name: "RETURN-FROM", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b011011, name: "CATCH", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b011100, name: "LEQ", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b011101, name: "MIN", legacy_mechanism: Some(0b00010001), surfaces: &["min", "найменше", "найменше", "alpatara"] },
    DomainOwnerRow { width: 6, bits: 0b011110, name: "GEQ", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b011111, name: "MAX", legacy_mechanism: Some(0b00010010), surfaces: &["max", "найбільше", "найбільше", "brhattara"] },
    DomainOwnerRow { width: 6, bits: 0b100000, name: "NCONC", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b100001, name: "LENGTH", legacy_mechanism: Some(0b00101000), surfaces: &["length", "довжина", "довжина", "pramāṇa"] },
    DomainOwnerRow { width: 6, bits: 0b100010, name: "NREVERSE", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b100011, name: "NTH", legacy_mechanism: Some(0b00101011), surfaces: &["nth", "елемент-списку-за-індексом", "елемент-списку-за-індексом", "kramāṅka"] },
    DomainOwnerRow { width: 6, bits: 0b100100, name: "EXPT", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b100101, name: "GCD", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b100110, name: "REMAINDER", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b100111, name: "RECIP", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101000, name: "CAAAAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101001, name: "CAAADR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101010, name: "CAADAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101011, name: "CAADDR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101100, name: "CADAAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101101, name: "CADADR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101110, name: "CADDAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b101111, name: "CADDDR", legacy_mechanism: Some(0b00110110), surfaces: &["cadddr", "перше-після-трьох-решт"] },
    DomainOwnerRow { width: 6, bits: 0b110000, name: "CDAAAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b110001, name: "CDAADR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b110010, name: "CDADAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b110011, name: "CDADDR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b110100, name: "CDDAAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b110101, name: "CDDADR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b110110, name: "CDDDAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b110111, name: "CDDDDR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b111000, name: "RASSOC", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b111001, name: "ACONS", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b111010, name: "INTERSECTION", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b111011, name: "UNION", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b111100, name: "MAPCAR", legacy_mechanism: None, surfaces: &[] },
    DomainOwnerRow { width: 6, bits: 0b111101, name: "MAPLIST", legacy_mechanism: Some(0b10101110), surfaces: &["maplist", "відобразити-залишки", "відобразити-залишки"] },
    DomainOwnerRow { width: 6, bits: 0b111110, name: "SUBLIS", legacy_mechanism: Some(0b10101101), surfaces: &["sublis", "підставити-пари", "підставити-пари"] },
    DomainOwnerRow { width: 6, bits: 0b111111, name: "COPY-TREE", legacy_mechanism: None, surfaces: &[] },
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

pub(crate) fn owner_name(identity_key: CoreDomainIdentity) -> Option<&'static str> {
    row_for_identity(identity_key).map(|row| row.name)
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
