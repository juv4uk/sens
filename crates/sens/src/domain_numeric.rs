//! Exact arithmetic for signed D12+ integers and exact NEG/RATIO compositions.
//! This is a Core VALUE mechanism, NOT a new SENS domain. Integer words use
//! two's complement; fraction components keep private unsigned magnitudes.
//! Domain identities remain explicit, with no host floats, mixed-domain
//! coercion, decimal literals, or invented binary semantic opcodes.
use crate::{BinaryNumber, Value};
use std::cmp::Ordering;

/// Executable canonical fractions over admitted D12/D24/... numeric domains.
///
/// Both unsigned-magnitude constituents retain the exact SAME admitted Dn.
/// Their sign and reduced rational shape are fraction-composition fields;
/// they do not reinterpret either component as a signed integer word.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DomainNumericComposition {
    // Private: only canonical() may construct these. Public enum variants
    // would allow callers to forge NEG(0), denominator=0 or unreduced RATIO.
    negative: bool,
    numerator: BinaryNumber,
    denominator: Option<BinaryNumber>, // None precisely for negative integer
}

impl DomainNumericComposition {
    pub fn domain_width(&self) -> usize {
        self.numerator
            .numeric_domain_width()
            .expect("admitted domain")
    }

    pub fn as_parts(&self) -> (bool, &BinaryNumber, Option<&BinaryNumber>) {
        (self.negative, &self.numerator, self.denominator.as_ref())
    }
}

fn normalized(a: &BinaryNumber) -> BinaryNumber {
    BinaryNumber::from_bits(a.as_bits().to_vec()).expect("admitted binary natural")
}

fn own_word(n: BinaryNumber, width: usize) -> Option<BinaryNumber> {
    if n.width() > width || !BinaryNumber::is_numeric_domain_width(width) {
        return None;
    }
    let mut bits = vec![0; width - n.width()];
    bits.extend_from_slice(n.as_bits());
    BinaryNumber::from_numeric_domain_bits(width, &bits)
}

/// Mathematical canonicalization. Invariants:
/// NEG(0) and RATIO(0,q) -> original domain-qualified zero;
/// RATIO(p,1) -> integer / NEG(integer);
/// otherwise gcd(num,den)=1, den>1, and no negative denominator.
fn canonical(
    negative: bool,
    numerator: BinaryNumber,
    denominator: BinaryNumber,
    minimum_width: usize,
) -> Option<Value> {
    if denominator.is_zero() || !BinaryNumber::is_numeric_domain_width(minimum_width) {
        return None;
    }
    let n = normalized(&numerator);
    let d = normalized(&denominator);
    let common = n.gcd(&d);
    let (n, nr) = n.div_rem(&common)?;
    let (d, dr) = d.div_rem(&common)?;
    if !nr.is_zero() || !dr.is_zero() {
        return None;
    }
    // Recognize the reduced unit before constructing an explicit Dn word.
    // BinaryNumber currently normalizes padded leading zeros, so checking
    // after own_word() also recognizes 1; doing it here avoids allocating
    // an entire temporary Dn denominator that integer/zero cases discard.
    let denominator_is_one = d.as_bits() == [1];

    let mut width = minimum_width;
    while n.width().max(d.width()) > width {
        width = width.checked_mul(2)?;
    }
    if n.is_zero() {
        return Some(Value::BinaryNumber(BinaryNumber::from_signed_magnitude(
            minimum_width,
            false,
            &n,
        )?));
    }
    if denominator_is_one {
        return Some(Value::BinaryNumber(
            BinaryNumber::from_signed_magnitude_growing(width, negative, &n)?,
        ));
    }
    let n = own_word(n, width)?;
    // Only an actual fraction needs a fully qualified Dn denominator.
    let d = own_word(d, width)?;
    Some(Value::NumericComposition(DomainNumericComposition {
        negative,
        numerator: n,
        denominator: Some(d),
    }))
}

fn ingredients(value: &Value) -> Option<(usize, bool, BinaryNumber, BinaryNumber)> {
    match value {
        Value::BinaryNumber(n) => {
            let width = n.numeric_domain_width()?;
            let (negative, magnitude) = n.signed_magnitude()?;
            Some((width, negative, magnitude, BinaryNumber::one()))
        }
        Value::NumericComposition(c) => {
            let width = c.domain_width();
            Some((
                width,
                c.negative,
                normalized(&c.numerator),
                c.denominator
                    .as_ref()
                    .map_or_else(BinaryNumber::one, normalized),
            ))
        }
        _ => None,
    }
}

/// Construct exact signed/rational Dn Value, preserving one base Dn or
/// growing only when its arithmetic result actually needs more bits.
pub fn canonical_parts(
    negative: bool,
    numerator: &BinaryNumber,
    denominator: &BinaryNumber,
) -> Option<Value> {
    let width = numerator.numeric_domain_width()?;
    if denominator.numeric_domain_width() != Some(width) {
        return None;
    }
    canonical(
        negative,
        normalized(numerator),
        normalized(denominator),
        width,
    )
}

/// Fast, non-semantic Dn admission. No rational cross-product, host magnitude
/// conversion, or shared binary prefix may stand in for the exact domain tag.
/// This does not compare mathematical values or authorize mixed-Dn coercion.
pub fn numeric_value_domain_width(value: &Value) -> Option<usize> {
    match value {
        Value::BinaryNumber(n) => n.numeric_domain_width(),
        Value::NumericComposition(c) => Some(c.domain_width()),
        _ => None,
    }
}

pub fn shared_numeric_domain_width(lhs: &Value, rhs: &Value) -> Option<usize> {
    let width = numeric_value_domain_width(lhs)?;
    (numeric_value_domain_width(rhs) == Some(width)).then_some(width)
}

pub fn is_domain_value(v: &Value) -> bool {
    numeric_value_domain_width(v).is_some()
}

/// Машинне обчислення двох доменно-допущених цілих D24/D48.
/// Точне зростання D24->D48 і D48->D96, без f64 і змішаних доменів.
fn signed_small_integer_fast(op: &str, lhs: &BinaryNumber, rhs: &BinaryNumber) -> Option<Value> {
    let width = lhs.numeric_domain_width()?;
    if !matches!(width, 24 | 48) || rhs.numeric_domain_width() != Some(width) {
        return None;
    }
    let decode = |number: &BinaryNumber| -> Option<i64> {
        let bits = number.exact_numeric_domain_bits()?;
        if bits.len() != width {
            return None;
        }
        let raw = bits.into_iter().fold(0_u64, |v, b| (v << 1) | u64::from(b));
        let shift = 64 - width;
        Some(((raw as i64) << shift) >> shift)
    };
    let (left, right) = (decode(lhs)?, decode(rhs)?);
    let math: i128 = match (width, op) {
        (24 | 48, "/") => i128::from(crate::machine_math::exact_small_integer_quotient(
            width, left, right,
        )?),
        (24, _) => i128::from(crate::machine_math::exact_i24_integer_op(op, left, right)?),
        (48, _) => crate::machine_math::exact_i48_integer_op(op, left, right)?,
        _ => return None,
    };
    let limit = 1_i128 << (width - 1);
    let out_width = if (-limit..=limit - 1).contains(&math) {
        width
    } else {
        2 * width
    };
    let bits = (0..out_width)
        .rev()
        .map(|shift| ((math >> shift) & 1) as u8)
        .collect::<Vec<_>>();
    Some(Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(
        out_width, &bits,
    )?))
}

