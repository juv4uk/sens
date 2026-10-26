//! Evaluator entry points and the special-form dispatcher.
//! Tochky vkhodu evaluator i dyspetcher spetsialnykh form.
//! Einstiegspunkte des Evaluators und der Sonderformen-Dispatcher.
//!
//! The evaluator is split by concern: this module owns the trampoline loop and
//! dispatch table, `arithmetic` owns exact/inexact number handling, `special_forms`
//! owns the McCarthy primitives plus compatibility `def`/`cond`,
//! `necessary_forms` owns the immutable DEFINE/LAMBDA identities, and `closures`
//! owns lambda construction and function/macro application.
pub(crate) use special_forms::digest::sha256 as digest_sha256;

mod arithmetic;
pub(crate) mod builtins;
pub(crate) mod canon;
mod capabilities;
mod closures;
mod d5_arithmetic;
mod d6_arithmetic;
pub(crate) mod lower;
mod macro_substrate;
pub(crate) mod necessary_forms;
mod profile_mechanisms_generated;
pub(crate) mod selector_law;
mod special_forms;

pub use capabilities::{
    capability_installed, installed_capabilities, register_capability,
    register_evaluated_capability, register_sens_capability, unregister_capability,
    unregister_sens_capability,
};
pub(crate) use macro_substrate::install as install_macro_substrate;
pub use special_forms::{exact_arity, json::parse_json};

/// Явна runtime-реалізація допущеного D10-слова монотонного годинника.
/// Завантажувач прив'язує її до одного точного D10 identity; сама резидентність
/// D10 не робить викличним жодне інше слово.
pub(crate) fn d10_monotonic_nanoseconds_builtin() -> Value {
    Value::host_function(std::rc::Rc::new(|args, environment, span| {
        builtins::monotonic_nanoseconds(args, environment, span)
    }))
}

/// Першокласне значення вже допущеного D8:11110100 механізму запису в текст.
pub(crate) fn d8_write_to_string_builtin() -> Value {
    Value::host_function(std::rc::Rc::new(|args, environment, span| {
        special_forms::write_to_string_values(args, environment, span)
    }))
}

/// Д8:11101101 — уже існуючий точний механізм STRING->SYMBOL.
/// Це лише першокласний адаптер для Lisp-виклику за українською назвою:
/// правило значення й перевірка типу залишаються в тому самому SENS-примітиві,
/// що обробляє точний D8 код; нової Rust-семантики тут немає.
pub(crate) fn d8_string_to_symbol_builtin() -> Value {
    Value::host_function(std::rc::Rc::new(|args, _environment, span| {
        special_forms::string_to_symbol_values(args, span)
    }))
}

/// Existing scalar-to-string representation bridge used by the pinned UTF-8
/// Lisp layer. UTF-8 policy remains in Lisp; this only materializes a scalar.
pub(crate) fn runtime_codepoint_to_string(
    args: &[Value],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    special_forms::codepoint_to_string_values(args, span)
}

use crate::canonical_reader::text7_binding_key;
use crate::{
    parse, CoreDomainIdentity, Environment, ErrorKind, Expr, ExprKind, LanguageError, Session,
    Span, Value,
};

/// Reads exactly one SENS datum without evaluating it.
///
/// Transport envelopes are untrusted data: do not turn them into a
/// dynamically constructed QUOTE program. Reuse the language's existing
/// D3 QUOTE data conversion, including exact-domain and D7 preservation,
/// but never enter EVAL or require a mutable Session.
pub fn read_single_quoted_datum(source: &str) -> Result<Value, LanguageError> {
    let expressions = parse(source)?;
    if expressions.len() != 1 {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "request envelope must contain exactly one top-level expression",
            Span { start: 0, end: source.len() },
        ));
    }
    special_forms::quoted(&expressions[0])
}

#[cfg(feature = "benchmark-ast-visits")]
std::thread_local! {
    static EVAL_AST_VISITS: std::cell::Cell<Option<u64>> = const {
        std::cell::Cell::new(None)
    };
}

#[cfg(feature = "benchmark-ast-visits")]
struct EvalVisitScope {
    parent: Option<u64>,
}

#[cfg(feature = "benchmark-ast-visits")]
impl EvalVisitScope {
    fn start() -> Self {
        let parent = EVAL_AST_VISITS.with(|visits| visits.replace(Some(0)));
        Self { parent }
    }

    fn finish(self) -> u64 {
        EVAL_AST_VISITS.with(std::cell::Cell::get).unwrap_or(0)
    }
}

#[cfg(feature = "benchmark-ast-visits")]
impl Drop for EvalVisitScope {
    fn drop(&mut self) {
        EVAL_AST_VISITS.with(|visits| {
            let measured = visits.replace(self.parent).unwrap_or(0);
            if let Some(parent) = self.parent {
                visits.set(Some(parent.saturating_add(measured)));
            }
        });
    }
}

#[cfg(feature = "benchmark-ast-visits")]
fn record_eval_ast_visit() {
    EVAL_AST_VISITS.with(|visits| {
        if let Some(count) = visits.get() {
            visits.set(Some(count.saturating_add(1)));
        }
    });
}

#[derive(Clone, Debug, PartialEq)]
pub struct EvalResult {
    pub value: Value,
    pub output: Vec<String>,
}

pub fn eval_parsed_expressions(
    expressions: &[Expr],
    session: &mut Session,
) -> Result<EvalResult, LanguageError> {
    eval_lowered_expressions(&lower::lower_program(expressions), session)
}

/// Виконати програму, вже зведену `lower_program`.
/// Мігрувані D3/D4 голови несуть exact domain identity; неперенесені
/// compatibility-голови ще можуть нести historical CoreDomainIdentity.
/// Прив'язати безадресну внутрішню помилку до виконуваної верхньої форми.
/// Точні діапазони помилок зберігаються; семантика виконання не змінюється.
fn top_level_error_span(mut error: LanguageError, expression: &Expr) -> LanguageError {
    if error.span == Span::default() {
        error.span = expression.span;
    }
    error
}

pub fn eval_lowered_expressions(
    expressions: &[Expr],
    session: &mut Session,
) -> Result<EvalResult, LanguageError> {
    let mut value = Value::Nil;
    for expression in expressions {
        value = evaluate(expression, &session.environment)
            .map_err(|error| top_level_error_span(error, expression))?;
    }
    Ok(EvalResult {
        value,
        output: session.environment.output_snapshot(),
    })
}

/// Execute expressions while counting AST nodes actually dispatched by the
/// evaluator. The optional metric is compiled only for the whole-program
/// optimization benchmark, so ordinary SENS builds carry no counter overhead.
#[cfg(feature = "benchmark-ast-visits")]
pub(crate) fn eval_expressions_with_visit_count(
    expressions: &[Expr],
    session: &mut Session,
) -> Result<(EvalResult, u64), LanguageError> {
    let scope = EvalVisitScope::start();
    let result = eval_lowered_expressions(expressions, session);
    let visits = scope.finish();
    result.map(|result| (result, visits))
}

pub fn eval_parsed_expressions_incremental(
    expressions: &[Expr],
    session: &mut Session,
) -> Result<EvalResult, LanguageError> {
    session.environment.output_take_new();
    let mut value = Value::Nil;
    for expression in lower::lower_program(expressions).iter() {
        value = evaluate(expression, &session.environment)?;
    }
    Ok(EvalResult {
        value,
        output: session.environment.output_take_new(),
    })
}

