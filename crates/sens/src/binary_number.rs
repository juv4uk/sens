//! Exact binary Number carrier for #3022 and signed D12+ numeric values.
//!
//! Language identity is the normalized binary bitstring. This type deliberately
//! carries no decimal spelling, Rational fields, fixed machine width, or host
//! integer identity. Host vectors are private storage only.
//!
//! Unqualified legacy values retain their canonical unsigned magnitude
//! projection. Explicit D12+ values interpret their exact-width words as
//! two's-complement integers; ratio components use private unsigned magnitudes.

use std::{cmp::Ordering, fmt, sync::Arc};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BinaryNumberError {
    Empty,
    NonBit,
    NonCanonicalLeadingZero,
}

#[derive(Clone, Eq, Hash, PartialEq)]
pub struct BinaryNumber {
    bits: Arc<Vec<u8>>,
    // None is the historic/unqualified normalized Number pathway.
    // Some(n) is an explicitly admitted numeric domain Dn (n=12*2^k).
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
            bits: Arc::new(bits.to_vec()),
            numeric_domain_width: None,
        })
    }

    fn normalize(bits: Vec<u8>) -> Self {
        let first_one = bits.iter().position(|bit| *bit == 1);
        match first_one {
            Some(index) => Self {
                bits: Arc::new(bits[index..].to_vec()),
                numeric_domain_width: None,
            },
            None => Self {
                bits: Arc::new(vec![0]),
                numeric_domain_width: None,
            },
        }
    }

    pub fn zero() -> Self {
        Self {
            bits: Arc::new(vec![0]),
            numeric_domain_width: None,
        }
    }

    pub fn one() -> Self {
        Self {
            bits: Arc::new(vec![1]),
            numeric_domain_width: None,
        }
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

    /// Decode an admitted D12+ exact-width word as (negative, unsigned magnitude).
    /// The returned magnitude is an unqualified mechanism value, not a Dn.
    pub(crate) fn signed_magnitude(&self) -> Option<(bool, Self)> {
        let mut word = self.exact_numeric_domain_bits()?;
        let negative = word[0] == 1;
        if negative {
            for bit in &mut word {
                *bit ^= 1;
            }
            let mut carry = 1u8;
            for bit in word.iter_mut().rev() {
                let sum = *bit + carry;
                *bit = sum & 1;
                carry = sum >> 1;
                if carry == 0 {
                    break;
                }
            }
        }
        Some((negative, Self::normalize(word)))
    }

    /// Encode an exact signed magnitude in Dn, rejecting values outside the
    /// two's-complement range. Magnitude must be an unsigned mechanism value.
    pub(crate) fn from_signed_magnitude(
        width: usize,
        negative: bool,
        magnitude: &Self,
    ) -> Option<Self> {
        if !Self::is_numeric_domain_width(width) || magnitude.width() > width {
            return None;
        }
        let fits = if negative {
            magnitude.width() < width
                || (magnitude.width() == width
                    && magnitude.bits[0] == 1
                    && magnitude.bits[1..].iter().all(|&bit| bit == 0))
        } else {
            magnitude.width() < width
        };
        if !fits {
            return None;
        }

        let mut word = vec![0; width - magnitude.width()];
        word.extend_from_slice(magnitude.as_bits());
        if negative && !magnitude.is_zero() {
            for bit in &mut word {
                *bit ^= 1;
            }
            let mut carry = 1u8;
            for bit in word.iter_mut().rev() {
                let sum = *bit + carry;
                *bit = sum & 1;
                carry = sum >> 1;
                if carry == 0 {
                    break;
                }
            }
        }
        Self::from_numeric_domain_bits(width, &word)
    }

    /// Encode a signed result at the smallest admitted rung no narrower than
    /// `minimum_width`, widening exactly rather than wrapping on overflow.
    pub(crate) fn from_signed_magnitude_growing(
        minimum_width: usize,
        negative: bool,
        magnitude: &Self,
    ) -> Option<Self> {
        let mut width = minimum_width;
        loop {
            if let Some(result) = Self::from_signed_magnitude(width, negative, magnitude) {
                return Some(result);
            }
            width = width.checked_mul(2)?;
        }
    }

    /// Same-domain signed integer addition. Retains Dn when representable and
    /// widens exactly to a ratified successor when the signed range is crossed.
    pub fn add_admitted_numeric(&self, other: &Self) -> Option<Self> {
        self.compute_admitted_integer(other, "+")
    }

    /// Same-domain signed integer multiplication, widening without truncation.
    pub fn mul_admitted_numeric(&self, other: &Self) -> Option<Self> {
        self.compute_admitted_integer(other, "*")
    }

    /// Same-domain signed integer subtraction, widening rather than wrapping.
    pub fn checked_sub_admitted_numeric(&self, other: &Self) -> Option<Self> {
        self.compute_admitted_integer(other, "-")
    }

    fn compute_admitted_integer(&self, other: &Self, operator: &str) -> Option<Self> {
        let width = self.numeric_domain_width?;
        if other.numeric_domain_width != Some(width) {
            return None;
        }
        match crate::domain_numeric::compute(
            operator,
            &crate::Value::BinaryNumber(self.clone()),
            &crate::Value::BinaryNumber(other.clone()),
        )? {
            crate::Value::BinaryNumber(ref result) => Some(result.clone()),
            _ => None,
        }
    }

    /// Euclidean quotient and remainder for nonnegative Dn operands.
    /// Signed language division is handled by the canonical RATIO evaluator;
    /// this magnitude helper is retained for gcd/component calculations.
    pub fn div_rem_admitted_numeric(&self, other: &Self) -> Option<(Self, Self)> {
        let width = self.numeric_domain_width?;
        if other.numeric_domain_width != Some(width) || other.is_zero() {
            return None;
        }
        let (left_negative, left_magnitude) = self.signed_magnitude()?;
        let (right_negative, right_magnitude) = other.signed_magnitude()?;
        if left_negative || right_negative {
            return None;
        }
        // Raw div_rem is intentionally a magnitude mechanism. Explicitly
        // strip tags only inside this private calculation and RE-ADMIT both
        // results into their original Dn at its boundary.
        let (quotient, remainder) = left_magnitude.div_rem(&right_magnitude)?;
        let admit =
            |value: Self| -> Option<Self> { Self::from_signed_magnitude(width, false, &value) };
        Some((admit(quotient)?, admit(remainder)?))
    }

    /// Return sign and unsigned magnitude of the signed difference.
    pub fn signed_difference_parts_admitted_numeric(&self, other: &Self) -> Option<(bool, Self)> {
        let difference = self.checked_sub_admitted_numeric(other)?;
        difference.signed_magnitude()
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

    /// Every explicitly admitted Dn integer can be negated exactly; the
    /// minimum two's-complement value widens to the next Dn instead of wrapping.
    pub fn can_be_negated_in_numeric_domain(&self) -> bool {
        self.numeric_domain_width.is_some()
    }

    /// Normalize positive *magnitude components* for exact RATIO(p,q).
    /// Inputs must be same-domain nonnegative D12+ values; q=0 is rejected.
    /// gcd(p,q)=1 is enforced by exact binary div_rem.
    ///
    /// This returns mechanism-level existing BinaryNumber constituents, NOT
    /// a new host semantic Rational, a language expression, binary opcode or
    /// evidence of callable signed/rational arithmetic. Caller must collapse
    /// p=0 to numeric zero and q=1 to an integer under the ratified law.
    /// Numerator and denominator MUST already have the exact same Dn.
    /// A matching magnitude is not permission to bridge D24 and D48.
    pub fn reduce_numeric_domain_ratio_parts(
        numerator: &Self,
        denominator: &Self,
    ) -> Option<(Self, Self)> {
        let width = numerator.numeric_domain_width?;
        if denominator.numeric_domain_width != Some(width) || denominator.is_zero() {
            return None;
        }
        let (numerator_negative, n) = numerator.signed_magnitude()?;
        let (denominator_negative, d) = denominator.signed_magnitude()?;
        if numerator_negative || denominator_negative {
            return None;
        }

        // Exact gcd uses private unqualified magnitudes only AFTER same-Dn
        // admission. The public result reattaches that very same domain.
        let divisor = n.gcd(&d);
        let (n_reduced, n_rem) = n.div_rem(&divisor)?;
        let (d_reduced, d_rem) = d.div_rem(&divisor)?;
        if !n_rem.is_zero() || !d_rem.is_zero() {
            return None;
        }
        Some((
            Self::from_signed_magnitude(width, false, &n_reduced)?,
            Self::from_signed_magnitude(width, false, &d_reduced)?,
        ))
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
        // Shift-and-add works on the unqualified magnitude: carrying a Dn
        // tag into intermediate shifts would misrepresent their bit width.
        // One bit-vector allocation replaces the old double-normalization
        // at the admitted Dn caller.
        let mut shifted = Self {
            bits: self.bits.clone(),
            numeric_domain_width: None,
        };
        for bit in other.bits.iter().rev() {
            if *bit == 1 {
                result = result.add(&shifted);
            }
            if !shifted.is_zero() {
                Arc::make_mut(&mut shifted.bits).push(0);
            }
        }
        result
    }

    /// Magnitude ordering is deliberately distinct from semantic identity
    /// ordering: Ord includes the exact numeric domain, while these private
    /// bit-arithmetic mechanisms must not compare domain tags as values.
    fn cmp_magnitude(&self, other: &Self) -> Ordering {
        self.width()
            .cmp(&other.width())
            .then_with(|| self.bits.cmp(&other.bits))
    }

    /// Exact subtraction in the natural Number slice. Underflow has no
    /// canonical natural result; signed encoding remains a separate law.
    /// The result is an unqualified mechanism magnitude, not Dn admission.
    pub fn checked_sub(&self, other: &Self) -> Option<Self> {
        if self.cmp_magnitude(other) == Ordering::Less {
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
        for &bit in self.bits.iter() {
            if remainder.is_zero() {
                Arc::make_mut(&mut remainder.bits)[0] = bit;
            } else {
                Arc::make_mut(&mut remainder.bits).push(bit);
            }
            if remainder.cmp_magnitude(divisor) != Ordering::Less {
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
        // GCD returns a private magnitude even if either source carries Dn.
        // Otherwise gcd(x, 0) would accidentally return a domain-qualified
        // value and later remainder comparisons could interpret tags as size.
        let mut a = Self::normalize(self.bits.as_ref().clone());
        let mut b = Self::normalize(other.bits.as_ref().clone());
        while !b.is_zero() {
            let (_, remainder) = a.div_rem(&b).expect("nonzero divisor");
            a = b;
            b = remainder;
        }
        a
    }

    /// Owner-ratified exact numeric domain family D12, D24, D48, D96, ...
    /// A width is legitimate only when it is 12 * 2^k, k >= 0.
    /// This checks domain-family membership, not physical transport or callability.
    pub fn is_numeric_domain_width(width: usize) -> bool {
        width >= 12 && width.is_multiple_of(12) && (width / 12).is_power_of_two()
    }

    /// Exact magnitude capacity of one admitted numeric domain.
    /// Domain identity must still be carried explicitly by the caller.
    pub fn fits_ratified_width(&self, width: usize) -> bool {
        Self::is_numeric_domain_width(width) && self.width() <= width
    }

    /// Mechanical realization of same-domain signed D12+ addition.
    /// Both operands must carry the same explicit Dn identity. The result
    /// remains Dn when representable or widens to the next D12+ rung.
    /// Returned bits retain the selected domain's FULL width.
    /// The (width, bits) pair is a mechanism boundary, not itself a SENS
    /// language value; generic mixed-domain coercion remains unratified.
    /// Both arguments MUST already carry the same explicit Dn identity.
    /// Passing a width alone must not promote an unqualified historical Number.
    pub fn add_in_numeric_domain(
        &self,
        other: &Self,
        input_domain_width: usize,
    ) -> Option<(usize, Vec<u8>)> {
        if !Self::is_numeric_domain_width(input_domain_width)
            || self.numeric_domain_width != Some(input_domain_width)
            || other.numeric_domain_width != Some(input_domain_width)
        {
            return None;
        }
        let result = self.add_admitted_numeric(other)?;
        let output_width = result.numeric_domain_width?;
        Some((output_width, result.exact_numeric_domain_bits()?))
    }

    /// Human-facing mathematical decimal projection without making a host
    /// integer the language identity. Explicit Dn words use two's complement;
    /// unqualified carrier values keep the unsigned magnitude projection.
    pub fn to_decimal_string(&self) -> String {
        let Some(_) = self.numeric_domain_width else {
            return self.to_unsigned_decimal_string();
        };
        let (negative, magnitude) = self.signed_magnitude().expect("valid Dn width");
        let decimal = magnitude.to_unsigned_decimal_string();
        if negative && !magnitude.is_zero() {
            format!("-{decimal}")
        } else {
            decimal
        }
    }

    /// Decimal projection of an unsigned bit magnitude, including private
    /// magnitude carriers inside a NEG/RATIO composition.
    pub fn to_unsigned_decimal_string(&self) -> String {
        Self::decimal_from_bits(&self.bits)
    }

    fn decimal_from_bits(bits: &[u8]) -> String {
        let mut digits = vec![0u8]; // little-endian base-10 mechanism digits
        for bit in bits {
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
    fn d12_signed_domain_preserves_identity_and_widens_without_wrap() {
        let mut maximum_bits = vec![1u8; 12];
        maximum_bits[0] = 0;
        let maximum = BinaryNumber::from_numeric_domain_bits(12, &maximum_bits).unwrap();

        let mut minimum_bits = vec![0u8; 12];
        minimum_bits[0] = 1;
        let minimum = BinaryNumber::from_numeric_domain_bits(12, &minimum_bits).unwrap();

        let minus_one = BinaryNumber::from_numeric_domain_bits(12, &[1u8; 12]).unwrap();
        let mut one_bits = vec![0u8; 12];
        one_bits[11] = 1;
        let one = BinaryNumber::from_numeric_domain_bits(12, &one_bits).unwrap();

        assert!(BinaryNumber::is_numeric_domain_width(12));
        assert!(BinaryNumber::is_numeric_domain_width(24));
        assert!(!BinaryNumber::is_numeric_domain_width(18));
        assert_eq!(maximum.numeric_domain_width(), Some(12));
        assert_eq!(maximum.to_decimal_string(), "2047");
        assert_eq!(minimum.numeric_domain_width(), Some(12));
        assert_eq!(minimum.to_decimal_string(), "-2048");
        assert_eq!(minus_one.to_decimal_string(), "-1");
        assert_eq!(maximum.exact_numeric_domain_bits(), Some(maximum_bits));

        let positive_overflow = maximum.add_admitted_numeric(&one).unwrap();
        assert_eq!(positive_overflow.numeric_domain_width(), Some(24));
        assert_eq!(positive_overflow.to_decimal_string(), "2048");

        let negative_overflow = minimum.checked_sub_admitted_numeric(&one).unwrap();
        assert_eq!(negative_overflow.numeric_domain_width(), Some(24));
        assert_eq!(negative_overflow.to_decimal_string(), "-2049");

        let same_payload_d24 = BinaryNumber::from_numeric_domain_bits(24, &[0u8; 24]).unwrap();
        assert!(maximum.add_admitted_numeric(&same_payload_d24).is_none());
        assert!(maximum.add_admitted_numeric(&BinaryNumber::one()).is_none());
        assert!(BinaryNumber::from_numeric_domain_bits(12, &[0u8; 11]).is_none());
    }

    #[test]
    fn d24_twos_complement_words_have_signed_decimal_projection() {
        let mut minus_five = vec![1u8; 24];
        minus_five[20..].copy_from_slice(&[1, 0, 1, 1]);
        let negative = BinaryNumber::from_numeric_domain_bits(24, &minus_five).unwrap();
        assert_eq!(negative.to_decimal_string(), "-5");

        let mut maximum = vec![1u8; 24];
        maximum[0] = 0;
        let positive = BinaryNumber::from_numeric_domain_bits(24, &maximum).unwrap();
        assert_eq!(positive.to_decimal_string(), "8388607");
        assert_eq!(
            BinaryNumber::from_numeric_domain_bits(24, &[0; 24])
                .unwrap()
                .to_decimal_string(),
            "0"
        );
    }

    #[test]
    fn d12_is_the_first_signed_numeric_domain_and_preserves_exact_boundaries() {
        assert!(BinaryNumber::is_numeric_domain_width(12));
        assert!(BinaryNumber::is_numeric_domain_width(24));
        assert!(BinaryNumber::is_numeric_domain_width(48));
        for width in [0usize, 1, 11, 13, 23, 25, 36, 60] {
            assert!(!BinaryNumber::is_numeric_domain_width(width), "D{width}");
        }

        let minimum =
            BinaryNumber::from_numeric_domain_bits(12, &[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                .unwrap();
        let maximum =
            BinaryNumber::from_numeric_domain_bits(12, &[0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
                .unwrap();
        let minus_one = BinaryNumber::from_numeric_domain_bits(12, &[1; 12]).unwrap();
        assert_eq!(minimum.numeric_domain_width(), Some(12));
        assert_eq!(maximum.numeric_domain_width(), Some(12));
        assert_eq!(minimum.to_decimal_string(), "-2048");
        assert_eq!(maximum.to_decimal_string(), "2047");
        assert_eq!(minus_one.to_decimal_string(), "-1");

        let one = BinaryNumber::from_numeric_domain_bits(12, &[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
            .unwrap();
        let two = one.add_admitted_numeric(&one).unwrap();
        assert_eq!(two.numeric_domain_width(), Some(12));
        assert_eq!(two.to_decimal_string(), "2");

        let carried = maximum.add_admitted_numeric(&one).unwrap();
        assert_eq!(carried.numeric_domain_width(), Some(24));
        assert_eq!(carried.to_decimal_string(), "2048");
        let borrowed = minimum.checked_sub_admitted_numeric(&one).unwrap();
        assert_eq!(borrowed.numeric_domain_width(), Some(24));
        assert_eq!(borrowed.to_decimal_string(), "-2049");

        let mut d24_two_bits = [0u8; 24];
        d24_two_bits[22] = 1;
        let d24_two = BinaryNumber::from_numeric_domain_bits(24, &d24_two_bits).unwrap();
        assert_eq!(two.to_decimal_string(), d24_two.to_decimal_string());
        assert_ne!(
            two, d24_two,
            "equal magnitudes in D12 and D24 keep distinct identities"
        );
        assert_eq!(two.add_admitted_numeric(&d24_two), None);
    }

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
    fn cloning_an_immutable_binary_number_shares_its_bit_storage() {
        let original = BinaryNumber::parse(&format!("1{}", "0".repeat(4095))).unwrap();
        let cloned = original.clone();

        assert!(
            std::ptr::eq(original.bits.as_ptr(), cloned.bits.as_ptr()),
            "evaluation clones should share immutable exact-number bits instead of copying them"
        );
        assert_eq!(original, cloned);
        assert_eq!(original.as_bits().len(), 4096);
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
    fn magnitude_mechanisms_do_not_compare_domain_identity_as_value() {
        // These are mechanism-only checks: no Dn arithmetic operation is
        // admitted by calling the raw unqualified helpers.
        let admitted = |width: usize, value: &str| {
            let magnitude = BinaryNumber::parse(value).unwrap();
            let mut word = vec![0; width - magnitude.width()];
            word.extend_from_slice(magnitude.as_bits());
            BinaryNumber::from_numeric_domain_bits(width, &word).unwrap()
        };
        let six = admitted(24, "110");
        let four = admitted(24, "100");
        let zero = admitted(24, "0");
        assert_ne!(six, BinaryNumber::parse("110").unwrap());
        assert_eq!(six.numeric_domain_width(), Some(24));

        assert_eq!(
            six.checked_sub(&four).unwrap(),
            BinaryNumber::parse("10").unwrap()
        );
        assert_eq!(four.checked_sub(&six), None);
        let (quotient, remainder) = six.div_rem(&four).unwrap();
        assert_eq!(quotient, BinaryNumber::one());
        assert_eq!(remainder, BinaryNumber::parse("10").unwrap());
        assert_eq!(six.gcd(&four), BinaryNumber::parse("10").unwrap());
        assert_eq!(six.gcd(&zero), BinaryNumber::parse("110").unwrap());
        assert_eq!(zero.gcd(&zero), BinaryNumber::zero());

        // The admitted Dn boundary still preserves D24 for outputs and
        // refuses a D24/D48 mixture; raw magnitude math changes no law.
        let (q, r) = six.div_rem_admitted_numeric(&four).unwrap();
        assert_eq!(q.numeric_domain_width(), Some(24));
        assert_eq!(r.numeric_domain_width(), Some(24));
        assert_eq!(q.exact_numeric_domain_bits().unwrap().len(), 24);
        assert_eq!(r.exact_numeric_domain_bits().unwrap().len(), 24);
        assert_eq!(six.div_rem_admitted_numeric(&admitted(48, "100")), None);
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
                    left.div_rem(&right).map(|(q, r)| (q.bits(), r.bits())),
                    a.checked_div(b)
                        .zip(a.checked_rem(b))
                        .map(|(q, r)| (format!("{q:b}"), format!("{r:b}")))
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
        // The number must already carry D24 identity; a width parameter
        // must never admit an old unqualified number after the fact.
        let mut max_word = vec![1; 24];
        max_word[0] = 0;
        let max = BinaryNumber::from_numeric_domain_bits(24, &max_word).unwrap();
        let (width, exact_bits) = max.add_in_numeric_domain(&max, 24).unwrap();
        assert_eq!(width, 48);
        assert_eq!(exact_bits.len(), 48);
        assert!(exact_bits[..width - 25].iter().all(|&bit| bit == 0));
        // Mechanism reduction to host integers is strictly an independent
        // oracle; the SENS result remains full exact D48 bits.
        let result = BinaryNumber::from_numeric_domain_bits(width, &exact_bits).unwrap();
        assert_eq!(
            result.to_decimal_string(),
            (2u64 * ((1u64 << 23) - 1)).to_string()
        );

        // Carry must not trigger promotion when a same-domain sum still fits.
        let mut one_word = vec![0; 24];
        one_word[23] = 1;
        let one = BinaryNumber::from_numeric_domain_bits(24, &one_word).unwrap();
        let (small_width, small_bits) = one.add_in_numeric_domain(&one, 24).unwrap();
        assert_eq!(small_width, 24);
        assert_eq!(small_bits.len(), 24);
        assert_eq!(&small_bits[..22], &[0; 22]);
        assert_eq!(&small_bits[22..], &[1, 0]);
    }

    #[test]
    fn numeric_domain_addition_widens_unbounded_rungs_and_rejects_bad_domains() {
        for width in [12, 24, 48, 96, 192, 384, 768] {
            let mut max_word = vec![1; width];
            max_word[0] = 0;
            let max = BinaryNumber::from_numeric_domain_bits(width, &max_word).unwrap();
            let (target_width, result) = max.add_in_numeric_domain(&max, width).unwrap();
            assert_eq!(target_width, width * 2);
            assert_eq!(result.len(), target_width);
            let mut expected = vec![0; width];
            expected.extend(std::iter::repeat_n(1, width - 1));
            expected.push(0);
            assert_eq!(result, expected);
            assert!(max.fits_ratified_width(width));
        }
        let mut one_word = vec![0; 24];
        one_word[23] = 1;
        let one = BinaryNumber::from_numeric_domain_bits(24, &one_word).unwrap();
        for invalid_width in [0, 1, 23, 25, 47, 72, 192 + 1] {
            assert_eq!(one.add_in_numeric_domain(&one, invalid_width), None);
        }
        let wide = BinaryNumber::from_bits(vec![1; 25]).unwrap();
        assert_eq!(wide.add_in_numeric_domain(&one, 24), None);
    }

    #[test]
    fn width_argument_never_admits_historical_unqualified_numbers() {
        for width in [24usize, 48, 96, 192] {
            let unqualified = BinaryNumber::one();
            let mut exact_one = vec![0; width];
            exact_one[width - 1] = 1;
            let qualified = BinaryNumber::from_numeric_domain_bits(width, &exact_one).unwrap();

            assert_eq!(unqualified.add_in_numeric_domain(&unqualified, width), None);
            assert_eq!(unqualified.add_in_numeric_domain(&qualified, width), None);
            assert_eq!(qualified.add_in_numeric_domain(&unqualified, width), None);
            let unqualified_zero = BinaryNumber::zero();
            assert_eq!(
                unqualified_zero.add_in_numeric_domain(&qualified, width),
                None
            );
            assert_eq!(
                qualified.add_in_numeric_domain(&unqualified_zero, width),
                None
            );
            let (result_width, result_bits) =
                qualified.add_in_numeric_domain(&qualified, width).unwrap();
            assert_eq!(result_width, width);
            assert_eq!(result_bits.len(), width);
            assert!(result_bits[..width - 2].iter().all(|&bit| bit == 0));
            assert_eq!(&result_bits[width - 2..], &[1, 0]);
        }
        let d24 = BinaryNumber::from_numeric_domain_bits(24, &[0; 24]).unwrap();
        let d48 = BinaryNumber::from_numeric_domain_bits(48, &[0; 48]).unwrap();
        assert_eq!(d24.add_in_numeric_domain(&d48, 24), None);
        assert_eq!(d24.add_in_numeric_domain(&d48, 48), None);
        assert_eq!(d48.add_in_numeric_domain(&d24, 24), None);
        assert_eq!(d48.add_in_numeric_domain(&d24, 48), None);
        assert_eq!(d24.add_in_numeric_domain(&d24, 48), None);
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
        assert_ne!(
            a,
            BinaryNumber::one(),
            "legacy unqualified value is not D24"
        );
        assert_eq!(a.cmp(&b), std::cmp::Ordering::Less);
        assert!(BinaryNumber::from_numeric_domain_bits(24, &[0; 23]).is_none());
        assert!(BinaryNumber::from_numeric_domain_bits(24, &[0; 25]).is_none());
        assert!(BinaryNumber::from_numeric_domain_bits(25, &[0; 25]).is_none());
        let mut invalid = d24;
        invalid[3] = 2;
        assert!(BinaryNumber::from_numeric_domain_bits(24, &invalid).is_none());
    }

    #[test]
    fn admitted_d24_arithmetic_uses_twos_complement_and_widens_signed_overflow() {
        let admitted =
            |bits: Vec<u8>| BinaryNumber::from_numeric_domain_bits(bits.len(), &bits).unwrap();
        let minus_one = admitted(vec![1; 24]);
        let one = admitted({
            let mut bits = vec![0; 24];
            bits[23] = 1;
            bits
        });
        let zero = minus_one.add_admitted_numeric(&one).unwrap();
        assert_eq!(zero.to_decimal_string(), "0");
        assert_eq!(zero.numeric_domain_width(), Some(24));

        let minus_two = admitted({
            let mut bits = vec![1; 24];
            bits[23] = 0;
            bits
        });
        let three = admitted({
            let mut bits = vec![0; 24];
            bits[22] = 1;
            bits[23] = 1;
            bits
        });
        assert_eq!(
            minus_two
                .mul_admitted_numeric(&three)
                .unwrap()
                .to_decimal_string(),
            "-6"
        );

        let minimum = admitted({
            let mut bits = vec![0; 24];
            bits[0] = 1;
            bits
        });
        let below_minimum = minimum.checked_sub_admitted_numeric(&one).unwrap();
        assert_eq!(below_minimum.numeric_domain_width(), Some(48));
        assert_eq!(below_minimum.to_decimal_string(), "-8388609");
    }

    #[test]
    fn admitted_d24_addition_promotes_through_real_domain_qualified_value() {
        let minus_one_bits = vec![1; 24];
        let minus_one = BinaryNumber::from_numeric_domain_bits(24, &minus_one_bits).unwrap();
        let negative_two = minus_one.add_admitted_numeric(&minus_one).unwrap();
        assert_eq!(negative_two.numeric_domain_width(), Some(24));
        assert_eq!(negative_two.to_decimal_string(), "-2");

        let mut maximum_positive_bits = vec![1; 24];
        maximum_positive_bits[0] = 0;
        let maximum_positive =
            BinaryNumber::from_numeric_domain_bits(24, &maximum_positive_bits).unwrap();
        let small = BinaryNumber::from_numeric_domain_bits(24, &[0; 24]).unwrap();
        let same = small.add_admitted_numeric(&small).unwrap();
        assert_eq!(same.numeric_domain_width(), Some(24));
        assert_eq!(same.exact_numeric_domain_bits(), Some(vec![0; 24]));
        let mut one_bits = vec![0; 24];
        one_bits[23] = 1;
        let one = BinaryNumber::from_numeric_domain_bits(24, &one_bits).unwrap();
        let widened = maximum_positive.add_admitted_numeric(&one).unwrap();
        assert_eq!(widened.numeric_domain_width(), Some(48));
        assert_eq!(widened.to_decimal_string(), (1i64 << 23).to_string());
        assert!(maximum_positive
            .add_admitted_numeric(&BinaryNumber::one())
            .is_none());
        let another_domain = BinaryNumber::from_numeric_domain_bits(48, &[0; 48]).unwrap();
        assert!(maximum_positive
            .add_admitted_numeric(&another_domain)
            .is_none());
    }

    #[test]
    fn d12_plus_same_domain_mul_sub_div_are_exact_and_closed() {
        let admitted = |width: usize, value: u64| {
            let mut word = vec![0; width];
            for i in 0..width.min(64) {
                word[width - 1 - i] = ((value >> i) & 1) as u8;
            }
            BinaryNumber::from_numeric_domain_bits(width, &word).unwrap()
        };
        for width in [12, 24, 48, 96, 192, 384] {
            let z = admitted(width, 0);
            let one = admitted(width, 1);
            let six = admitted(width, 6);
            let two = admitted(width, 2);
            assert_eq!(six.mul_admitted_numeric(&two).unwrap(), admitted(width, 12));
            assert_eq!(
                six.checked_sub_admitted_numeric(&two).unwrap(),
                admitted(width, 4)
            );
            assert_eq!(six.checked_sub_admitted_numeric(&six).unwrap(), z);
            assert_eq!(
                two.checked_sub_admitted_numeric(&six)
                    .unwrap()
                    .to_decimal_string(),
                "-4"
            );
            assert_eq!(
                six.div_rem_admitted_numeric(&two).unwrap(),
                (admitted(width, 3), z.clone())
            );
            assert_eq!(
                one.div_rem_admitted_numeric(&six).unwrap(),
                (z.clone(), one.clone())
            );
            assert!(six.div_rem_admitted_numeric(&z).is_none());
            assert_eq!(
                six.signed_difference_parts_admitted_numeric(&two).unwrap(),
                (false, BinaryNumber::parse("100").unwrap())
            );
            assert_eq!(
                two.signed_difference_parts_admitted_numeric(&six).unwrap(),
                (true, BinaryNumber::parse("100").unwrap())
            );
            let (negative, magnitude) = one.signed_difference_parts_admitted_numeric(&one).unwrap();
            assert!(!negative);
            assert!(magnitude.is_zero());
            assert!(z.can_be_negated_in_numeric_domain());
        }
        let a24 = admitted(24, 12);
        let b48 = admitted(48, 2);
        assert!(a24.mul_admitted_numeric(&b48).is_none());
        assert!(a24.checked_sub_admitted_numeric(&b48).is_none());
        assert!(a24.div_rem_admitted_numeric(&b48).is_none());
        assert!(a24.signed_difference_parts_admitted_numeric(&b48).is_none());
        assert!(a24.mul_admitted_numeric(&BinaryNumber::one()).is_none());
    }

    #[test]
    fn full_d12_plus_multiplication_promotes_to_exact_double_width() {
        for width in [12, 24, 48, 96, 192, 384] {
            let mut max_word = vec![1; width];
            max_word[0] = 0;
            let max = BinaryNumber::from_numeric_domain_bits(width, &max_word).unwrap();
            let product = max.mul_admitted_numeric(&max).unwrap();
            assert_eq!(product.numeric_domain_width(), Some(2 * width));
            assert!(product.width() <= 2 * width);
            let product_word = product.exact_numeric_domain_bits().unwrap();
            assert_eq!(product_word.len(), 2 * width);
            // Dn's positive maximum is 2^(n-1)-1; compare its exact square.
            let magnitude = BinaryNumber::from_bits(vec![1; width - 1]).unwrap();
            let raw_square = magnitude.mul(&magnitude);
            let mut expected = vec![0u8; 2 * width - raw_square.width()];
            expected.extend_from_slice(raw_square.as_bits());
            assert_eq!(product_word, expected);
            let zero_bits = vec![0; width];
            let zero = BinaryNumber::from_numeric_domain_bits(width, &zero_bits).unwrap();
            assert_eq!(
                max.mul_admitted_numeric(&zero)
                    .unwrap()
                    .numeric_domain_width(),
                Some(width)
            );
        }
    }

    #[test]
    fn d24_plus_arithmetic_matches_independent_small_integer_oracle() {
        let make = |n: u32| {
            let mut bits = vec![0u8; 24];
            for i in 0..24 {
                bits[23 - i] = ((n >> i) & 1) as u8;
            }
            BinaryNumber::from_numeric_domain_bits(24, &bits).unwrap()
        };
        for a in 0u32..64 {
            for b in 0u32..64 {
                let left = make(a);
                let right = make(b);
                let product = left.mul_admitted_numeric(&right).unwrap();
                assert_eq!(product.to_decimal_string(), (a * b).to_string());
                assert_eq!(product.numeric_domain_width(), Some(24));
                assert_eq!(
                    left.checked_sub_admitted_numeric(&right)
                        .map(|n| n.to_decimal_string()),
                    Some((a as i64 - b as i64).to_string())
                );
                assert_eq!(
                    left.signed_difference_parts_admitted_numeric(&right)
                        .map(|(negative, n)| (negative, n.to_decimal_string())),
                    Some((a < b, a.abs_diff(b).to_string()))
                );
                assert_eq!(
                    left.div_rem_admitted_numeric(&right)
                        .map(|(q, r)| (q.to_decimal_string(), r.to_decimal_string())),
                    a.checked_div(b)
                        .zip(a.checked_rem(b))
                        .map(|(q, r)| (q.to_string(), r.to_string()))
                );
            }
        }
    }

    #[test]
    fn d24_plus_twos_complement_words_preserve_signed_boundaries() {
        for width in [24, 48, 96, 192, 384] {
            let all_ones = vec![1; width];
            let minus_one = BinaryNumber::from_numeric_domain_bits(width, &all_ones).unwrap();
            assert_eq!(minus_one.to_decimal_string(), "-1");
            assert!(minus_one.can_be_negated_in_numeric_domain());
            let mut minimum_bits = vec![0; width];
            minimum_bits[0] = 1;
            let minimum = BinaryNumber::from_numeric_domain_bits(width, &minimum_bits).unwrap();
            let (negative, magnitude) = minimum.signed_magnitude().unwrap();
            assert!(negative);
            assert_eq!(magnitude.width(), width);
            assert_eq!(magnitude.as_bits()[0], 1);
            assert!(magnitude.as_bits()[1..].iter().all(|&bit| bit == 0));
            let zero = BinaryNumber::from_numeric_domain_bits(width, &zero_bits).unwrap();
            assert_eq!(zero.to_decimal_string(), "0");
            assert!(zero.can_be_negated_in_numeric_domain());
        }
        assert!(
            !BinaryNumber::one().can_be_negated_in_numeric_domain(),
            "unqualified historic Number cannot claim D24 NEG law"
        );
    }

    #[test]
    fn d24_plus_rational_parts_are_gcd_reduced_and_keep_component_domains() {
        let admitted = |width, n: u64| {
            let mut bits = vec![0; width];
            for index in 0..width.min(64) {
                bits[width - index - 1] = ((n >> index) & 1) as u8;
            }
            BinaryNumber::from_numeric_domain_bits(width, &bits).unwrap()
        };
        for width in [24usize, 48, 96, 192, 384] {
            let two = admitted(width, 2);
            let four = admitted(width, 4);
            let (n, d) = BinaryNumber::reduce_numeric_domain_ratio_parts(&two, &four)
                .expect("same-Dn reduced RATIO");
            assert_eq!(n, admitted(width, 1));
            assert_eq!(d, admitted(width, 2));
            assert_eq!(n.numeric_domain_width(), Some(width));
            assert_eq!(d.numeric_domain_width(), Some(width));
            assert_eq!(n.exact_numeric_domain_bits().unwrap().len(), width);
            assert_eq!(d.exact_numeric_domain_bits().unwrap().len(), width);

            let zero = admitted(width, 0);
            let five = admitted(width, 5);
            let (zn, zd) = BinaryNumber::reduce_numeric_domain_ratio_parts(&zero, &five)
                .expect("same-Dn zero numerator");
            assert_eq!(zn, zero);
            assert_eq!(zd, admitted(width, 1)); // Canonical Value collapses zero.
            let (an, ad) = BinaryNumber::reduce_numeric_domain_ratio_parts(
                &admitted(width, 15),
                &admitted(width, 3),
            )
            .expect("same-Dn unit denominator");
            assert_eq!(an, admitted(width, 5));
            assert_eq!(ad, admitted(width, 1));
            assert!(
                BinaryNumber::reduce_numeric_domain_ratio_parts(&two, &zero).is_none(),
                "D{width}: division by zero must fail"
            );
            assert!(
                BinaryNumber::reduce_numeric_domain_ratio_parts(&BinaryNumber::one(), &four)
                    .is_none()
            );
            assert!(
                BinaryNumber::reduce_numeric_domain_ratio_parts(&two, &BinaryNumber::one())
                    .is_none()
            );
        }
        for (numerator, denominator) in [
            (admitted(24, 2), admitted(48, 4)),
            (admitted(48, 2), admitted(24, 4)),
            (admitted(24, 0), admitted(48, 5)),
            (admitted(48, 0), admitted(24, 5)),
            (admitted(24, 15), admitted(48, 3)),
            (admitted(48, 15), admitted(24, 3)),
        ] {
            assert!(
                BinaryNumber::reduce_numeric_domain_ratio_parts(&numerator, &denominator).is_none(),
                "mixed exact Dn identities are not a rational composition"
            );
        }
        assert!(
            BinaryNumber::reduce_numeric_domain_ratio_parts(
                &BinaryNumber::parse("10").unwrap(),
                &BinaryNumber::parse("100").unwrap(),
            )
            .is_none(),
            "two unqualified Number values are not D24+"
        );
    }

    #[test]
    fn d24_plus_ratio_reduction_matches_independent_small_integer_oracle() {
        let admitted = |n: u32| {
            let mut word = vec![0u8; 24];
            for index in 0..24 {
                word[23 - index] = ((n >> index) & 1) as u8;
            }
            BinaryNumber::from_numeric_domain_bits(24, &word).unwrap()
        };
        let gcd = |mut a: u32, mut b: u32| -> u32 {
            while b != 0 {
                (a, b) = (b, a % b);
            }
            a
        };
        for numerator in 0..32 {
            for denominator in 1..32 {
                let (n, d) = BinaryNumber::reduce_numeric_domain_ratio_parts(
                    &admitted(numerator),
                    &admitted(denominator),
                )
                .unwrap();
                let divisor = gcd(numerator, denominator);
                assert_eq!(n.to_decimal_string(), (numerator / divisor).to_string());
                assert_eq!(d.to_decimal_string(), (denominator / divisor).to_string());
                assert_eq!(n.numeric_domain_width(), Some(24));
                assert_eq!(d.numeric_domain_width(), Some(24));
            }
        }
    }

    #[test]
    fn human_decimal_projection_is_not_semantic_identity() {
        assert_eq!(BinaryNumber::parse("101").unwrap().to_decimal_string(), "5");
        assert_eq!(
            BinaryNumber::parse("1111111111111111")
                .unwrap()
                .to_decimal_string(),
            "65535"
        );
    }
}
