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