pub fn eval_program(source: &str, session: &mut Session) -> Result<EvalResult, LanguageError> {
    let parsed = parse(source)?;
    let expressions =
        crate::source_projection::project_ukr_decimal_integer_literals(&parsed, source)?;
    eval_parsed_expressions(&expressions, session)
}

/// Fail closed before the first side effect of an exact-domain program.
///
/// Compatibility-only surface names are not admitted Dn call heads; otherwise
/// a raw List could reach the evaluator's historical symbol dispatcher.
/// Traversal is iterative and skips D3 quoted data and D4 binder positions.
pub(crate) fn validate_exact_executable_heads(expressions: &[Expr]) -> Result<(), LanguageError> {
    let mut pending: Vec<&Expr> = expressions.iter().collect();
    while let Some(expr) = pending.pop() {
        match &expr.kind {
            ExprKind::Sid(_) | ExprKind::Call(_, _) => {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    "exact-domain program cannot contain historical W8 AST operations",
                    expr.span,
                ));
            }
            ExprKind::List(items) => {
                if let Some(Expr {
                    kind: ExprKind::Symbol(head),
                    span,
                }) = items.first()
                {
                    if crate::semantic_registry::admitted_semantic_id_for_surface(head).is_some()
                        && crate::semantic_registry::domain_identity_for_surface(head).is_none()
                    {
                        return Err(LanguageError::new(
                            ErrorKind::InvalidForm,
                            format!(
                                "historical-only call surface is not a ratified Dn head: {head}"
                            ),
                            *span,
                        ));
                    }
                }
                pending.extend(items.iter());
            }
            ExprKind::DomainCall(identity, args) if is_d3(*identity, 0b001) => {
                // D3 QUOTE stores literal syntax, including symbols which are
                // intentionally not executable heads.
                let _ = args;
            }
            ExprKind::DomainCall(identity, args)
                if necessary_forms::identity_for_domain_identity(*identity).is_some() =>
            {
                // First D4 LAMBDA/DEFINE argument is a binder, not a call.
                pending.extend(args.iter().skip(1));
            }
            ExprKind::DomainCall(_, args) => pending.extend(args.iter()),
            ExprKind::Pair(head, tail) => {
                pending.push(head);
                pending.push(tail);
            }
            _ => {}
        }
    }
    Ok(())
}

/// Виконати точне джерело D1–D9 без історичного восьмибітного читача.
///
/// Ширина слова зберігається у DomainIdentity. Резидентність не надає права
/// виклику; перевірка механізму відбувається в доменному evaluator-і.
/// Літерали чисел D24+ не допускаються цим читачем до окремого HANDOFF.
pub fn eval_exact_domain_program(
    source: &str,
    session: &mut Session,
) -> Result<EvalResult, LanguageError> {
    let expressions = crate::parser::parse_exact_domain_source(source)?;
    // Never pass canonical Dn source through historical W8 head lowering,
    // or permit a legacy-only textual head to reach the compatibility evaluator.
    let lowered = lower::lower_exact_domain_program(&expressions);
    validate_exact_executable_heads(&lowered)?;
    eval_lowered_expressions(&lowered, session)
}

pub(crate) enum EvalStep {
    Value(Value),
    TailCall {
        expression: Expr,
        environment: Environment,
    },
}

/// Допоміжний виклик значення лише для предметних тестів SENS.
/// Виробничий обчислювач використовує справжній dispatch із хвостовими викликами.
#[cfg(test)]
pub(crate) fn invoke_value(
    function: &Value,
    arguments: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    match function {
        Value::DomainIdentity(identity) => {
            // D8–D10 селектори — одна сім'я точного закону. D9 не має
            // втрачати свій закон при приведенні до CoreDomainIdentity.
            if let Some(result) = selector_law::invoke(*identity, arguments, span) {
                return result;
            }
            if let Some(core_identity) = identity.core_operation() {
                return canon::invoke_domain_identity(core_identity, arguments, environment, span);
            }
            // A bounded D9 mechanism cut remains outside CoreDomainIdentity.
            if canon::has_d9_mechanism(*identity) {
                return canon::invoke_d9_mechanism(*identity, arguments, environment, span)
                    .expect("exact D9 string-mechanism route was checked above");
            }
            match environment.domain_code_slot(*identity).as_ref() {
                Some(Value::Builtin(builtin)) => (builtin.func)(arguments, environment, span),
                Some(Value::Closure(closure)) => {
                    closures::apply_values(closure.clone(), arguments, span)
                }
                _ => Err(LanguageError::new(
                    ErrorKind::Type,
                    format!(
                        "domain identity is not callable under its ratified law: D{} {}",
                        identity.width(), identity
                    ),
                    span,
                )),
            }
        }
        Value::Sid(sid) => canon::invoke_semantic_ref(*sid, arguments, environment, span),
        Value::Builtin(builtin) => (builtin.func)(arguments, environment, span),
        Value::Closure(closure) => closures::apply_values(closure.clone(), arguments, span),
        _ => Err(LanguageError::new(
            ErrorKind::Type,
                format!(
                    "expression is not callable · vyraz ne mozhna vyklykaty · Ausdruck ist nicht aufrufbar (носій: {})",
                match function {
                    Value::Nil => "порожня структура",
                    Value::Bool(_) => "історичний булевий носій",
                    Value::Number(_, _) | Value::Rational(_) => "число",
                    Value::BinaryNumber(_) => "двійкове число",
                    Value::Symbol(_) => "символ",
                    Value::Pair(_) => "пара",
                    Value::Macro(_) => "макрос",
                    Value::String(_) | Value::Text7(_) => "текст",
                    _ => "інший невикликний носій",
                },
            ),
            span,
        )),
    }
}

pub fn evaluate(expression: &Expr, environment: &Environment) -> Result<Value, LanguageError> {
    let (mut owned_expression, mut owned_environment) =
        match evaluate_step(expression, environment)? {
            EvalStep::Value(value) => return Ok(value),
            EvalStep::TailCall {
                expression,
                environment,
            } => (expression, environment),
        };

    loop {
        match evaluate_step(&owned_expression, &owned_environment)? {
            EvalStep::Value(value) => return Ok(value),
            EvalStep::TailCall {
                expression: next,
                environment: next_environment,
            } => {
                owned_expression = next;
                owned_environment = next_environment;
            }
        }
    }
}

