//! The McCarthy primitives (`eq`, `car`, `cdr`, `cons`, `cond`, `quote`'s
//! helper), plus the compatibility `def` surface. Language-owned `defmacro`
//! is bootstrapped from `lib/macro.lisp`; the Rust kernel no longer implements it.

use crate::eval::canon;
use crate::eval::{evaluate, evaluate_step, EvalStep};
use crate::{Environment, ErrorKind, Expr, ExprKind, LanguageError, Span, Value};

use std::rc::Rc;

/// D3:010 ATOM is a total predicate. Its answer is exact D1, never NIL/list truth.
pub(crate) fn atom_value(value: &Value, _environment: &Environment) -> Value {
    Value::predicate_bit(!matches!(value, Value::Pair(_, _)))
}
pub(crate) fn evaluate_definition(
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_sens_arity(crate::sens!(00001011), arguments, 2, span)?;
    let ExprKind::Symbol(name) = &arguments[0].kind else {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "def expects a symbol name · def ochikuie nazvu-symvol · def erwartet einen Symbolnamen",
            arguments[0].span,
        ));
    };
    canon::ensure_bindable(name, arguments[0].span)?;
    let value = evaluate(&arguments[1], environment)?;
    // The shared lexical frame makes recursive definitions visible to their closure after binding.
    // Spilnyi leksychnyi freim robyt rekursyvne vyznachennia vydymym zamykanniu pislia zv’yazuvannia.
    // Der gemeinsame lexikalische Frame macht rekursive Definitionen nach der Bindung für ihre Closure sichtbar.
    canon::bind_language_definition(name, &value, environment);
    environment.define(name.clone(), value.clone());
    Ok(value)
}

/// Mechanism-only projection from admitted predicate/no-witness values to
/// the single control question "select this clause?".  Returning `false`
/// for both D1:0 and `()` does not equate those language values.
fn cond_selects(value: &Value, span: Span) -> Result<bool, LanguageError> {
    match value.as_predicate_bit() {
        Some(bit) => Ok(bit),
        None if matches!(value, Value::Nil) => Ok(false),
        None => Err(LanguageError::new(
            ErrorKind::Type,
            format!("cond test must return exact D1 PredicateBit or structural (); got {value}"),
            span,
        )),
    }
}
pub(crate) fn evaluate_cond(
    clauses: &[Expr],
    environment: &Environment,
    _span: Span,
) -> Result<EvalStep, LanguageError> {
    for clause in clauses {
        let ExprKind::List(parts) = &clause.kind else {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                "cond expects list clauses · cond ochikuie spysky-umovy · cond erwartet Listenklauseln",
                clause.span,
            ));
        };

        if parts.len() != 2 {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                "cond expects exactly (test expression) clauses",
                clause.span,
            ));
        }

        let value = evaluate(&parts[0], environment)?;
        if cond_selects(&value, parts[0].span)? {
            return evaluate_step(&parts[1], environment);
        }
    }

    Ok(EvalStep::Value(Value::Nil))
}

pub fn exact_arity(
    operator: &str,
    arguments: &[Expr],
    expected: usize,
    span: Span,
) -> Result<(), LanguageError> {
    if arguments.len() == expected {
        return Ok(());
    }
    Err(LanguageError::new(
        ErrorKind::Arity,
        format!(
            "{operator}: expected / ochikuvalosia / erwartet {expected}; received / otrymano / erhalten {}",
            arguments.len()
        ),
        span,
    ))
}

/// Arity check for a SENS form inside the core: the form is named by its
/// 8-bit code, never by a surface spelling. `exact_arity` stays for host
/// capabilities, which are not SENS identities.
pub fn exact_sens_arity(
    operator: crate::Sens8,
    arguments: &[Expr],
    expected: usize,
    span: Span,
) -> Result<(), LanguageError> {
    if arguments.len() == expected {
        return Ok(());
    }
    Err(LanguageError::new(
        ErrorKind::Arity,
        format!(
            "{operator}: expected / ochikuvalosia / erwartet {expected}; received / otrymano / erhalten {}",
            arguments.len()
        ),
        span,
    ))
}

