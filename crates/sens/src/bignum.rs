//! A small, hand-rolled arbitrary-precision signed integer, used only by
//! `Rational` (see `value.rs`). Deliberately not a crate dependency: this
//! crate stays at zero dependencies (see docs/language-core.md's
//! capability-free contract), and "Rust doing the low-level numeric
//! algorithm it's exceptionally good at" doesn't require pulling in a
//! third-party implementation of it — schoolbook algorithms, kept simple
//! and correct, not optimized for cryptographic-scale numbers this
//! language has no use for.
//! Malenke, napysane vruchnu tsile chyslo dovilnoi tochnosti zi znakom,
//! vykorystovuietsia lyshe `Rational` (dyv. `value.rs`). Navmysno ne
//! crate-zalezhnist: tsei kreit lyshaietsia na nulovii kilkosti
//! zalezhnostei (dyv. capability-free kontrakt u docs/language-core.md), a
//! "Rust, shcho robyt nyzkorivnevyi chyslovyi alhorytm, u yakomu vin
//! osoblyvo sylnyi" ne vymahaie pidtiahuvannia storonoi realizatsii —
//! shkilni alhorytmy, prosti y korektni, ne optymizovani pid chysla
//! kryptohrafichnoho masshtabu, yakym tsia mova ne znakhodyt zastosuvannia.
//! Eine kleine, von Hand geschriebene Ganzzahl beliebiger Genauigkeit mit
//! Vorzeichen, nur von `Rational` verwendet (siehe `value.rs`). Bewusst
//! keine Crate-Abhängigkeit: dieses Crate bleibt bei null Abhängigkeiten
//! (siehe den capability-freien Vertrag in docs/language-core.md), und
//! "Rust macht den Low-Level-Zahlenalgorithmus, in dem es besonders stark
//! ist" erfordert nicht, eine Drittanbieter-Implementierung davon
//! einzubinden — Schulbuch-Algorithmen, einfach und korrekt gehalten,
//! nicht für kryptografisch große Zahlen optimiert, für die diese Sprache
//! keine Verwendung hat.

use std::borrow::Cow;
use std::cmp::Ordering;
use std::fmt;
use std::str::FromStr;

/// Unsigned magnitude with two representations, kept in one canonical form:
/// every value that fits in 64 bits — including zero — lives inline in a
/// `u64` and allocates nothing; anything wider is a little-endian base-2^32
/// limb vector with no trailing zero limbs. The canonical shape is therefore
/// fixed: `Inline` for `0..=u64::MAX`, `Heap` only for values strictly wider
/// than 64 bits (so a `Heap` always has at least three limbs and a nonzero
/// top limb). Every constructor and every operation returns a value in that
/// shape, which keeps `PartialEq`/`Eq` (defined here as value equality via
/// `cmp`) a single canonical comparison.
/// Bezznakova velychyna z dvoma predstavlenniamy v odnii kanonichnii formi:
/// kozhne znachennia, shcho vmistytulia v 64 bity — vkliuchno z nulem —
/// lezhyt inline u `u64` i ne alokuye nichoho; vse shyrshe — tse
/// little-endian vektor limbiv bazy 2^32 bez kintsevykh nulovykh limbiv.
/// Kanonichna forma tozh fiksovana: `Inline` dlia `0..=u64::MAX`, `Heap`
/// lyshe dlia znachen stroho shyryshykh za 64 bity (tozh `Heap` zavzhdy maie
/// shchonaimenshe try limby i nenulovyi verkhniy limb). Kozhen konstruktor i
/// kozhna operatsiia povertaiut znachennia u tsii formi, shcho robyt
/// `PartialEq`/`Eq` (tut vyznacheni yak rivnist znachen cherez `cmp`)
/// yedynym kanonichnym porivnianniam.
/// Vorzeichenlose Größe mit zwei Darstellungen in einer kanonischen Form:
/// jeder Wert, der in 64 Bits passt — einschließlich Null — liegt inline in
/// einem `u64` und allokiert nichts; alles Breitere ist ein
/// Little-Endian-Limb-Vektor zur Basis 2^32 ohne abschließende Null-Limbs.
/// Die kanonische Gestalt ist damit festgelegt: `Inline` für `0..=u64::MAX`,
/// `Heap` nur für Werte, die strikt breiter als 64 Bits sind (ein `Heap` hat
/// daher immer mindestens drei Limbs und ein von null verschiedenes
/// oberstes Limb). Jeder Konstruktor und jede Operation liefert einen Wert
/// in dieser Gestalt, wodurch `PartialEq`/`Eq` (hier als Wertgleichheit über
/// `cmp` definiert) ein einziger kanonischer Vergleich bleibt.
#[derive(Clone, Debug)]
enum Magnitude {
    /// Values in `0..=u64::MAX`, zero included, held with no heap allocation.
    Inline(u64),
    /// Values strictly wider than 64 bits: little-endian base-2^32 limbs, no
    /// trailing zero limbs (at least three limbs, top limb nonzero).
    Heap(Vec<u32>),
}