pub(crate) fn evaluate_step(
    expression: &Expr,
    environment: &Environment,
) -> Result<EvalStep, LanguageError> {
    if environment.consume_eval_step().is_err() {
        return Err(LanguageError::new(
            ErrorKind::OutOfMemory,
            "network SENS evaluator step budget exhausted",
            expression.span,
        ));
    }
    #[cfg(feature = "benchmark-ast-visits")]
    record_eval_ast_visit();

    match &expression.kind {
        ExprKind::Number(number, exactness) => Ok(EvalStep::Value(Value::Number(*number, *exactness))),
        ExprKind::Rational(rational) => Ok(EvalStep::Value(Value::Rational(rational.clone()))),
        ExprKind::BinaryNumber(number) => Ok(EvalStep::Value(Value::BinaryNumber(number.clone()))),
        ExprKind::Sid(sid) => Ok(EvalStep::Value(Value::Sid(*sid))),
        ExprKind::DomainIdentity(identity) => {
            Ok(EvalStep::Value(Value::DomainIdentity(*identity)))
        }
        ExprKind::NumericBuffer(buffer) => Ok(EvalStep::Value(Value::NumericBuffer(buffer.clone()))),
        ExprKind::String(value) => Ok(EvalStep::Value(Value::String(value.clone()))),
        ExprKind::Symbol(symbol) => {
            // Поверхня «укр» є лише проєкцією точного доменного слова.
            // Функцію можна зберігати, передавати та викликати як значення.
            // Особливі форми залишаються синтаксисом: їм потрібні сирі AST.
            let current = crate::semantic_registry::exact_uk_callable_for_source_head(symbol);
            if let Some(identity) = current {
                if let Some(core) = identity.core_operation() {
                    if is_d3(core, 0b001)
                        || is_d3(core, 0b110)
                        || is_d5(core, 0b00100)
                        || is_d5(core, 0b00110)
                        || is_d5(core, 0b00111)
                        || necessary_forms::identity_for_domain_identity(core).is_some()
                    {
                        return Err(LanguageError::new(
                            ErrorKind::InvalidForm,
                            format!("exact domain form is syntax-only in this position: D{} {}", identity.width(), identity),
                            expression.span,
                        ));
                    }
                    if matches!(core, CoreDomainIdentity::D3(_)) {
                        // Незмінна Д3 функція має першокласну тотожність
                        // навіть без DEFINE і без історичного SID8.
                        return Ok(EvalStep::Value(Value::DomainIdentity(identity)));
                    }
                }
            }
            if current.is_none() {
                if let Some(sid) = canon::routed_sid_for_surface(symbol) {
                    return Err(LanguageError::new(
                        ErrorKind::InvalidForm,
                        format!(
                            "function SID is syntax-only in this position · function SID тут лише синтаксис · Funktions-SID ist nur Syntax: {sid}"
                        ),
                        expression.span,
                    ));
                }
            }
            if necessary_forms::identity_for_symbol(symbol).is_some() {
                return Err(LanguageError::new(
                    ErrorKind::UnknownSymbol,
                    format!("evaluator-owned necessary form is syntax-only: {symbol}"),
                    expression.span,
                ));
            }
            if let Some(value) = environment.get(symbol) {
                // Лексичний параметр залишається значенням, але незмінна
                // Д3 identity вище не може бути затінена.
                return Ok(EvalStep::Value(value));
            }
            if let Some(identity) = current {
                return Ok(EvalStep::Value(Value::DomainIdentity(identity)));
            }
            // Клавіатурний D7 токен — вже створений Lisp binding, а не
            // нова функція, псевдо-SID8 чи host-реєстр. Відновлюємо лише
            // ІСНУЮЧЕ зв'язування того самого українського написання.
            // Невідома назва без такого зв'язування й далі дає UnknownSymbol.
            if let Ok(text7) = crate::encode_text7(symbol, crate::Text7Layout::Uk) {
                if let Some(value) = environment.get(&text7.to_canonical_wire_token()) {
                    return Ok(EvalStep::Value(value));
                }
            }
            // Тільки незв'язані Д1 поверхні читаємо за ратифікованою
            // таблицею, як у точному reader. Це не host truthiness,
            // не арифметика 0/1 і не другий реєстр кодів.
            if let Some(identity) = crate::semantic_registry::d1_value_for_uk_surface(symbol) {
                return Ok(EvalStep::Value(Value::DomainIdentity(identity)));
            }
            Err(LanguageError::new(
                ErrorKind::UnknownSymbol,
                format!("unknown symbol · nevidomyi symvol · unbekanntes Symbol: {symbol}"),
                expression.span,
            ))
        }
        // Empty structure is a structural value, not any function SID.
        ExprKind::List(items) if items.is_empty() => Ok(EvalStep::Value(Value::Nil)),
        ExprKind::List(items) => {
            // A whole D2/W7 frame is a Text7 identifier only when the
            // executable context already has the corresponding binding.
            // This is the value-reference case for local/global variables;
            // quoted/data lists never reach here as executable references.
            if let Some(key) = text7_binding_key(expression) {
                if let Some(value) = environment.get(&key) {
                    return Ok(EvalStep::Value(value));
                }
                // Legacy source-bound names (including bootstrap D24 roots)
                // may already live under their Ukrainian surface spelling.
                // In an *executable reference position* only, use the
                // owner-ratified reversible D7 keyboard projection to find
                // that existing binding. Never invent a value or a callable
                // identity from a glyph list. D3 QUOTE bypasses evaluation
                // and continues to preserve the literal W7/D2 structure.
                if let Ok(text7) = crate::Text7::from_canonical_wire_token(&key) {
                    if let Ok(name) = crate::render_text7(&text7, crate::Text7Layout::Uk) {
                        if let Some(value) = environment.get(&name) {
                            return Ok(EvalStep::Value(value));
                        }
                    }
                }
            }
            evaluate_list(items, environment, expression.span)
        },
        ExprKind::Call(sid, arguments) => {
            dispatch_call(None, Some(*sid), None, arguments, environment, expression.span)
        }
        ExprKind::DomainCall(identity, arguments) => {
            dispatch_domain_call(*identity, arguments, environment, expression.span)
        }
        // Виконання залежить лише від числових координат (#1697): слот або є,
        // або названа помилка — пошуку за іменем більше немає.
        ExprKind::Local { depth, index } => environment
            .get_local(*depth, *index)
            .map(EvalStep::Value)
            .ok_or_else(|| {
                LanguageError::new(
                    ErrorKind::UnknownSymbol,
                    format!(
                        "lexical slot {depth}.{index} is not bound in this frame · leksychnyi slot {depth}.{index} ne zv'iazanyi u tsomu freimi · lexikalischer Slot {depth}.{index} ist in diesem Frame nicht gebunden"
                    ),
                    expression.span,
                )
            }),
        ExprKind::Pair(_, _) => Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "a dotted pair is not executable code · dotted-para ne ye vykonuvanym kodom · ein Dotted Pair ist kein ausführbarer Code",
            expression.span,
        )),
    }
}

