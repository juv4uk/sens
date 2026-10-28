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

/// Host arithmetic is a mechanism, not a language operation selector.
/// SENS owns the exact domain/code/укр lookup; Zig alone transports its bits.
/// Rust receives a typed execution request AFTER that admission. In particular
/// no W8 byte, D7 text or domain-width guessing can select a mechanism here.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ArithmeticMechanism {
    Add, Sub, Mul, Div, Abs, Min, Max, Mod, Quotient,
}

/// Execute an already-selected *mechanism*. This API accepts neither SID8
/// nor domain words: choosing their meaning remains exclusively SENS's job.
pub fn parse_arithmetic_mechanism(
    operation: ArithmeticMechanism, payload: &str,
) -> Result<NumericExpr, DatalogMathError> {
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