impl Magnitude {
    const ZERO: Magnitude = Magnitude::Inline(0);
    const KARATSUBA_THRESHOLD: usize = 32;

    /// Canonical constructor from little-endian limbs: drops trailing zero
    /// limbs and folds anything that fits in 64 bits back into `Inline`, so
    /// every returned magnitude satisfies the canonical-shape invariant.
    fn from_limbs(mut limbs: Vec<u32>) -> Self {
        while limbs.last() == Some(&0) {
            limbs.pop();
        }
        match limbs.len() {
            0 => Magnitude::Inline(0),
            1 => Magnitude::Inline(u64::from(limbs[0])),
            2 => Magnitude::Inline(u64::from(limbs[0]) | (u64::from(limbs[1]) << 32)),
            _ => Magnitude::Heap(limbs),
        }
    }

    /// Canonical constructor from a 128-bit intermediate (sum or product of
    /// two inline values), folding back into `Inline` when it fits.
    fn from_u128(value: u128) -> Self {
        if value <= u64::MAX as u128 {
            Magnitude::Inline(value as u64)
        } else {
            Magnitude::from_limbs(vec![
                (value & 0xFFFF_FFFF) as u32,
                ((value >> 32) & 0xFFFF_FFFF) as u32,
                ((value >> 64) & 0xFFFF_FFFF) as u32,
                (value >> 96) as u32,
            ])
        }
    }

    fn from_u64(value: u64) -> Self {
        // The whole point of the inline branch: a value that fits in 64 bits
        // costs no heap allocation at all (no Vec, no growth, no capacity
        // guess). Zero stays the canonical `Inline(0)`.
        Magnitude::Inline(value)
    }

    /// Number of significant limbs (0 for zero) — the canonical limb count.
    fn limb_len(&self) -> usize {
        match self {
            Magnitude::Inline(value) => {
                if *value == 0 {
                    0
                } else if *value <= u32::MAX as u64 {
                    1
                } else {
                    2
                }
            }
            Magnitude::Heap(limbs) => limbs.len(),
        }
    }

    /// `index`-th base-2^32 limb (little-endian), `0` past the top — lets
    /// limb-wise readers work without materializing a slice for `Inline`.
    fn limb_at(&self, index: usize) -> u32 {
        match self {
            Magnitude::Inline(value) => match index {
                0 => (*value & 0xFFFF_FFFF) as u32,
                1 => (*value >> 32) as u32,
                _ => 0,
            },
            Magnitude::Heap(limbs) => limbs.get(index).copied().unwrap_or(0),
        }
    }

