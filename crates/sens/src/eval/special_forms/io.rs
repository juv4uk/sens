//! Механізми `write-to-string`, `read`/`eval` без доступу ядра до ОС.
//! Інтерактивний ввід належить зовнішньому хосту, а не READ ядра.
//!
//! These operations are value-level mechanisms. Their callable identities are
//! ordinary root `Value::Builtin` bindings; the evaluator does not dispatch on
//! their names.

use super::core::quoted;
use crate::eval::{closures, evaluate, lower};
use crate::{Environment, ErrorKind, Expr, LanguageError, Span, Value};
use std::rc::Rc;

fn contains_predicate_bit(value: &Value) -> bool {
    match value {
        Value::DomainIdentity(crate::DomainIdentity::D1(_)) => true,
        Value::Pair(node) => {
            contains_predicate_bit(&node.head) || contains_predicate_bit(&node.tail)
        }
        Value::Vector(values) => values.borrow().iter().any(contains_predicate_bit),
        _ => false,
    }
}

pub(crate) fn write_to_string_values(
    arguments: &[Value],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_values("write-to-string", arguments, 1, span)?;
    if contains_predicate_bit(&arguments[0]) {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "write-to-string cannot serialize contextual predicate results",
            span,
        ));
    }
    Ok(Value::String(Rc::from(
        arguments[0].to_canonical_wire_string(),
    )))
}

pub(crate) fn read_values(
    arguments: &[Value],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if arguments.len() > 1 {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            "read expects zero or one arguments · read ochikuie nul abo odyn arhument · read erwartet null oder ein Argument",
            span,
        ));
    }
    let source = if let Some(argument) = arguments.first() {
        match argument {
            Value::String(text) => text.to_string(),
            _ => return Err(LanguageError::new(
                ErrorKind::Type,
                "read expects a string · read ochikuie riadok · read erwartet eine Zeichenkette",
                span,
            )),
        }
    } else {
        return Err(LanguageError::new(
            ErrorKind::MechanismUnavailable,
            "READ_HOST_INPUT_UNAVAILABLE: ядро SENS не має неявного вводу ОС; передайте значення для READ через зовнішній ввід",
            span,
        ));
    };
    let expressions = crate::parse_canonical_value_wire(&source).map_err(|mut error| {
        error.span = span;
        error
    })?;
    match <[Expr; 1]>::try_from(expressions) {
        Ok([expression]) => quoted(&expression),
        Err(expressions) => Err(LanguageError::new(
            ErrorKind::InvalidForm,
            format!(
                "read expects exactly one expression, found {} · read ochikuie rivno odyn vyraz, znaideno {} · read erwartet genau einen Ausdruck, gefunden {}",
                expressions.len(), expressions.len(), expressions.len()
            ),
            span,
        )),
    }
}

/// Parse every top-level source form as data. Numeric source values use the
/// exact D24+ projection selected by the current mixed-domain reader.
pub(crate) fn read_all_values(
    arguments: &[Value],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_values("read-all", arguments, 1, span)?;
    let Value::String(source) = &arguments[0] else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "read-all expects a source string",
            span,
        ));
    };
    let expressions = crate::parse_mixed_exact_domain(source).map_err(|mut error| {
        error.span = span;
        error
    })?;
    expressions
        .iter()
        .map(quoted)
        .collect::<Result<Vec<_>, _>>()
        .map(Value::list)
}

pub(crate) fn eval_values(
    arguments: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_values("eval", arguments, 1, span)?;
    let datum = arguments[0].clone();
    if matches!(datum, Value::Closure(_) | Value::Macro(_)) {
        return Ok(datum);
    }
    let expression = closures::value_to_expr(datum, span)?;
    let lowered = lower::lower_program(std::slice::from_ref(&expression));
    evaluate(&lowered[0], environment)
}

fn exact_values(
    name: &'static str,
    arguments: &[Value],
    expected: usize,
    span: Span,
) -> Result<(), LanguageError> {
    if arguments.len() != expected {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            format!("{name} expects exactly {expected} argument(s)"),
            span,
        ));
    }
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn read_without_host_input_has_no_implicit_os_capability() {
        let span = Span::default();
        let error = read_values(&[], &Environment::root(), span)
            .expect_err("ядро без хостового вводу не повинно читати stdin");
        assert_eq!(error.kind, ErrorKind::MechanismUnavailable);
        assert!(error.message.contains("READ_HOST_INPUT_UNAVAILABLE"));
        assert_eq!(error.span, span);
    }

    #[test]
    fn read_preserves_exact_d7_word_from_canonical_write_wire() {
        let result = read_values(
            &[Value::String(Rc::from("1100110"))],
            &Environment::root(),
            Span::default(),
        )
        .expect("canonical D7 word must be readable as data");

        assert_eq!(
            result,
            Value::DomainIdentity(crate::DomainIdentity::D7(crate::D7DataWord::from_word(
                crate::Bit7::new(0b1100110).unwrap(),
            ))),
            "D7 W7 identity must not turn into a mathematical number during READ"
        );
    }

    fn assert_predicate_wire_rejected(value: Value) {
        let error = write_to_string_values(&[value], &Environment::root(), Span::default())
            .expect_err("PredicateBit must not enter canonical wire");
        assert_eq!(error.kind, ErrorKind::Type);
    }

    #[test]
    fn canonical_wire_rejects_predicate_bit_without_numeric_coercion() {
        assert_predicate_wire_rejected(Value::predicate_bit(true));
        assert_predicate_wire_rejected(Value::predicate_bit(false));
        assert_predicate_wire_rejected(Value::list([Value::predicate_bit(true)]));

        let vector = Value::Vector(Rc::new(std::cell::RefCell::new(vec![
            Value::Number(7.0, crate::Exactness::Exact),
            Value::predicate_bit(false),
        ])));
        assert_predicate_wire_rejected(vector);

        let number = write_to_string_values(
            &[Value::Number(1.0, crate::Exactness::Exact)],
            &Environment::root(),
            Span::default(),
        )
        .expect("ordinary exact Number wire remains supported");
        assert_eq!(number, Value::String(Rc::from("#q2:1/1")));
    }

    #[test]
    fn read_all_returns_all_forms_as_data_with_exact_d24_numbers() {
        let result = read_all_values(
            &[Value::String(Rc::from("alpha 42"))],
            &Environment::root(),
            Span::default(),
        )
        .expect("D9 read-all parses all source forms as data");
        let Value::Pair(first) = &result else {
            panic!("two forms must produce a two-element list");
        };
        assert_eq!(first.head, Value::Symbol(Rc::from("alpha")));
        let Value::Pair(rest) = &first.tail else {
            panic!("the second source form must remain in the result list");
        };
        assert!(
            matches!(&rest.head, Value::BinaryNumber(value) if value.numeric_domain_width() == Some(24) && value.to_string() == "42")
        );
        assert!(matches!(&rest.tail, Value::Nil));

        let empty = read_all_values(
            &[Value::String(Rc::from(""))],
            &Environment::root(),
            Span::default(),
        )
        .expect("empty source has no forms");
        assert!(matches!(empty, Value::Nil));

        let type_error = read_all_values(
            &[Value::Symbol(Rc::from("not-text"))],
            &Environment::root(),
            Span::default(),
        )
        .expect_err("read-all accepts source text only");
        assert_eq!(type_error.kind, ErrorKind::Type);
    }
}
