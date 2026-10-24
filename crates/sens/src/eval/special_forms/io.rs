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

// Канонічний дріт приймає лише ті legacy exact f64, для яких
// перетворення на i64 не насичується і не змінює значення.
// Точні числа D24+ мають окремий BinaryNumber-носій і сюди не входять.
fn contains_noncanonical_exact_number(value: &Value) -> bool {
    match value {
        Value::Number(number, crate::Exactness::Exact) => {
            !number.is_finite()
                || number.fract() != 0.0
                || *number < i64::MIN as f64
                || *number >= -(i64::MIN as f64)
        }
        Value::Pair(node) => {
            contains_noncanonical_exact_number(&node.head)
                || contains_noncanonical_exact_number(&node.tail)
        }
        Value::Vector(values) => values
            .borrow()
            .iter()
            .any(contains_noncanonical_exact_number),
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
    if contains_noncanonical_exact_number(&arguments[0]) {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "write-to-string cannot serialize a legacy exact Number without loss",
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
    let expressions = crate::parser::parse_canonical_value_wire(&source).map_err(|mut error| {
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
    fn legacy_exact_number_wire_refuses_saturating_float_to_integer_cast() {
        // as i64 насичує 2^63 до i64::MAX: це не канонічний запис.
        let above_max = Value::Number(-(i64::MIN as f64), crate::Exactness::Exact);
        let below_min = Value::Number((i64::MIN as f64) * 2.0, crate::Exactness::Exact);
        let nested = Value::list([Value::Number(
            -(i64::MIN as f64),
            crate::Exactness::Exact,
        )]);
        let vector = Value::Vector(Rc::new(std::cell::RefCell::new(vec![
            Value::Number(1.0, crate::Exactness::Exact),
            above_max.clone(),
        ])));
        for value in [
            above_max,
            below_min,
            nested,
            vector,
            Value::Number(f64::INFINITY, crate::Exactness::Exact),
            Value::Number(0.5, crate::Exactness::Exact),
        ] {
            let error = write_to_string_values(
                &[value],
                &Environment::root(),
                Span::default(),
            )
            .expect_err("непредставиме exact f64 не може дати успішний wire");
            assert_eq!(error.kind, ErrorKind::Type);
        }

        // Нижня межа i64 представима точно; не відкидати коректні дані.
        let lower_edge = Value::Number(i64::MIN as f64, crate::Exactness::Exact);
        assert!(write_to_string_values(
            &[lower_edge],
            &Environment::root(),
            Span::default(),
        )
        .is_ok());
    }

    #[test]
    fn канонічний_d7_read_write_зберігає_точні_вкладені_комірки() {
        // Rust перевіряє лише механізм запису/читання D7-носія;
        // семантичні закони залишаються в Lisp → SENS.
        let original = Value::list([
            Value::Text7(crate::Text7::from_cells(vec![0x00, 0x7f]).unwrap()),
            Value::list([Value::Text7(
                crate::Text7::from_cells(Vec::new()).unwrap(),
            )]),
        ]);
        let wire = write_to_string_values(
            &[original.clone()],
            &Environment::root(),
            Span::default(),
        )
        .expect("точний D7-носій повинен записуватися");
        let restored = read_values(&[wire], &Environment::root(), Span::default())
            .expect("READ повинен відновити D7, а не Symbol");
        assert_eq!(restored, original);
    }

    #[test]
    fn read_write_зберігає_структурні_d7_слова_без_десяткового_мосту() {
        // D2-список W7 не є Text7. Його точні доменні комірки
        // повинні пережити D8 WRITE→READ без перетворення на Number.
        let w7 = |bits| {
            Value::DomainIdentity(crate::DomainIdentity::from_source_word(
                crate::BinarySourceWord::W7(crate::Bit7::new(bits).unwrap()),
            ))
        };
        let original = Value::list([
            w7(0b0100001),
            Value::list([w7(0b1100001), w7(0b1111111)]),
            Value::String(Rc::from("1100001")),
            Value::Number(5.0, crate::Exactness::Exact),
        ]);
        let wire = write_to_string_values(
            &[original.clone()],
            &Environment::root(),
            Span::default(),
        )
        .expect("WRITE має прийняти канонічні дані");
        let restored = read_values(&[wire], &Environment::root(), Span::default())
            .expect("READ має відновити точні доменні комірки");
        assert_eq!(restored, original);
    }

    #[test]
    fn read_write_зберігає_точну_ширину_числових_d24_plus_слів() {
        for width in [24, 48] {
            let mut bits = vec![0; width];
            bits[width - 1] = 1;
            let original = Value::BinaryNumber(
                crate::BinaryNumber::from_numeric_domain_bits(width, &bits)
                    .expect("exact admitted D24+ word"),
            );
            let wire = write_to_string_values(&[original.clone()], &Environment::root(), Span::default())
                .expect("D24+ exact words must have a reader-safe wire form");
            let expected = format!("#d{width}:{}", "0".repeat(width - 1) + "1");
            assert_eq!(wire, Value::String(Rc::from(expected)));
            let restored = read_values(&[wire], &Environment::root(), Span::default())
                .expect("canonical READ must restore the admitted D24+ word");
            assert_eq!(restored, original);
        }
    }

    #[test]
    fn read_відхиляє_пошкоджений_d7_носій() {
        for source in ["#t7:0", "#t7:80", "#t7:4A", "#t7:gg"] {
            let error = read_values(
                &[Value::String(Rc::from(source))],
                &Environment::root(),
                Span::default(),
            )
            .expect_err("пошкоджений D7 не може стати Symbol");
            assert_eq!(error.kind, ErrorKind::Parse, "{source}");
        }
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