    /// Borrowed limbs for `Heap`, materialized once for `Inline`.
    fn limbs(&self) -> Cow<'_, [u32]> {
        match self {
            Magnitude::Heap(limbs) => Cow::Borrowed(limbs.as_slice()),
            Magnitude::Inline(_) => {
                let len = self.limb_len();
                Cow::Owned((0..len).map(|i| self.limb_at(i)).collect())
            }
        }
    }

    /// Number of trailing zero bits across all limbs (0 for zero magnitude).
    /// Kilkist kintsevykh nulovykh bitiv usikh limbiv.
    fn trailing_zeros(&self) -> u32 {
        match self {
            Magnitude::Inline(value) => {
                if *value == 0 {
                    0
                } else {
                    value.trailing_zeros()
                }
            }
            Magnitude::Heap(limbs) => {
                let mut zeros = 0u32;
                for limb in limbs {
                    if *limb == 0 {
                        zeros += 32;
                    } else {
                        zeros += limb.trailing_zeros();
                        break;
                    }
                }
                zeros
            }
        }
    }

    /// In-place logical right shift by `bits` (< total bit length).
    /// Pobitovyi zsun vpravo na `bits` bil in-place.
    fn shr_assign(&mut self, bits: u32) {
        if let Magnitude::Inline(value) = self {
            *self = if bits >= 64 {
                Magnitude::ZERO
            } else {
                Magnitude::Inline(*value >> bits)
            };
            return;
        }
        let Magnitude::Heap(limbs) = self else {
            unreachable!("matched Inline above")
        };
        let whole = (bits / 32) as usize;
        let rem = bits % 32;
        if whole >= limbs.len() {
            *self = Magnitude::ZERO;
            return;
        }
        if whole > 0 {
            limbs.drain(0..whole);
        }
        if rem > 0 {
            let mut carry = 0u32;
            for limb in limbs.iter_mut().rev() {
                let next_carry = *limb << (32 - rem);
                *limb = (*limb >> rem) | carry;
                carry = next_carry;
            }
        }
        let normalized = Magnitude::from_limbs(std::mem::take(limbs));
        *self = normalized;
    }

    /// Shift a limb vector left in place by `bits` (limb count may grow).
    fn shift_limbs_left(limbs: &mut Vec<u32>, bits: u32) {
        let whole = (bits / 32) as usize;
        let rem = bits % 32;
        if rem > 0 {
            let mut carry = 0u32;
            for limb in limbs.iter_mut() {
                let next_carry = *limb >> (32 - rem);
                *limb = (*limb << rem) | carry;
                carry = next_carry;
            }
            if carry != 0 {
                limbs.push(carry);
            }
        }
        if whole > 0 {
            limbs.splice(0..0, std::iter::repeat_n(0, whole));
        }
    }

    /// In-place logical left shift by `bits`.
    /// Pobitovyi zsun vlivo na `bits` bil.
    fn shl_assign(&mut self, bits: u32) {
        if let Magnitude::Inline(value) = self {
            let value = *value;
            if value == 0 {
                return;
            }
            if bits <= value.leading_zeros() {
                *self = Magnitude::Inline(value << bits);
                return;
            }
            let mut limbs = vec![value as u32, (value >> 32) as u32];
            Magnitude::shift_limbs_left(&mut limbs, bits);
            *self = Magnitude::from_limbs(limbs);
            return;
        }
        let Magnitude::Heap(limbs) = self else {
            unreachable!("matched Inline above")
        };
        Magnitude::shift_limbs_left(limbs, bits);
        let normalized = Magnitude::from_limbs(std::mem::take(limbs));
        *self = normalized;
    }

    fn is_zero(&self) -> bool {
        match self {
            Magnitude::Inline(value) => *value == 0,
            Magnitude::Heap(limbs) => limbs.is_empty(),
        }
    }

    fn trim(self) -> Self {
        match self {
            Magnitude::Inline(value) => Magnitude::Inline(value),
            Magnitude::Heap(limbs) => Magnitude::from_limbs(limbs),
        }
    }

    fn cmp(&self, other: &Self) -> Ordering {
        match (self, other) {
            (Magnitude::Inline(a), Magnitude::Inline(b)) => a.cmp(b),
            // Every inline value is below 2^64; every heap value is at or
            // above 2^64, so the branches never overlap.
            (Magnitude::Inline(_), Magnitude::Heap(_)) => Ordering::Less,
            (Magnitude::Heap(_), Magnitude::Inline(_)) => Ordering::Greater,
            (Magnitude::Heap(a), Magnitude::Heap(b)) => a
                .len()
                .cmp(&b.len())
                .then_with(|| a.iter().rev().cmp(b.iter().rev())),
        }
    }

    fn add(&self, other: &Self) -> Self {
        if let (Magnitude::Inline(a), Magnitude::Inline(b)) = (self, other) {
            return Magnitude::from_u128(u128::from(*a) + u128::from(*b));
        }
        let a = self.limbs();
        let b = other.limbs();
        let mut result = Vec::with_capacity(a.len().max(b.len()) + 1);
        let mut carry = 0u64;
        for i in 0..a.len().max(b.len()) {
            let sum = carry
                + u64::from(a.get(i).copied().unwrap_or(0))
                + u64::from(b.get(i).copied().unwrap_or(0));
            result.push((sum & 0xFFFF_FFFF) as u32);
            carry = sum >> 32;
        }
        if carry != 0 {
            result.push(carry as u32);
        }
        Magnitude::from_limbs(result)
    }

    /// Assumes `self >= other`; panics otherwise (only called that way from `BigInt`).
    fn sub(&self, other: &Self) -> Self {
        if let (Magnitude::Inline(a), Magnitude::Inline(b)) = (self, other) {
            debug_assert!(*a >= *b, "sub called with self < other");
            return Magnitude::Inline(*a - *b);
        }
        let a = self.limbs();
        let mut result = Vec::with_capacity(a.len());
        let mut borrow = 0i64;
        for i in 0..a.len() {
            let diff = i64::from(a[i]) - i64::from(other.limb_at(i)) - borrow;
            if diff < 0 {
                result.push((diff + (1i64 << 32)) as u32);
                borrow = 1;
            } else {
                result.push(diff as u32);
                borrow = 0;
            }
        }
        debug_assert_eq!(borrow, 0, "sub called with self < other");
        Magnitude::from_limbs(result)
    }

    fn mul_schoolbook(&self, other: &Self) -> Self {
        if self.is_zero() || other.is_zero() {
            return Magnitude::ZERO;
        }
        if let (Magnitude::Inline(a), Magnitude::Inline(b)) = (self, other) {
            return Magnitude::from_u128(u128::from(*a) * u128::from(*b));
        }
        let a = self.limbs();
        let b = other.limbs();
        let mut result = vec![0u32; a.len() + b.len()];
        for (i, &ai) in a.iter().enumerate() {
            let mut carry = 0u64;
            for (j, &bj) in b.iter().enumerate() {
                let product = u64::from(ai) * u64::from(bj) + u64::from(result[i + j]) + carry;
                result[i + j] = (product & 0xFFFF_FFFF) as u32;
                carry = product >> 32;
            }
            let mut k = i + b.len();
            while carry != 0 {
                let sum = u64::from(result[k]) + carry;
                result[k] = (sum & 0xFFFF_FFFF) as u32;
                carry = sum >> 32;
                k += 1;
            }
        }
        Magnitude::from_limbs(result)
    }

    fn shl_limbs(&self, limbs: usize) -> Self {
        if self.is_zero() {
            return Magnitude::ZERO;
        }
        let source = self.limbs();
        let mut shifted = Vec::with_capacity(source.len() + limbs);
        shifted.resize(limbs, 0);
        shifted.extend_from_slice(&source);
        Magnitude::from_limbs(shifted)
    }

    /// Karatsuba multiplication for large magnitudes; schoolbook remains the
    /// base case. The split uses the smaller operand so unbalanced products
    /// never index past a short limb vector.
    fn mul(&self, other: &Self) -> Self {
        if self.is_zero() || other.is_zero() {
            return Magnitude::ZERO;
        }
        let a = self.limbs();
        let b = other.limbs();
        if a.len().min(b.len()) < Self::KARATSUBA_THRESHOLD {
            return self.mul_schoolbook(other);
        }
        let split = a.len().min(b.len()) / 2;
        let a_low = Magnitude::from_limbs(a[..split].to_vec());
        let a_high = Magnitude::from_limbs(a[split..].to_vec());
        let b_low = Magnitude::from_limbs(b[..split].to_vec());
        let b_high = Magnitude::from_limbs(b[split..].to_vec());
        let z0 = a_low.mul(&b_low);
        let z2 = a_high.mul(&b_high);
        let z1 = a_low
            .add(&a_high)
            .mul(&b_low.add(&b_high))
            .sub(&z0)
            .sub(&z2);
        z2.shl_limbs(split * 2).add(&z1.shl_limbs(split)).add(&z0)
    }

    fn bit_len(&self) -> u32 {
        match self {
            Magnitude::Inline(value) => {
                if *value == 0 {
                    0
                } else {
                    64 - value.leading_zeros()
                }
            }
            Magnitude::Heap(limbs) => match limbs.last() {
                None => 0,
                Some(&top) => (limbs.len() as u32 - 1) * 32 + (32 - top.leading_zeros()),
            },
        }
    }

    fn get_bit(&self, index: u32) -> bool {
        match self {
            Magnitude::Inline(value) => index < 64 && (*value >> index) & 1 == 1,
            Magnitude::Heap(limbs) => {
                let limb = (index / 32) as usize;
                let bit = index % 32;
                limbs
                    .get(limb)
                    .is_some_and(|&value| (value >> bit) & 1 == 1)
            }
        }
    }

    fn shl1(&self) -> Self {
        match self {
            Magnitude::Inline(value) => Magnitude::from_u128(u128::from(*value) << 1),
            Magnitude::Heap(limbs) => {
                let mut result = Vec::with_capacity(limbs.len() + 1);
                let mut carry = 0u32;
                for &limb in limbs {
                    result.push((limb << 1) | carry);
                    carry = limb >> 31;
                }
                if carry != 0 {
                    result.push(carry);
                }
                Magnitude::from_limbs(result)
            }
        }
    }

    fn set_bit(&mut self, index: u32) {
        let limb = (index / 32) as usize;
        let bit = index % 32;
        match self {
            Magnitude::Inline(value) => {
                if index < 64 {
                    *value |= 1u64 << index;
                } else {
                    let mut limbs = vec![0u32; limb + 1];
                    limbs[0] = (*value & 0xFFFF_FFFF) as u32;
                    limbs[1] = (*value >> 32) as u32;
                    limbs[limb] |= 1 << bit;
                    *self = Magnitude::from_limbs(limbs);
                }
            }
            Magnitude::Heap(limbs) => {
                if limbs.len() <= limb {
                    limbs.resize(limb + 1, 0);
                }
                limbs[limb] |= 1 << bit;
            }
        }
    }

    /// Schoolbook binary long division — O(bit_len^2), not the fastest
    /// algorithm that exists, but correct regardless of quotient size (unlike
    /// repeated subtraction) and simple enough to read and trust. This
    /// language has no performance requirement that would justify anything
    /// more sophisticated (see the header comment).
    /// Shkilne binarne dovhe dilennia — O(bit_len^2), ne naishvydshyi
    /// alhorytm, shcho isnuie, ale korektnyi nezalezhno vid rozmiru chastky (na
    /// vidminu vid povtornoho vidnimannia) i dostatno prostyi, shchob chytaty
    /// y doviriaty. Tsia mova ne maie vymohy shvydkodii, yaka vypravdala b shchos
    /// skladnishe (dyv. header-komentar).
    /// Schulbuch-Binärlangdivision — O(bit_len^2), nicht der schnellste
    /// existierende Algorithmus, aber korrekt unabhängig von der Größe des
    /// Quotienten (anders als wiederholte Subtraktion) und einfach genug,
    /// um sie zu lesen und ihr zu vertrauen. Diese Sprache hat keine
    /// Performance-Anforderung, die etwas Ausgefeilteres rechtfertigen
    /// würde (siehe Header-Kommentar).
    fn divmod(&self, divisor: &Self) -> Option<(Self, Self)> {
        if divisor.is_zero() {
            return None;
        }
        if self.cmp(divisor) == Ordering::Less {
            return Some((Magnitude::ZERO, self.clone()));
        }
        let mut quotient = Magnitude::ZERO;
        let mut remainder = Magnitude::ZERO;
        let one = Magnitude::Inline(1);
        for i in (0..self.bit_len()).rev() {
            remainder = remainder.shl1();
            if self.get_bit(i) {
                remainder = remainder.add(&one);
            }
            if remainder.cmp(divisor) != Ordering::Less {
                remainder = remainder.sub(divisor);
                quotient.set_bit(i);
            }
        }
        Some((quotient.trim(), remainder))
    }

    fn to_f64(&self) -> f64 {
        match self {
            Magnitude::Inline(value) => *value as f64,
            Magnitude::Heap(limbs) => limbs
                .iter()
                .rev()
                .fold(0.0, |acc, &limb| acc * 4294967296.0 + f64::from(limb)),
        }
    }

    fn to_u64(&self) -> Option<u64> {
        match self {
            Magnitude::Inline(value) => Some(*value),
            // A heap magnitude is strictly wider than 64 bits by construction.
            Magnitude::Heap(_) => None,
        }
    }
}

