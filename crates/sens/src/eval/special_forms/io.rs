//! Поточні механізми `write-to-string`, `read`/`eval` та єдине місце ядра,
//! що читає stdin (`read_stdin_line`, лише для `(read)` без аргументів).
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

// Відновлюємо тільки явно типізовані D7-слова канонічного WRITE.
// Звичайний source-reader не змінює символи на Text7 за подібністю назв.
fn quoted_canonical_wire(expression: &Expr, depth: u32) -> Result<Value, LanguageError> {
    if depth > crate::syntax::MAX_STRUCTURE_DEPTH {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "read: canonical wire exceeds structure depth",
            expression.span,
        ));
    }
    match &expression.kind {
        crate::ExprKind::Symbol(token) if token.starts_with(crate::Text7::WIRE_TAG) => {
            crate::Text7::from_canonical_wire_token(token)
                .map(Value::Text7)
                .map_err(|error| {
                    LanguageError::new(
                        ErrorKind::Parse,
                        format!("read: invalid exact D7 wire token: {error:?}"),
                        expression.span,
                    )
                })
        }
        crate::ExprKind::List(items) => {
            let values = items
                .iter()
                .map(|item| quoted_canonical_wire(item, depth + 1))
                .collect::<Result<Vec<_>, _>>()?;
            Ok(Value::list(values))
        }
        crate::ExprKind::Pair(head, tail) => Ok(Value::Pair(Rc::new(crate::PairNode {
            head: quoted_canonical_wire(head, depth + 1)?,
            tail: quoted_canonical_wire(tail, depth + 1)?,
        }))),
        _ => quoted(expression),
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
        read_stdin_line(span)?
    };
    let expressions = crate::parse(&source).map_err(|mut error| {
        error.span = span;
        error
    })?;
    match <[Expr; 1]>::try_from(expressions) {
        Ok([expression]) => quoted_canonical_wire(&expression, 0),
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

#[cfg(not(target_arch = "wasm32"))]
fn read_stdin_line(span: Span) -> Result<String, LanguageError> {
    use std::io::BufRead;
    let mut line = String::new();
    std::io::stdin().lock().read_line(&mut line).map_err(|error| {
        LanguageError::new(
            ErrorKind::InvalidForm,
            format!("read: failed to read from stdin · read: ne vdalos prochytaty stdin · read: Lesen von stdin fehlgeschlagen: {error}"),
            span,
        )
    })?;
    Ok(line.trim_end_matches(['\n', '\r']).to_string())
}

#[cfg(target_arch = "wasm32")]
fn read_stdin_line(span: Span) -> Result<String, LanguageError> {
    Err(LanguageError::new(
        ErrorKind::InvalidForm,
        "read: interactive stdin is not available in this build · read: interaktyvnyi stdin nedostupnyi u tsii zbirtsi · read: interaktives stdin ist in diesem Build nicht verfügbar",
        span,
    ))
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
    fn read_restores_nested_exact_d7_wire_values() {
        let text = crate::Text7::from_cells(vec![0x41, 0x42])
            .expect("exact D7 cells");
        let original = Value::list([
            Value::Text7(text.clone()),
            Value::list([Value::Text7(text)]),
        ]);
        let wire = write_to_string_values(
            &[original.clone()],
            &Environment::root(),
            Span::default(),
        )
        .expect("canonical WRITE");
        let restored = read_values(&[wire], &Environment::root(), Span::default())
            .expect("canonical READ");
        assert_eq!(restored, original, "Text7 must not become a Symbol");
    }

    #[test]
    fn read_rejects_malformed_d7_wire_and_keeps_quoted_string() {
        let error = read_values(
            &[Value::String(Rc::from("#t7:80"))],
            &Environment::root(),
            Span::default(),
        )
        .expect_err("a high-bit D7 cell must fail closed");
        assert_eq!(error.kind, ErrorKind::Parse);

        let literal = read_values(
            &[Value::String(Rc::from("\"#t7:41\""))],
            &Environment::root(),
            Span::default(),
        )
        .expect("quoted source string remains a String");
        assert_eq!(literal, Value::String(Rc::from("#t7:41")));
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