fn evaluate_list(
    items: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<EvalStep, LanguageError> {
    // Фізичний односимвольний D7 токен може бути ВЖЕ зв'язаним Text7 ім'ям.
    // Лише голова виклику та лише точне наявне зв'язування дають маршрут
    // до джерельного символу; повторно виконувати D7-список тут не можна.
    if matches!(
        items[0].kind,
        ExprKind::DomainIdentity(crate::DomainIdentity::D7(_))
    ) {
        let framed = Expr {
            kind: ExprKind::List(std::rc::Rc::from(vec![items[0].clone()].into_boxed_slice())),
            span: items[0].span,
        };
        if let Some(key) = text7_binding_key(&framed) {
            if environment.get(&key).is_some() {
                let head = Expr {
                    kind: ExprKind::Symbol(key),
                    span: items[0].span,
                };
                return dispatch_call(None, None, Some(&head), &items[1..], environment, span);
            }
            let source_name = crate::Text7::from_canonical_wire_token(&key)
                .ok()
                .and_then(|text| crate::render_text7(&text, crate::Text7Layout::Uk).ok());
            if let Some(name) = source_name.filter(|name| environment.get(name).is_some()) {
                let head = Expr {
                    kind: ExprKind::Symbol(name.into()),
                    span: items[0].span,
                };
                return dispatch_call(None, None, Some(&head), &items[1..], environment, span);
            }
        }
    }
    if let Some(identity) = binary_head_domain_identity(&items[0]) {
        return dispatch_domain_call(identity, &items[1..], environment, span);
    }
    // A D2/W7 frame is a lookup route only while it is the call head.
    // Dispatch the already-resolved symbol, not the frame as a second program:
    // evaluating the frame again would reinterpret its first D7 cell as code.
    if let Some(key) = text7_binding_key(&items[0]) {
        if environment.get(&key).is_none() {
            let text = crate::Text7::from_canonical_wire_token(&key).ok();
            let surface = text.as_ref().and_then(|text| {
                crate::text7_projection::render_text7(text, crate::Text7Layout::Uk).ok()
            });
            let exact_d6 = surface
                .as_deref()
                .and_then(crate::semantic_registry::d6_binding_identity_for_definition)
                .filter(|identity| environment.domain_code_slot(*identity).is_some());
            if let Some(crate::DomainIdentity::D6(word)) = exact_d6 {
                return dispatch_domain_call(
                    CoreDomainIdentity::D6(word),
                    &items[1..],
                    environment,
                    span,
                );
            }
            if let Some(name) = surface.filter(|name| environment.get(name).is_some()) {
                let head = Expr {
                    kind: ExprKind::Symbol(name.into()),
                    span: items[0].span,
                };
                return dispatch_call(None, None, Some(&head), &items[1..], environment, span);
            }
            return Err(LanguageError::new(
                ErrorKind::UnknownSymbol,
                format!("unknown Text7 binding: {key}"),
                items[0].span,
            ));
        }
        let head = Expr {
            kind: ExprKind::Symbol(key),
            span: items[0].span,
        };
        return dispatch_call(None, None, Some(&head), &items[1..], environment, span);
    }
    dispatch_call(
        items[0].kind.as_symbol(),
        binary_head_sid(&items[0]),
        Some(&items[0]),
        &items[1..],
        environment,
        span,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn evaluator_budget_counts_real_dispatches_and_fails_named() {
        let expr = crate::parse("(quote ())").expect("quote is syntactically valid");
        let environment = Environment::root().with_eval_step_budget(1);
        let first = evaluate(&expr[0], &environment).expect("first dispatch admitted");
        assert_eq!(first, Value::Nil);
        let second = evaluate(&expr[0], &environment)
            .expect_err("exhausted budget must not be treated as SENS success");
        assert_eq!(second.kind, ErrorKind::OutOfMemory);
        assert!(second.message.contains("evaluator step budget exhausted"));
    }

    #[test]
    fn physical_d7_call_head_uses_existing_ukrainian_source_binding_only() {
        let name = "перевірка";
        let text7 = crate::encode_text7(name, crate::Text7Layout::Uk)
            .expect("ratified Ukrainian D7 glyphs");
        let key = text7.to_canonical_wire_token();
        let glyphs = text7
            .cells()
            .iter()
            .map(|cell| format!("{cell:07b}"))
            .collect::<Vec<_>>()
            .join(" ");
        let physical_source = format!("10 10 {glyphs} 01 1 01");
        let expressions = crate::parse_canonical_binary(&physical_source)
            .expect("physical D2/D7 call head");
        let mut bound_session = Session::bare();
        bound_session.environment.define(
            name,
            Value::host_function(std::rc::Rc::new(|arguments, _, _| {
                Ok(arguments.first().cloned().unwrap_or(Value::Nil))
            })),
        );
        assert!(
            bound_session.environment.get(&key).is_none(),
            "physical alias must not be fabricated for an existing source binding"
        );
        let result = eval_parsed_expressions(&expressions, &mut bound_session)
            .expect("exact D7 call must reach the existing source closure");
        assert_eq!(result.value.as_predicate_bit(), Some(true));

        let mut unbound_session = Session::bare();
        let error = eval_parsed_expressions(&expressions, &mut unbound_session)
            .expect_err("unbound glyph call must remain noncallable");
        assert_eq!(error.kind, ErrorKind::UnknownSymbol);
    }

    #[test]
    fn physical_single_glyph_d7_call_uses_existing_ukrainian_binding_only() {
        // D7 1111000 — один гліф української клавіатури, не функція D7.
        // Позитив перевіряє тільки механізм пошуку наявного зв'язування.
        let name = "х";
        let text7 = crate::encode_text7(name, crate::Text7Layout::Uk)
            .expect("ratified D7 Ukrainian glyph");
        assert_eq!(text7.cells().len(), 1);
        let wire = text7.to_canonical_wire_token();
        let glyph = format!("{:07b}", text7.cells()[0]);
        let source = format!("10 10 {glyph} 01 1 01");
        let expressions = crate::parse_canonical_binary(&source)
            .expect("exact physical single-glyph call");
        let mut session = Session::bare();
        session.environment.define(
            name,
            Value::host_function(std::rc::Rc::new(|arguments, _, _| {
                Ok(arguments.first().cloned().unwrap_or(Value::Nil))
            })),
        );
        assert!(
            session.environment.get(&wire).is_none(),
            "the test must not invent a wire-token alias"
        );
        let result = eval_parsed_expressions(&expressions, &mut session)
            .expect("one glyph calls the existing Ukrainian source binding");
        assert_eq!(result.value.as_predicate_bit(), Some(true));

        // Невідомий односимвольний ключ НЕ стає новою викличною координатою.
        let mut unbound = Session::bare();
        assert!(
            eval_parsed_expressions(&expressions, &mut unbound).is_err(),
            "an unbound D7 glyph is not an executable domain identity"
        );
    }

    #[test]
    fn text7_call_head_dispatches_an_already_bound_builtin() {
        let mut session = Session::bare();
        let name = "функція";
        let text7 = crate::encode_text7(name, crate::Text7Layout::Uk)
            .expect("supported Ukrainian Text7 name");
        let key = text7.to_canonical_wire_token();
        session.environment.define(
            key,
            Value::host_function(std::rc::Rc::new(|arguments, _, _| {
                if arguments.is_empty() {
                    Ok(Value::Nil)
                } else {
                    Ok(arguments[0].clone())
                }
            })),
        );

        let glyphs = text7
            .cells()
            .iter()
            .map(|cell| format!("{cell:07b}"))
            .collect::<Vec<_>>()
            .join(" ");
        let source = format!("10 10 {glyphs} 01 1 01");
        let expressions = crate::parse_canonical_binary(&source).expect("binary source parses");
        let result = eval_parsed_expressions(&expressions, &mut session)
            .expect("Text7-bound host function is callable");

        assert_eq!(result.value.as_predicate_bit(), Some(true));
    }

    #[test]
    fn exact_d8_read_surface_runs_the_admitted_reader_mechanism() {
        let mut session = Session::bare();
        let result = eval_program(r#"(прочитати "(alpha beta)")"#, &mut session)
            .expect("the exact Ukrainian D8 READ projection is executable");
        let Value::Pair(pair) = &result.value else {
            panic!("READ of a two-item list must return a structural pair");
        };
        // Rust перевіряє лише механічну форму результату READ;
        // рівність вмісту й семантику символів засвідчує Lisp/SENS.
        assert!(matches!(&pair.head, Value::Symbol(_)));
        let Value::Pair(rest) = &pair.tail else {
            panic!("READ must preserve the second list cell");
        };
        assert!(matches!(&rest.head, Value::Symbol(_)));
        assert!(matches!(&rest.tail, Value::Nil));
    }
}

fn is_d3(identity: CoreDomainIdentity, bits: u8) -> bool {
    matches!(
        identity,
        CoreDomainIdentity::D3(word) if word.word().packed_bits() == bits
    )
}

fn is_d5(identity: CoreDomainIdentity, bits: u8) -> bool {
    matches!(
        identity,
        CoreDomainIdentity::D5(word) if word.word().packed_bits() == bits
    )
}

fn evaluate_d5_label(
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<EvalStep, LanguageError> {
    special_forms::exact_arity("D5:00100", arguments, 2, span)?;

    // LABEL accepts a name in the canonical D2/D7 binding context. Keep
    // the same Text7 wire key used by variable lookup and LAMBDA parameter
    // binding; do not stringify D7 bits as human names or introduce a SID map.
    let name = if let Some(name) = text7_binding_key(&arguments[0]) {
        canon::ensure_bindable(&name, arguments[0].span)?;
        name
    } else {
        match &arguments[0].kind {
            ExprKind::Symbol(name) => {
                canon::ensure_bindable(name, arguments[0].span)?;
                name.clone()
            }
            _ => {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "D5:00100 LABEL name must be a literal symbol or D2-framed D7 Text7 binder",
                    arguments[0].span,
                ));
            }
        }
    };

    // LABEL is local self-reference, not global DEFINE.  The closure captures
    // this child frame; replacing the temporary cell after construction makes
    // recursive calls observe the closure itself through the same Rc-backed
    // environment without adding a second recursion mechanism.
    let recursive_environment = environment.child();
    recursive_environment.define(name.clone(), Value::Nil);
    let value = evaluate(&arguments[1], &recursive_environment)?;
    if !matches!(value, Value::Closure(_)) {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "D5:00100 LABEL value must evaluate to a function closure",
            arguments[1].span,
        ));
    }
    recursive_environment.define(name, value.clone());
    Ok(EvalStep::Value(value))
}