impl PartialEq for Magnitude {
    fn eq(&self, other: &Self) -> bool {
        self.cmp(other) == Ordering::Equal
    }
}

impl Eq for Magnitude {}

/// Internal convenience mirroring the former tuple-struct constructor: build
/// a canonical magnitude from raw little-endian limbs. Used by the unit tests
/// below; kept out of non-test builds.
        }
        // Repeatedly divide by 10^9 so each step peels off up to nine decimal
        // digits at once instead of one, keeping this from being needlessly
        // slow for large numbers despite the O(n^2) division underneath.
        let mut chunks = Vec::new();
        let mut remaining = self.clone();
        let ten_to_nine = Magnitude::from_u64(1_000_000_000);
        while !remaining.is_zero() {
            let (quotient, remainder) = remaining.divmod(&ten_to_nine).expect("divisor is nonzero");
            chunks.push(remainder.to_u64().expect("< 10^9 fits in u64") as u32);
            remaining = quotient;
        }
        write!(formatter, "{}", chunks.pop().unwrap_or(0))?;
        for chunk in chunks.into_iter().rev() {
            write!(formatter, "{chunk:09}")?;
        }
        Ok(())
    }
}

/// An arbitrary-precision signed integer: sign plus magnitude. Zero is
/// always represented with `negative: false` so that `PartialEq`/`Eq` (both
/// derived) and `Magnitude`'s inline zero stay a single canonical form —
/// there's no separate "negative zero" this type could accidentally produce.
/// Tsile chyslo dovilnoi tochnosti zi znakom: znak plius velychyna. Nul
/// zavzhdy predstavlenyi z `negative: false`, tozh `PartialEq`/`Eq` (obydva
/// derived) i inline-nul `Magnitude` lyshaiutsia yedynoiu kanonichnoiu
/// formoiu — nemaie okremoho "vidiemnoho nulia", yakyi tsei typ mih by
/// vypadkovo vyrobyty.
/// Eine Ganzzahl beliebiger Genauigkeit mit Vorzeichen: Vorzeichen plus
/// Größe. Null wird immer mit `negative: false` dargestellt, sodass
/// `PartialEq`/`Eq` (beide derived) und `Magnitude`s Inline-Null eine
/// einzige kanonische Form bleiben — es gibt keine separate "negative
/// Null", die dieser Typ versehentlich erzeugen könnte.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BigInt {
    negative: bool,
    magnitude: Magnitude,
}

