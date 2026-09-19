//! Людське подання значень і діагностик для інтерактивних поверхонь.
//!
//! Канонічні `Value::Display` і `LanguageError::render` не змінюються: ними
//! користуються conformance-перевірки, машинні протоколи й точне відтворення
//! джерела. Цей модуль змінює лише те, що інтерактивна поверхня показує людині.

use crate::{semantic_registry, ErrorKind, Exactness, LanguageError, NumericBuffer, Value};
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PresentationLanguage {
    Canonical,
    English,
    Ukrainian,
    Sanskrit,
}

fn uk_operation_name(name: &str) -> String {
    match name {
        "PRIM_ATOM" => "атом?".to_string(),
        "PRIM_EQ" => "тотожне?".to_string(),
        "PRIM_CONS" => "сполучити".to_string(),
        "PRIM_CAR" => "перше".to_string(),
        "PRIM_CDR" => "решта".to_string(),
        other => semantic_registry::semantic_id_for_surface(other)
            .map(uk_semantic_name)
            .unwrap_or_else(|| other.to_string()),
    }
}

fn uk_semantic_name(semantic_id: u8) -> String {
    semantic_registry::admitted_surfaces_with_namespace_for_semantic_id(semantic_id)
        .into_iter()
        .find_map(|(namespace, name)| (namespace == "uk").then_some(name.to_string()))
        .unwrap_or_else(|| format!("SID {}", semantic_registry::semantic_id_bits(semantic_id)))
}

fn canonical_inexact(number: f64) -> String {
    if number.fract() == 0.0 && number.is_finite() {
        format!("{number:.1}")
    } else {
        number.to_string()
    }
}

fn uk_decimal(text: String) -> String {
    text.replace('.', ",")
}

fn render_uk(value: &Value) -> String {
    match value {
        Value::SemanticRef(semantic_id) => {
            format!("#<вбудована {}>", uk_semantic_name(*semantic_id))
        }
        Value::Builtin(builtin) => {
            format!("#<вбудована {}>", uk_operation_name(builtin.name))
        }
        Value::HostHandle { kind, .. } => format!("#<host-об'єкт {kind}>"),
        Value::Vector(vector) => {
            let items = vector.borrow().iter().map(render_uk).collect::<Vec<_>>();
            format!("#({})", items.join(" "))
        }
        Value::NumericBuffer(NumericBuffer::I32(values)) => {
            let items = values.iter().map(i32::to_string).collect::<Vec<_>>();
            format!("#i32({})", items.join(" "))
        }
        Value::NumericBuffer(NumericBuffer::F32(values)) => {
            let items = values
                .iter()
                .map(|number| {
                    let text = if number.fract() == 0.0 {
                        format!("{number:.1}")
                    } else {
                        number.to_string()
                    };
                    uk_decimal(text)
                })
                .collect::<Vec<_>>();
            format!("#f32({})", items.join(" "))
        }
        Value::Nil | Value::Bool(false) => "()".to_string(),
        Value::Bool(true) => "істина".to_string(),
        Value::Number(number, Exactness::Exact) => number.to_string(),
        Value::Number(number, Exactness::Inexact) => uk_decimal(canonical_inexact(*number)),
        Value::Rational(number) => number.to_string(),
        Value::String(text) => {
            let mut escaped = String::with_capacity(text.len() + 2);
            escaped.push('"');
            for ch in text.chars() {
                match ch {
                    '"' => escaped.push_str("\\\""),
                    '\\' => escaped.push_str("\\\\"),
                    '\n' => escaped.push_str("\\n"),
                    '\t' => escaped.push_str("\\t"),
                    other => escaped.push(other),
                }
            }
            escaped.push('"');
            escaped
        }
        Value::Symbol(symbol) if symbol.as_ref() == "t" => "істина".to_string(),
        Value::Symbol(symbol) => symbol.to_string(),
        Value::Pair(_, _) => render_pair_uk(value),
        Value::Closure(_) => "<функція>".to_string(),
        Value::Macro(_) => "<макрос>".to_string(),
        Value::TcpConnection(_) => "<tcp-з'єднання>".to_string(),
        Value::TcpListener(_) => "<tcp-слухач>".to_string(),
    }
}

fn render_pair_uk(value: &Value) -> String {
    let mut output = String::from("(");
    let mut current = value;
    let mut first = true;
    loop {
        match current {
            Value::Pair(head, tail) => {
                if !first {
                    output.push(' ');
                }
                output.push_str(&render_uk(head));
                current = tail;
                first = false;
            }
            Value::Nil => {
                output.push(')');
                return output;
            }
            tail => {
                output.push_str(" . ");
                output.push_str(&render_uk(tail));
                output.push(')');
                return output;
            }
        }
    }
}

pub fn render_value_for_presentation(value: &Value, language: PresentationLanguage) -> String {
    match language {
        PresentationLanguage::Ukrainian => render_uk(value),
        PresentationLanguage::Canonical
        | PresentationLanguage::English
        | PresentationLanguage::Sanskrit => value.to_string(),
    }
}

