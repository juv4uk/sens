//! Рядкові й символьні механізми на Rust.
//! Identity та допуск визначає доменний диспетчер; тут лише виконавчі функції
//! для явно підключених маршрутів.

use crate::{ErrorKind, LanguageError, Span, Value};
use std::rc::Rc;

fn exact_value_arity(
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

pub(crate) fn string_append_values(
    arguments: &[Value],
    span: Span,
) -> Result<Value, LanguageError> {
    exact_value_arity("string-append", arguments, 2, span)?;
    let Value::String(left) = &arguments[0] else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "string-append expects two strings · string-append ochikuie dva riadky · string-append erwartet zwei Zeichenketten",
            span,
        ));
    };
    let Value::String(right) = &arguments[1] else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "string-append expects two strings · string-append ochikuie dva riadky · string-append erwartet zwei Zeichenketten",
            span,
        ));
    };
    Ok(Value::String(Rc::from(format!("{left}{right}").as_str())))
}

pub(crate) fn symbol_to_string_values(
    arguments: &[Value],
    span: Span,
) -> Result<Value, LanguageError> {
    exact_value_arity("symbol->string", arguments, 1, span)?;
    match &arguments[0] {
        Value::Symbol(symbol) => Ok(Value::String(symbol.clone())),
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "symbol->string expects a symbol · symbol->string ochikuie symvol · symbol->string erwartet ein Symbol",
            span,
        )),
    }
}

pub(crate) fn string_to_symbol_values(
    arguments: &[Value],
    span: Span,
) -> Result<Value, LanguageError> {
    exact_value_arity("string->symbol", arguments, 1, span)?;
    match &arguments[0] {
        Value::String(text) => Ok(Value::Symbol(text.clone())),
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "string->symbol expects a string · string->symbol ochikuie riadok · string->symbol erwartet eine Zeichenkette",
            span,
        )),
    }
}

pub(crate) fn string_first_values(arguments: &[Value], span: Span) -> Result<Value, LanguageError> {
    exact_value_arity("string-first", arguments, 1, span)?;
    match &arguments[0] {
        Value::String(text) => match text.chars().next() {
            Some(character) => Ok(Value::String(Rc::from(character.to_string().as_str()))),
            None => Err(LanguageError::new(
                ErrorKind::Type,
                "string-first expects a non-empty string · string-first ochikuie neporozhnii riadok · string-first erwartet eine nicht leere Zeichenkette",
                span,
            )),
        },
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "string-first expects a string · string-first ochikuie riadok · string-first erwartet eine Zeichenkette",
            span,
        )),
    }
}

pub(crate) fn string_rest_values(arguments: &[Value], span: Span) -> Result<Value, LanguageError> {
    exact_value_arity("string-rest", arguments, 1, span)?;
    match &arguments[0] {
        Value::String(text) => {
            let mut characters = text.chars();
            if characters.next().is_none() {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "string-rest expects a non-empty string · string-rest ochikuie neporozhnii riadok · string-rest erwartet eine nicht leere Zeichenkette",
                    span,
                ));
            }
            Ok(Value::String(Rc::from(characters.as_str())))
        }
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "string-rest expects a string · string-rest ochikuie riadok · string-rest erwartet eine Zeichenkette",
            span,
        )),
    }
}