impl BigInt {
    pub fn from_i64(value: i64) -> Self {
        BigInt {
            negative: value < 0,
            magnitude: Magnitude::from_u64(value.unsigned_abs()),
        }
    }

    pub fn zero() -> Self {
        BigInt {
            negative: false,
            magnitude: Magnitude::ZERO,
        }
    }

    /// Parses an explicit base-2 integer used by the canonical numeric wire.
    /// This is not the ordinary source-number reader: the caller must already
    /// have selected the tagged wire grammar.
    pub(crate) fn from_binary_str(text: &str) -> Result<Self, ()> {
        let (negative, digits) = match text.strip_prefix('-') {
            Some(rest) => (true, rest),
            None => (false, text.strip_prefix('+').unwrap_or(text)),
        };
        if digits.is_empty() || !digits.bytes().all(|byte| matches!(byte, b'0' | b'1')) {
            return Err(());
        }

        let one = Magnitude::from_u64(1);
        let mut magnitude = Magnitude::ZERO;
        for byte in digits.bytes() {
            magnitude.shl_assign(1);
            if byte == b'1' {
                magnitude = magnitude.add(&one);
            }
        }
        Ok(Self::normalized(negative, magnitude))
    }

    /// Canonical base-2 spelling for the tagged numeric wire. Magnitude uses
    /// no leading zeros; zero is always exactly "0".
    pub(crate) fn to_binary_string(&self) -> String {
        if self.is_zero() {
            return "0".to_string();
        }
        let width = self.bit_length();
        let mut out = String::with_capacity(width + self.negative as usize);
        if self.negative {
            out.push('-');
        }
        for bit in (0..width).rev() {
            let limb = self.magnitude.limb_at(bit / 32);
            let value = (limb >> (bit % 32)) & 1;
            out.push(if value == 0 { '0' } else { '1' });
        }
        out
    }