/// Точний D96 × D96 -> D96 або D192, включно зі знаком і переповненням.
/// СЕНС уже перевірив однакові домени; ASM множить лише 96-бітні модулі.
fn signed_d96_mul_fast(lhs: &BinaryNumber, rhs: &BinaryNumber) -> Option<Value> {
    if lhs.numeric_domain_width() != Some(96) || rhs.numeric_domain_width() != Some(96) {
        return None;
    }
    let decode = |number: &BinaryNumber| -> Option<i128> {
        let word = number.exact_numeric_domain_bits()?;
        if word.len() != 96 {
            return None;
        }
        let raw = word
            .into_iter()
            .fold(0_u128, |acc, bit| (acc << 1) | u128::from(bit));
        Some(((raw as i128) << 32) >> 32)
    };
    let (a, b) = (decode(lhs)?, decode(rhs)?);
    let mut limbs = crate::machine_math::exact_u96_multiply(a.unsigned_abs(), b.unsigned_abs())?;
    let negative = (a < 0) != (b < 0) && limbs != [0, 0, 0];
    // Межа двійково-доповняльного D96: додатні <2^95,
    // від'ємні можуть дорівнювати -2^95.
    let fits = limbs[2] == 0
        && (limbs[1] < (1_u64 << 31) || (negative && limbs[1] == (1_u64 << 31) && limbs[0] == 0));
    let width = if fits { 96 } else { 192 };
    if negative {
        let mut carry = 1_u128;
        for limb in &mut limbs {
            let result = u128::from(!*limb) + carry;
            *limb = result as u64;
            carry = result >> 64;
        }
    }
    let bits = (0..width)
        .rev()
        .map(|shift| ((limbs[shift / 64] >> (shift % 64)) & 1) as u8)
        .collect::<Vec<_>>();
    Some(Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(
        width, &bits,
    )?))
}

/// Машинна сума/різниця двох допущених D96 з точним виходом D96/D192.
/// Знак старших бітів D192 продовжує знак результату i128.
fn signed_d96_add_sub_fast(op: &str, lhs: &BinaryNumber, rhs: &BinaryNumber) -> Option<Value> {
    if lhs.numeric_domain_width() != Some(96) || rhs.numeric_domain_width() != Some(96) {
        return None;
    }
    let decode = |number: &BinaryNumber| -> Option<i128> {
        let bits = number.exact_numeric_domain_bits()?;
        if bits.len() != 96 {
            return None;
        }
        let word = bits
            .into_iter()
            .fold(0_u128, |v, bit| (v << 1) | u128::from(bit));
        Some(((word as i128) << 32) >> 32)
    };
    let value = crate::machine_math::exact_i96_add_sub(op, decode(lhs)?, decode(rhs)?)?;
    let limit = 1_i128 << 95;
    let out_width = if (-limit..=limit - 1).contains(&value) {
        96
    } else {
        192
    };
    let bits = (0..out_width)
        .rev()
        .map(|shift| {
            if shift >= 128 {
                u8::from(value < 0)
            } else {
                ((value >> shift) & 1) as u8
            }
        })
        .collect::<Vec<_>>();
    Some(Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(
        out_width, &bits,
    )?))
}

/// Точний ASM ADD/SUB для знакових D192 та наступних D(24·2^k).
///
/// Вхідні слова зберігають ЯВНУ доменну ідентичність; ASM не вирішує
/// допуск або розширення. Додаємо 64-бітний знаковий резерв, щоб
/// результат Dn + Dn не загубив перенос. Вихід лише Dn або D(2n).
fn signed_wide_add_sub_fast(op: &str, lhs: &BinaryNumber, rhs: &BinaryNumber) -> Option<Value> {
    let width = lhs.numeric_domain_width()?;
    if width < 192 || width % 64 != 0 || rhs.numeric_domain_width() != Some(width) {
        return None;
    }
    let words_count = width / 64;
    let read = |n: &BinaryNumber| -> Option<Vec<u64>> {
        let bits = n.exact_numeric_domain_bits()?;
        if bits.len() != width {
            return None;
        }
        let mut words = Vec::with_capacity(words_count + 1);
        for block in bits.rchunks(64) {
            let mut value = 0_u64;
            for bit in block {
                value = (value << 1) | u64::from(*bit);
            }
            words.push(value);
        }
        words.push(if bits[0] == 1 { u64::MAX } else { 0 });
        Some(words)
    };
    let left = read(lhs)?;
    let right = read(rhs)?;
    let result = crate::machine_math::exact_words_add_sub(op, &left, &right)?;
    // Якщо додаткове слово дорівнює знаковому розширенню Dn, Dn вистачає.
    // Інакше рівно наступний ратифікований D(2n), без кругового переповнення.
    let sign = result[words_count - 1] >> 63 != 0;
    let sign_extension = if sign { u64::MAX } else { 0 };
    let fits = result[words_count] == sign_extension;
    let result_width = if fits { width } else { width.checked_mul(2)? };
    let mut output_words = if fits {
        result[..words_count].to_vec()
    } else {
        let top_sign = result[words_count] >> 63 != 0;
        let mut full = result;
        full.resize(result_width / 64, if top_sign { u64::MAX } else { 0 });
        full
    };
    if output_words.len().checked_mul(64)? != result_width {
        return None;
    }
    let mut bits = Vec::with_capacity(result_width);
    for word in output_words.drain(..).rev() {
        for shift in (0..64).rev() {
            bits.push(((word >> shift) & 1) as u8);
        }
    }
    Some(Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(
        result_width,
        &bits,
    )?))
}

/// Точне ASM-множення знакових D192/D384/... без семантичного дублювання.
///
/// Тільки числа з двох однакових ратифікованих доменів. Машинний
/// механізм множить модулі, а SENS встановлює знак та Dn/D(2n).
fn signed_wide_mul_fast(lhs: &BinaryNumber, rhs: &BinaryNumber) -> Option<Value> {
    let width = lhs.numeric_domain_width()?;
    if width < 192 || width % 64 != 0 || rhs.numeric_domain_width() != Some(width) {
        return None;
    }
    let n = width / 64;
    let double_width = width.checked_mul(2)?;
    let unsigned_magnitude = |number: &BinaryNumber| -> Option<(bool, Vec<u64>)> {
        let bits = number.exact_numeric_domain_bits()?;
        if bits.len() != width {
            return None;
        }
        let negative = bits[0] == 1;
        let mut limbs = bits
            .rchunks(64)
            .map(|part| {
                part.iter()
                    .fold(0_u64, |acc, bit| (acc << 1) | u64::from(*bit))
            })
            .collect::<Vec<_>>();
        if negative {
            let mut carry = true;
            for word in &mut limbs {
                let (value, next) = (!*word).overflowing_add(u64::from(carry));
                *word = value;
                carry = next;
            }
        }
        Some((negative, limbs))
    };
    let (left_sign, left) = unsigned_magnitude(lhs)?;
    let (right_sign, right) = unsigned_magnitude(rhs)?;
    let mut product = crate::machine_math::exact_words_mul_unsigned(&left, &right)?;
    if product.len() != n.checked_mul(2)? {
        return None;
    }
    let negative = left_sign != right_sign && product.iter().any(|&word| word != 0);
    let fits = product[n..].iter().all(|&word| word == 0)
        && (product[n - 1] < (1_u64 << 63)
            || (negative
                && product[n - 1] == (1_u64 << 63)
                && product[..n - 1].iter().all(|&word| word == 0)));
    let out_width = if fits { width } else { double_width };
    if negative {
        let mut carry = true;
        for word in &mut product {
            let (value, next) = (!*word).overflowing_add(u64::from(carry));
            *word = value;
            carry = next;
        }
    }
    let result_words = if fits { &product[..n] } else { &product[..] };
    let mut bits = Vec::with_capacity(out_width);
    for &word in result_words.iter().rev() {
        for shift in (0..64).rev() {
            bits.push(((word >> shift) & 1) as u8);
        }
    }
    Some(Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(
        out_width, &bits,
    )?))
}

/// Точна цілочисельна частка двох вже допущених знакових D96+.
/// Машинний дільник може займати довільну кількість слів. Для ненульової остачі
/// виконується попередній канонічний закон RATIO — без округлення.
fn signed_wide_div_exact_fast(lhs: &BinaryNumber, rhs: &BinaryNumber) -> Option<Value> {
    let width = lhs.numeric_domain_width()?;
    if width < 96 || rhs.numeric_domain_width() != Some(width) {
        return None;
    }
    let (a_negative, a) = lhs.signed_magnitude()?;
    let (b_negative, b) = rhs.signed_magnitude()?;
    if b.is_zero() {
        return None;
    }
    // Довільна ширина дільника: маленький використовує DIVQ, широкий SBB.
    // Ідентичність числового домену вже перевірена, жодного f64.
    let unpack = |n: &BinaryNumber| -> Vec<u64> {
        n.as_bits()
            .rchunks(64)
            .map(|part| {
                part.iter()
                    .fold(0_u64, |bits, bit| (bits << 1) | u64::from(*bit))
            })
            .collect()
    };
    let mut limbs = unpack(&a);
    let mut divisor = unpack(&b);
    let n = limbs.len().max(divisor.len());
    limbs.resize(n, 0);
    divisor.resize(n, 0);
    let (quotient, remainder) =
        crate::machine_math::exact_words_div_rem_unsigned(&limbs, &divisor)?;
    if remainder.iter().any(|&word| word != 0) {
        return None;
    }
    let bits = quotient
        .iter()
        .rev()
        .flat_map(|limb| (0..64).rev().map(move |shift| ((limb >> shift) & 1) as u8))
        .collect::<Vec<_>>();
    let magnitude = BinaryNumber::from_bits(bits).ok()?;
    let signed =
        BinaryNumber::from_signed_magnitude_growing(width, a_negative != b_negative, &magnitude)?;
    Some(Value::BinaryNumber(signed))
}

