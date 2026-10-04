//! Canonical variable-width natural Number for #3022.
//!
//! Language identity is the normalized binary bitstring. This type deliberately
//! carries no decimal spelling, Rational fields, fixed machine width, or host
//! integer identity. Host vectors are private storage only.
//!
//! First live slice: non-negative integers. Signed and rational encodings are
//! separate later laws under #3021.

use std::{cmp::Ordering, fmt};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BinaryNumberError {
    Empty,
    NonBit,
    NonCanonicalLeadingZero,
}

#[derive(Clone, Eq, Hash, PartialEq)]
pub struct BinaryNumber {
    bits: Vec<u8>,
}

impl BinaryNumber {
    /// Parse a binary Number projection and normalize leading zeroes.
    ///
    /// Canonical zero is exactly `0`; every non-zero Number starts with `1`.
    pub fn parse(text: &str) -> Result<Self, BinaryNumberError> {
        if text.is_empty() {
            return Err(BinaryNumberError::Empty);
        }
        let mut bits = Vec::with_capacity(text.len());
        for byte in text.bytes() {
            match byte {
                b'0' => bits.push(0),
                b'1' => bits.push(1),
                _ => return Err(BinaryNumberError::NonBit),
            }
        }
        Ok(Self::normalize(bits))
    }

    /// Build from mechanism bits, normalizing the same way as source input.
    pub fn from_bits(bits: impl IntoIterator<Item = u8>) -> Result<Self, BinaryNumberError> {
        let bits = bits.into_iter().collect::<Vec<_>>();
        if bits.is_empty() {
            return Err(BinaryNumberError::Empty);
        }
        if bits.iter().any(|bit| *bit > 1) {
            return Err(BinaryNumberError::NonBit);
        }
        Ok(Self::normalize(bits))
    }

    /// Decode an already-canonical binary Number. Used by FASL/wire so
    /// non-canonical encodings fail closed rather than silently normalize.
    pub fn from_canonical_bits(bits: &[u8]) -> Result<Self, BinaryNumberError> {
        if bits.is_empty() {
            return Err(BinaryNumberError::Empty);
        }
        if bits.iter().any(|bit| *bit > 1) {
            return Err(BinaryNumberError::NonBit);
        }
        if bits.len() > 1 && bits[0] == 0 {
            return Err(BinaryNumberError::NonCanonicalLeadingZero);
        }
        Ok(Self {
            bits: bits.to_vec(),
        })
    }

    fn normalize(bits: Vec<u8>) -> Self {
        let first_one = bits.iter().position(|bit| *bit == 1);
        match first_one {
            Some(index) => Self {
                bits: bits[index..].to_vec(),
            },
            None => Self { bits: vec![0] },
        }
    }

    pub fn zero() -> Self {
        Self { bits: vec![0] }
    }

    pub fn one() -> Self {
        Self { bits: vec![1] }
    }

    pub fn is_zero(&self) -> bool {
        self.bits.len() == 1 && self.bits[0] == 0
    }

    pub fn width(&self) -> usize {
        self.bits.len()
    }

    pub fn as_bits(&self) -> &[u8] {
        &self.bits
    }

    pub fn bits(&self) -> String {
        self.bits
            .iter()
            .map(|bit| if *bit == 0 { '0' } else { '1' })
            .collect()
    }

    /// Exact arbitrary-width binary addition. No host numeric value is used.
    pub fn add(&self, other: &Self) -> Self {
        let mut out_rev = Vec::with_capacity(self.width().max(other.width()) + 1);
        let mut li = self.bits.len();
        let mut ri = other.bits.len();
        let mut carry = 0u8;

        while li > 0 || ri > 0 || carry != 0 {
            let left = if li > 0 {
                li -= 1;
                self.bits[li]
            } else {
                0
            };
            let right = if ri > 0 {
                ri -= 1;
                other.bits[ri]
            } else {
                0
            };
            let sum = left + right + carry;
            out_rev.push(sum & 1);
            carry = sum >> 1;
        }

        if out_rev.is_empty() {
            return Self::zero();
        }
        out_rev.reverse();
        Self::normalize(out_rev)
    }

    /// Exact arbitrary-width binary multiplication via shift-and-add.
    /// Storage choices are mechanism only; the result identity is its bits.
    pub fn mul(&self, other: &Self) -> Self {
        if self.is_zero() || other.is_zero() {
            return Self::zero();
        }

        let mut result = Self::zero();
        let mut shifted = self.clone();
        for bit in other.bits.iter().rev() {
            if *bit == 1 {
                result = result.add(&shifted);
            }
            if !shifted.is_zero() {
                shifted.bits.push(0);
            }
        }
        result
    }

    /// Human-facing decimal projection without making a host integer the
    /// language identity. Repeated decimal digit doubling consumes only bits.
    pub fn to_decimal_string(&self) -> String {
        let mut digits = vec![0u8]; // little-endian base-10 mechanism digits
        for bit in &self.bits {
            let mut carry = *bit;
            for digit in &mut digits {
                let value = *digit * 2 + carry;
                *digit = value % 10;
                carry = value / 10;
            }
            while carry != 0 {
                digits.push(carry % 10);
                carry /= 10;
            }
        }
        digits
            .iter()
            .rev()
            .map(|digit| char::from(b'0' + *digit))
            .collect()
    }
}

impl Ord for BinaryNumber {
    fn cmp(&self, other: &Self) -> Ordering {
        self.width()
            .cmp(&other.width())
            .then_with(|| self.bits.cmp(&other.bits))
    }
}

impl PartialOrd for BinaryNumber {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl fmt::Debug for BinaryNumber {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "BinaryNumber({})", self.bits())
    }
}

impl fmt::Display for BinaryNumber {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.to_decimal_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn normalization_has_one_zero_and_no_nonzero_leading_zero() {
        assert_eq!(BinaryNumber::parse("0000").unwrap().bits(), "0");
        assert_eq!(BinaryNumber::parse("00101").unwrap().bits(), "101");
        assert_eq!(
            BinaryNumber::from_canonical_bits(&[0, 1]),
            Err(BinaryNumberError::NonCanonicalLeadingZero)
        );
    }

    #[test]
    fn owner_acceptance_examples_are_bits_to_bits() {
        let two = BinaryNumber::parse("10").unwrap();
        let three = BinaryNumber::parse("11").unwrap();
        assert_eq!(two.add(&three).bits(), "101");
        assert_eq!(three.mul(&two).bits(), "110");
    }

    #[test]
    fn arbitrary_width_does_not_change_identity_law() {
        let wide = BinaryNumber::parse(&"1".repeat(256)).unwrap();
        let widened = wide.add(&BinaryNumber::one());
        assert_eq!(wide.width(), 256);
        assert_eq!(widened.width(), 257);
        assert_eq!(widened.bits(), format!("1{}", "0".repeat(256)));
    }

    #[test]
    fn ordering_is_numeric_for_canonical_bits() {
        let three = BinaryNumber::parse("11").unwrap();
        let four = BinaryNumber::parse("100").unwrap();
        assert!(three < four);
        assert_eq!(BinaryNumber::parse("0011").unwrap(), three);
    }

    #[test]
    fn human_decimal_projection_is_not_semantic_identity() {
        assert_eq!(BinaryNumber::parse("101").unwrap().to_decimal_string(), "5");
        assert_eq!(
            BinaryNumber::parse("1111111111111111").unwrap().to_decimal_string(),
            "65535"
        );
    }
}