fn evaluate_d5_set_family(
    identity: CoreDomainIdentity,
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<EvalStep, LanguageError> {
    let is_set = is_d5(identity, 0b00110);
    let is_setq = is_d5(identity, 0b00111);
    debug_assert!(is_set || is_setq);

    let label = if is_set { "D5:00110" } else { "D5:00111" };
    special_forms::exact_arity(label, arguments, 2, span)?;

    let target = if is_set {
        match evaluate(&arguments[0], environment)? {
            Value::Symbol(ref name) => name.clone(),
            _ => {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    format!("{label} target must evaluate to a symbol"),
                    arguments[0].span,
                ));
            }
        }
    } else {
        match &arguments[0].kind {
            ExprKind::Symbol(name) => name.clone(),
            _ => {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    format!("{label} target must be a literal symbol"),
                    arguments[0].span,
                ));
            }
        }
    };
    let value = evaluate(&arguments[1], environment)?;
    if !environment.update_nearest_existing(&target, value.clone()) {
        return Err(LanguageError::new(
            ErrorKind::UnknownSymbol,
            format!("{label} target is not an existing binding: {target}"),
            arguments[0].span,
        ));
    }

    Ok(EvalStep::Value(value))
}

fn dispatch_domain_call(
    identity: CoreDomainIdentity,
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<EvalStep, LanguageError> {
    if is_d3(identity, 0b001) {
        special_forms::exact_arity("D3:001", arguments, 1, span)?;
        return special_forms::quoted(&arguments[0]).map(EvalStep::Value);
    }

    match necessary_forms::identity_for_domain_identity(identity) {
        Some(necessary_forms::NecessaryFormIdentity::Lambda) => {
            return closures::create_lambda(arguments, environment, span).map(EvalStep::Value);
        }
        Some(necessary_forms::NecessaryFormIdentity::Define) => {
            return special_forms::evaluate_definition(arguments, environment, span)
                .map(EvalStep::Value);
        }
        None => {}
    }

    if is_d3(identity, 0b110) {
        return special_forms::evaluate_domain_cond(arguments, environment, span);
    }

    if is_d5(identity, 0b00100) {
        return evaluate_d5_label(arguments, environment, span);
    }

    if is_d5(identity, 0b00110) || is_d5(identity, 0b00111) {
        return evaluate_d5_set_family(identity, arguments, environment, span);
    }

    let domain_identity: crate::DomainIdentity = identity.into();
    if canon::has_d9_mechanism(domain_identity) {
        let mut values = Vec::with_capacity(arguments.len());
        for argument in arguments {
            values.push(evaluate(argument, environment)?);
        }
        return canon::invoke_d9_mechanism(domain_identity, &values, environment, span)
            .expect("exact D9 string-mechanism route was checked above")
            .map(EvalStep::Value);
    }

    // Admitted D5 Core mechanisms are identity-owned. Do not let a
    // language-owned closure bound to the same resident (for compatibility
    // callers) shadow its ratified arithmetic law. All other D5 definitions
    // retain the ordinary language-defined fast path below.
    if !d5_arithmetic::has_mechanism(identity) && !selector_law::is_selector(identity.into()) {
        if let Some(bound) = environment.domain_code_slot(identity) {
            match &bound {
                Value::Macro(closure) => {
                    return closures::apply_macro(closure.clone(), arguments, environment, span);
                }
                Value::Closure(_) if !canon::has_language_result_boundary(identity) => {
                    return closures::apply(bound.clone(), arguments, environment, span);
                }
                // #3060: exact D5 MEMBER keeps the same Lisp closure/search law,
                // but its canonical result must cross the D1 PredicateBit boundary.
                // Fall through to evaluated-value invocation so canon can normalize
                // only the final result carrier; every other closure keeps the
                // ordinary tail-call fast path above.
                Value::Closure(_) => {}
                _ => {}
            }
        }
    }

    let mut values = Vec::with_capacity(arguments.len());
    for argument in arguments {
        values.push(evaluate(argument, environment)?);
    }
    canon::invoke_domain_identity(identity, &values, environment, span).map(EvalStep::Value)
}

/// Спільний compatibility-диспетчер виклику. Для `ExprKind::Call` ім'я голови відсутнє:
/// функція — лише 1 байт `head_sid`.
/// Єдина семантика першокласного доменного коду для прямої голови
/// та контекстного Д7-зв'язування. Резидент без механізму не викликається.
pub(super) fn apply_exact_domain_value(
    identity: &crate::DomainIdentity,
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<EvalStep, LanguageError> {
    // Точні селектори Д3–Д10 мають однаковий закон і як голова,
    // і як передане значення; особливо Д9 не губиться в Core-маршруті.
    if selector_law::is_selector(*identity) {
        let mut values = Vec::with_capacity(arguments.len());
        for argument in arguments {
            values.push(evaluate(argument, environment)?);
        }
        return selector_law::invoke(*identity, &values, span)
            .expect("exact selector family was checked above")
            .map(EvalStep::Value);
    }
    if let Some(core_identity) = identity.core_operation() {
        let mut values = Vec::with_capacity(arguments.len());
        for argument in arguments {
            values.push(evaluate(argument, environment)?);
        }
        return canon::invoke_domain_identity(core_identity, &values, environment, span)
            .map(EvalStep::Value);
    }
    // Лише D9-резиденти з реалізованим механізмом мають прямий виклик.
    // Решта проходять звичайний шлях пошуку доменного слота.
    if canon::has_d9_mechanism(*identity) {
        let mut values = Vec::with_capacity(arguments.len());
        for argument in arguments {
            values.push(evaluate(argument, environment)?);
        }
        return canon::invoke_d9_mechanism(*identity, &values, environment, span)
            .expect("exact D9 string-mechanism route was checked above")
            .map(EvalStep::Value);
    }
    let Some(bound) = environment.domain_code_slot(*identity) else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            format!(
                "domain identity is not callable under its ratified law: D{} {}",
                identity.width(),
                identity
            ),
            span,
        ));
    };
    match &bound {
        Value::Macro(closure) => {
            closures::apply_macro(closure.clone(), arguments, environment, span)
        }
        Value::Closure(_) => closures::apply(bound.clone(), arguments, environment, span),
        Value::Builtin(builtin) => {
            let mut values = Vec::with_capacity(arguments.len());
            for argument in arguments {
                values.push(evaluate(argument, environment)?);
            }
            (builtin.func)(&values, environment, span).map(EvalStep::Value)
        }
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            format!(
                "exact domain mechanism slot is not callable: D{} {}",
                identity.width(),
                identity
            ),
            span,
        )),
    }
}

