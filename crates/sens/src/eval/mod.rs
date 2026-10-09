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
mod d5_arithmetic;
mod d6_arithmetic;
pub(crate) mod builtins;
pub(crate) mod canon;
mod capabilities;
mod closures;
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

use crate::{parse, Environment, ErrorKind, Expr, ExprKind, LanguageError, Session, Sens8, Span, Value};
use crate::CoreDomainIdentity;
use crate::canonical_reader::text7_binding_key;

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
/// compatibility-голови ще можуть нести historical Sens8.
pub fn eval_lowered_expressions(
    expressions: &[Expr],
    session: &mut Session,
) -> Result<EvalResult, LanguageError> {
    let mut value = Value::Nil;
    for expression in expressions {
        value = evaluate(expression, &session.environment)?;
    }
    Ok(EvalResult {
        value,
        output: session.environment.output_snapshot(),
    })
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
    let expressions = parse(source)?;
    eval_parsed_expressions(&expressions, session)
}

pub(crate) enum EvalStep {
    Value(Value),
    TailCall {
        expression: Expr,
        environment: Environment,
    },
}

pub(crate) fn invoke_value(
    function: &Value,
    arguments: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    match function {
        Value::DomainIdentity(identity) => match identity.core_operation() {
            Some(core_identity) => {
                canon::invoke_domain_identity(core_identity, arguments, environment, span)
            }
            None => Err(LanguageError::new(
                ErrorKind::Type,
                format!(
                    "domain identity is not callable under its ratified law: D{} {}",
                    identity.width(),
                    identity
                ),
                span,
            )),
        }
        Value::Sid(sid) => canon::invoke_semantic_ref(*sid, arguments, environment, span),
        Value::Builtin(builtin) => (builtin.func)(arguments, environment, span),
        Value::Closure(closure) => closures::apply_values(closure.clone(), arguments, span),
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "expression is not callable · vyraz ne mozhna vyklykaty · Ausdruck ist nicht aufrufbar",
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
            if let Some(sid) = canon::routed_sid_for_surface(symbol) {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    format!(
                        "function SID is syntax-only in this position · function SID тут лише синтаксис · Funktions-SID ist hier nur Syntax: {sid}"
                    ),
                    expression.span,
                ));
            }
            if necessary_forms::identity_for_symbol(symbol).is_some() {
                return Err(LanguageError::new(
                    ErrorKind::UnknownSymbol,
                    format!("evaluator-owned necessary form is syntax-only: {symbol}"),
                    expression.span,
                ));
            }
            if let Some(value) = environment.get(symbol) {
                return Ok(EvalStep::Value(value));
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
    if let Some(identity) = binary_head_domain_identity(&items[0]) {
        return dispatch_domain_call(identity, &items[1..], environment, span);
    }
    // A D2/W7 frame becomes a Text7 binding only in executable call-head
    // position. Ordinary D2 lists, quoted data and dotted data remain governed
    // solely by the canonical D2 reader.
    if let Some(key) = text7_binding_key(&items[0]) {
        let function = environment.get(&key).ok_or_else(|| {
            LanguageError::new(
                ErrorKind::UnknownSymbol,
                format!("unknown Text7 binding: {key}"),
                items[0].span,
            )
        })?;
        return closures::apply(function, &items[1..], environment, span);
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

    let mut values = Vec::with_capacity(arguments.len());
    for argument in arguments {
        values.push(evaluate(argument, environment)?);
    }
    canon::invoke_domain_identity(identity, &values, environment, span).map(EvalStep::Value)
}

/// Спільний compatibility-диспетчер виклику. Для `ExprKind::Call` ім'я голови відсутнє:
/// функція — лише 1 байт `head_sid`.
fn dispatch_call(
    head_name: Option<&str>,
    head_sid: Option<Sens8>,
    head_expr: Option<&Expr>,
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<EvalStep, LanguageError> {
    let routed_head_sid = head_sid
        .filter(|sid| canon::route_kind_for_sid(*sid).is_some())
        .or_else(|| head_name.and_then(canon::routed_sid_for_surface));
    let necessary_head = head_name
        .and_then(necessary_forms::identity_for_symbol)
        .or_else(|| head_sid.and_then(necessary_forms::identity_for_semantic_id));

    if routed_head_sid == Some(crate::sens!(00000001)) {
        special_forms::exact_sens_arity(crate::sens!(00000001), arguments, 1, span)?;
        let value = special_forms::quoted(&arguments[0])?;
        return Ok(EvalStep::Value(value));
    }
    if necessary_head == Some(necessary_forms::NecessaryFormIdentity::Lambda) {
        return closures::create_lambda(arguments, environment, span).map(EvalStep::Value);
    }
    if necessary_head == Some(necessary_forms::NecessaryFormIdentity::Define) {
        return special_forms::evaluate_definition(arguments, environment, span).map(EvalStep::Value);
    }
    if routed_head_sid == Some(crate::sens!(00000111)) {
        return special_forms::evaluate_cond(arguments, environment, span);
    }

    if let Some(name) = head_name {
        if let Some(result) =
            capabilities::dispatch_capability(name, arguments, environment, span)
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
        Value::DomainIdentity(identity) => {
            let Some(core_identity) = identity.core_operation() else {
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
            let mut values = Vec::with_capacity(arguments.len());
            for argument in arguments {
                values.push(evaluate(argument, environment)?);
            }
            canon::invoke_domain_identity(core_identity, &values, environment, span)
                .map(EvalStep::Value)
        }
        Value::Sid(sid) => {
            // #1455: макрос, прив'язаний до коду, розгортається до обчислення аргументів.
            if !canon::has_primitive(*sid) {
                match &environment.code_slot(*sid) {
                    Some(Value::Macro(closure)) => {
                        return closures::apply_macro(closure.clone(), arguments, environment, span);
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
            canon::invoke_semantic_ref(*sid, &values, environment, span)
                .map(EvalStep::Value)
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

fn binary_head_sid(expression: &Expr) -> Option<Sens8> {
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
