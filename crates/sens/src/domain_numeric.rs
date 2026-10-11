//! Exact arithmetic for mathematical NEG/RATIO compositions over existing D24+
//! natural atoms. This is a Core VALUE mechanism, NOT a new SENS domain.
//! Domain identities remain explicit, with no host floats, mixed-domain
//! coercion, decimal literals, or invented binary semantic opcodes.
use crate::{BinaryNumber, Value};
use std::cmp::Ordering;

/// Executable canonical compositions of admitted D24/D48/... natural atoms.
///
/// Both constituent numeric atoms always occupy the exact SAME admitted Dn.
/// This guarantees unique sign and reduced rational shape *within* that
/// numeric domain, without taking any of its 2^n natural payloads.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum DomainNumericComposition {
    Negative(BinaryNumber),
    Ratio {
        negative: bool,
        numerator: BinaryNumber,
        denominator: BinaryNumber,
    },
}

impl DomainNumericComposition {
    pub fn domain_width(&self) -> usize {
        match self {
            Self::Negative(m) => m.numeric_domain_width().expect("admitted domain"),
            Self::Ratio { numerator, .. } => numerator.numeric_domain_width().expect("admitted domain"),
        }
    }

    pub fn as_parts(&self) -> (bool, &BinaryNumber, Option<&BinaryNumber>) {
        match self {
            Self::Negative(m) => (true, m, None),
            Self::Ratio { negative, numerator, denominator } => {
                (*negative, numerator, Some(denominator))
            }
        }
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

fn unit(width: usize) -> Option<BinaryNumber> {
    own_word(BinaryNumber::one(), width)
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

    let mut width = minimum_width;
    while n.width().max(d.width()) > width {
        width = width.checked_mul(2)?;
    }
    let n = own_word(n, width)?;
    let d = own_word(d, width)?;
    if n.is_zero() { return Some(Value::BinaryNumber(n)); }
    if d.as_bits() == [1] {
        if negative {
            return Some(Value::NumericComposition(DomainNumericComposition::Negative(n)));
        }
        return Some(Value::BinaryNumber(n));
    }
    Some(Value::NumericComposition(DomainNumericComposition::Ratio {
        negative, numerator: n, denominator: d,
    }))
}

fn ingredients(value: &Value) -> Option<(usize, bool, BinaryNumber, BinaryNumber)> {
    match value {
        Value::BinaryNumber(n) => {
            let width = n.numeric_domain_width()?;
            Some((width, false, normalized(n), BinaryNumber::one()))
        }
        Value::NumericComposition(c) => {
            let width = c.domain_width();
            match c {
                DomainNumericComposition::Negative(n) =>
                    Some((width, true, normalized(n), BinaryNumber::one())),
                DomainNumericComposition::Ratio { negative, numerator, denominator } =>
                    Some((width, *negative, normalized(numerator), normalized(denominator))),
            }
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
    if denominator.numeric_domain_width() != Some(width) { return None; }
    canonical(negative, normalized(numerator), normalized(denominator), width)
}

pub fn is_domain_value(v: &Value) -> bool {
    matches!(v, Value::NumericComposition(_))
        || matches!(v, Value::BinaryNumber(n) if n.numeric_domain_width().is_some())
}

/// Exactly two operands in the SAME Dn; arithmetic creates no unqualified
/// identity. The specific result-domain growth is explicit and validated.
pub fn compute(operator: &str, lhs: &Value, rhs: &Value) -> Option<Value> {
    let (width, x_neg, x_num, x_den) = ingredients(lhs)?;
    let (other_width, y_neg, y_num, y_den) = ingredients(rhs)?;
    if width != other_width { return None; }

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
            if y_num.is_zero() { return None; }
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
    let (width, x_neg, xn, xd) = ingredients(lhs)?;
    let (other_width, y_neg, yn, yd) = ingredients(rhs)?;
    if width != other_width { return None; }
    let order = match (x_neg, y_neg) {
        (true, false) => Ordering::Less,
        (false, true) => Ordering::Greater,
        (left_neg, _) => {
            let cmp = xn.mul(&yd).cmp(&yn.mul(&xd));
            if left_neg { cmp.reverse() } else { cmp }
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
        for i in 0..width.min(64) { bits[width - 1 - i] = ((u >> i) & 1) as u8; }
        BinaryNumber::from_numeric_domain_bits(width, &bits).unwrap()
    }

    #[test]
    fn composition_normalizes_sign_gcd_unit_and_zero() {
        let zero = Value::BinaryNumber(d(24, 0));
        assert_eq!(unary("-", &zero), Some(zero.clone()));
        assert_eq!(compute("/", &zero, &Value::BinaryNumber(d(24, 3))), Some(zero));
        assert_eq!(canonical_parts(false, &d(24, 2), &d(24, 4)),
            canonical_parts(false, &d(24, 1), &d(24, 2)));
        assert_eq!(canonical_parts(false, &d(24, 6), &d(24, 3)),
            Some(Value::BinaryNumber(d(24, 2))));
        assert_eq!(canonical_parts(true, &d(24, 5), &d(24, 1)),
            unary("-", &Value::BinaryNumber(d(24, 5))));
        assert!(canonical_parts(false, &d(24, 1), &d(24, 0)).is_none());
        assert!(canonical_parts(false, &d(24, 1), &d(48, 2)).is_none());
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
        assert_eq!(compute("+", &negative, &two), Some(Value::BinaryNumber(d(24, 0))));
        assert_eq!(compute("*", &negative, &half), unary("-", &one));
        assert_eq!(compute("/", &one, &half), Some(two));
        assert_eq!(compare("<", &negative, &half), Some(true));
        assert_eq!(compare("=", &half, &half), Some(true));
        assert_eq!(compare(">", &third, &half), Some(false));
        assert!(compute("/", &one, &Value::BinaryNumber(d(24, 0))).is_none());
    }
}
