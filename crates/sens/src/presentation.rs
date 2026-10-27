//! Людське подання значень і діагностик для інтерактивних поверхонь.
//!
//! Канонічні `Value::Display` і `LanguageError::render` не змінюються: ними
//! користуються conformance-перевірки, машинні протоколи й точне відтворення
//! джерела. Цей модуль змінює лише те, що інтерактивна поверхня показує людині.

use crate::{
    semantic_registry, ErrorKind, Exactness, Expr, ExprKind, LanguageError, NumericBuffer, Value,
};
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PresentationLanguage {
    Canonical,
    English,
    Ukrainian,
    Sanskrit,
}

fn uk_operation_name(name: &str) -> String {
    match name {
        "atom" => "атом?".to_string(),
        "eq" => "тотожне?".to_string(),
        "cons" => "сполучити".to_string(),
        "car" => "перше".to_string(),
        "cdr" => "решта".to_string(),
        "PRIM_ATOM" => "атом?".to_string(),
        "PRIM_EQ" => "тотожне?".to_string(),
        "PRIM_CONS" => "сполучити".to_string(),
        "PRIM_CAR" => "перше".to_string(),
        "PRIM_CDR" => "решта".to_string(),
        // Виключно чинна точнодоменна проєкція: старі W8/SID8
        // та англомовний історичний реєстр не визначають українську назву.
        other => semantic_registry::domain_identity_for_surface(other)
            .and_then(|identity| {
                semantic_registry::surface_for_domain_identity(identity.into(), "ukr")
            })
            .map(str::to_string)
            .unwrap_or_else(|| other.to_string()),
    }
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

fn render_d7_identity(
    identity: crate::DomainIdentity,
    mode: crate::d7_keyboard::D7Mode,
) -> Option<String> {
    let crate::DomainIdentity::D7(word) = identity else {
        return None;
    };
    let code = word.word().packed_bits();
    if code < 32 || code == 127 {
        return Some(identity.to_string());
    }
    crate::d7_keyboard::project(code, mode)
        .ok()
        .map(|character| character.to_string())
}

fn render_d7_sanskrit_identity(identity: crate::DomainIdentity) -> Option<String> {
    let crate::DomainIdentity::D7(word) = identity else {
        return None;
    };
    let code = word.word().packed_bits();
    if code < 32 || code == 127 {
        return Some(identity.to_string());
    }
    let text = crate::Text7::from_cells(vec![code]).ok()?;
    crate::render_text7(&text, crate::Text7Layout::SaIast).ok()
}

fn render_uk(value: &Value) -> String {
    match value {
        Value::Builtin(builtin) => {
            format!("#<вбудована {}>", uk_operation_name(builtin.name))
        }
        Value::HostHandle { kind, .. } => match kind.as_ref() {
            "tcp-connection" => "<tcp-з'єднання>".to_string(),
            "tcp-listener" => "<tcp-слухач>".to_string(),
            _ => format!("#<host-об'єкт {kind}>"),
        },
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
        Value::BinaryNumber(number) => number.to_decimal_string(),
        Value::NumericComposition(number) => {
            let (negative, numerator, denominator) = number.as_parts();
            let sign = if negative { "-" } else { "" };
            match denominator {
                Some(d) => format!(
                    "{sign}{}/{}",
                    numerator.to_unsigned_decimal_string(),
                    d.to_unsigned_decimal_string()
                ),
                None => format!("-{}", numerator.to_unsigned_decimal_string()),
            }
        }
        Value::Sid(sid) => {
            // Історичний W8 має окремий простір від D8. Лише доведена
            // семантична відповідність D3 дозволяє показати його чинну
            // ратифіковану проєкцію. Інші W8 — лише сумісність.
            if let Some(domain) =
                semantic_registry::compatibility_d3_route_from_ratified_domains(*sid)
            {
                semantic_registry::surface_for_domain_identity(domain.into(), "ukr")
                    .map(str::to_string)
                    .unwrap_or_else(|| format!("#<домен D{}:{domain}>", domain.width()))
            } else {
                let ukrainian_surface =
                    semantic_registry::admitted_surfaces_with_namespace_for_semantic_id(*sid)
                        .into_iter()
                        .find_map(|(namespace, name)| {
                            (namespace == "укр").then_some(name.to_string())
                        });
                format!(
                    "#<сумісний W8:{} {}>",
                    sid,
                    ukrainian_surface.unwrap_or_else(|| format!(
                        "W8:{}",
                        semantic_registry::semantic_id_bits(*sid)
                    ))
                )
            }
        }
        Value::DomainIdentity(identity) => {
            render_d7_identity(*identity, crate::d7_keyboard::D7Mode::Uk)
                .or_else(|| {
                    semantic_registry::surface_for_domain_identity(*identity, "ukr")
                        .map(str::to_string)
                })
                .unwrap_or_else(|| format!("#<домен D{}:{identity}>", identity.width()))
        }
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
        Value::Pair(_) => render_pair_uk(value),
        Value::Closure(_) => "<функція>".to_string(),
        Value::Macro(_) => "<макрос>".to_string(),
        Value::Text7(text) => format!("#<текст7 {} комірок>", text.len()),
    }
}

fn render_pair_uk(value: &Value) -> String {
    let mut output = String::from("(");
    let mut current = value;
    let mut first = true;
    loop {
        match current {
            Value::Pair(node) => {
                if !first {
                    output.push(' ');
                }
                output.push_str(&render_uk(&node.head));
                current = &node.tail;
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

fn unchanged_non_domain_presentation(value: &Value) -> String {
    value.to_string()
}

fn render_sa(value: &Value) -> String {
    match value {
        Value::DomainIdentity(identity) => render_d7_sanskrit_identity(*identity)
            .or_else(|| {
                semantic_registry::surface_for_domain_identity(*identity, "sa").map(str::to_string)
            })
            .unwrap_or_else(|| value.to_string()),
        Value::Pair(_) => {
            let mut output = String::from("(");
            let mut current = value;
            let mut first = true;
            loop {
                match current {
                    Value::Pair(node) => {
                        if !first {
                            output.push(' ');
                        }
                        output.push_str(&render_sa(&node.head));
                        current = &node.tail;
                        first = false;
                    }
                    Value::Nil => {
                        output.push(')');
                        return output;
                    }
                    tail => {
                        output.push_str(" . ");
                        output.push_str(&render_sa(tail));
                        output.push(')');
                        return output;
                    }
                }
            }
        }
        Value::Vector(vector) => {
            let items = vector.borrow().iter().map(render_sa).collect::<Vec<_>>();
            format!("#({})", items.join(" "))
        }
        _ => unchanged_non_domain_presentation(value),
    }
}

pub fn render_value_for_presentation(value: &Value, language: PresentationLanguage) -> String {
    match language {
        PresentationLanguage::Ukrainian => render_uk(value),
        PresentationLanguage::Sanskrit => render_sa(value),
        PresentationLanguage::Canonical | PresentationLanguage::English => value.to_string(),
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

    // Exact-domain arity diagnostics are produced by the canonical domain
    // mechanism and contain the exact-width binary operator, not a legacy SID8.
    // Keep the width visible: 010 and 00000010 are different identities.
    if let Some((operator, rest)) = message.split_once(": expected ") {
        if (3..=9).contains(&operator.len())
            && operator.bytes().all(|bit| bit == b'0' || bit == b'1')
        {
            if let Some((expected, received)) = rest.split_once("; received ") {
                if let Some(expected) = expected.strip_suffix(" arguments") {
                    if expected.parse::<usize>().is_ok() && received.parse::<usize>().is_ok() {
                        return format!(
                            "D{}:{operator}: очікувалося {expected}; отримано {received}",
                            operator.len()
                        );
                    }
                }
            }
        }
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

    const NUMERIC_DOMAIN_ERROR: &str = "math requires explicit D12+ operands; D1-D10 bit words and unqualified numbers are not arithmetic values";
    if let Some(suffix) = english.strip_prefix(NUMERIC_DOMAIN_ERROR) {
        let suffix = suffix
            .replace("operand_position=", "позиція_операнда=")
            .replace("actual_kind=non-numeric", "фактичний_тип=нечисловий")
            .replace("physical_form_index=", "номер_фізичної_форми=")
            .replace("physical_word_start=", "початок_фізичного_слова=")
            .replace("physical_word_end=", "кінець_фізичного_слова=");
        return format!(
            "для математики потрібні явні операнди D12+; бітові слова D1–D10 і числа без домену не є математичними операндами{suffix}"
        );
    }

    match english {
        "unexpected closing parenthesis" => "неочікувана закривна дужка".to_string(),
        "unclosed list" => "незакритий список".to_string(),
        "unclosed string" => "незакритий текстовий рядок".to_string(),
        "unclosed numeric buffer" => "незакритий числовий буфер".to_string(),
        "unexpected end of input" | "unexpected eof" => "неочікуваний кінець вводу".to_string(),
        "division by zero" => "Ділення на нуль".to_string(),
        "numeric division requires admitted same-Dn values" => {
            "числове ділення потребує допущених значень одного числового домену".to_string()
        }
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
        ErrorKind::UnsatisfiedConditional => {
            format!("Умовний вираз не має відповідної гілки: {message}")
        }
        ErrorKind::MechanismUnavailable => format!("Механізм недоступний: {message}"),
        ErrorKind::OutOfMemory => format!("Вичерпано ресурс пам'яті: {message}"),
        ErrorKind::NumericOverflow => format!("Перевищено числову межу: {message}"),
        ErrorKind::DivisionByZero if message == "Ділення на нуль" => message,
        ErrorKind::DivisionByZero => format!("Ділення на нуль: {message}"),
    }
}

/// Render an evaluator diagnostic without assuming its span indexes source
/// text. Physical T5M execution spans are exact-word offsets, not UTF-8 bytes.
pub fn render_error_summary_for_presentation(
    error: &LanguageError,
    language: PresentationLanguage,
) -> String {
    if language == PresentationLanguage::Ukrainian {
        uk_error_line(error)
    } else {
        format!("{:?}: {}", error.kind, error.message)
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
    let clamp = |offset: usize| {
        let mut offset = offset.min(source.len());
        while !source.is_char_boundary(offset) {
            offset -= 1;
        }
        offset
    };
    let span_start = clamp(error.span.start);
    let span_end = clamp(error.span.end).max(span_start);
    let span_chars = source[span_start..span_end].chars().count().max(1);
    let gutter = format!("{line}");
    let indent = " ".repeat(gutter.len());
    let caret = " ".repeat(column.saturating_sub(1)) + &"^".repeat(span_chars);

    format!(
        "{message}\n{indent} --> рядок {line}, стовпець {column}\n{indent} |\n{gutter} | {line_text}\n{indent} | {caret}",
        message = uk_error_line(error),
    )
}


/// Один рядок подання вузла дерева розбору: текст і байтовий спан вузла.
///
/// Спільне подання для CLI-команди `:розбір` і хостів (TUI) — щоб дерево
/// розбору рендерилося ОДНІЄЮ реалізацією, а не дублем у кожному хості.
pub struct AstLine {
    pub text: String,
    pub span: (usize, usize),
}

/// Класифікація вузла дерева розбору — семантика SENS. Підписи (uk/de/en/…)
/// належать хосту: CLI рендерить канонічно, TUI — своєю UI-мовою.
pub enum AstNodeKind {
    List { items: usize, head: Option<String> },
    Pair,
    Call { identity: String, arguments: usize },
    DomainCall { identity: String, arguments: usize },
    Number,
    Rational,
    BinaryNumber,
    NumericBuffer,
    Sid { identity: String },
    DomainIdentity { identity: String },
    String,
    Symbol,
    Local { depth: String, index: String },
}

/// Один видимий рядок дерева: глибина, класифікація, спан і витяг джерела.
pub struct AstNode {
    pub depth: usize,
    pub kind: AstNodeKind,
    pub span: (usize, usize),
    pub excerpt: String,
}

fn classify(expression: &Expr, source: &str) -> AstNodeKind {
    match &expression.kind {
        ExprKind::List(items) => AstNodeKind::List {
            items: items.len(),
            head: items
                .first()
                .and_then(|first| source.get(first.span.start..first.span.end))
                .map(|raw| raw.trim().chars().take(48).collect()),
        },
        ExprKind::Pair(..) => AstNodeKind::Pair,
        ExprKind::Call(identity, arguments) => AstNodeKind::Call {
            identity: format!("{identity:?}"),
            arguments: arguments.len(),
        },
        ExprKind::DomainCall(identity, arguments) => AstNodeKind::DomainCall {
            identity: format!("{identity:?}"),
            arguments: arguments.len(),
        },
        ExprKind::Number(..) => AstNodeKind::Number,
        ExprKind::Rational(..) => AstNodeKind::Rational,
        ExprKind::BinaryNumber(..) => AstNodeKind::BinaryNumber,
        ExprKind::NumericBuffer(..) => AstNodeKind::NumericBuffer,
        ExprKind::Sid(identity) => AstNodeKind::Sid {
            identity: format!("{identity:?}"),
        },
        ExprKind::DomainIdentity(identity) => AstNodeKind::DomainIdentity {
            identity: format!("{identity:?}"),
        },
        ExprKind::String(..) => AstNodeKind::String,
        ExprKind::Symbol(..) => AstNodeKind::Symbol,
        ExprKind::Local { depth, index } => AstNodeKind::Local {
            depth: format!("{depth}"),
            index: format!("{index}"),
        },
    }
}

fn collect_nodes(source: &str, expression: &Expr, depth: usize, out: &mut Vec<AstNode>) {
    let span = (expression.span.start, expression.span.end);
    let excerpt = source.get(span.0..span.1).unwrap_or("").to_string();
    out.push(AstNode {
        depth,
        kind: classify(expression, source),
        span,
        excerpt,
    });
    match &expression.kind {
        ExprKind::List(items) => {
            for item in items.iter() {
                collect_nodes(source, item, depth + 1, out);
            }
        }
        ExprKind::Pair(head, tail) => {
            collect_nodes(source, head, depth + 1, out);
            collect_nodes(source, tail, depth + 1, out);
        }
        ExprKind::Call(_, arguments) | ExprKind::DomainCall(_, arguments) => {
            for argument in arguments.iter() {
                collect_nodes(source, argument, depth + 1, out);
            }
        }
        _ => {}
    }
}

/// Плоский обхід дерева розбору вже розібраних форм (та сама класифікація,
/// що й у CLI-команді `:розбір`). Читач обирає хост; обхід і класифікація спільні.
pub fn ast_nodes(source: &str, forms: &[Expr]) -> Vec<AstNode> {
    let mut out = Vec::new();
    for form in forms {
        collect_nodes(source, form, 1, &mut out);
    }
    out
}

fn ast_label(language: PresentationLanguage, node: &AstNode) -> String {
    let uk = matches!(language, PresentationLanguage::Ukrainian);
    match &node.kind {
        AstNodeKind::List { items, .. } => {
            if uk {
                format!("Список ({items} елементів)")
            } else {
                format!("List ({items} elements)")
            }
        }
        AstNodeKind::Pair => {
            if uk {
                "Пара".to_string()
            } else {
                "Pair".to_string()
            }
        }
        AstNodeKind::Call {
            identity,
            arguments,
        } => {
            if uk {
                format!("Виклик резидента {identity} ({arguments} аргументів)")
            } else {
                format!("Resident call {identity} ({arguments} arguments)")
            }
        }
        AstNodeKind::DomainCall {
            identity,
            arguments,
        } => {
            if uk {
                format!("Доменний виклик {identity} ({arguments} аргументів)")
            } else {
                format!("Domain call {identity} ({arguments} arguments)")
            }
        }
        AstNodeKind::Number => {
            if uk {
                format!("Число: {}", node.excerpt)
            } else {
                format!("Number: {}", node.excerpt)
            }
        }
        AstNodeKind::Rational => {
            if uk {
                format!("Дріб: {}", node.excerpt)
            } else {
                format!("Rational: {}", node.excerpt)
            }
        }
        AstNodeKind::BinaryNumber => {
            if uk {
                format!("Двійкове число: {}", node.excerpt)
            } else {
                format!("Binary number: {}", node.excerpt)
            }
        }
        AstNodeKind::NumericBuffer => {
            if uk {
                format!("Числовий буфер: {}", node.excerpt)
            } else {
                format!("Numeric buffer: {}", node.excerpt)
            }
        }
        AstNodeKind::Sid { identity } => {
            if uk {
                format!("Історична identity {identity}: {}", node.excerpt)
            } else {
                format!("Historical identity {identity}: {}", node.excerpt)
            }
        }
        AstNodeKind::DomainIdentity { identity } => {
            if uk {
                format!("Доменна identity {identity}: {}", node.excerpt)
            } else {
                format!("Domain identity {identity}: {}", node.excerpt)
            }
        }
        AstNodeKind::String => {
            if uk {
                format!("Рядок: {}", node.excerpt)
            } else {
                format!("String: {}", node.excerpt)
            }
        }
        AstNodeKind::Symbol => {
            if uk {
                format!("Символ: {}", node.excerpt)
            } else {
                format!("Symbol: {}", node.excerpt)
            }
        }
        AstNodeKind::Local { depth, index } => {
            if uk {
                format!("Локальний слот: depth={depth}, index={index}")
            } else {
                format!("Local slot: depth={depth}, index={index}")
            }
        }
    }
}

/// Дерево розбору для всієї форми-джерела (канонічний рендер CLI).
pub fn render_ast(
    source: &str,
    language: PresentationLanguage,
) -> Result<Vec<AstLine>, LanguageError> {
    let forms = crate::parse_mixed_exact_domain(source)?;
    Ok(ast_nodes(source, &forms)
        .into_iter()
        .map(|node| AstLine {
            text: format!("{}{}", "  ".repeat(node.depth), ast_label(language, &node)),
            span: node.span,
        })
        .collect())
}

/// Рендер одного вузла (для CLI, що друкує заголовок на кожну форму).
pub fn render_ast_node(
    source: &str,
    expression: &Expr,
    depth: usize,
    language: PresentationLanguage,
    lines: &mut Vec<AstLine>,
) {
    let mut nodes = Vec::new();
    collect_nodes(source, expression, depth, &mut nodes);
    lines.extend(nodes.into_iter().map(|node| AstLine {
        text: format!("{}{}", "  ".repeat(node.depth), ast_label(language, &node)),
        span: node.span,
    }));
}