fn argument_word(count: usize) -> &'static str {
    let tens = count % 100;
    let ones = count % 10;
    if tens == 11 {
        "аргументів"
    } else if ones == 1 {
        "аргумент"
    } else if (2..=4).contains(&ones) && !(12..=14).contains(&tens) {
        "аргументи"
    } else {
        "аргументів"
    }
}

fn translate_expectation(text: &str) -> String {
    if let Some(count) = text
        .strip_prefix("exactly ")
        .and_then(|rest| rest.strip_suffix(" argument(s)"))
        .and_then(|digits| digits.parse::<usize>().ok())
    {
        return format!("рівно {count} {}", argument_word(count));
    }

    match text {
        "a non-empty list" => "непорожній список".to_string(),
        "two atoms" => "два атоми".to_string(),
        "a callable function" => "функцію, яку можна викликати".to_string(),
        "a symbol name" => "ім'я-символ".to_string(),
        "list clauses" => "спискові гілки".to_string(),
        "(test expression) clauses" => "гілки виду (перевірка вираз)".to_string(),
        "zero or one arguments" => "нуль або один аргумент".to_string(),
        "an exact non-negative integer" => "точне невід'ємне ціле число".to_string(),
        "a string" => "текст".to_string(),
        "a string path" => "текстовий шлях".to_string(),
        "a list of strings for its second argument" => {
            "список текстів другим аргументом".to_string()
        }
        other => other
            .replace("non-empty list", "непорожній список")
            .replace("list of strings", "список текстів")
            .replace("string", "текст")
            .replace("integer", "ціле число")
            .replace("number", "число")
            .replace("symbol", "символ")
            .replace("vector", "вектор")
            .replace("argument(s)", "аргументів")
            .replace("arguments", "аргументи"),
    }
}

fn ukrainian_message(message: &str) -> String {
    if message.starts_with("unknown symbol") {
        let symbol = message
            .rsplit_once(": ")
            .map(|(_, symbol)| symbol)
            .unwrap_or("?");
        return format!("Невідомий символ: {symbol}");
    }

    if let Some((operator, rest)) = message.split_once(": expected / ochikuvalosia / erwartet ") {
        if let Some((expected, received)) = rest.split_once("; received / otrymano / erhalten ") {
            return format!(
                "{}: очікувалося {expected}; отримано {received}",
                uk_operation_name(operator)
            );
        }
    }

    let english = message.split(" · ").next().unwrap_or(message).trim();

    match english {
        "unexpected closing parenthesis" => "неочікувана закривна дужка".to_string(),
        "unclosed list" => "незакритий список".to_string(),
        "unclosed string" => "незакритий текстовий рядок".to_string(),
        "unclosed numeric buffer" => "незакритий числовий буфер".to_string(),
        "unexpected end of input" | "unexpected eof" => "неочікуваний кінець вводу".to_string(),
        "division by zero" => "Ділення на нуль".to_string(),
        "a dotted pair is not executable code" => {
            "крапкова пара не є виконуваним кодом".to_string()
        }
        "quoted structure exceeds reader limit" => {
            "цитована структура перевищує межу читача".to_string()
        }
        _ => {
            if let Some((operator, expectation)) = english.split_once(" expects ") {
                return format!(
                    "{} очікує {}",
                    uk_operation_name(operator),
                    translate_expectation(expectation)
                );
            }
            if let Some(operator) = english.strip_suffix(": resource limit reached") {
                return format!("{}: досягнуто межі ресурсу", uk_operation_name(operator));
            }

            english
                .replace("numeric literal", "числовий літерал")
                .replace("resource limit", "межа ресурсу")
                .replace("invalid form", "некоректна форма")
                .replace("invalid", "некоректний")
                .replace("expected", "очікувалося")
                .replace("received", "отримано")
                .replace("unexpected", "неочікуваний")
        }
    }
}

pub fn present_system_message(message: &str, language: PresentationLanguage) -> String {
    match language {
        PresentationLanguage::Ukrainian => ukrainian_message(message),
        PresentationLanguage::Canonical
        | PresentationLanguage::English
        | PresentationLanguage::Sanskrit => message.to_string(),
    }
}

fn uk_error_line(error: &LanguageError) -> String {
    let message = ukrainian_message(&error.message);
    match error.kind {
        ErrorKind::Parse => format!("Синтаксична помилка: {message}"),
        ErrorKind::UnknownSymbol => message,
        ErrorKind::Arity => format!("Помилка кількості аргументів: {message}"),
        ErrorKind::Type => format!("Помилка типу: {message}"),
        ErrorKind::InvalidForm => format!("Некоректна форма: {message}"),
        ErrorKind::OutOfMemory => format!("Вичерпано ресурс пам'яті: {message}"),
        ErrorKind::NumericOverflow => format!("Перевищено числову межу: {message}"),
        ErrorKind::DivisionByZero if message == "Ділення на нуль" => message,
        ErrorKind::DivisionByZero => format!("Ділення на нуль: {message}"),
    }
}