/// Exactly two operands in the SAME Dn; arithmetic creates no unqualified
/// identity. The specific result-domain growth is explicit and validated.
pub fn compute(operator: &str, lhs: &Value, rhs: &Value) -> Option<Value> {
    // Reject mixed-domain or unqualified operands BEFORE cloning potentially
    // wide rational constituents into the private calculation.
    let width = shared_numeric_domain_width(lhs, rhs)?;
    // Для широких Dn машинний DIVQ повертає лише точні цілі частки.
    // Остача або великий дільник переходять до існуючого RATIO.
    if width >= 96 && operator == "/" {
        if let (Value::BinaryNumber(left), Value::BinaryNumber(right)) = (lhs, rhs) {
            if let Some(result) = signed_wide_div_exact_fast(left, right) {
                return Some(result);
            }
        }
    }
    // У D24/D48 машинний IDIV працює лише для цілих часток.
    // Із ненульовою остачею повертаємося до точного закону RATIO.
    if matches!(width, 24 | 48) && matches!(operator, "+" | "-" | "*" | "/") {
        if let (Value::BinaryNumber(left), Value::BinaryNumber(right)) = (lhs, rhs) {
            if let Some(result) = signed_small_integer_fast(operator, left, right) {
                return Some(result);
            }
            if operator != "/" {
                return None;
            }
        }
    }
    // Два допущені цілі D96: +/- через ADC/SBB, * через повний 192-бітний MUL.
    if width == 96 && matches!(operator, "+" | "-" | "*") {
        if let (Value::BinaryNumber(left), Value::BinaryNumber(right)) = (lhs, rhs) {
            return if operator == "*" {
                signed_d96_mul_fast(left, right)
            } else {
                signed_d96_add_sub_fast(operator, left, right)
            };
        }
    }
    // D192+ цілі: ASM ADD/SUB/MUL; доменний закон зберігає знак і Dn.
    if width >= 192 && matches!(operator, "+" | "-" | "*") {
        if let (Value::BinaryNumber(left), Value::BinaryNumber(right)) = (lhs, rhs) {
            return if operator == "*" {
                signed_wide_mul_fast(left, right)
            } else {
                signed_wide_add_sub_fast(operator, left, right)
            };
        }
    }
    let (_, x_neg, x_num, x_den) = ingredients(lhs)?;
    let (_, y_neg, y_num, y_den) = ingredients(rhs)?;

    let (negative, numerator, denominator) = match operator {
        "+" | "-" => {
            let y_effective_neg = if operator == "-" { !y_neg } else { y_neg };
            let xn = x_num.mul(&y_den);
            let yn = y_num.mul(&x_den);
            let d = x_den.mul(&y_den);
            let (neg, num) = if x_neg == y_effective_neg {
                (x_neg, xn.add(&yn))
            } else if xn >= yn {
                (x_neg, xn.checked_sub(&yn)?)
            } else {
                (y_effective_neg, yn.checked_sub(&xn)?)
            };
            (neg, num, d)
        }
        "*" => (x_neg ^ y_neg, x_num.mul(&y_num), x_den.mul(&y_den)),
        "/" => {
            if y_num.is_zero() {
                return None;
            }
            (x_neg ^ y_neg, x_num.mul(&y_den), x_den.mul(&y_num))
        }
        _ => return None,
    };
    canonical(negative, numerator, denominator, width)
}

pub fn unary(operator: &str, value: &Value) -> Option<Value> {
    let (width, negative, n, d) = ingredients(value)?;
    match operator {
        "-" => canonical(!negative, n, d, width),
        "/" if !n.is_zero() => canonical(negative, d, n, width),
        _ => None,
    }
}

