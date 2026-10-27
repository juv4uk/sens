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

fn twos_complement_in_place(word: &mut [u8]) {
    for bit in word.iter_mut() {
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

fn is_nonempty_binary_word(bits: &[u8]) -> bool {
    !bits.is_empty() && bits.iter().all(|bit| *bit <= 1)
}

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
        let mut bits = Vec::with_capacity(text.len());
        for byte in text.bytes() {
            match byte {
                b'0' => bits.push(0),
                b'1' => bits.push(1),
                _ => return Err(BinaryNumberError::NonBit),
            }
        }
        Self::from_unqualified_bits(bits)
    }

    /// Build from mechanism bits, normalizing the same way as source input.
    pub fn from_bits(bits: impl IntoIterator<Item = u8>) -> Result<Self, BinaryNumberError> {
        Self::from_unqualified_bits(bits.into_iter().collect())
    }

    fn from_unqualified_bits(bits: Vec<u8>) -> Result<Self, BinaryNumberError> {
        if bits.is_empty() {
            return Err(BinaryNumberError::Empty);
        }
        if !is_nonempty_binary_word(&bits) {
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
        if !is_nonempty_binary_word(bits) {
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
            || !is_nonempty_binary_word(word)
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
            twos_complement_in_place(&mut word);
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
            twos_complement_in_place(&mut word);
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
            .then_with(|| self.cmp_magnitude(other))
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