pub fn render_error_for_presentation(
    error: &LanguageError,
    source: &str,
    language: PresentationLanguage,
) -> String {
    if language != PresentationLanguage::Ukrainian {
        return error.render(source);
    }

    let (line, column) = error.line_col(source);
    let line_text = source.lines().nth(line - 1).unwrap_or("");
    let span_chars = source[error.span.start.min(source.len())..error.span.end.min(source.len())]
        .chars()
        .count()
        .max(1);
    let gutter = format!("{line}");
    let indent = " ".repeat(gutter.len());
    let caret = " ".repeat(column.saturating_sub(1)) + &"^".repeat(span_chars);

    format!(
        "{message}\n{indent} --> рядок {line}, стовпець {column}\n{indent} |\n{gutter} | {line_text}\n{indent} | {caret}",
        message = uk_error_line(error),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{eval_program, parse, Session, Span};

    #[test]
    fn ukrainian_value_presentation_changes_only_the_human_view() {
        // Presentation owns only the human-facing rendering of a value.
        // Do not manufacture a boolean through a Lisp semantic operation such
        // as `atom`: #218 correctly returns a structural result there now.
        let truth = Value::Bool(true);
        assert_eq!(truth.to_string(), "t", "canonical value must not change");
        assert_eq!(
            render_value_for_presentation(&truth, PresentationLanguage::Ukrainian),
            "істина"
        );
        assert_eq!(
            render_value_for_presentation(&truth, PresentationLanguage::Canonical),
            "t"
        );
    }

    #[test]
    fn ukrainian_presentation_uses_decimal_comma_for_inexact_numbers() {
        let value = Value::Number(12.5, Exactness::Inexact);
        assert_eq!(
            render_value_for_presentation(&value, PresentationLanguage::Ukrainian),
            "12,5"
        );
        assert_eq!(value.to_string(), "12.5");
    }

    #[test]
    fn ukrainian_presentation_localizes_builtin_and_function_markers() {
        let mut session = Session::default();
        let builtin = eval_program("atom", &mut session)
            .expect("atom value")
            .value;
        assert_eq!(
            render_value_for_presentation(&builtin, PresentationLanguage::Ukrainian),
            "#<вбудована атом?>"
        );
        let closure = eval_program("(lambda (x) x)", &mut session)
            .expect("closure")
            .value;
        assert_eq!(
            render_value_for_presentation(&closure, PresentationLanguage::Ukrainian),
            "<функція>"
        );
    }

    #[test]
    fn ukrainian_error_presentation_has_no_mixed_line_label() {
        let source = "(car 5)";
        let mut session = Session::default();
        let error = eval_program(source, &mut session).expect_err("type error");
        let rendered =
            render_error_for_presentation(&error, source, PresentationLanguage::Ukrainian);
        assert!(rendered.contains("Помилка типу"), "{rendered}");
        assert!(
            rendered.contains("перше очікує непорожній список"),
            "{rendered}"
        );
        assert!(rendered.contains("рядок 1, стовпець 1"), "{rendered}");
        assert!(!rendered.contains("line/riadok/Zeile"), "{rendered}");
        assert!(!rendered.contains("car expects"), "{rendered}");
    }

    #[test]
    fn ukrainian_unknown_symbol_and_parser_errors_are_human_facing() {
        let unknown_source = "(cons невідоме ())";
        let mut session = Session::default();
        let unknown = eval_program(unknown_source, &mut session).expect_err("unknown symbol");
        let rendered = render_error_for_presentation(
            &unknown,
            unknown_source,
            PresentationLanguage::Ukrainian,
        );
        assert!(
            rendered.contains("Невідомий символ: невідоме"),
            "{rendered}"
        );

        let parse_source = ")";
        let parse_error = parse(parse_source).expect_err("parse error");
        let rendered = render_error_for_presentation(
            &parse_error,
            parse_source,
            PresentationLanguage::Ukrainian,
        );
        assert!(rendered.contains("Синтаксична помилка"), "{rendered}");
        assert!(
            rendered.contains("неочікувана закривна дужка"),
            "{rendered}"
        );
    }

    #[test]
    fn ukrainian_exact_arity_names_canonical_primitive_by_surface_name() {
        let source = "(атом?)";
        let mut session = Session::default();
        let error = eval_program(source, &mut session).expect_err("arity");
        let rendered =
            render_error_for_presentation(&error, source, PresentationLanguage::Ukrainian);
        assert!(
            rendered.contains("атом?: очікувалося 1; отримано 0"),
            "{rendered}"
        );
    }

    #[test]
    fn raw_user_strings_and_symbols_are_not_translated() {
        let string = Value::String("Hello".into());
        let symbol = Value::Symbol("London".into());
        assert_eq!(
            render_value_for_presentation(&string, PresentationLanguage::Ukrainian),
            "\"Hello\""
        );
        assert_eq!(
            render_value_for_presentation(&symbol, PresentationLanguage::Ukrainian),
            "London"
        );

        let error = LanguageError::new(ErrorKind::Type, "boom", Span { start: 0, end: 1 });
        let rendered = render_error_for_presentation(&error, "x", PresentationLanguage::Canonical);
        assert!(rendered.starts_with("boom"));
    }
}
