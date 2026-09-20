//! Datalog-owned integer arithmetic execution.
//!
//! This module is execution machinery only. Semantic meaning and any external
//! semantic identity remain owned by my-lisp.
//!
//! The first admitted surface is deliberately small:
//! +, -, *, /, mod, quotient, abs, min and max over i64 integers.

use std::collections::HashMap;
use std::fmt;

use crate::Value;

#[derive(Clone, Debug, PartialEq, Eq)]
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
                lhs.checked_div(rhs).ok_or_else(|| {
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
                lhs.checked_rem(rhs).ok_or_else(|| {
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
    DivisionByZero,
    Overflow,
}

impl fmt::Display for DatalogMathError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::MissingVariable(name) => write!(formatter, "datalog-math-missing-variable:{name}"),
            Self::NonIntegerValue(value) => write!(formatter, "datalog-math-non-integer:{value:?}"),
            Self::DivisionByZero => write!(formatter, "datalog-math-division-by-zero"),
            Self::Overflow => write!(formatter, "datalog-math-overflow"),
        }
    }
}

impl std::error::Error for DatalogMathError {}

pub fn parse_abi_request(text: &str) -> Result<NumericExpr, DatalogMathError> {
    let mut parts = text.split_whitespace();
    if parts.next() != Some("math") {
        return Err(DatalogMathError::MissingVariable("request".to_string()));
    }

    let operation = parts.next().unwrap_or_default();
    let args: Result<Vec<i64>, DatalogMathError> = parts
        .map(|raw| raw.parse::<i64>().map_err(|_| {
            DatalogMathError::NonIntegerValue(Value::Symbol(raw.to_string()))
        }))
        .collect();
    let args = args?;

    fn need_two(args: &[i64]) -> Result<(i64, i64), DatalogMathError> {
        match args {
            [left, right] => Ok((*left, *right)),
            _ => Err(DatalogMathError::MissingVariable("two-operands".to_string())),
        }
    }

    fn need_one(args: &[i64]) -> Result<i64, DatalogMathError> {
        match args {
            [value] => Ok(*value),
            _ => Err(DatalogMathError::MissingVariable("one-operand".to_string())),
        }
    }

    use NumericExpr::*;
    let expr = match operation {
        "+" => {
            let (left, right) = need_two(&args)?;
            Add(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        "-" => {
            let (left, right) = need_two(&args)?;
            Sub(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        "*" => {
            let (left, right) = need_two(&args)?;
            Mul(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        "/" => {
            let (left, right) = need_two(&args)?;
            Div(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        "mod" => {
            let (left, right) = need_two(&args)?;
            Mod(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        "quotient" => {
            let (left, right) = need_two(&args)?;
            Quotient(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        "abs" => Abs(Box::new(Literal(need_one(&args)?))),
        "min" => {
            let (left, right) = need_two(&args)?;
            Min(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        "max" => {
            let (left, right) = need_two(&args)?;
            Max(Box::new(Literal(left)), Box::new(Literal(right)))
        }
        _ => return Err(DatalogMathError::MissingVariable(format!("unsupported-operation:{operation}"))),
    };

    if parts.next().is_some() {
        return Err(DatalogMathError::MissingVariable("trailing-operands".to_string()));
    }

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
    fn abi_request_parses_only_the_admitted_math_surface() {
        let expr = parse_abi_request("math + 2 3").expect("add request");
        assert_eq!(expr.evaluate(&HashMap::new()), Ok(Value::Int(5)));
        assert!(parse_abi_request("math sqrt 9").is_err());
    }
}