    pub fn is_zero(&self) -> bool {
        self.magnitude.is_zero()
    }

    pub fn is_negative(&self) -> bool {
        self.negative
    }

    /// Bit width of the magnitude (sign ignored), `0` for zero itself —
    /// used only to enforce an *opt-in* numeric resource limit
    /// (`Environment::with_numeric_bit_limit`), never in ordinary
    /// arithmetic. The reference Rust implementation stays unbounded by
    /// default (see `docs/language-core-axioms.md`'s S1).
    /// Shyryna velychyny v bitakh (znak ihnoruietsia), `0` dlia samoho nulia —
    /// vykorystovuietsia lyshe dlia prymusovoho *optsiinoho* chyslovoho
    /// obmezhennia resursu (`Environment::with_numeric_bit_limit`), nikoly v
    /// zvychainii aryfmetytsi. Etalonna Rust-realizatsiia lyshaietsia
    /// neobmezhenoiu za zamovchuvanniam (dyv. S1 u `docs/language-core-axioms.md`).
    /// Remainder of self divided by a single-limb magnitude divisor.
    /// O(limbs) linear pass — used by the gcd small-operand fast path.
    fn rem_by_limb(&self, divisor: u32) -> u32 {
        let mut rem: u64 = 0;
        for i in (0..self.magnitude.limb_len()).rev() {
            rem = ((rem << 32) | (self.magnitude.limb_at(i) as u64)) % (divisor as u64);
        }
        rem as u32
    }

