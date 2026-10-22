//! Datalog-owned integer arithmetic execution.
//!
//! This module is execution machinery only. Semantic meaning and any external
//! semantic identity remain owned by sens.
//!
//! The first bounded mechanism set is deliberately small.
//! The historical 8-bit C ABI slot is a *transport compatibility selector*,
//! NOT an SENS domain identity. Modern calls use exact ratified D5/D6 words.
//! D7 and operator text never select execution; unproven laws fail closed.
//! LEGACY_ABI_* constants are historical C-ABI transport tags, not D5/D6/D8
//! codes. Their numeric values MUST NOT grant SENS-language callability.

use std::collections::HashMap;
use std::fmt;

use crate::Value;

pub const LEGACY_ABI_ADD: u8 = 0b0000_1100;
pub const LEGACY_ABI_SUB: u8 = 0b0000_1101;
pub const LEGACY_ABI_MUL: u8 = 0b0000_1110;
pub const LEGACY_ABI_DIV: u8 = 0b0000_1111;
pub const LEGACY_ABI_ABS: u8 = 0b0001_0000;
pub const LEGACY_ABI_MIN: u8 = 0b0001_0001;
pub const LEGACY_ABI_MAX: u8 = 0b0001_0010;
pub const LEGACY_ABI_MOD: u8 = 0b0001_0011;
pub const LEGACY_ABI_QUOTIENT: u8 = 0b0001_0100;

pub fn is_legacy_math_id(legacy_abi_byte: u8) -> bool {
    matches!(
        legacy_abi_byte,
        LEGACY_ABI_ADD
            | LEGACY_ABI_SUB
            | LEGACY_ABI_MUL
            | LEGACY_ABI_DIV
            | LEGACY_ABI_ABS
            | LEGACY_ABI_MIN
            | LEGACY_ABI_MAX
            | LEGACY_ABI_MOD
            | LEGACY_ABI_QUOTIENT
    )
}

/// A Datalog arithmetic mechanism, never a domain identity by itself.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum ArithmeticMechanism {
    Add, Sub, Mul, Div, Abs, Min, Max, Mod, Quotient,
}

/// Only mechanisms with a verified matching domain law enter this path.
/// Both exact width and bits are required: an historical SID8 byte cannot
/// make an operation callable in present-day D8.
pub fn parse_exact_domain_request(
    width: u8, bits: &str, payload: &str
) -> Result<NumericExpr, DatalogMathError> {
    use ArithmeticMechanism as Op;
    let operation = match (width, bits) {
        (5, "01010") => Op::Add,  // додати
        (5, "01011") => Op::Sub,  // відняти
        (5, "10110") => Op::Mul,  // помножити
        (6, "010011") => Op::Abs, // модуль
        (6, "110101") => Op::Min, // найменше
        (6, "110111") => Op::Max, // найбільше
        // Quotient, division and remainder wait for exact signed/rational
        // SENS parity; an i64 adapter must not invent their laws.
        _ => return Err(DatalogMathError::UnsupportedDomainOperation {
            width, bits: bits.to_owned(),
        }),
    };
    parse_math_operation(operation, payload)
}

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum NumericExpr {
    Literal(i64),
    Variable(String),
    Add(Box<Self>, Box<Self>),
    Sub(Box<Self>, Box<Self>),
    Mul(Box<Self>, Box<Self>),
    Div(Box<Self>, Box<Self>),
    Mod(Box<Self>, Box<Self>),
    Quotient(Box<Self>, Box<Self>),
    Abs(Box<Self>),
    Min(Box<Self>, Box<Self>),
    Max(Box<Self>, Box<Self>),
}