/// Exact mathematical signed-rational compare under one explicit Dn.
/// The semantic identity in Value::eq remains domain-qualified and structural.
pub fn compare(operator: &str, lhs: &Value, rhs: &Value) -> Option<bool> {
    // Admitted integer values already carry their exact D24/D48/... identity.
    // Compare their normalized binary magnitudes directly: the generic
    // rational path below allocates four clones and two products needlessly.
    // Domain width is checked BEFORE comparing; equal naked bits in
    // different domains must never become comparable through this shortcut.
    if let (Value::BinaryNumber(left), Value::BinaryNumber(right)) = (lhs, rhs) {
        let width = left.numeric_domain_width()?;
        if right.numeric_domain_width() != Some(width) {
            return None;
        }
        let (left_negative, left_magnitude) = left.signed_magnitude()?;
        let (right_negative, right_magnitude) = right.signed_magnitude()?;
        let order = match (left_negative, right_negative) {
            (true, false) => Ordering::Less,
            (false, true) => Ordering::Greater,
            (negative, _) => {
                let magnitude_order = left_magnitude.cmp(&right_magnitude);
                if negative {
                    magnitude_order.reverse()
                } else {
                    magnitude_order
                }
            }
        };
        return Some(match operator {
            "=" => order == Ordering::Equal,
            "<" => order == Ordering::Less,
            ">" => order == Ordering::Greater,
            _ => return None,
        });
    }

    // The generic signed/rational comparison needs exact products only after
    // both operands have independently passed the domain-identity gate.
    shared_numeric_domain_width(lhs, rhs)?;
    let (_, x_neg, xn, xd) = ingredients(lhs)?;
    let (_, y_neg, yn, yd) = ingredients(rhs)?;
    let order = match (x_neg, y_neg) {
        (true, false) => Ordering::Less,
        (false, true) => Ordering::Greater,
        (left_neg, _) => {
            let cmp = xn.mul(&yd).cmp(&yn.mul(&xd));
            if left_neg {
                cmp.reverse()
            } else {
                cmp
            }
        }
    };
    Some(match operator {
        "=" => order == Ordering::Equal,
        "<" => order == Ordering::Less,
        ">" => order == Ordering::Greater,
        _ => return None,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn d(width: usize, u: u64) -> BinaryNumber {
        let mut bits = vec![0; width];
        for i in 0..width.min(64) {
            bits[width - 1 - i] = ((u >> i) & 1) as u8;
        }
        BinaryNumber::from_numeric_domain_bits(width, &bits).unwrap()
    }

    #[test]
    fn wide_divisor_machine_path_preserves_exact_domain_and_ratio() {
        let word = |width: usize, powers: &[usize]| -> Value {
            let mut bits = vec![0_u8; width];
            for &bit in powers {
                bits[width - 1 - bit] = 1;
            }
            Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(width, &bits).unwrap())
        };
        // Дільник у кожному випадку ширший за одне машинне слово.
        for (width, high, divisor_bit) in [
            (96_usize, 85_usize, 65_usize),
            (192, 170, 110),
            (384, 320, 210),
            (768, 700, 510),
        ] {
            let numerator = word(width, &[high, divisor_bit]);
            let divisor = word(width, &[divisor_bit]);
            let expected = word(width, &[high - divisor_bit, 0]);
            let quotient = compute("/", &numerator, &divisor).unwrap();
            assert_eq!(quotient, expected, "D{width}: точна ціла частка");

            // За ненульової остачі залишається вже ратифікована
            // канонічна дробова композиція, а не округлена частка.
            let fractional = word(width, &[high, 0]);
            let actual = compute("/", &fractional, &divisor).unwrap();
            let (_, a_neg, a_num, a_den) = ingredients(&fractional).unwrap();
            let (_, b_neg, b_num, b_den) = ingredients(&divisor).unwrap();
            let previous_law =
                canonical(a_neg ^ b_neg, a_num.mul(&b_den), a_den.mul(&b_num), width).unwrap();
            assert_eq!(actual, previous_law, "D{width}: остача не загублена");
            assert!(compute("/", &numerator, &word(width * 2, &[1])).is_none());
            assert!(compute("/", &numerator, &word(width, &[])).is_none());
        }
    }

    #[test]
    fn wide_divrem_respects_full_d96_plus_semantics_and_fractions() {
        let admitted = |width: usize, n: i64| -> Value {
            let bits = (0..width)
                .rev()
                .map(|shift| {
                    if shift >= 64 {
                        u8::from(n < 0)
                    } else {
                        ((n >> shift) & 1) as u8
                    }
                })
                .collect::<Vec<_>>();
            Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(width, &bits).unwrap())
        };
        for width in [96_usize, 192, 384, 768] {
            for (a, b, expected) in [
                (6, 3, "2"),
                (-6, 3, "-2"),
                (6, -3, "-2"),
                (-6, -3, "2"),
                (0, 3, "0"),
                (7, 3, "7/3"),
                (-7, 3, "-7/3"),
                (7, -3, "-7/3"),
            ] {
                let left = admitted(width, a);
                let right = admitted(width, b);
                let got = compute("/", &left, &right).unwrap();
                assert_eq!(got.to_string(), expected, "D{width}: {a}/{b}");
                let (_, an, am, ad) = ingredients(&left).unwrap();
                let (_, bn, bm, bd) = ingredients(&right).unwrap();
                let original = canonical(an ^ bn, am.mul(&bd), ad.mul(&bm), width).unwrap();
                assert_eq!(got, original, "D{width}: бітово точний попередній закон");
            }
            let mut min_bits = vec![0; width];
            min_bits[0] = 1;
            let min = Value::BinaryNumber(
                BinaryNumber::from_numeric_domain_bits(width, &min_bits).unwrap(),
            );
            let out = compute("/", &min, &admitted(width, -1)).unwrap();
            let Value::BinaryNumber(ref number) = out else {
                panic!("ціле Dn");
            };
            assert_eq!(number.numeric_domain_width(), Some(width * 2));
            let mut expected_bits = vec![0; width * 2];
            expected_bits[width] = 1;
            assert_eq!(number.exact_numeric_domain_bits().unwrap(), expected_bits);
            assert!(compute("/", &admitted(width, 1), &admitted(width * 2, 1)).is_none());
            assert!(compute("/", &admitted(width, 1), &admitted(width, 0)).is_none());
        }
    }

    #[test]
    fn d24_d48_idiv_integrates_without_losing_rational_or_domain_laws() {
        let number = |width: usize, value: i64| -> Value {
            let bits = (0..width)
                .rev()
                .map(|i| ((value >> i) & 1) as u8)
                .collect::<Vec<_>>();
            Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(width, &bits).unwrap())
        };
        for width in [24_usize, 48] {
            let min = -(1_i64 << (width - 1));
            for (a, b, expected, overflow) in [
                (6, 3, "2", false),
                (-6, 3, "-2", false),
                (6, -3, "-2", false),
                (-6, -3, "2", false),
                (0, 3, "0", false),
                (min, -1, "wide", true),
                (7, 3, "7/3", false),
                (-7, 3, "-7/3", false),
                (7, -3, "-7/3", false),
                (-7, -3, "7/3", false),
            ] {
                let value = compute("/", &number(width, a), &number(width, b)).unwrap();
                assert_eq!(
                    value.to_string(),
                    if overflow {
                        (1_i64 << (width - 1)).to_string()
                    } else {
                        expected.to_owned()
                    }
                );
                if a % b == 0 {
                    let Value::BinaryNumber(ref integer) = value else {
                        panic!("точна ціла частка");
                    };
                    assert_eq!(
                        integer.numeric_domain_width(),
                        Some(if overflow { width * 2 } else { width })
                    );
                } else {
                    assert!(matches!(value, Value::NumericComposition(_)));
                }
            }
            assert!(compute("/", &number(width, 1), &number(width, 0)).is_none());
        }
        assert!(compute("/", &number(24, 6), &number(48, 3)).is_none());
        assert!(compute(
            "/",
            &Value::BinaryNumber(BinaryNumber::one()),
            &number(24, 1)
        )
        .is_none());
    }

    #[test]
    fn wide_asm_seeded_full_domain_parity() {
        // Чинний закон SENS — незалежний оракул: старе точне
        // множення двійкових величин та канонічний результат, а не ASM.
        // Це реальний Value/DomainNumeric шлях, а не текстовий муляж.
        fn admitted(width: usize, state: &mut u64) -> Value {
            let mut bits = Vec::with_capacity(width);
            for _ in 0..width {
                *state ^= *state << 13;
                *state ^= *state >> 7;
                *state ^= *state << 17;
                bits.push((*state >> 63) as u8);
            }
            Value::BinaryNumber(
                BinaryNumber::from_numeric_domain_bits(width, &bits).expect("точний D24+ домен"),
            )
        }
        let mut state = 0xc3a5_c85c_97cb_3127_u64;
        for width in [24_usize, 48, 96, 192, 384, 768] {
            for case in 0..5 {
                let left = admitted(width, &mut state);
                let right = admitted(width, &mut state);
                let (_, x_negative, x_num, x_den) = ingredients(&left).unwrap();
                let (_, y_negative, y_num, y_den) = ingredients(&right).unwrap();
                for op in ["+", "-", "*"] {
                    let (negative, numerator, denominator) = match op {
                        "+" | "-" => {
                            let y_sign = if op == "-" { !y_negative } else { y_negative };
                            let xn = x_num.mul(&y_den);
                            let yn = y_num.mul(&x_den);
                            let d = x_den.mul(&y_den);
                            if x_negative == y_sign {
                                (x_negative, xn.add(&yn), d)
                            } else if xn >= yn {
                                (x_negative, xn.checked_sub(&yn).unwrap(), d)
                            } else {
                                (y_sign, yn.checked_sub(&xn).unwrap(), d)
                            }
                        }
                        "*" => (
                            x_negative ^ y_negative,
                            x_num.mul(&y_num),
                            x_den.mul(&y_den),
                        ),
                        _ => unreachable!(),
                    };
                    let expected = canonical(negative, numerator, denominator, width)
                        .expect("точний нормативний механізм");
                    let actual = compute(op, &left, &right).expect("чинне виконання домену");
                    assert_eq!(actual, expected, "D{width}, набір {case}, операція {op}");
                    // Перевіряємо не лише десятковий вигляд, а й домен
                    // і кожен біт — через точну структурну рівність Value.
                }
            }
        }
        // Межа знакового двійкового доповнення: мінімальне Dn, помножене
        // на -1, має вирости до D(2n), інакше найвищий біт загубиться.
        for width in [24_usize, 48, 96, 192, 384, 768] {
            let mut min_word = vec![0; width];
            min_word[0] = 1;
            let negative_min = Value::BinaryNumber(
                BinaryNumber::from_numeric_domain_bits(width, &min_word).unwrap(),
            );
            let minus_one = Value::BinaryNumber(
                BinaryNumber::from_numeric_domain_bits(width, &vec![1; width]).unwrap(),
            );
            let positive = compute("*", &negative_min, &minus_one).unwrap();
            let Value::BinaryNumber(ref result) = positive else {
                panic!("цілий Dn");
            };
            assert_eq!(result.numeric_domain_width(), Some(width * 2));
            let mut expected_bits = vec![0; width * 2];
            expected_bits[width] = 1; // +2^(width-1)
            assert_eq!(result.exact_numeric_domain_bits().unwrap(), expected_bits);
            let more_negative = compute("+", &negative_min, &minus_one).unwrap();
            let Value::BinaryNumber(ref widened) = more_negative else {
                panic!("знаковий Dn");
            };
            assert_eq!(widened.numeric_domain_width(), Some(width * 2));
        }

        // Різні домени не стають однаковими через однакові величини.
        let one = |width| {
            let mut bits = vec![0; width];
            bits[width - 1] = 1;
            Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(width, &bits).unwrap())
        };
        for (small, large) in [(24, 48), (48, 96), (96, 192), (192, 384), (384, 768)] {
            for op in ["+", "-", "*"] {
                assert!(
                    compute(op, &one(small), &one(large)).is_none(),
                    "змішані D{small}/D{large}, {op}"
                );
            }
        }
    }

    #[test]
    fn wide_asm_multiplication_matches_original_exact_binary_law() {
        let admitted = |width: usize, word: Vec<u8>| -> Value {
            Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(width, &word).unwrap())
        };
        for width in [192_usize, 384, 768] {
            let zero = vec![0; width];
            let one = {
                let mut x = zero.clone();
                x[width - 1] = 1;
                x
            };
            let neg_one = vec![1; width];
            let max = {
                let mut x = neg_one.clone();
                x[0] = 0;
                x
            };
            let min = {
                let mut x = zero.clone();
                x[0] = 1;
                x
            };
            let two = {
                let mut x = zero.clone();
                x[width - 2] = 1;
                x
            };
            let inputs = [zero, one, neg_one, max, min, two];
            for (i, j) in [
                (0, 0),
                (0, 3),
                (1, 1),
                (1, 4),
                (2, 2),
                (2, 3),
                (3, 3),
                (3, 4),
                (4, 4),
                (5, 2),
            ] {
                let a = admitted(width, inputs[i].clone());
                let b = admitted(width, inputs[j].clone());
                let (_, an, am, ad) = ingredients(&a).unwrap();
                let (_, bn, bm, bd) = ingredients(&b).unwrap();
                let old = canonical(an ^ bn, am.mul(&bm), ad.mul(&bd), width)
                    .expect("попередній точний математичний закон");
                let new = compute("*", &a, &b).expect("повний ASM-добуток");
                assert_eq!(new, old, "D{width}: випадок {i}x{j}");
            }
        }
        let one = |w: usize| {
            let mut bits = vec![0; w];
            bits[w - 1] = 1;
            admitted(w, bits)
        };
        assert!(compute("*", &one(192), &one(384)).is_none());
        assert_eq!(compute("/", &one(192), &one(192)).unwrap().to_string(), "1");
        assert_eq!(compute("+", &one(384), &one(384)).unwrap().to_string(), "2");
    }

    #[test]
    fn d192_d384_wide_asm_keeps_exact_sign_carry_and_domain_laws() {
        let signed = |width: usize, word: &[u8]| -> Value {
            Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(width, word).unwrap())
        };
        for width in [192_usize, 384, 768] {
            let zero = vec![0; width];
            let one = {
                let mut bits = zero.clone();
                bits[width - 1] = 1;
                bits
            };
            let minus_one = vec![1; width];
            let max = {
                let mut bits = minus_one.clone();
                bits[0] = 0;
                bits
            };
            let min = {
                let mut bits = zero.clone();
                bits[0] = 1;
                bits
            };
            let v = |data: &[u8]| signed(width, data);
            let verify = |op: &str, a: &[u8], b: &[u8], result_width: usize, expected: Vec<u8>| {
                let Value::BinaryNumber(ref n) = compute(op, &v(a), &v(b)).expect("точна сума Dn")
                else {
                    panic!("результат має бути цілим");
                };
                assert_eq!(n.numeric_domain_width(), Some(result_width));
                assert_eq!(n.exact_numeric_domain_bits().unwrap(), expected);
            };
            verify("+", &max, &one, width * 2, {
                let mut bits = vec![0; width * 2];
                bits[width] = 1;
                bits
            });
            verify("-", &min, &one, width * 2, {
                // -2^(n-1)-1 у D(2n): усі старші n бітів одиниці,
                // далі 0, потім n-2 одиниці, останній біт 1.
                let mut bits = vec![1; width * 2];
                bits[width] = 0;
                bits
            });
            verify("+", &minus_one, &one, width, zero.clone());
            verify("-", &zero, &one, width, minus_one.clone());
            verify("+", &min, &max, width, minus_one.clone());
            verify("-", &max, &min, width * 2, {
                let mut bits = vec![0; width * 2];
                bits[width - 1] = 1; // 2^n-1
                bits[..width].fill(0);
                bits[width..].fill(1);
                bits
            });
        }
        let d192_one = {
            let mut b = vec![0; 192];
            b[191] = 1;
            signed(192, &b)
        };
        let d384_one = {
            let mut b = vec![0; 384];
            b[383] = 1;
            signed(384, &b)
        };
        assert!(compute("+", &d192_one, &d384_one).is_none());
        assert_eq!(compute("/", &d192_one, &d192_one).unwrap().to_string(), "1");
    }

    #[test]
    fn d96_machine_signed_product_retains_full_d192_and_compositions() {
        const MIN: i128 = -(1_i128 << 95);
        const MAX: i128 = (1_i128 << 95) - 1;
        let word = |width: usize, value: i128| -> Value {
            let bits = (0..width)
                .rev()
                .map(|shift| {
                    if shift >= 128 {
                        u8::from(value < 0)
                    } else {
                        ((value >> shift) & 1) as u8
                    }
                })
                .collect::<Vec<_>>();
            Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(width, &bits).unwrap())
        };
        for a in [MIN, MIN + 1, -2, -1, 0, 1, 2, MAX - 1, MAX] {
            for b in [MIN, -1, 0, 1, MAX] {
                let actual = compute("*", &word(96, a), &word(96, b)).expect("D96*D96");
                let got = actual.to_string();
                let expected_negative = (a < 0) != (b < 0) && a != 0 && b != 0;
                // Високобітний знак контролюється незалежною композицією,
                // а мала частина — вбудованим точним i128 оракулом.
                if a == 0 || b == 0 {
                    assert_eq!(got, "0");
                } else if a.unsigned_abs() <= (1 << 32) && b.unsigned_abs() <= (1 << 32) {
                    assert_eq!(got, (a * b).to_string());
                }
                let Value::BinaryNumber(ref bits) = actual else {
                    panic!("D96 or D192")
                };
                let w = bits.numeric_domain_width().unwrap();
                assert!(w == 96 || w == 192);
                assert_eq!(bits.exact_numeric_domain_bits().unwrap().len(), w);
                let negative = bits.exact_numeric_domain_bits().unwrap()[0] == 1;
                assert_eq!(negative, expected_negative);
            }
        }
        let big = compute("*", &word(96, MIN), &word(96, MIN)).unwrap();
        let Value::BinaryNumber(ref big_word) = big else {
            panic!("D192 full word");
        };
        assert_eq!(big_word.numeric_domain_width(), Some(192));
        let bits = big_word.exact_numeric_domain_bits().unwrap();
        assert_eq!(bits.iter().filter(|&&x| x == 1).count(), 1);
        assert_eq!(bits[1], 1); // 2^190 in a 192-bit D192 word
        assert!(compute("*", &word(96, 1), &word(48, 1)).is_none());
        assert_eq!(
            compute("/", &word(96, 1), &word(96, 2))
                .unwrap()
                .to_string(),
            "1/2"
        );
    }

    #[test]
    fn d96_assembly_widens_into_exact_d192_and_preserves_laws() {
        const MIN: i128 = -(1_i128 << 95);
        const MAX: i128 = (1_i128 << 95) - 1;
        let word = |w: usize, n: i128| -> Value {
            let bits = (0..w)
                .rev()
                .map(|shift| {
                    if shift >= 128 {
                        u8::from(n < 0)
                    } else {
                        ((n >> shift) & 1) as u8
                    }
                })
                .collect::<Vec<_>>();
            Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(w, &bits).unwrap())
        };
        for a in [MIN, MIN + 1, -1, 0, 1, MAX - 1, MAX] {
            for b in [MIN, -1, 0, 1, MAX] {
                for (op, oracle) in [("+", a + b), ("-", a - b)] {
                    let result = compute(op, &word(96, a), &word(96, b)).unwrap();
                    assert_eq!(result.to_string(), oracle.to_string());
                    let Value::BinaryNumber(ref bits) = result else {
                        panic!("integer D96/D192")
                    };
                    let limit = 1_i128 << 95;
                    let width = if (-limit..=limit - 1).contains(&oracle) {
                        96
                    } else {
                        192
                    };
                    assert_eq!(bits.numeric_domain_width(), Some(width));
                    assert_eq!(bits.exact_numeric_domain_bits().unwrap().len(), width);
                }
            }
        }
        assert!(compute("+", &word(96, 1), &word(48, 1)).is_none());
        assert!(compute("+", &word(96, 1), &word(192, 1)).is_none());
        assert_eq!(
            compute("/", &word(96, 1), &word(96, 2))
                .unwrap()
                .to_string(),
            "1/2"
        );
        assert_eq!(
            compute("*", &word(96, 3), &word(96, 7))
                .unwrap()
                .to_string(),
            "21"
        );
    }

    #[test]
    fn d48_asm_preserves_d96_widening_no_mixed_domains_or_float() {
        const MIN: i64 = -(1_i64 << 47);
        const MAX: i64 = (1_i64 << 47) - 1;
        let make = |w: usize, v: i128| -> Value {
            let bits = (0..w)
                .rev()
                .map(|i| ((v >> i) & 1) as u8)
                .collect::<Vec<_>>();
            Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(w, &bits).unwrap())
        };
        for a in [MIN, MIN + 1, -1, 0, 1, MAX] {
            for b in [MIN, -1, 0, 1, MAX] {
                for (op, oracle) in [
                    ("+", i128::from(a) + i128::from(b)),
                    ("-", i128::from(a) - i128::from(b)),
                    ("*", i128::from(a) * i128::from(b)),
                ] {
                    let output =
                        compute(op, &make(48, i128::from(a)), &make(48, i128::from(b))).unwrap();
                    assert_eq!(output.to_string(), oracle.to_string());
                    let Value::BinaryNumber(ref word) = output else {
                        panic!("D48/D96 word");
                    };
                    let limit = 1_i128 << 47;
                    let w = if (-limit..=limit - 1).contains(&oracle) {
                        48
                    } else {
                        96
                    };
                    assert_eq!(word.numeric_domain_width(), Some(w));
                    assert_eq!(word.exact_numeric_domain_bits().unwrap().len(), w);
                }
            }
        }
        assert!(compute("+", &make(24, 1), &make(48, 1)).is_none());
        assert!(compute("*", &make(48, 1), &make(96, 1)).is_none());
        assert_eq!(
            compute("/", &make(48, 1), &make(48, 2))
                .unwrap()
                .to_string(),
            "1/2"
        );
        assert_eq!(
            compute("+", &make(96, 1), &make(96, 2))
                .unwrap()
                .to_string(),
            "3"
        );
    }

    #[test]
    fn real_d24_asm_math_preserves_signed_bits_and_widening() {
        fn d24_signed(v: i64) -> Value {
            let bits: Vec<u8> = (0..24).rev().map(|s| ((v >> s) & 1) as u8).collect();
            Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(24, &bits).unwrap())
        }
        // Незалежна арифметична перевірка та перевірка ратифікованого
        // механізму D24 -> D48, без f64 і без змішаних доменів.
        for a in [-(1 << 23), -(1 << 23) + 1, -2, -1, 0, 1, 2, (1 << 23) - 1] {
            for b in [-(1 << 23), -1, 0, 1, (1 << 23) - 1] {
                let left = d24_signed(a);
                let right = d24_signed(b);
                for (operator, expected) in [("+", a + b), ("-", a - b), ("*", a * b)] {
                    let value =
                        compute(operator, &left, &right).expect("точна машинна операція D24");
                    assert_eq!(
                        value.to_string(),
                        expected.to_string(),
                        "{a} {operator} {b}"
                    );
                    let Value::BinaryNumber(ref result) = value else {
                        panic!("ціле D24+");
                    };
                    let width = if (-(1_i64 << 23)..=(1_i64 << 23) - 1).contains(&expected) {
                        24
                    } else {
                        48
                    };
                    assert_eq!(result.numeric_domain_width(), Some(width));
                    assert_eq!(result.exact_numeric_domain_bits().unwrap().len(), width);
                }
            }
        }
        let d48 = Value::BinaryNumber(d(48, 1));
        assert!(
            compute("+", &d24_signed(1), &d48).is_none(),
            "суміш D24 і D48 недопустима"
        );
        let half =
            compute("/", &d24_signed(1), &d24_signed(2)).expect("дробова композиція лишилась");
        assert_eq!(half.to_string(), "1/2");
    }

    #[test]
    fn d24_twos_complement_arithmetic_decodes_sign_before_exact_growth() {
        let word = |bits: Vec<u8>| {
            Value::BinaryNumber(BinaryNumber::from_numeric_domain_bits(24, &bits).unwrap())
        };
        let zero = word(vec![0; 24]);
        let one = Value::BinaryNumber(d(24, 1));
        let minus_one = word(vec![1; 24]);
        let minus_two = word({
            let mut bits = vec![1; 24];
            bits[23] = 0;
            bits
        });
        let maximum = word({
            let mut bits = vec![1; 24];
            bits[0] = 0;
            bits
        });

        assert_eq!(compute("-", &zero, &one).unwrap().to_string(), "-1");
        assert_eq!(compute("+", &minus_one, &one), Some(zero.clone()));
        assert_eq!(
            compute("*", &minus_two, &Value::BinaryNumber(d(24, 3)))
                .unwrap()
                .to_string(),
            "-6"
        );

        let carried =
            compute("+", &maximum, &one).expect("positive signed overflow widens exactly");
        assert_eq!(carried.to_string(), "8388608");
        let Value::BinaryNumber(ref carried_word) = carried else {
            panic!("integer result")
        };
        assert_eq!(carried_word.numeric_domain_width(), Some(48));

        let third = compute("/", &minus_one, &Value::BinaryNumber(d(24, 3)))
            .expect("existing exact ratio law remains available");
        assert_eq!(third.to_string(), "-1/3");
    }

    /// Mechanism regression: no numeric-domain widening, textual decimal
    /// intermediary or rational cross-products for two admitted naturals.
    #[test]
    fn signed_dn_integer_comparison_retains_width_and_order_without_rational_bridge() {
        for width in [24usize, 48, 96, 192] {
            let zero = Value::BinaryNumber(d(width, 0));
            let two = Value::BinaryNumber(d(width, 2));
            let three = Value::BinaryNumber(d(width, 3));

            for (left, right, equal, less, greater) in [
                (&zero, &zero, true, false, false),
                (&two, &three, false, true, false),
                (&three, &two, false, false, true),
                (&three, &three, true, false, false),
            ] {
                for (operator, expected) in [("=", equal), ("<", less), (">", greater)] {
                    let actual = compare(operator, left, right);
                    assert_eq!(
                        actual, Some(expected),
                        "test_id=signed-dn-compare layer=eval domain=D{width} op={operator} expected={expected} actual={actual:?}; reproduce=cargo test -p sens signed_dn_integer_comparison_retains_width_and_order_without_rational_bridge"
                    );
                }
            }
            assert_eq!(compare("+", &two, &three), None);
            assert_eq!(
                compare("=", &two, &Value::BinaryNumber(d(width * 2, 2))),
                None,
                "D{width} and D{} cannot share a numeric identity",
                width * 2,
            );

            // Signed compositions must continue through the existing
            // rational/signed comparison mechanism, not this shortcut.
            let neg_two =
                canonical_parts(true, &d(width, 2), &d(width, 1)).expect("admitted signed Dn");
            assert_eq!(compare("<", &neg_two, &zero), Some(true));
            assert_eq!(compare("=", &neg_two, &two), Some(false));
        }
        let legacy = Value::BinaryNumber(BinaryNumber::one());
        let d24 = Value::BinaryNumber(d(24, 1));
        assert_eq!(compare("=", &legacy, &d24), None);
        assert_eq!(compare("=", &d24, &legacy), None);
    }

    #[test]
    fn exact_dn_admission_never_depends_on_rational_value_equality() {
        let unqualified = Value::BinaryNumber(BinaryNumber::one());
        for width in [24usize, 48, 96, 192, 384] {
            let one = Value::BinaryNumber(d(width, 1));
            let two = Value::BinaryNumber(d(width, 2));
            let fraction = canonical_parts(false, &d(width, 1), &d(width, 3))
                .expect("exact nonintegral fraction in Dn");
            let signed = canonical_parts(true, &d(width, 1), &d(width, 1))
                .expect("exact negative integer in Dn");
            let same_magnitude_doubled_width = Value::BinaryNumber(d(width * 2, 1));

            assert_eq!(numeric_value_domain_width(&fraction), Some(width));
            assert_eq!(numeric_value_domain_width(&signed), Some(width));
            for lhs in [&one, &fraction, &signed] {
                for rhs in [&two, &fraction, &signed] {
                    assert_eq!(
                        shared_numeric_domain_width(lhs, rhs),
                        Some(width),
                        "D{width}: admission depends only on exact Dn tags"
                    );
                }
                assert_eq!(
                    shared_numeric_domain_width(lhs, &same_magnitude_doubled_width),
                    None
                );
                assert_eq!(
                    shared_numeric_domain_width(&same_magnitude_doubled_width, lhs),
                    None
                );
                assert_eq!(shared_numeric_domain_width(lhs, &unqualified), None);
                assert_eq!(shared_numeric_domain_width(&unqualified, lhs), None);
            }
        }
    }

    #[test]
    fn signed_dn_vs_natural_is_ordered_without_rational_cross_products() {
        for width in [24usize, 48, 96, 192] {
            let zero = Value::BinaryNumber(d(width, 0));
            let two = Value::BinaryNumber(d(width, 2));
            let neg_fraction = canonical_parts(true, &d(width, 2), &d(width, 3))
                .expect("ratified negative Dn rational");
            let positive_fraction = canonical_parts(false, &d(width, 2), &d(width, 3))
                .expect("ratified positive Dn rational");
            for (op, expected_forward, expected_reverse) in
                [("=", false, false), ("<", false, true), (">", true, false)]
            {
                for natural in [&zero, &two] {
                    let forward = compare(op, natural, &neg_fraction);
                    let reverse = compare(op, &neg_fraction, natural);
                    assert_eq!(
                        forward, Some(expected_forward),
                        "test_id=dn-sign-shortcut layer=eval D{width} op={op} positive-versus-negative: expected={expected_forward}, actual={forward:?}; reproduce=cargo test -p sens signed_dn_vs_natural_is_ordered_without_rational_cross_products"
                    );
                    assert_eq!(
                        reverse, Some(expected_reverse),
                        "test_id=dn-sign-shortcut layer=eval D{width} op={op} negative-versus-positive: expected={expected_reverse}, actual={reverse:?}; reproduce=cargo test -p sens signed_dn_vs_natural_is_ordered_without_rational_cross_products"
                    );
                }
            }
            // The ordinary rational path must still handle *positive*
            // signed/rational compositions rather than the sign shortcut.
            assert_eq!(compare(">", &two, &positive_fraction), Some(true));
            assert_eq!(compare("<", &positive_fraction, &two), Some(true));
            assert_eq!(compare("=", &two, &positive_fraction), Some(false));
            let other_width = width * 2;
            let wrong = Value::BinaryNumber(d(other_width, 2));
            assert_eq!(compare("=", &neg_fraction, &wrong), None);
            assert_eq!(compare("=", &wrong, &neg_fraction), None);
            let unqualified = Value::BinaryNumber(BinaryNumber::one());
            assert_eq!(compare("=", &neg_fraction, &unqualified), None);
            assert_eq!(compare("=", &unqualified, &neg_fraction), None);
        }
    }

    #[test]
    fn composition_normalizes_sign_gcd_unit_and_zero() {
        let zero = Value::BinaryNumber(d(24, 0));
        assert_eq!(unary("-", &zero), Some(zero.clone()));
        assert_eq!(
            compute("/", &zero, &Value::BinaryNumber(d(24, 3))),
            Some(zero)
        );
        assert_eq!(
            canonical_parts(false, &d(24, 2), &d(24, 4)),
            canonical_parts(false, &d(24, 1), &d(24, 2))
        );
        assert_eq!(
            canonical_parts(false, &d(24, 6), &d(24, 3)),
            Some(Value::BinaryNumber(d(24, 2)))
        );
        assert_eq!(
            canonical_parts(true, &d(24, 5), &d(24, 1)),
            unary("-", &Value::BinaryNumber(d(24, 5)))
        );
        assert!(canonical_parts(false, &d(24, 1), &d(24, 0)).is_none());
        assert!(canonical_parts(false, &d(24, 1), &d(48, 2)).is_none());
    }

    #[test]
    fn one_bit_denominator_mutation_keeps_d24_plus_integers_canonical() {
        // Targeted witness: the one-bit change 000...001 -> 000...011
        // is exactly what separates an integer from a rational.
        // Every intermediate constituent still belongs to the same Dn.
        for width in [24usize, 48, 96, 192] {
            let one = d(width, 1);
            let two = d(width, 2);
            let three = d(width, 3);
            let zero = d(width, 0);

            // as_bits() returns a normalized magnitude. The *domain word*
            // must be compared at its authoritative full Dn width.
            let one_bits = one.exact_numeric_domain_bits().expect("exact Dn(1)");
            let three_bits = three.exact_numeric_domain_bits().expect("exact Dn(3)");
            assert_eq!(one_bits.len(), width);
            assert_eq!(three_bits.len(), width);
            let bit_distance: usize = one_bits
                .iter()
                .zip(three_bits.iter())
                .map(|(a, b)| usize::from(a != b))
                .sum();
            assert_eq!(bit_distance, 1, "D{width}: single-bit mutation");

            let integer = canonical_parts(false, &two, &one)
                .expect("unit denominator reduces to an admitted integer Dn");
            assert_eq!(
                integer,
                Value::BinaryNumber(two.clone()),
                "D{width}: RATIO(2,1) must not survive as an extra tag"
            );

            let negative =
                canonical_parts(true, &two, &one).expect("negative integer still uses exact Dn");
            let Value::BinaryNumber(ref neg) = negative else {
                panic!("D{width}: negative integer is a two's-complement Dn word")
            };
            assert_eq!(neg.numeric_domain_width(), Some(width));
            assert_eq!(neg.to_decimal_string(), "-2");
            assert_eq!(negative.to_string(), "-2");

            let ratio = canonical_parts(false, &two, &three)
                .expect("one-bit-mutated denominator is a valid fraction");
            let Value::NumericComposition(ref fraction) = ratio else {
                panic!("D{width}: the mutated denominator is not unity")
            };
            assert_eq!(ratio.to_string(), "2/3");
            assert_eq!(fraction.domain_width(), width);
            let (_, numerator, denominator) = fraction.as_parts();
            assert_eq!(numerator.numeric_domain_width(), Some(width));
            assert_eq!(
                denominator.expect("actual fraction").numeric_domain_width(),
                Some(width)
            );

            let divided = compute(
                "/",
                &Value::BinaryNumber(d(width, 6)),
                &Value::BinaryNumber(d(width, 3)),
            )
            .expect("same domain 6/3");
            assert_eq!(
                divided,
                Value::BinaryNumber(two),
                "D{width}: reduced division becomes exactly Dn(2)"
            );
            assert_eq!(
                canonical_parts(true, &zero, &one),
                Some(Value::BinaryNumber(zero)),
                "D{width}: negative zero must not allocate a sign or denominator"
            );
            assert!(
                canonical_parts(false, &d(width, 2), &d(width * 2, 1)).is_none(),
                "D{width}: mixed Dn values are forbidden"
            );
        }
    }

    #[test]
    fn signed_rational_arithmetic_matches_independent_exact_i128_oracle() {
        let gcd = |mut a: i128, mut b: i128| -> i128 {
            while b != 0 {
                (a, b) = (b, a % b);
            }
            a.abs()
        };
        let mut seed = 0x1234_5678_9abc_def1u64;
        let mut next = || {
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            seed
        };
        for _ in 0..4096 {
            let a = (next() % 33) as i128;
            let b = (next() % 32 + 1) as i128;
            let c = (next() % 33) as i128;
            let d0 = (next() % 32 + 1) as i128;
            let left_negative = next() & 1 != 0;
            let right_negative = next() & 1 != 0;
            let left = canonical_parts(left_negative, &d(24, a as u64), &d(24, b as u64)).unwrap();
            let right =
                canonical_parts(right_negative, &d(24, c as u64), &d(24, d0 as u64)).unwrap();
            let x = if left_negative { -a } else { a };
            let y = if right_negative { -c } else { c };
            for op in ["+", "-", "*", "/"] {
                let pair = match op {
                    "+" => (x * d0 + y * b, b * d0),
                    "-" => (x * d0 - y * b, b * d0),
                    "*" => (x * y, b * d0),
                    "/" if y != 0 => (x * d0, b * y),
                    "/" => {
                        assert!(compute(op, &left, &right).is_none());
                        continue;
                    }
                    _ => unreachable!(),
                };
                let (mut n, mut den) = pair;
                if den < 0 {
                    n = -n;
                    den = -den;
                }
                let common = gcd(n.abs(), den);
                let n = n / common;
                let den = den / common;
                let expected = if den == 1 {
                    n.to_string()
                } else {
                    format!("{n}/{den}")
                };
                let got = compute(op, &left, &right).unwrap();
                assert_eq!(got.to_string(), expected, "input {x}/{b} {op} {y}/{d0}");
                if let Value::NumericComposition(c) = &got {
                    assert_eq!(c.domain_width(), 24);
                    let (negative, num, denominator) = c.as_parts();
                    assert_eq!(negative, n < 0);
                    assert!(!num.is_zero());
                    assert_eq!(num.numeric_domain_width(), Some(24));
                    if let Some(denominator) = denominator {
                        assert_eq!(denominator.numeric_domain_width(), Some(24));
                        assert!(denominator.as_bits() != [0] && denominator.as_bits() != [1]);
                    }
                    assert!(got.to_canonical_wire_string().contains("WIRE-UNSUPPORTED"));
                }
            }
            assert_eq!(compare("=", &left, &right), Some(x * d0 == y * b));
            assert_eq!(compare("<", &left, &right), Some(x * d0 < y * b));
        }
    }

    #[test]
    fn rational_high_bit_products_promote_components_from_d24_to_d48_without_loss() {
        let n = (1u64 << 24) - 1;
        let den = n - 1;
        let ratio = canonical_parts(false, &d(24, n), &d(24, den)).unwrap();
        assert_eq!(ratio.to_string(), format!("{n}/{den}"));
        let squared = compute("*", &ratio, &ratio).unwrap();
        let Value::NumericComposition(ref r) = squared else {
            panic!("exact RATIO")
        };
        assert_eq!(r.domain_width(), 48);
        let (neg, numerator, denominator) = r.as_parts();
        assert!(!neg);
        let denominator = denominator.expect("reduced RATIO requires denominator");
        assert_eq!(numerator.numeric_domain_width(), Some(48));
        assert_eq!(denominator.numeric_domain_width(), Some(48));
        assert_eq!(numerator.to_unsigned_decimal_string(), (n * n).to_string());
        assert_eq!(
            denominator.to_unsigned_decimal_string(),
            (den * den).to_string()
        );
        assert_eq!(squared.to_string(), format!("{}/{}", n * n, den * den));
        let negated = unary("-", &squared).unwrap();
        assert_eq!(negated.to_string(), format!("-{}/{}", n * n, den * den));
        assert_eq!(
            compute("+", &squared, &negated),
            Some(Value::BinaryNumber(
                BinaryNumber::from_numeric_domain_bits(48, &[0; 48]).unwrap()
            ))
        );
        // The original operand still belongs to D24. No generic D24 <-> D48 bridge.
        assert!(compute("+", &squared, &ratio).is_none());
    }

    #[test]
    fn composite_domain_is_not_inferred_and_overflow_retains_all_bits() {
        let a = Value::BinaryNumber(d(24, (1 << 23) - 1));
        let b = Value::BinaryNumber(d(24, 2));
        let result = compute("*", &a, &b).unwrap();
        let Value::BinaryNumber(ref bits) = result else {
            panic!("integer");
        };
        assert_eq!(bits.numeric_domain_width(), Some(48));
        let neg = unary("-", &result).unwrap();
        assert_eq!(neg.to_string(), format!("-{}", ((1u64 << 23) - 1) * 2));
        let Value::BinaryNumber(ref negative_integer) = neg else {
            panic!("signed integer");
        };
        assert_eq!(negative_integer.numeric_domain_width(), Some(48));
        let other = Value::BinaryNumber(d(48, 2));
        assert!(compute("+", &neg, &other).is_some());
        assert!(compute("+", &neg, &b).is_none());
        assert!(compare("=", &neg, &b).is_none());
    }

    #[test]
    fn one_bit_boundary_diagnostic_preserves_every_domain_bit() {
        // Незалежний оракул: (2^(n-1)-2)+1 досягає iN max;
        // iN max + 1 переходить у наступний Dn без переповнення.
        // Зміна ОДНОГО біта на вході змінює обраний домен результату.
        for width in [24usize, 48, 96, 192] {
            let mut nearly_full = vec![1u8; width];
            nearly_full[0] = 0;
            nearly_full[width - 1] = 0;
            let mut maximum_word = vec![1u8; width];
            maximum_word[0] = 0;
            let mut one = vec![0u8; width];
            one[width - 1] = 1;
            let admitted = |word: &[u8]| {
                Value::BinaryNumber(
                    BinaryNumber::from_numeric_domain_bits(width, word)
                        .expect("точна бітність D24+"),
                )
            };
            let almost = admitted(&nearly_full);
            let maximum = admitted(&maximum_word);
            let unit = admitted(&one);

            let fitting = compute("+", &almost, &unit).expect("вміщується в Dn");
            let Value::BinaryNumber(fitted) = &fitting else {
                panic!("ціле натуральне має залишитися доменним числом")
            };
            assert_eq!(fitted.numeric_domain_width(), Some(width), "D{width}: fit");
            assert_eq!(
                fitted.exact_numeric_domain_bits(),
                Some(maximum_word.clone()),
                "D{width}: iN максимум має зберегти точні біти"
            );

            let crossing = compute("+", &maximum, &unit).expect("точне перенесення");
            let Value::BinaryNumber(carried) = &crossing else {
                panic!("carry мусить залишитися натуральним числом")
            };
            let mut expected = vec![0u8; 2 * width];
            expected[width] = 1;
            assert_eq!(
                carried.numeric_domain_width(),
                Some(2 * width),
                "D{width}: не можна обрізати старший біт"
            );
            assert_eq!(
                carried.exact_numeric_domain_bits(),
                Some(expected),
                "D{width}: єдиний біт перенесення на точній D(2n) позиції"
            );

            let unchanged =
                compute("*", &maximum, &unit).expect("множення на одиницю того самого домену");
            assert_eq!(unchanged, maximum, "D{width}: natural MUL path");
            let mut two = vec![0u8; width];
            two[width - 2] = 1;
            let doubled =
                compute("*", &maximum, &admitted(&two)).expect("точне множення з перенесенням");
            let Value::BinaryNumber(product) = &doubled else {
                panic!("добуток має залишитися точним натуральним словом")
            };
            let mut product_bits = vec![0u8; 2 * width];
            product_bits[width..(2 * width - 1)].fill(1);
            assert_eq!(product.numeric_domain_width(), Some(2 * width));
            assert_eq!(product.exact_numeric_domain_bits(), Some(product_bits));

            let legacy_one = Value::BinaryNumber(BinaryNumber::one());
            for op in ["+", "*"] {
                assert!(
                    compute(op, &maximum, &legacy_one).is_none(),
                    "D{width}: {op} must reject unqualified one"
                );
                assert!(
                    compute(op, &legacy_one, &maximum).is_none(),
                    "D{width}: {op} must reject unqualified first operand"
                );
                let other_domain = Value::BinaryNumber(
                    BinaryNumber::from_numeric_domain_bits(2 * width, &vec![0; 2 * width]).unwrap(),
                );
                assert!(
                    compute(op, &maximum, &other_domain).is_none(),
                    "D{width}: {op} must reject mixed Dn/D(2n)"
                );
            }
        }
    }

    #[test]
    fn arithmetic_closes_over_negative_and_exact_rational_values() {
        let one = Value::BinaryNumber(d(24, 1));
        let two = Value::BinaryNumber(d(24, 2));
        let three = Value::BinaryNumber(d(24, 3));
        let half = compute("/", &one, &two).unwrap();
        let third = compute("/", &one, &three).unwrap();
        assert_eq!(compute("+", &half, &half), Some(one.clone()));
        let sixth = compute("/", &half, &three).unwrap();
        assert_eq!(compute("+", &third, &sixth), Some(half.clone()));
        let negative = compute("-", &one, &three).unwrap();
        assert_eq!(
            compute("+", &negative, &two),
            Some(Value::BinaryNumber(d(24, 0)))
        );
        assert_eq!(compute("*", &negative, &half), unary("-", &one));
        assert_eq!(compute("/", &one, &half), Some(two));
        assert_eq!(compare("<", &negative, &half), Some(true));
        assert_eq!(compare("=", &half, &half), Some(true));
        assert_eq!(compare(">", &third, &half), Some(false));
        assert!(compute("/", &one, &Value::BinaryNumber(d(24, 0))).is_none());
    }
}
