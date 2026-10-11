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
    // None is the historic/unqualified normalized Number pathway.
    // Some(n) is an explicitly admitted numeric domain Dn (n=24*2^k).
    // The field is authority-bearing and therefore participates in Eq/Hash.
    numeric_domain_width: Option<usize>,
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
            numeric_domain_width: None,
        })
    }

    fn normalize(bits: Vec<u8>) -> Self {
        let first_one = bits.iter().position(|bit| *bit == 1);
        match first_one {
            Some(index) => Self {
                bits: bits[index..].to_vec(),
                numeric_domain_width: None,
            },
            None => Self { bits: vec![0], numeric_domain_width: None },
        }
    }

    pub fn zero() -> Self {
        Self { bits: vec![0], numeric_domain_width: None }
    }

    pub fn one() -> Self {
        Self { bits: vec![1], numeric_domain_width: None }
    }

    pub fn is_zero(&self) -> bool {
        self.bits.len() == 1 && self.bits[0] == 0
    }

    pub fn width(&self) -> usize {
        self.bits.len()
    }

    /// The explicitly admitted SENS numeric-domain identity, when present.
    /// Width of the normalized *magnitude* is a different property.
    pub fn numeric_domain_width(&self) -> Option<usize> {
        self.numeric_domain_width
    }

    /// Construct an admitted numeric value from a FULL-WIDTH binary domain
    /// word. No source literal, text round-trip, or inferred domain.
    /// Leading zeroes are retained logically via the exact domain field.
    pub fn from_numeric_domain_bits(width: usize, word: &[u8]) -> Option<Self> {
        if !Self::is_numeric_domain_width(width)
            || word.len() != width
            || word.iter().any(|&bit| bit > 1)
        {
            return None;
        }
        let mut value = Self::normalize(word.to_vec());
        value.numeric_domain_width = Some(width);
        Some(value)
    }

    /// Exact-width binary word of an already-domain-qualified value.
    /// None means legacy/unqualified Number, never guessed from magnitude.
    pub fn exact_numeric_domain_bits(&self) -> Option<Vec<u8>> {
        let domain_width = self.numeric_domain_width?;
        let mut out = vec![0; domain_width.checked_sub(self.width())?];
        out.extend_from_slice(&self.bits);
        Some(out)
    }

    /// Owner-ratified SAME-DOMAIN natural addition, preserving explicit Dn
    /// on no carry and carrying exact bits into D(2n) on overflow.
    /// Mixed domains, legacy/qualified mixes, and unadmitted widths fail closed.
    pub fn add_admitted_numeric(&self, other: &Self) -> Option<Self> {
        let width = self.numeric_domain_width?;
        if other.numeric_domain_width != Some(width) {
            return None;
        }
        let (out_width, out_bits) = self.add_in_numeric_domain(other, width)?;
        Self::from_numeric_domain_bits(out_width, &out_bits)
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


    /// Exact subtraction in the natural Number slice. Underflow has no
    /// canonical natural result; signed encoding remains a separate law.
    /// All arithmetic runs on canonical binary digits, never host integers.
    pub fn checked_sub(&self, other: &Self) -> Option<Self> {
        if self < other {
            return None;
        }
        let mut reversed = Vec::with_capacity(self.bits.len());
        let mut borrow = 0i16;
        for offset in 0..self.bits.len() {
            let left = i16::from(self.bits[self.bits.len() - 1 - offset]);
            let right = if offset < other.bits.len() {
                i16::from(other.bits[other.bits.len() - 1 - offset])
            } else {
                0
            };
            let digit = left - right - borrow;
            if digit < 0 {
                reversed.push((digit + 2) as u8);
                borrow = 1;
            } else {
                reversed.push(digit as u8);
                borrow = 0;
            }
        }
        debug_assert_eq!(borrow, 0);
        reversed.reverse();
        Some(Self::normalize(reversed))
    }

    /// Euclidean division over exact natural Number bits.
    /// Returns None only for a zero divisor; quotient and remainder are
    /// canonical. A nonzero remainder does NOT authorize rational Number
    /// encoding (whose canonical layout has not yet been ratified).
    pub fn div_rem(&self, divisor: &Self) -> Option<(Self, Self)> {
        if divisor.is_zero() {
            return None;
        }
        let mut quotient = Vec::with_capacity(self.width());
        let mut remainder = Self::zero();
        for &bit in &self.bits {
            if remainder.is_zero() {
                remainder.bits[0] = bit;
            } else {
                remainder.bits.push(bit);
            }
            if &remainder >= divisor {
                remainder = remainder.checked_sub(divisor)?;
                quotient.push(1);
            } else {
                quotient.push(0);
            }
        }
        Some((Self::normalize(quotient), remainder))
    }

    /// Euclidean greatest common divisor. The result is again binary Number.
    pub fn gcd(&self, other: &Self) -> Self {
        let mut a = self.clone();
        let mut b = other.clone();
        while !b.is_zero() {
            let (_, remainder) = a.div_rem(&b).expect("nonzero divisor");
            a = b;
            b = remainder;
        }
        a
    }

    /// Owner-ratified numeric domain family D24, D48, D96, D192, ...
    /// A width is legitimate only when it is 24 * 2^k, k >= 0.
    /// This helper checks the *domain family*, not resident admissibility.
    pub fn is_numeric_domain_width(width: usize) -> bool {
        width >= 24 && width % 24 == 0 && (width / 24).is_power_of_two()
    }

    /// Exact magnitude capacity of one admitted numeric domain.
    /// Domain identity must still be carried explicitly by the caller.
    pub fn fits_ratified_width(&self, width: usize) -> bool {
        Self::is_numeric_domain_width(width) && self.width() <= width
    }

    /// Mechanical realization of the owner-ratified, SAME-DOMAIN natural
    /// addition law. Both operands are already admitted by their caller as
    /// Dn; this function neither infers domain membership from bits nor
    /// creates a second semantic representation.
    ///
    /// Exact carry over n bits raises the result to the next domain D(2n).
    /// Otherwise the result remains in Dn. Returned bits are explicitly
    /// zero-filled to the selected domain's FULL width (not normalized).
    /// The (width, bits) pair is a mechanism boundary, not itself a SENS
    /// language value; generic mixed-domain coercion remains unratified.
    pub fn add_in_numeric_domain(
        &self,
        other: &Self,
        input_domain_width: usize,
    ) -> Option<(usize, Vec<u8>)> {
        if !self.fits_ratified_width(input_domain_width)
            || !other.fits_ratified_width(input_domain_width)
            || self.numeric_domain_width.is_some_and(|d| d != input_domain_width)
            || other.numeric_domain_width.is_some_and(|d| d != input_domain_width)
        {
            return None;
        }
        let sum = self.add(other);
        let output_width = if sum.width() > input_domain_width {
            input_domain_width.checked_mul(2)?
        } else {
            input_domain_width
        };
        let mut exact_domain_bits = vec![0; output_width - sum.width()];
        exact_domain_bits.extend_from_slice(sum.as_bits());
        Some((output_width, exact_domain_bits))
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
        self.numeric_domain_width
            .cmp(&other.numeric_domain_width)
            .then_with(|| self.width().cmp(&other.width()))
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
    fn natural_subtraction_division_and_gcd_are_exact_bits() {
        let a = BinaryNumber::parse("110").unwrap();
        let b = BinaryNumber::parse("10").unwrap();
        assert_eq!(a.checked_sub(&b).unwrap().bits(), "100");
        assert_eq!(b.checked_sub(&a), None);
        assert_eq!(a.checked_sub(&a).unwrap().bits(), "0");
        let (q, r) = a.div_rem(&b).unwrap();
        assert_eq!(q.bits(), "11");
        assert_eq!(r.bits(), "0");
        let (q, r) = BinaryNumber::parse("111").unwrap().div_rem(&b).unwrap();
        assert_eq!((q.bits(), r.bits()), ("11".into(), "1".into()));
        assert_eq!(a.div_rem(&BinaryNumber::zero()), None);
        assert_eq!(a.gcd(&BinaryNumber::parse("100").unwrap()).bits(), "10");
        assert_eq!(BinaryNumber::zero().gcd(&BinaryNumber::zero()).bits(), "0");
    }

    #[test]
    fn exact_binary_arithmetic_matches_independent_small_integer_oracle() {
        for a in 0u32..128 {
            for b in 0u32..128 {
                let left = BinaryNumber::parse(&format!("{a:b}")).unwrap();
                let right = BinaryNumber::parse(&format!("{b:b}")).unwrap();
                assert_eq!(
                    left.checked_sub(&right).map(|value| value.bits()),
                    a.checked_sub(b).map(|n| format!("{n:b}"))
                );
                assert_eq!(
                    left.div_rem(&right)
                        .map(|(q, r)| (q.bits(), r.bits())),
                    if b == 0 { None } else {
                        Some((format!("{:b}", a / b), format!("{:b}", a % b)))
                    }
                );
            }
        }
    }

    #[test]
    fn division_and_ratified_capacity_do_not_truncate_wide_number() {
        let wide = BinaryNumber::parse(&format!("1{}", "0".repeat(256))).unwrap();
        let two = BinaryNumber::parse("10").unwrap();
        let (quotient, remainder) = wide.div_rem(&two).unwrap();
        assert_eq!(quotient.bits(), format!("1{}", "0".repeat(255)));
        assert!(remainder.is_zero());
        assert_eq!(quotient.mul(&two), wide);
        assert!(BinaryNumber::parse("1").unwrap().fits_ratified_width(24));
        assert!(!BinaryNumber::parse("1").unwrap().fits_ratified_width(7));
        assert!(!wide.fits_ratified_width(192));
        for width in [24usize, 48, 96, 192] {
            let max = BinaryNumber::parse(&"1".repeat(width)).unwrap();
            assert!(max.fits_ratified_width(width));
            assert!(!max.add(&BinaryNumber::one()).fits_ratified_width(width));
        }
    }

    #[test]
    fn numeric_domain_addition_carries_d24_into_d48_without_truncation() {
        // Inputs are direct bits with explicit domain width, not literals.
        let max = BinaryNumber::from_bits(vec![1; 24]).unwrap();
        let (width, exact_bits) = max.add_in_numeric_domain(&max, 24).unwrap();
        assert_eq!(width, 48);
        assert_eq!(exact_bits.len(), 48);
        assert_eq!(&exact_bits[..23], &[0; 23]);
        assert_eq!(&exact_bits[23..47], &[1; 24]);
        assert_eq!(exact_bits[47], 0);
        // Mechanism reduction to host integers is strictly an independent
        // oracle; the SENS result remains full exact D48 bits.
        let magnitude = BinaryNumber::from_bits(exact_bits).unwrap();
        assert_eq!(magnitude.to_decimal_string(), (2u64 * ((1u64 << 24) - 1)).to_string());

        // Carry must not trigger promotion when a same-domain sum still fits.
        let one = BinaryNumber::one();
        let (small_width, small_bits) = one.add_in_numeric_domain(&one, 24).unwrap();
        assert_eq!(small_width, 24);
        assert_eq!(small_bits.len(), 24);
        assert_eq!(&small_bits[..22], &[0; 22]);
        assert_eq!(&small_bits[22..], &[1, 0]);
    }

    #[test]
    fn numeric_domain_addition_widens_unbounded_rungs_and_rejects_bad_domains() {
        for width in [24, 48, 96, 192, 384, 768] {
            let max = BinaryNumber::from_bits(vec![1; width]).unwrap();
            let (target_width, result) = max.add_in_numeric_domain(&max, width).unwrap();
            assert_eq!(target_width, width * 2);
            assert_eq!(result.len(), target_width);
            assert_eq!(result.iter().take(width - 1).filter(|&&b| b != 0).count(), 0);
            assert!(result[(width - 1)..(2 * width - 1)].iter().all(|&bit| bit == 1));
            assert_eq!(result[2 * width - 1], 0);
            assert!(max.fits_ratified_width(width));
        }
        let one = BinaryNumber::one();
        for invalid_width in [0, 1, 23, 25, 47, 72, 192 + 1] {
            assert_eq!(one.add_in_numeric_domain(&one, invalid_width), None);
        }
        let wide = BinaryNumber::from_bits(vec![1; 25]).unwrap();
        assert_eq!(wide.add_in_numeric_domain(&one, 24), None);
    }

    #[test]
    fn admitted_domain_number_is_part_of_value_identity_and_keeps_exact_word() {
        let mut d24 = vec![0; 24];
        d24[23] = 1;
        let mut d48 = vec![0; 48];
        d48[47] = 1;
        let a = BinaryNumber::from_numeric_domain_bits(24, &d24).unwrap();
        let b = BinaryNumber::from_numeric_domain_bits(48, &d48).unwrap();
        assert_eq!(a.numeric_domain_width(), Some(24));
        assert_eq!(b.numeric_domain_width(), Some(48));
        assert_eq!(a.exact_numeric_domain_bits(), Some(d24.clone()));
        assert_eq!(b.exact_numeric_domain_bits(), Some(d48.clone()));
        assert_ne!(a, b, "different admitted numeric domains must never alias");
        assert_ne!(a, BinaryNumber::one(), "legacy unqualified value is not D24");
        assert_eq!(a.cmp(&b), std::cmp::Ordering::Less);
        assert!(BinaryNumber::from_numeric_domain_bits(24, &[0; 23]).is_none());
        assert!(BinaryNumber::from_numeric_domain_bits(24, &[0; 25]).is_none());
        assert!(BinaryNumber::from_numeric_domain_bits(25, &[0; 25]).is_none());
        let mut invalid = d24;
        invalid[3] = 2;
        assert!(BinaryNumber::from_numeric_domain_bits(24, &invalid).is_none());
    }

    #[test]
    fn admitted_d24_addition_promotes_through_real_domain_qualified_value() {
        let full = BinaryNumber::from_numeric_domain_bits(24, &vec![1; 24]).unwrap();
        let sum = full.add_admitted_numeric(&full).unwrap();
        assert_eq!(sum.numeric_domain_width(), Some(48));
        let exact = sum.exact_numeric_domain_bits().unwrap();
        assert_eq!(exact.len(), 48);
        assert_eq!(&exact[..23], &[0; 23]);
        assert!(exact[23..47].iter().all(|&b| b == 1));
        assert_eq!(exact[47], 0);
        let small = BinaryNumber::from_numeric_domain_bits(24, &vec![0; 24]).unwrap();
        let same = small.add_admitted_numeric(&small).unwrap();
        assert_eq!(same.numeric_domain_width(), Some(24));
        assert_eq!(same.exact_numeric_domain_bits(), Some(vec![0; 24]));
        assert!(full.add_admitted_numeric(&BinaryNumber::one()).is_none());
        let another_domain = BinaryNumber::from_numeric_domain_bits(48, &vec![0; 48]).unwrap();
        assert!(full.add_admitted_numeric(&another_domain).is_none());
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