impl NumericExpr {
    pub fn evaluate(&self, bindings: &HashMap<String, Value>) -> Result<Value, DatalogMathError> {
        use NumericExpr::*;

        let integer = |expr: &NumericExpr| -> Result<i64, DatalogMathError> {
            match expr.evaluate(bindings)? {
                Value::Int(value) => Ok(value),
                value => Err(DatalogMathError::NonIntegerValue(value)),
            }
        };

        let result = match self {
            Literal(value) => *value,
            Variable(name) => match bindings.get(name) {
                Some(Value::Int(value)) => *value,
                Some(value) => return Err(DatalogMathError::NonIntegerValue(value.clone())),
                None => return Err(DatalogMathError::MissingVariable(name.clone())),
            },
            Add(left, right) => integer(left)?
                .checked_add(integer(right)?)
                .ok_or(DatalogMathError::Overflow)?,
            Sub(left, right) => integer(left)?
                .checked_sub(integer(right)?)
                .ok_or(DatalogMathError::Overflow)?,
            Mul(left, right) => integer(left)?
                .checked_mul(integer(right)?)
                .ok_or(DatalogMathError::Overflow)?,
            Div(left, right) | Quotient(left, right) => {
                let lhs = integer(left)?;
                let rhs = integer(right)?;
                lhs.checked_div(rhs).ok_or({
                    if rhs == 0 {
                        DatalogMathError::DivisionByZero
                    } else {
                        DatalogMathError::Overflow
                    }
                })?
            }
            Mod(left, right) => {
                let lhs = integer(left)?;
                let rhs = integer(right)?;
                lhs.checked_rem(rhs).ok_or({
                    if rhs == 0 {
                        DatalogMathError::DivisionByZero
                    } else {
                        DatalogMathError::Overflow
                    }
                })?
            }
            Abs(value) => integer(value)?
                .checked_abs()
                .ok_or(DatalogMathError::Overflow)?,
            Min(left, right) => integer(left)?.min(integer(right)?),
            Max(left, right) => integer(left)?.max(integer(right)?),
        };

        Ok(Value::Int(result))
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum DatalogMathError {
    MissingVariable(String),
    NonIntegerValue(Value),
    InvalidArgument(String),
    UnsupportedLegacyAbiId(u8),
    UnsupportedDomainOperation { width: u8, bits: String },
    DivisionByZero,
    Overflow,
}

impl fmt::Display for DatalogMathError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::MissingVariable(name) => {
                write!(formatter, "datalog-math-missing-variable:{name}")
            }
            Self::NonIntegerValue(value) => write!(formatter, "datalog-math-non-integer:{value:?}"),
            Self::InvalidArgument(value) => {
                write!(formatter, "datalog-math-invalid-argument:{value}")
            }
            Self::UnsupportedLegacyAbiId(sid) => {
                write!(formatter, "datalog-math-unsupported-legacy-abi-slot:{sid:08b}")
            }
            Self::UnsupportedDomainOperation { width, bits } => {
                write!(formatter, "datalog-math-unsupported-domain:D{width}:{bits}")
            }
            Self::DivisionByZero => write!(formatter, "datalog-math-division-by-zero"),
            Self::Overflow => write!(formatter, "datalog-math-overflow"),
        }
    }
}

impl std::error::Error for DatalogMathError {}

/// Explicit historical one-byte WSM C ABI bridge, not current SENS.
pub fn parse_legacy_abi_request(
    semantic_id: u8,
    payload: &str,
) -> Result<NumericExpr, DatalogMathError> {
    use ArithmeticMechanism as Op;
    let operation = match semantic_id {
        LEGACY_ABI_ADD => Op::Add,
        LEGACY_ABI_SUB => Op::Sub,
        LEGACY_ABI_MUL => Op::Mul,
        LEGACY_ABI_DIV => Op::Div,
        LEGACY_ABI_ABS => Op::Abs,
        LEGACY_ABI_MIN => Op::Min,
        LEGACY_ABI_MAX => Op::Max,
        LEGACY_ABI_MOD => Op::Mod,
        LEGACY_ABI_QUOTIENT => Op::Quotient,
        other => return Err(DatalogMathError::UnsupportedLegacyAbiId(other)),
    };
    parse_math_operation(operation, payload)
}

