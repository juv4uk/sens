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
pub(crate) mod lower;
mod macro_substrate;
pub(crate) mod necessary_forms;
mod profile_mechanisms_generated;
mod selector_law;
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
        Value::DomainIdentity(identity) => {
            canon::invoke_domain_identity(*identity, arguments, environment, span)
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
        ExprKind::List(items) => evaluate_list(items, environment, expression.span),
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

    if is_d3(identity, 0b011) {
        return special_forms::evaluate_cond(arguments, environment, span);
    }

    if let Some(bound) = environment.domain_code_slot(identity) {
        match &bound {
            Value::Macro(closure) => {
                return closures::apply_macro(closure.clone(), arguments, environment, span);
            }
            Value::Closure(_) => {
                return closures::apply(bound.clone(), arguments, environment, span);
            }
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
            let mut values = Vec::with_capacity(arguments.len());
            for argument in arguments {
                values.push(evaluate(argument, environment)?);
            }
            canon::invoke_domain_identity(*identity, &values, environment, span)
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
    Some(identity)
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

#[cfg(test)]
mod single_pass_eval_tests {
    use super::*;

    #[test]
    fn single_pass_eval_parsed_expressions_evaluates_preparsed_ast() {
        let source = "(def x (/ 1 3)) (cons x (quote ()))";
        let forms = parse(source).expect("parsing should succeed");
        let mut session = Session::default();
        let result = eval_parsed_expressions(&forms, &mut session)
            .expect("eval_parsed_expressions should succeed");
        assert_eq!(result.value.to_string(), "(1/3)");
    }

    #[test]
    fn canonical_define_introduces_a_binding() {
        let source = "(define x 41) (+ x 1)";
        let mut session = Session::default();
        let result = eval_program(source, &mut session).expect("define should bind x");
        assert_eq!(result.value.to_string(), "42");
    }

    #[test]
    fn binary_sids_dispatch_canon_and_necessary_forms_in_list_head() {
        let source = r#"
            (00001001 make-pair
              (00001000 (left right)
                (00000100 left (00000100 right ()))))
            (00000101 (make-pair 1 2))
        "#;
        let mut session = Session::default();
        let result = eval_program(source, &mut session)
            .expect("8-bit SID list heads should execute their registered meaning");
        assert_eq!(result.value.to_string(), "1");
    }

    #[test]
    fn binary_sids_keep_quote_and_cond_as_syntax() {
        let source = r#"
            (00000111
              ((00000010 (00000001 atom)) (1) (00000001 selected))
              (t t (00000001 missed)))
        "#;
        let mut session = Session::default();
        let result = eval_program(source, &mut session)
            .expect("SID QUOTE and COND should retain their syntax-only behavior");
        assert_eq!(result.value.to_string(), "selected");
    }

    #[test]
    fn canonical_define_and_lambda_support_recursion() {
        let source = r#"
            (define count-down
              (lambda (n)
                (cond
                  ((eq? n 0) (quote done))
                  (t (count-down (- n 1))))))
            (count-down 1000)
        "#;
        let mut session = Session::default();
        let result = eval_program(source, &mut session)
            .expect("DEFINE + LAMBDA should preserve recursive binding semantics");
        assert_eq!(result.value.to_string(), "done");
    }

    #[test]
    fn make_macro_is_the_minimal_closure_to_macro_substrate() {
        let source = "(define identity-macro (make-macro (lambda (x) x))) (identity-macro 42)";
        let mut session = Session::default();
        let result = eval_program(source, &mut session)
            .expect("MAKE_MACRO should turn a closure into a macro value");
        assert_eq!(result.value.to_string(), "42");
    }

    #[test]
    fn macros_expand_and_evaluate_correctly() {
        let source = r#"
            (defmacro unless (condition body)
                (cons (quote cond)
                    (cons (cons condition (cons (quote ()) (quote ())))
                    (cons (cons (quote t) (cons body (quote ()))) (quote ())))))
            (unless () (quote success))
        "#;
        let mut session = Session::default();
        let result = eval_program(source, &mut session).expect("eval should succeed");
        assert_eq!(result.value.to_string(), "success");
    }

    #[test]
    fn macro_expansion_preserves_exact_rationals() {
        let source = r#"
            (defmacro half-of-third ()
                (/ 1 6))
            (half-of-third)
        "#;
        let mut session = Session::default();
        let result = eval_program(source, &mut session).expect("eval should succeed");
        assert_eq!(result.value.to_string(), "1/6");
    }

    #[test]
    fn canon_zero_empty_list_evaluates_directly() {
        let mut session = Session::default();
        let result = eval_program("()", &mut session).expect("empty structure should evaluate");
        assert_eq!(result.value.to_string(), "()");
    }

    #[test]
    fn ukrainian_canonical_surface_executes_the_core() {
        let source = r#"
            (за-умовою
              ((атом? (як-є кіт)) () (перше
                 (сполучити
                   (як-є груша)
                   (сполучити (як-є слива) ()))))
              ((атом? (як-є кіт)) (1) (перше
                 (сполучити
                   (як-є груша)
                   (сполучити (як-є слива) ()))))
              (t (як-є помилка)))
        "#;
        let mut session = Session::default();
        let result = eval_program(source, &mut session)
            .expect("Ukrainian canonical surface should evaluate");
        assert_eq!(result.value.to_string(), "груша");
    }

    #[test]
    fn ukrainian_rest_obeys_proper_list_semantics() {
        let mut session = Session::default();
        let result = eval_program("(решта (як-є (яблуко груша слива)))", &mut session)
            .expect("решта should return the structural remainder");
        assert_eq!(result.value.to_string(), "(груша слива)");
    }

    #[test]
    fn ukrainian_double_projection_reads_the_tree() {
        let mut session = Session::default();
        let result = eval_program("(перше (решта (як-є (яблуко груша слива))))", &mut session)
            .expect("canonical composition should evaluate");
        assert_eq!(result.value.to_string(), "груша");
    }

    #[test]
    fn sanskrit_canonical_surface_executes_the_same_core() {
        let source = r#"
            (anukrama
              ((aṇu (svarūpa phalam))
               (ādi
                 (saṃyuj
                   (svarūpa prathama)
                   (saṃyuj (svarūpa śeṣaḥ) ()))))
              (t (svarūpa doṣa)))
        "#;
        let mut session = Session::default();
        let result =
            eval_program(source, &mut session).expect("Sanskrit canonical surface should evaluate");
        assert_eq!(result.value.to_string(), "prathama");
    }

    #[test]
    fn surfaces_routing_to_function_sids_cannot_be_redefined() {
        for source in [
            "(def car 42)",
            "(def перше 42)",
            "(def ādi 42)",
            "(def quote 42)",
            "(def за-умовою 42)",
        ] {
            let mut session = Session::default();
            let error = eval_program(source, &mut session)
                .expect_err("surface routing to a function SID must reject redefinition");
            assert_eq!(error.kind, ErrorKind::InvalidForm, "source: {source}");
            assert!(error.message.contains("surface routes to immutable function SID"));
        }
    }

    #[test]
    fn surfaces_routing_to_function_sids_cannot_be_lambda_parameters() {
        for source in [
            "(lambda (car) car)",
            "(lambda (перше) перше)",
            "(lambda (ādi) ādi)",
            "(lambda atom? atom?)",
        ] {
            let mut session = Session::default();
            let error = eval_program(source, &mut session)
                .expect_err("surface routing to a function SID must reject parameter binding");
            assert_eq!(error.kind, ErrorKind::InvalidForm, "source: {source}");
            assert!(error.message.contains("surface routes to immutable function SID"));
        }
    }

    #[test]
    fn ordinary_nonregistry_bindings_remain_lexical() {
        let source = "(def local-add (lambda (a b) (quote shadowed))) (local-add 1 2)";
        let mut session = Session::default();
        let result = eval_program(source, &mut session)
            .expect("ordinary non-registry bindings remain lexical values");
        assert_eq!(result.value.to_string(), "shadowed");
    }

    #[test]
    fn canonical_resolution_ignores_even_preexisting_environment_shadow() {
        let mut session = Session::default();
        session.environment.define(
            "car",
            Value::Number(99.0, crate::Exactness::Exact),
        );
        let result = eval_program("(car (quote (1 2)))", &mut session)
            .expect("Canon resolver must outrank Environment");
        assert_eq!(result.value.to_string(), "1");
    }
}