pub(crate) fn quoted(expression: &Expr) -> Result<Value, LanguageError> {
    fn go(expression: &Expr, depth: u32) -> Result<Value, LanguageError> {
        if depth > crate::syntax::MAX_STRUCTURE_DEPTH {
            return Err(LanguageError::new(
                ErrorKind::Parse,
                "quoted structure exceeds reader limit · struktura perevyshchuie mezhu chytacha · zitierte Struktur überschreitet das Reader-Limit",
                Span { start: 0, end: 0 },
            ));
        }
        Ok(match &expression.kind {
            ExprKind::Number(number, exactness) => Value::Number(*number, *exactness),
            ExprKind::Rational(rational) => Value::Rational(rational.clone()),
            ExprKind::BinaryNumber(number) => Value::BinaryNumber(number.clone()),
            ExprKind::Sid(sid) => Value::Sid(*sid),
            ExprKind::DomainIdentity(identity) => Value::DomainIdentity(*identity),
            ExprKind::NumericBuffer(buffer) => Value::NumericBuffer(buffer.clone()),
            ExprKind::String(value) => Value::String(value.clone()),
            ExprKind::Symbol(symbol) => Value::Symbol(symbol.clone()),
            // Слот — координата виконання, не дані: у quote-позиції його не буває
            // (розв'язувач її не чіпає), тож така поява — порушення інваріанта.
            ExprKind::Local { .. } => {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    "a lexical slot has no source datum · leksychnyi slot ne maie danykh dzherela · ein lexikalischer Slot hat kein Quelldatum",
                    expression.span,
                ));
            }
            ExprKind::List(items) => {
                let mut out = Vec::with_capacity(items.len());
                for item in items.iter() {
                    out.push(go(item, depth + 1)?);
                }
                Value::list(out)
            }
            ExprKind::Pair(head, tail) => {
                Value::Pair(Rc::new(go(head, depth + 1)?), Rc::new(go(tail, depth + 1)?))
            }
            // Зведений виклик як дані — список із функцією СЕНС у голові.
            ExprKind::Call(sid, arguments) => {
                let mut out = Vec::with_capacity(arguments.len() + 1);
                out.push(Value::Sid(*sid));
                for argument in arguments.iter() {
                    out.push(go(argument, depth + 1)?);
                }
                Value::list(out)
            }
            ExprKind::DomainCall(identity, arguments) => {
                let mut out = Vec::with_capacity(arguments.len() + 1);
                out.push(Value::DomainIdentity((*identity).into()));
                for argument in arguments.iter() {
                    out.push(go(argument, depth + 1)?);
                }
                Value::list(out)
            }
        })
    }
    go(expression, 0)
}

// ── contract 2.1: value-level entry points (first-class builtins) ──
// Same compute as the expr-handlers above; arguments arrive
// pre-evaluated. The expr-handlers delegate here after evaluating.

pub(crate) fn car_value(value: &Value, span: Span) -> Result<Value, LanguageError> {
    match value {
        Value::Pair(ref head, _) => Ok((**head).clone()),
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "car expects a non-empty list · car ochikuie neporozhnii spysok · car erwartet eine nicht leere Liste",
            span,
        )),
    }
}

pub(crate) fn cdr_value(value: &Value, span: Span) -> Result<Value, LanguageError> {
    match value {
        Value::Pair(_, ref tail) => Ok((**tail).clone()),
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "cdr expects a non-empty list · cdr ochikuie neporozhnii spysok · cdr erwartet eine nicht leere Liste",
            span,
        )),
    }
}

pub(crate) fn cons_values(
    head: Value,
    tail: Value,
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if environment.try_alloc_cons().is_err() {
        return Err(LanguageError::new(
            ErrorKind::OutOfMemory,
            "cons: resource limit reached · cons: dosiahnuto mezhi resursu · cons: Ressourcengrenze erreicht",
            span,
        ));
    }
    Ok(Value::Pair(std::rc::Rc::new(head), std::rc::Rc::new(tail)))
}

pub(crate) fn eq_values(left: Value, right: Value, _span: Span) -> Result<Value, LanguageError> {
    if !left.is_atom() || !right.is_atom() {
        // #3161: EQ is a partial predicate. Outside its admitted atom domain,
        // structural EMPTY means no witness; it is neither FALSE nor an error.
        return Ok(Value::Nil);
    }
    Ok(Value::predicate_bit(left == right))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::Exactness;

    fn span() -> Span {
        Span { start: 0, end: 0 }
    }

    #[test]
    fn empty_and_no_are_distinct_values_but_both_do_not_select_cond() {
        let no = Value::predicate_bit(false);
        let empty = Value::Nil;
        assert_ne!(no, empty);
        assert!(!cond_selects(&no, span()).unwrap());
        assert!(!cond_selects(&empty, span()).unwrap());
        assert!(cond_selects(&Value::predicate_bit(true), span()).unwrap());
    }

    #[test]
    fn cond_rejects_ordinary_numeric_truthiness() {
        let error = cond_selects(&Value::Number(1.0, Exactness::Exact), span())
            .expect_err("ordinary Number 1 is not D1 PredicateBit");
        assert_eq!(error.kind, ErrorKind::Type);
    }

    #[test]
    fn atom_is_total_but_eq_can_return_empty_no_witness() {
        let env = Environment::root();
        assert_eq!(atom_value(&Value::Nil, &env).as_predicate_bit(), Some(true));
        let pair = Value::Pair(Rc::new(Value::Nil), Rc::new(Value::Nil));
        assert_eq!(atom_value(&pair, &env).as_predicate_bit(), Some(false));

        assert_eq!(
            eq_values(Value::Nil, Value::Nil, span()).unwrap().as_predicate_bit(),
            Some(true)
        );
        assert_eq!(
            eq_values(
                Value::Number(1.0, Exactness::Exact),
                Value::Number(2.0, Exactness::Exact),
                span(),
            )
            .unwrap()
            .as_predicate_bit(),
            Some(false)
        );
        assert!(matches!(
            eq_values(pair, Value::Nil, span()).unwrap(),
            Value::Nil
        ));
    }
}