fn parse_math_operation(
    operation: ArithmeticMechanism, payload: &str,
) -> Result<NumericExpr, DatalogMathError> {
    let args: Result<Vec<i64>, DatalogMathError> = payload
        .split_whitespace()
        .map(|raw| {
            raw.parse::<i64>()
                .map_err(|_| DatalogMathError::InvalidArgument(raw.to_string()))
        })
        .collect();
    let args = args?;

    fn need_two(args: &[i64]) -> Result<(i64, i64), DatalogMathError> {
        match args {
            [left, right] => Ok((*left, *right)),
            _ => Err(DatalogMathError::InvalidArgument(format!(
                "expected-two-operands-got-{}",
                args.len()
            ))),
        }
    }

    fn need_one(args: &[i64]) -> Result<i64, DatalogMathError> {
        match args {
            [value] => Ok(*value),
            _ => Err(DatalogMathError::InvalidArgument(format!(
                "expected-one-operand-got-{}",
                args.len()
            ))),
        }
    }

    use NumericExpr::*;
    let expr = match operation {
        ArithmeticMechanism::Add => {
            let (left, right) = need_two(&args)?;
            Add(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        ArithmeticMechanism::Sub => {
            let (left, right) = need_two(&args)?;
            Sub(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        ArithmeticMechanism::Mul => {
            let (left, right) = need_two(&args)?;
            Mul(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        ArithmeticMechanism::Div => {
            let (left, right) = need_two(&args)?;
            Div(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        ArithmeticMechanism::Abs => Abs(Box::new(Literal(need_one(&args)?))),
        ArithmeticMechanism::Min => {
            let (left, right) = need_two(&args)?;
            Min(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        ArithmeticMechanism::Max => {
            let (left, right) = need_two(&args)?;
            Max(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        ArithmeticMechanism::Mod => {
            let (left, right) = need_two(&args)?;
            Mod(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        ArithmeticMechanism::Quotient => {
            let (left, right) = need_two(&args)?;
            Quotient(Box::new(Literal(left)), Box::new(Literal(right)))
        }
    };

    Ok(expr)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ratified_domain_math_is_not_legacy_sid8() {
        let cases = [
            (5, "01010", "2 3", 5),    // укр додати
            (5, "01011", "7 3", 4),    // укр відняти
            (5, "10110", "6 7", 42),   // укр помножити
            (6, "010011", "-5", 5),    // укр модуль
            (6, "110101", "4 9", 4),   // укр найменше
            (6, "110111", "4 9", 9),   // укр найбільше
        ];
        for (width, bits, input, expected) in cases {
            let expr = parse_exact_domain_request(width, bits, input)
                .expect("ratified exact-domain mechanism");
            assert_eq!(expr.evaluate(&HashMap::new()), Ok(Value::Int(expected)));
        }
        // Historic W8 ADD is not D8 ADD, nor is a width silently padded.
        assert!(matches!(
            parse_exact_domain_request(8, "00001100", "2 3"),
            Err(DatalogMathError::UnsupportedDomainOperation { width: 8, .. })
        ));
        assert!(parse_exact_domain_request(6, "01010", "2 3").is_err());
        assert!(parse_exact_domain_request(5, "00001100", "2 3").is_err());
        // Exact SENS quotient cannot be assumed to be truncated i64 division.
        assert!(parse_exact_domain_request(5, "10111", "7 3").is_err());
        assert!(parse_exact_domain_request(5, "01010", "+ 2 3").is_err());
        let expr = parse_exact_domain_request(
            5, "01010", "9223372036854775807 1",
        ).expect("exact addition mechanism");
        assert_eq!(expr.evaluate(&HashMap::new()), Err(DatalogMathError::Overflow));
    }

    #[test]
    fn basic_integer_operations() {
        let bindings = HashMap::new();
        assert_eq!(
            NumericExpr::Add(
                Box::new(NumericExpr::Literal(2)),
                Box::new(NumericExpr::Literal(3))
            )
            .evaluate(&bindings),
            Ok(Value::Int(5))
        );
        assert_eq!(
            NumericExpr::Sub(
                Box::new(NumericExpr::Literal(7)),
                Box::new(NumericExpr::Literal(3))
            )
            .evaluate(&bindings),
            Ok(Value::Int(4))
        );
        assert_eq!(
            NumericExpr::Mul(
                Box::new(NumericExpr::Literal(6)),
                Box::new(NumericExpr::Literal(7))
            )
            .evaluate(&bindings),
            Ok(Value::Int(42))
        );
        assert_eq!(
            NumericExpr::Div(
                Box::new(NumericExpr::Literal(8)),
                Box::new(NumericExpr::Literal(2))
            )
            .evaluate(&bindings),
            Ok(Value::Int(4))
        );
        assert_eq!(
            NumericExpr::Mod(
                Box::new(NumericExpr::Literal(7)),
                Box::new(NumericExpr::Literal(3))
            )
            .evaluate(&bindings),
            Ok(Value::Int(1))
        );
        assert_eq!(
            NumericExpr::Quotient(
                Box::new(NumericExpr::Literal(7)),
                Box::new(NumericExpr::Literal(3))
            )
            .evaluate(&bindings),
            Ok(Value::Int(2))
        );
        assert_eq!(
            NumericExpr::Abs(Box::new(NumericExpr::Literal(-5))).evaluate(&bindings),
            Ok(Value::Int(5))
        );
        assert_eq!(
            NumericExpr::Min(
                Box::new(NumericExpr::Literal(4)),
                Box::new(NumericExpr::Literal(9))
            )
            .evaluate(&bindings),
            Ok(Value::Int(4))
        );
        assert_eq!(
            NumericExpr::Max(
                Box::new(NumericExpr::Literal(4)),
                Box::new(NumericExpr::Literal(9))
            )
            .evaluate(&bindings),
            Ok(Value::Int(9))
        );
    }

    #[test]
    fn variable_expression_uses_relation_bindings() {
        let bindings = HashMap::from([("X".to_string(), Value::Int(7))]);
        let expr = NumericExpr::Add(
            Box::new(NumericExpr::Variable("X".into())),
            Box::new(NumericExpr::Literal(3)),
        );
        assert_eq!(expr.evaluate(&bindings), Ok(Value::Int(10)));
    }

    #[test]
    fn arithmetic_failures_are_named() {
        let bindings = HashMap::new();
        assert_eq!(
            NumericExpr::Div(
                Box::new(NumericExpr::Literal(1)),
                Box::new(NumericExpr::Literal(0))
            )
            .evaluate(&bindings),
            Err(DatalogMathError::DivisionByZero)
        );
        assert_eq!(
            NumericExpr::Abs(Box::new(NumericExpr::Literal(i64::MIN))).evaluate(&bindings),
            Err(DatalogMathError::Overflow)
        );
        assert_eq!(
            NumericExpr::Add(
                Box::new(NumericExpr::Literal(i64::MAX)),
                Box::new(NumericExpr::Literal(1)),
            )
            .evaluate(&bindings),
            Err(DatalogMathError::Overflow)
        );
    }

    #[test]
    fn semantic_request_uses_sid_as_operation_identity() {
        let add = parse_legacy_abi_request(LEGACY_ABI_ADD, "2 3").expect("add request");
        assert_eq!(add.evaluate(&HashMap::new()), Ok(Value::Int(5)));

        let sub = parse_legacy_abi_request(LEGACY_ABI_SUB, "7 3").expect("sub request");
        assert_eq!(sub.evaluate(&HashMap::new()), Ok(Value::Int(4)));

        assert!(
            parse_legacy_abi_request(LEGACY_ABI_ADD, "+ 2 3").is_err(),
            "operator text must not be accepted as semantic identity"
        );
        assert!(matches!(
            parse_legacy_abi_request(0xff, "2 3"),
            Err(DatalogMathError::UnsupportedLegacyAbiId(0xff))
        ));
    }
}
