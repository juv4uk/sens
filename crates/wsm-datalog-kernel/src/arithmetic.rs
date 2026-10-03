//! Datalog-owned integer arithmetic execution.
//!
//! This module is execution machinery only. Semantic meaning and any external
//! semantic identity remain owned by sens.
//!
//! The first bounded mechanism set is deliberately small.
//! Semantic operation identity is always the exact 8-bit SID carried by the
//! shared ABI; payload text contains arguments only and can never select an operation.

use std::collections::HashMap;
use std::fmt;

use crate::Value;

pub const SID_ADD: u8 = 0b0000_1100;
pub const SID_SUB: u8 = 0b0000_1101;
pub const SID_MUL: u8 = 0b0000_1110;
pub const SID_DIV: u8 = 0b0000_1111;
pub const SID_ABS: u8 = 0b0001_0000;
pub const SID_MIN: u8 = 0b0001_0001;
pub const SID_MAX: u8 = 0b0001_0010;
pub const SID_MOD: u8 = 0b0001_0011;
pub const SID_QUOTIENT: u8 = 0b0001_0100;

pub fn is_legacy_math_id(sid: u8) -> bool {
    matches!(
        sid,
        SID_ADD
            | SID_SUB
            | SID_MUL
            | SID_DIV
            | SID_ABS
            | SID_MIN
            | SID_MAX
            | SID_MOD
            | SID_QUOTIENT
    )
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
            Add(left, right) => integer(left)?.checked_add(integer(right)?).ok_or(DatalogMathError::Overflow)?,
            Sub(left, right) => integer(left)?.checked_sub(integer(right)?).ok_or(DatalogMathError::Overflow)?,
            Mul(left, right) => integer(left)?.checked_mul(integer(right)?).ok_or(DatalogMathError::Overflow)?,
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
            Abs(value) => integer(value)?.checked_abs().ok_or(DatalogMathError::Overflow)?,
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
            Self::MissingVariable(name) => write!(formatter, "datalog-math-missing-variable:{name}"),
            Self::NonIntegerValue(value) => write!(formatter, "datalog-math-non-integer:{value:?}"),
            Self::InvalidArgument(value) => write!(formatter, "datalog-math-invalid-argument:{value}"),
            Self::UnsupportedLegacyAbiId(sid) => {
                write!(formatter, "datalog-math-unsupported-semantic-id:{sid:08b}")
            }
            Self::DivisionByZero => write!(formatter, "datalog-math-division-by-zero"),
            Self::Overflow => write!(formatter, "datalog-math-overflow"),
        }
    }
}

impl std::error::Error for DatalogMathError {}

pub fn parse_legacy_abi_request(
    semantic_id: u8,
    payload: &str,
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
    let expr = match semantic_id {
        SID_ADD => {
            let (left, right) = need_two(&args)?;
            Add(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        SID_SUB => {
            let (left, right) = need_two(&args)?;
            Sub(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        SID_MUL => {
            let (left, right) = need_two(&args)?;
            Mul(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        SID_DIV => {
            let (left, right) = need_two(&args)?;
            Div(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        SID_ABS => Abs(Box::new(Literal(need_one(&args)?))),
        SID_MIN => {
            let (left, right) = need_two(&args)?;
            Min(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        SID_MAX => {
            let (left, right) = need_two(&args)?;
            Max(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        SID_MOD => {
            let (left, right) = need_two(&args)?;
            Mod(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        SID_QUOTIENT => {
            let (left, right) = need_two(&args)?;
            Quotient(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        other => return Err(DatalogMathError::UnsupportedLegacyAbiId(other)),
    };

    Ok(expr)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn basic_integer_operations() {
        let bindings = HashMap::new();
        assert_eq!(
            NumericExpr::Add(Box::new(NumericExpr::Literal(2)), Box::new(NumericExpr::Literal(3)))
                .evaluate(&bindings),
            Ok(Value::Int(5))
        );
        assert_eq!(
            NumericExpr::Sub(Box::new(NumericExpr::Literal(7)), Box::new(NumericExpr::Literal(3)))
                .evaluate(&bindings),
            Ok(Value::Int(4))
        );
        assert_eq!(
            NumericExpr::Mul(Box::new(NumericExpr::Literal(6)), Box::new(NumericExpr::Literal(7)))
                .evaluate(&bindings),
            Ok(Value::Int(42))
        );
        assert_eq!(
            NumericExpr::Div(Box::new(NumericExpr::Literal(8)), Box::new(NumericExpr::Literal(2)))
                .evaluate(&bindings),
            Ok(Value::Int(4))
        );
        assert_eq!(
            NumericExpr::Mod(Box::new(NumericExpr::Literal(7)), Box::new(NumericExpr::Literal(3)))
                .evaluate(&bindings),
            Ok(Value::Int(1))
        );
        assert_eq!(
            NumericExpr::Quotient(Box::new(NumericExpr::Literal(7)), Box::new(NumericExpr::Literal(3)))
                .evaluate(&bindings),
            Ok(Value::Int(2))
        );
        assert_eq!(
            NumericExpr::Abs(Box::new(NumericExpr::Literal(-5))).evaluate(&bindings),
            Ok(Value::Int(5))
        );
        assert_eq!(
            NumericExpr::Min(Box::new(NumericExpr::Literal(4)), Box::new(NumericExpr::Literal(9)))
                .evaluate(&bindings),
            Ok(Value::Int(4))
        );
        assert_eq!(
            NumericExpr::Max(Box::new(NumericExpr::Literal(4)), Box::new(NumericExpr::Literal(9)))
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
            NumericExpr::Div(Box::new(NumericExpr::Literal(1)), Box::new(NumericExpr::Literal(0)))
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
        let add = parse_legacy_abi_request(SID_ADD, "2 3").expect("add request");
        assert_eq!(add.evaluate(&HashMap::new()), Ok(Value::Int(5)));

        let sub = parse_legacy_abi_request(SID_SUB, "7 3").expect("sub request");
        assert_eq!(sub.evaluate(&HashMap::new()), Ok(Value::Int(4)));

        assert!(
            parse_legacy_abi_request(SID_ADD, "+ 2 3").is_err(),
            "operator text must not be accepted as semantic identity"
        );
        assert!(matches!(
            parse_legacy_abi_request(0xff, "2 3"),
            Err(DatalogMathError::UnsupportedLegacyAbiId(0xff))
        ));
    }
}