fn dispatch_call(
    head_name: Option<&str>,
    head_sid: Option<CoreDomainIdentity>,
    head_expr: Option<&Expr>,
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<EvalStep, LanguageError> {
    let routed_head_sid = head_sid
        .filter(|sid| canon::route_kind_for_sid(*sid).is_some())
        .or_else(|| head_name.and_then(canon::routed_sid_for_surface));
    // Ratified D4 source surfaces take the exact-domain evaluator path,
    // including historical spelling aliases already resolved by the owner
    // registry. Only a genuinely historical W8 head retains the legacy route.
    // Never infer a current D8 identity from an eight-bit payload.
    if let Some(identity) = head_name.and_then(necessary_forms::domain_identity_for_symbol) {
        return dispatch_domain_call(identity, arguments, environment, span);
    }
    let necessary_head = head_sid.and_then(necessary_forms::identity_for_semantic_id);

    // Історичні W8 QUOTE/COND не утворюють незалежного закону виконання:
    // лише засвідчена українська/санскритська проєкція реєстру може
    // направити сумісний виклик до справжнього D3. Однаковий payload
    // інших W8 і D8 не допускає такого переходу.
    let compatible_d3 = routed_head_sid
        .and_then(crate::semantic_registry::compatibility_d3_route_from_ratified_domains);
    if let Some(identity) = compatible_d3 {
        if is_d3(identity, 0b001) || is_d3(identity, 0b110) {
            return dispatch_domain_call(identity, arguments, environment, span);
        }
    }
    if necessary_head == Some(necessary_forms::NecessaryFormIdentity::Lambda) {
        return closures::create_lambda(arguments, environment, span).map(EvalStep::Value);
    }
    if necessary_head == Some(necessary_forms::NecessaryFormIdentity::Define) {
        return special_forms::evaluate_definition(arguments, environment, span)
            .map(EvalStep::Value);
    }

    // One mathematically admitted selector family needs no per-resident DEFINE for
    // each word. Resolve only a *unique owner-ratified Ukrainian head*, then
    // apply the exact CAR/CDR composition; no English/SID8/JSON shortcut.
    if let Some(identity) = head_name
        .and_then(crate::semantic_registry::exact_uk_callable_for_source_head)
        .filter(|id| {
            matches!(
                id,
                crate::DomainIdentity::D6(_)
                    | crate::DomainIdentity::D8(_)
                    | crate::DomainIdentity::D9(_)
                    | crate::DomainIdentity::D10(_)
            ) && selector_law::is_selector(*id)
        })
    {
        let mut values = Vec::with_capacity(arguments.len());
        for argument in arguments {
            values.push(evaluate(argument, environment)?);
        }
        return selector_law::invoke(identity, &values, span)
            .expect("unique ratified D6-D10 selector head")
            .map(EvalStep::Value);
    }

    // The ordinary Lisp reader retains a Ukrainian call head as a Symbol.
    // Admit only the small exact D8 spelling list shared with the T5M reader,
    // and only when canon.rs has an implemented mechanism at that exact D8
    // coordinate. D8 residency or an English/legacy spelling is not enough.
    if let Some(name) = head_name {
        if crate::semantic_registry::admitted_d8_uk_callable_bits(name).is_some() {
            if let Some(crate::DomainIdentity::D8(word)) =
                crate::semantic_registry::exact_uk_callable_for_source_head(name)
            {
                let identity = CoreDomainIdentity::D8(word);
                if canon::domain_primitive_kind(identity).is_some() {
                    return dispatch_domain_call(identity, arguments, environment, span);
                }
            }
        }
    }

    // D6-визначення беруть точний рядок згенерованої таблиці «ім'я → домен».
    // Текстовий зв'язувач джерела не стає identity сам собою: викликаємо її,
    // лише якщо точний D6-слот уже містить механізм.
    // D6 library definitions use an exact generated name-to-domain row, but
    // their Text7 source binder is intentionally projection-neutral inside
    // the runtime. Route a Ukrainian source head only when that exact D6 slot
    // already contains a concrete mechanism; residency alone is insufficient.
    if let Some(identity) = head_name
        .and_then(crate::semantic_registry::d6_binding_identity_for_definition)
        .filter(|identity| environment.domain_code_slot(*identity).is_some())
    {
        return apply_exact_domain_value(
            &identity,
            arguments,
            environment,
            span,
        );
    }

    if let Some(name) = head_name {
        if let Some(result) = capabilities::dispatch_capability(name, arguments, environment, span)
        {
            return result;
        }
    }
    let function = match head_sid {
        Some(sid) => Value::Sid(sid),
        None => evaluate(
            head_expr.expect("a call without a SID head keeps its head expression"),
            environment,
        )?,
    };
    match &function {
        Value::DomainIdentity(identity) => apply_exact_domain_value(identity, arguments, environment, span),
        Value::Sid(sid) => {
            // #1455: макрос, прив'язаний до коду, розгортається до обчислення аргументів.
            if !canon::has_primitive(*sid) {
                match &environment.code_slot(*sid) {
                    Some(Value::Macro(closure)) => {
                        return closures::apply_macro(
                            closure.clone(),
                            arguments,
                            environment,
                            span,
                        );
                    }
                    // A language-defined function reached through its code
                    // takes the same path as a call by name: arguments and
                    // body run through `closures::apply`, whose tail call
                    // keeps deep recursion (meta-eval) off the Rust stack.
                    Some(closure @ Value::Closure(_)) => {
                        return closures::apply(closure.clone(), arguments, environment, span);
                    }
                    _ => {}
                }
            }
            let mut values = Vec::with_capacity(arguments.len());
            for argument in arguments {
                values.push(evaluate(argument, environment)?);
            }
            canon::invoke_semantic_ref(*sid, &values, environment, span).map(EvalStep::Value)
        }
        Value::Builtin(builtin) => {
            let mut values = Vec::with_capacity(arguments.len());
            for argument in arguments {
                values.push(evaluate(argument, environment)?);
            }
            (builtin.func)(&values, environment, span).map(EvalStep::Value)
        }
        Value::Macro(closure) => {
            closures::apply_macro(closure.clone(), arguments, environment, span)
        }
        _ => closures::apply(function, arguments, environment, span),
    }
}

/// A fixed-width binary token names a semantic identity only as a list head.
/// The same SID remains `Value::Sid` when it occurs as data or under
/// QUOTE, so a source file can carry bit data without making it executable.
fn binary_head_domain_identity(expression: &Expr) -> Option<CoreDomainIdentity> {
    let ExprKind::DomainIdentity(identity) = expression.kind else {
        return None;
    };
    identity.core_operation()
}

fn binary_head_sid(expression: &Expr) -> Option<CoreDomainIdentity> {
    let ExprKind::Sid(sid) = expression.kind else {
        return None;
    };
    Some(sid)
}

trait ExprKindExt {
    fn as_symbol(&self) -> Option<&str>;
}

impl ExprKindExt for ExprKind {
    fn as_symbol(&self) -> Option<&str> {
        match self {
            ExprKind::Symbol(symbol) => Some(symbol),
            _ => None,
        }
    }
}

#[cfg(test)]
mod top_level_error_span_tests {
    use super::*;

    #[test]
    fn preserves_precise_span_and_recovers_missing_top_level_location() {
        let source = "; Початковий коментар\n(1)";
        let forms = parse(source).expect("джерельна форма");
        let form = &forms[0];
        assert_eq!(form.span.start, source.find("(1)").unwrap());

        let missing = LanguageError::new(ErrorKind::Type, "не можна викликати", Span::default());
        let repaired = top_level_error_span(missing, form);
        assert_eq!(repaired.span, form.span);
        assert_eq!(repaired.line_col(source), (2, 1));

        let precise = Span {
            start: form.span.start + 1,
            end: form.span.start + 2,
        };
        let already_located = LanguageError::new(ErrorKind::Type, "точний діапазон", precise);
        assert_eq!(top_level_error_span(already_located, form).span, precise);
    }
}

#[cfg(test)]
mod exact_domain_surface_value_position_tests {
    use super::*;

    #[test]
    fn ukrainian_d3_code_is_a_first_class_function_without_sid8() {
        let mut session = Session::default();
        let bare = eval_program("атом?", &mut session)
            .expect("Д3 функцію можна прочитати як першокласне значення");
        assert!(matches!(
            bare.value,
            Value::DomainIdentity(identity)
                if identity.width() == 3 && identity.packed_bits() == 0b010
        ));
        let result = eval_program(
            "(визначити обрана-дія-для-свідка атом?) ((функція (дія-для-свідка) (дія-для-свідка (як-є ()))) обрана-дія-для-свідка)",
            &mut session,
        )
        .expect("точний код Д3 передано в замикання і викликано");
        assert_eq!(result.value.as_predicate_bit(), Some(true));
    }

    #[test]
    fn d8_d9_d10_selector_codes_are_first_class_values_inside_closures() {
        let expected = eval_program("(як-є атом?)", &mut Session::default())
            .expect("цитований атом у чинному SENS")
            .value;
        for (domain, depth) in [
            (
                crate::DomainIdentity::D8(crate::CoreD8::from_word(
                    crate::Bit8::new(0b10000000).unwrap(),
                )),
                6usize,
            ),
            (
                crate::DomainIdentity::D9(crate::CoreD9::from_word(
                    crate::Bit9::new(0b100000000).unwrap(),
                )),
                7,
            ),
            (
                crate::DomainIdentity::D10(crate::DomainD10::new(0b1000000000).unwrap()),
                8,
            ),
        ] {
            let mut session = Session::default();
            session.environment.define("код-для-передачі", Value::DomainIdentity(domain));
            let mut input = "(як-є атом?)".to_owned();
            for _ in 0..depth {
                input = format!("(сполучити {input} (як-є ()))");
            }
            let program = format!(
                "((функція (операція) (операція {input})) код-для-передачі)"
            );
            let result = eval_program(&program, &mut session)
                .expect("ратифікований код передається як значення, а потім виконується");
            assert_eq!(result.value, expected, "Д{}: точна identity має бути першокласною", domain.width());
        }
    }

    #[test]
    fn unadmitted_d10_code_is_a_value_but_not_a_fabricated_function() {
        let mut session = Session::default();
        let code = crate::DomainIdentity::D10(
            crate::DomainD10::new(0b0000000010).unwrap(),
        );
        session.environment.define("невикличний-код", Value::DomainIdentity(code));
        assert_eq!(
            eval_program("невикличний-код", &mut session)
                .expect("резидент є першокласним значенням")
                .value,
            Value::DomainIdentity(code),
        );
        let error = eval_program("(невикличний-код)", &mut session)
            .expect_err("невизначений механізм не створюється з ширини");
        assert_eq!(error.kind, ErrorKind::Type);
        assert!(error.message.contains("domain identity"), "{}", error.message);
    }
}

#[cfg(test)]
mod exact_domain_program_tests {
    use super::*;

    #[test]
    fn exact_d3_quote_keeps_the_current_d8_data_identity() {
        let mut session = Session::bare();
        let result = eval_exact_domain_program("(001 11110111)", &mut session)
            .expect("ратифікована D3 цитата виконується без історичного SID");
        assert!(matches!(
            result.value,
            Value::DomainIdentity(identity)
                if identity.width() == 8 && identity.packed_bits() == 0b11110111
        ));
    }

    #[test]
    fn exact_execution_rejects_unadmitted_english_surface_before_any_side_effect() {
        let mut session = Session::bare();
        let error = eval_exact_domain_program("(def x (001 1))", &mut session)
            .expect_err("unadmitted English `def` is not the Ukrainian D4 DEFINE surface");
        assert_eq!(error.kind, ErrorKind::UnknownSymbol);
        assert!(
            error.message.contains("unknown symbol"),
            "{}",
            error.message
        );
        assert_eq!(&"(def x (001 1))"[error.span.start..error.span.end], "def");
        assert!(session.environment.get("x").is_none());
    }

    #[test]
    fn exact_quote_preserves_historical_looking_symbols_as_inert_data() {
        let mut session = Session::bare();
        let result = eval_exact_domain_program("(001 (def x 11110111))", &mut session)
            .expect("D3 quoted syntax must not be mistaken for a call");
        assert!(matches!(result.value, Value::Pair(_)));
    }

    #[test]
    fn noncallable_current_d8_cannot_inherit_historical_quote_dispatch() {
        let mut session = Session::bare();
        let error = eval_exact_domain_program("(00000001 (001 1))", &mut session)
            .expect_err("D8:00000001 is not historical W8 QUOTE");
        assert!(matches!(
            error.kind,
            ErrorKind::Type | ErrorKind::MechanismUnavailable
        ));
    }

    #[test]
    fn exact_source_rejects_implicit_decimal_literals() {
        let mut session = Session::bare();
        let error = eval_exact_domain_program("(001 42)", &mut session)
            .expect_err("числа потребують окремого допуску D24+");
        assert_eq!(error.kind, ErrorKind::Parse);
    }
}

#[cfg(test)]
mod domain_eval_cutover_necessary_forms {
    use super::*;

    fn arguments(source: &str) -> (Vec<Expr>, Span) {
        let parsed = parse(source).expect("допущена історична проєкція D4");
        let expression = &parsed[0];
        let ExprKind::List(parts) = &expression.kind else {
            panic!("очікуємо викличну форму");
        };
        (parts[1..].to_vec(), expression.span)
    }

    #[test]
    fn ukrainian_lambda_source_uses_exact_d4_mechanism() {
        let (args, span) = arguments("(функція (x) x)");
        let env = Environment::root();
        let via_source = dispatch_call(Some("функція"), None, None, &args, &env, span)
            .expect("джерельна проєкція D4:0010");
        let identity =
            necessary_forms::domain_identity_for_symbol("функція").expect("ратифікована функція");
        assert!(matches!(via_source, EvalStep::Value(Value::Closure(_))));
        assert!(matches!(
            dispatch_domain_call(identity, &args, &env, span).expect("точна D4:0010"),
            EvalStep::Value(Value::Closure(_))
        ));
        assert_eq!(identity.width(), 4);
    }

    #[test]
    fn ukrainian_define_source_uses_exact_d4_mechanism() {
        let (args, span) = arguments("(визначити перевірка ())");
        let source_env = Environment::root();
        let exact_env = Environment::root();
        let identity =
            necessary_forms::domain_identity_for_symbol("визначити").expect("ратифікована D4:0011");
        dispatch_call(Some("визначити"), None, None, &args, &source_env, span)
            .expect("визначення через доменну таблицю");
        dispatch_domain_call(identity, &args, &exact_env, span).expect("пряме визначення D4:0011");
        assert!(matches!(source_env.get("перевірка"), Some(Value::Nil)));
        assert!(matches!(exact_env.get("перевірка"), Some(Value::Nil)));
    }

    #[test]
    fn only_necessary_d4_heads_gain_this_route() {
        assert!(necessary_forms::domain_identity_for_symbol("функція").is_some());
        assert!(necessary_forms::domain_identity_for_symbol("визначити").is_some());
        // D3 ATOM, a foreign symbol, and an old bare byte must not inherit
        // the D4 necessary-form mechanism by payload or spelling.
        assert!(necessary_forms::domain_identity_for_symbol("атом?").is_none());
        assert!(necessary_forms::domain_identity_for_symbol("чужий-виклик").is_none());
        assert!(necessary_forms::domain_identity_for_symbol("00001000").is_none());
    }

    #[test]
    fn exact_d9_string_mechanism_takes_precedence_over_its_surface_wrapper_slot() {
        let domain_identity =
            crate::semantic_registry::d9_binding_identity_for_definition("рядок-порожній?")
                .expect("ратифікований D9 резидент");
        let identity = domain_identity
            .core_operation()
            .expect("допущений D9 механізм");
        let (wrapper_args, wrapper_span) = arguments("(функція (текст) \"не викликати\")");
        let environment = Environment::root();
        let wrapper = closures::create_lambda(&wrapper_args, &environment, wrapper_span)
            .expect("тестова поверхнева обгортка");
        assert!(environment.bind_domain_code_slot_once(domain_identity, wrapper));

        let (args, span) = arguments("(рядок-порожній? \"\")");
        let result = dispatch_domain_call(identity, &args, &environment, span)
            .expect("D9 exact mechanism bypasses the surface wrapper slot");
        assert!(matches!(result, EvalStep::Value(value) if value.as_predicate_bit().is_some()));
    }
}

#[cfg(test)]
mod domain_eval_cutover_d3_compatibility {
    use super::*;

    #[test]
    fn only_ratified_d3_projection_bridges_historical_quote_and_cond() {
        for (legacy, bits) in [
            (
                crate::CoreDomainIdentity::D3(crate::Bija3::from_word(
                    crate::Bit3::new(0b001).expect("quote"),
                )),
                0b001u8,
            ),
            (
                crate::CoreDomainIdentity::D3(crate::Bija3::from_word(
                    crate::Bit3::new(0b110).expect("cond"),
                )),
                0b110u8,
            ),
        ] {
            let identity =
                crate::semantic_registry::compatibility_d3_route_from_ratified_domains(legacy)
                    .expect("історичний W8 має доказову проєкцію в D3");
            assert!(is_d3(identity, bits));
            assert_eq!(identity.width(), 3);
        }
        for unrelated in [
            crate::CoreDomainIdentity::D8(crate::CoreD8::from_word(
                crate::Bit8::new(0b10101000).expect("legacy W8 payload"),
            )),
            crate::CoreDomainIdentity::D6(crate::CoreD6::from_word(
                crate::Bit6::new(0b110111).expect("unrelated D6 value"),
            )),
        ] {
            assert!(
                crate::semantic_registry::compatibility_d3_route_from_ratified_domains(unrelated)
                    .is_none(),
                "невідома W8-комірка не може стати чинним D3/D8"
            );
        }
    }

    #[test]
    fn ukrainian_quote_runs_identically_to_exact_d3_quote() {
        let mut projected = Session::bare();
        let mut exact = Session::bare();
        let projected_value = eval_program("(як-є (a b))", &mut projected)
            .expect("українська проєкція має пройти чинний D3-маршрут");
        let new_value = eval_exact_domain_program("(001 (a b))", &mut exact)
            .expect("чинне точнодоменне цитування");
        assert_eq!(projected_value.value, new_value.value);
    }

    #[test]
    fn legacy_cond_rejects_three_part_clause_by_current_d3_contract() {
        let mut session = Session::bare();
        let err =
            eval_exact_domain_program("(110 ((010 (001 ())) (001 yes) (001 no)))", &mut session)
                .expect_err("двопольний D3 COND забороняє тричастинну клаузу");
        assert_eq!(err.kind, ErrorKind::InvalidForm);
        assert!(err.message.contains("D3:110"), "{}", err.message);
    }
}


#[cfg(test)]
mod physical_d7_existing_binding_regressions {
    use super::*;

    // Mechanism-only proof: a physical D2 frame of exact W7 words refers
    // to an already-installed Ukrainian binding, never grants the glyphs
    // a callable identity or a new semantic law.
    // Одногліфове ім'я фізично є D7-словом, а не D2-списком.
    // Викличність дає тільки вже наявне українське DEFINE-зв'язування.
    #[test]
    fn physical_single_glyph_ukrainian_call_needs_existing_binding() {
        let spelling = "а";
        let text = crate::encode_text7(spelling, crate::Text7Layout::Uk)
            .expect("ратифікована українська D7 клавіатура");
        assert_eq!(text.len(), 1, "справжнє однословне D7 ім'я");
        let glyph = text.cells()[0];
        let source = format!("10 {glyph:07b} 1 01");
        let forms = crate::parse_canonical_binary(&source)
            .expect("фізична форма D2(D7, D1)");

        let mut bound = Session::bare();
        bound.environment.define(
            spelling,
            Value::host_function(std::rc::Rc::new(|args, _, _| {
                Ok(args.first().cloned().unwrap_or(Value::Nil))
            })),
        );
        assert!(
            bound.environment.get(&text.to_canonical_wire_token()).is_none(),
            "допуск не створює прихованого D7 binding"
        );
        let result = eval_parsed_expressions(&forms, &mut bound)
            .expect("наявне Lisp-зв'язування викликається точною D7 головою");
        assert_eq!(result.value.as_predicate_bit(), Some(true));

        let mut unknown = Session::bare();
        let error = eval_parsed_expressions(&forms, &mut unknown)
            .expect_err("невідомий D7 атом не отримує викличності");
        assert!(
            error.message.contains("domain identity is not callable"),
            "невідоме ім'я не перетворюється на функцію: {}",
            error.message
        );
    }

    #[test]
    fn physical_d7_frame_reads_existing_ukrainian_binding_without_host_oracle() {
        let spelling = "число-нуль";
        let text = crate::encode_text7(spelling, crate::Text7Layout::Uk)
            .expect("ratified D7 keyboard admits this source spelling");
        let glyphs = text
            .cells()
            .iter()
            .map(|&cell| Expr {
                kind: ExprKind::DomainIdentity(crate::DomainIdentity::from_coordinate(
                    crate::domain_ladder::DomainCoordinate::new(7, u16::from(cell))
                        .expect("all exact W7 cells are admitted"),
                )),
                span: Span::default(),
            })
            .collect::<Vec<_>>();
        let reference = Expr {
            kind: ExprKind::List(glyphs.into()),
            span: Span::default(),
        };

        // The exact physical key is deliberately absent: this models a
        // bootstrap binding installed by its source spelling.
        let environment = Environment::root();
        environment.define(spelling, Value::Nil);
        assert!(environment
            .get(&text.to_canonical_wire_token())
            .is_none());

        let value = evaluate(&reference, &environment)
            .expect("a previously defined source name is readable from D7");
        assert_eq!(value, Value::Nil, "existing binding keeps its exact value");

        let unknown = Environment::root();
        assert!(
            evaluate(&reference, &unknown).is_err(),
            "unbound glyph frames must not become executable functions"
        );
    }
}
