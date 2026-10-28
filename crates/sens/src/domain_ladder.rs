//! Механічна драбина D1–D10 без жодної Rust-семантики.
//!
//! Координата — рівно (ширина, біти). Значення, назви, закони,
//! допуск до виконання та оракули належать доменним джерелам SENS.
//! Це НЕ другий реєстр функцій; викличність визначають точні SENS-механізми.
//!
//! Аксіома бітності: ширина ключа = адреса домену. D*n* ніколи не
//! приймає ключ іншої довжини. Рівний packed payload у різних ширинах
//! — різні координати.
//!
//! D7: `knowledge/d7-keyboard-v2-ratified.json` — чинні 128/128
//! семибітних координат даних. Жодна координата не надає callability.

/// Exact 10-bit mechanical carrier. It has no implicit widening/narrowing to
/// D9 or historical Function8; callable slots are installed separately.
/// The host stores its payload in u16, but only ten bits belong to SENS.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct DomainD10 {
    bits: u16,
}

impl DomainD10 {
    pub const fn new(bits: u16) -> Option<Self> {
        if bits < (1u16 << 10) {
            Some(Self { bits })
        } else {
            None
        }
    }

    pub const fn packed_bits(self) -> u16 {
        self.bits
    }

    pub const fn coordinate(self) -> DomainCoordinate {
        DomainCoordinate {
            width: 10,
            bits: self.bits,
        }
    }

    pub const fn from_coordinate(coordinate: DomainCoordinate) -> Option<Self> {
        if coordinate.width != 10 {
            return None;
        }
        Self::new(coordinate.bits)
    }
}

/// A width-qualified, meaning-free code word in the D1–D10 ladder.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct DomainCoordinate {
    width: u8,
    bits: u16,
}

impl DomainCoordinate {
    /// Fail closed for out-of-range rungs and truncated payloads.
    pub const fn new(width: u8, bits: u16) -> Option<Self> {
        if width == 0 || width > 10 || bits >= (1u16 << width) {
            return None;
        }
        Some(Self { width, bits })
    }

    /// Mechanically project any already-validated D1-D9 source identity.
    /// D7 is an exact W7 coordinate; this grants neither a sound role nor
    /// generic callability. D10 remains representable via `new` only.
    pub const fn from_domain_identity(identity: crate::DomainIdentity) -> Self {
        Self {
            width: identity.width() as u8,
            bits: identity.packed_bits(),
        }
    }

    pub const fn width(self) -> u8 {
        self.width
    }

    pub const fn bits(self) -> u16 {
        self.bits
    }

    /// Convert only D1–D9 coordinates into the bounded source enum.
    /// D10 remains in the full-width identity carrier.
    pub fn source_word(self) -> Option<crate::BinarySourceWord> {
        let bits = self.bits as u8;
        match self.width {
            1 => crate::Bit1::new(bits).map(crate::BinarySourceWord::W1),
            2 => crate::Bit2::new(bits).map(crate::BinarySourceWord::W2),
            3 => crate::Bit3::new(bits).map(crate::BinarySourceWord::W3),
            4 => crate::Bit4::new(bits).map(crate::BinarySourceWord::W4),
            5 => crate::Bit5::new(bits).map(crate::BinarySourceWord::W5),
            6 => crate::Bit6::new(bits).map(crate::BinarySourceWord::W6),
            7 => crate::Bit7::new(bits).map(crate::BinarySourceWord::W7),
            8 => crate::Bit8::new(bits).map(crate::BinarySourceWord::W8),
            9 => crate::Bit9::new(self.bits).map(crate::BinarySourceWord::W9),
            _ => None,
        }
    }

    /// Точний видимий запис однієї координати без домішування десяткових
    /// чисел, пробілів чи текстових назв. Ведучі нулі є частиною identity.
    /// Це механічний розбір, а НЕ доказ виконуваності.
    pub fn з_видимих_бітів(слово: &str) -> Option<Self> {
        let raw = слово.as_bytes();
        if !(1..=10).contains(&raw.len()) {
            return None;
        }
        let mut bits = 0u16;
        for &digit in raw {
            bits = (bits << 1)
                | match digit {
                    b'0' => 0,
                    b'1' => 1,
                    _ => return None,
                };
        }
        Self::new(raw.len() as u8, bits)
    }

    /// Точна source-проєкція збереженої координати; без округлення до байта.
    /// Canonical binary-source projection: emit each identity bit directly.
    /// No decimal formatting/parsing step can erase the width or leading zeroes.
    pub fn видимі_біти(self) -> String {
        let width = usize::from(self.width);
        let mut source = String::with_capacity(width);
        for offset in 0..width {
            let shift = width - 1 - offset;
            let bit = (self.bits >> shift) & 1;
            source.push(if bit == 0 { '0' } else { '1' });
        }
        source
    }

    /// Pure occupancy projection from owner-ratified domain sources.
    ///
    /// D3–D7 are a generated coordinate subset. D8/D9 have independent
    /// full-width owner certificates; Contract 11.9 separately ratifies
    /// D10 as one complete 1024/1024 domain, without runtime admission.
    /// D1/D2 structural/predicate roles stay unprojected.
    /// Some(true) proves occupancy, never a callable mechanism or human name.
    ///
    /// D7: all 128 current keyboard coordinates are resident, but remain
    /// typed text/data, never callable merely because of their width.
    pub fn owner_residency(self) -> Option<bool> {
        if self.width == 10 {
            // Whole-domain ratification; NOT physical T5 or callability.
            return Some(true);
        }
        if crate::domain_owner_generated::DOMAIN_OWNER_FULL_WIDTHS.contains(&self.width) {
            return Some(true);
        }
        if !(3..=7).contains(&self.width) {
            return None;
        }
        // Generated D3..D7 bitmap positions follow exact widths (index=width-3).
        // A mismatch must fail closed rather than reinterpret another domain.
        // This removes the per-lookup linear scan over all bitmap descriptors.
        let mask =
            crate::domain_owner_generated::DOMAIN_OWNER_BITMAPS.get(usize::from(self.width - 3))?;
        if mask.width != self.width {
            return None;
        }
        let slot = usize::from(self.bits / 64);
        Some(((mask.slots[slot] >> (self.bits % 64)) & 1) != 0)
    }
}