    /// FASL support: append sign + little-endian limb encoding to `out`.
    /// Pidtrymka FASL: znak + LE limby u `out`.
    pub(crate) fn write_fasl(&self, out: &mut Vec<u8>) {
        out.push(self.is_negative() as u8);
        let len = self.magnitude.limb_len();
        out.extend_from_slice(&(len as u32).to_le_bytes());
        for i in 0..len {
            out.extend_from_slice(&self.magnitude.limb_at(i).to_le_bytes());
        }
    }

    /// FASL inverse: parse what `write_fasl` produced. Returns None on
    /// truncation/corruption so callers fall back to text parsing.
    pub(crate) fn read_fasl(bytes: &[u8], pos: &mut usize) -> Option<Self> {
        let tag = *bytes.get(*pos)?;
        *pos += 1;
        let len = u32::from_le_bytes(bytes.get(*pos..*pos + 4)?.try_into().ok()?) as usize;
        *pos += 4;
        let mut limbs = Vec::with_capacity(len.min(1 << 20));
        for _ in 0..len {
            let limb = u32::from_le_bytes(bytes.get(*pos..*pos + 4)?.try_into().ok()?);
            *pos += 4;
            limbs.push(limb);
        }
        if tag > 1 {
            return None;
        }
        Some(Self::normalized(tag == 1, Magnitude::from_limbs(limbs)))
    }

    pub fn bit_length(&self) -> usize {
        self.magnitude.bit_len() as usize
    }

    fn normalized(negative: bool, magnitude: Magnitude) -> Self {
        let is_zero = magnitude.is_zero();
        BigInt {
            negative: negative && !is_zero,
            magnitude,
        }
    }

    pub fn neg(&self) -> Self {
        Self::normalized(!self.negative, self.magnitude.clone())
    }

    pub fn abs(&self) -> Self {
        Self::normalized(false, self.magnitude.clone())
    }

    pub fn add(&self, other: &Self) -> Self {
        if self.negative == other.negative {
            Self::normalized(self.negative, self.magnitude.add(&other.magnitude))
        } else {
            match self.magnitude.cmp(&other.magnitude) {
                Ordering::Equal => Self::zero(),
                Ordering::Greater => {
                    Self::normalized(self.negative, self.magnitude.sub(&other.magnitude))
                }
                Ordering::Less => {
                    Self::normalized(other.negative, other.magnitude.sub(&self.magnitude))
                }
            }
        }
    }

    pub fn sub(&self, other: &Self) -> Self {
        self.add(&other.neg())
    }

    pub fn mul(&self, other: &Self) -> Self {
        Self::normalized(
            self.negative != other.negative,
            self.magnitude.mul(&other.magnitude),
        )
    }

    /// Truncating division (remainder takes the dividend's sign, same as
    /// Rust's own `//%` on integers) — the only caller, `Rational`'s GCD
    /// reduction and exact-division-by-gcd, always works with either
    /// non-negative operands or a remainder it discards, so the rounding
    /// direction on negative operands is never actually observed.
    /// Dilennia z vidkydanniam (zalyshok bere znak dilenoho, tak samo yak
    /// vbudovani `/`/`%` Rust dlia tsilykh) — yedynyi vyklyk, skorochennia GCD i
    /// tochne dilennia na gcd u `Rational`, zavzhdy pratsiuie abo z nevidiemnymy
    /// operandamy, abo z zalyshkom, yakyi vidkydaietsia, tozh napriam
    /// okruhlennia dlia vidiemnykh operandiv naspravdi nikoly ne
    /// sposterihaietsia.
    /// Abschneidende Division (Rest übernimmt das Vorzeichen des
    /// Dividenden, genau wie Rusts eigene `/`/`%` bei Ganzzahlen) — der
    /// einzige Aufrufer, die GGT-Reduktion und exakte Division durch den
    /// GGT in `Rational`, arbeitet immer entweder mit nichtnegativen
    /// Operanden oder einem verworfenen Rest, daher wird die
    /// Rundungsrichtung bei negativen Operanden nie tatsächlich
    /// beobachtet.
    pub fn div_rem(&self, other: &Self) -> Option<(Self, Self)> {
        let (quotient, remainder) = self.magnitude.divmod(&other.magnitude)?;
        Some((
            Self::normalized(self.negative != other.negative, quotient),
            Self::normalized(self.negative, remainder),
        ))
    }

