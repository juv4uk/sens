//! Exact source-shaped program-data representation.
//!
//! Converts already-lowered SENS AST into ordinary runtime data without
//! reintroducing human spellings or legacy SID8 identity.
//! DomainCall(identity,args...) becomes a proper list headed by the exact
//! first-class DomainIdentity. This module owns representation only.

use crate::{DomainIdentity, ErrorKind, Expr, ExprKind, LanguageError, Span, Value};
use std::rc::Rc;

fn invalid_program_data(message: impl Into<String>) -> LanguageError {
    LanguageError::new(ErrorKind::InvalidForm, message, Span::default())
}

/// Convert one already-lowered expression into source-shaped exact program-data.
pub fn expr_to_exact_program_data(expr: &Expr) -> Result<Value, LanguageError> {
    Ok(match &expr.kind {
        ExprKind::Number(value, exactness) => Value::Number(*value, *exactness),
        ExprKind::Rational(value) => Value::Rational(value.clone()),
        ExprKind::BinaryNumber(value) => Value::BinaryNumber(value.clone()),
        ExprKind::NumericBuffer(value) => Value::NumericBuffer(value.clone()),
        ExprKind::DomainIdentity(identity) => Value::DomainIdentity(*identity),
        ExprKind::String(value) => Value::String(value.clone()),
        ExprKind::Symbol(value) => Value::Symbol(value.clone()),
        ExprKind::List(items) => Value::list(
            items
                .iter()
                .map(expr_to_exact_program_data)
                .collect::<Result<Vec<_>, _>>()?,
        ),
        ExprKind::Pair(head, tail) => Value::Pair(
            Rc::new(expr_to_exact_program_data(head)?),
            Rc::new(expr_to_exact_program_data(tail)?),
        ),
        ExprKind::DomainCall(identity, arguments) => {
            let mut items = Vec::with_capacity(arguments.len() + 1);
            items.push(Value::DomainIdentity(DomainIdentity::from(*identity)));
            for argument in arguments.iter() {
                items.push(expr_to_exact_program_data(argument)?);
            }
            Value::list(items)
        }
        ExprKind::Sid(_) | ExprKind::Call(_, _) => {
            return Err(invalid_program_data(
                "exact program-data must not contain legacy Sid/Call nodes",
            ));
        }
        ExprKind::Local { .. } => {
            return Err(invalid_program_data(
                "source-shaped exact program-data must not contain resolved Local nodes",
            ));
        }
    })
}

/// Convert an already-lowered top-level program into a proper data list.
pub fn lowered_program_to_exact_data(program: &[Expr]) -> Result<Value, LanguageError> {
    Ok(Value::list(
        program
            .iter()
            .map(expr_to_exact_program_data)
            .collect::<Result<Vec<_>, _>>()?,
    ))
}