    pub fn cmp(&self, other: &Self) -> Ordering {
        match (self.negative, other.negative) {
            (false, true) => Ordering::Greater,
            (true, false) => Ordering::Less,
            (false, false) => self.magnitude.cmp(&other.magnitude),
            (true, true) => other.magnitude.cmp(&self.magnitude),
        }
    }

    pub fn to_f64(&self) -> f64 {
        let value = self.magnitude.to_f64();
        if self.negative {
            -value
        } else {
            value
        }
    }

    pub fn to_i64(&self) -> Option<i64> {
        let magnitude = self.magnitude.to_u64()?;
        if self.negative {
            (magnitude <= i64::MAX as u64 + 1).then(|| {
                if magnitude == i64::MAX as u64 + 1 {
                    i64::MIN
                } else {
                    -(magnitude as i64)
                }
            })
        } else {
            i64::try_from(magnitude).ok()
        }
    }

    /// Euclidean algorithm via `div_rem`; both inputs are used through
    /// their absolute value, so the result is always non-negative,
    /// matching the convention `Rational`'s reduction step expects.
    /// Alhorytm Evklida cherez `div_rem`; obydva vkhody vykorystovuiutsia
    /// cherez svii modul, tozh rezultat zavzhdy nevidiemnyi, vidpovidno do
    /// konventsii, yakoi ochikuie krok skorochennia `Rational`.
    /// Euklidischer Algorithmus über `div_rem`; beide Eingaben werden über
    /// ihren Absolutwert verwendet, daher ist das Ergebnis immer
    /// nichtnegativ, passend zur Konvention, die der Reduktionsschritt von
    /// `Rational` erwartet.
    pub fn gcd(&self, other: &Self) -> Self {
        // Fast path: huge × small (≤64-bit) — the rational-chain shape is
        // exactly gcd(giant accumulated denominator, small term denominator).
        // One linear pass computes giant % small, and from there both
        // operands are tiny; full binary stepping on equal-size giants
        // would be orders of magnitude slower.
        if other.magnitude.limb_len() == 1 && self.magnitude.limb_len() > 2 {
            let divisor = other.magnitude.limb_at(0);
            let r = self.rem_by_limb(divisor);
            let mut x = BigInt::from_i64(r as i64);
            let mut y = BigInt::from_i64(divisor as i64);
            while !y.is_zero() {
                let (_, rem) = x.div_rem(&y).expect("nonzero divisor");
                x = y;
                y = rem;
            }
            return x.abs();
        }
        // Stein's binary GCD: shifts and subtractions only — no div_rem.
        // Each Rational reduction step pays this cost, and div_rem-based
        // Euclid was the dominant term in exact-rational chains
        // (benchmarks/rational stress, WSM-24 shape).
        // Binarnyi gcd Shtaina: tilky zsuny ta vidnimannia — bez div_rem;
        // same skorochennia Rational platytse za tsei krok.
        if self.is_zero() {
            return other.abs();
        }
        if other.is_zero() {
            return self.abs();
        }
        let a_mag = self.abs().magnitude;
        let b_mag = other.abs().magnitude;
        let shared = a_mag.trailing_zeros().min(b_mag.trailing_zeros());
        let mut a = a_mag;
        a.shr_assign(a.trailing_zeros());
        let mut b = b_mag;
        loop {
            b.shr_assign(b.trailing_zeros());
            if a.cmp(&b) == Ordering::Greater {
                std::mem::swap(&mut a, &mut b);
            }
            b = b.sub(&a);
            if b.is_zero() {
                break;
            }
        }
        a.shl_assign(shared);
        BigInt::normalized(false, a)
    }
}

impl FromStr for BigInt {
    type Err = ();

    fn from_str(text: &str) -> Result<Self, Self::Err> {
        let (negative, digits) = match text.strip_prefix('-') {
            Some(rest) => (true, rest),
            None => (false, text.strip_prefix('+').unwrap_or(text)),
        };
        if digits.is_empty() || !digits.bytes().all(|b| b.is_ascii_digit()) {
            return Err(());
        }
        let mut magnitude = Magnitude::ZERO;
        let ten = Magnitude::from_u64(10);
        for byte in digits.bytes() {
            magnitude = magnitude
                .mul(&ten)
                .add(&Magnitude::from_u64(u64::from(byte - b'0')));
        }
        Ok(BigInt::normalized(negative, magnitude))
    }
}

impl fmt::Display for BigInt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.negative {
            write!(formatter, "-")?;
        }
        write!(formatter, "{}", self.magnitude)
    }
}

