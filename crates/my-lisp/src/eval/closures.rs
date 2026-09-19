//! `lambda` construction and applying closures/macros to arguments.
//! Pobudova `lambda` ta zastosuvannia zamykan/makrosiv do arhumentiv.
//! Bau von `lambda` und Anwendung von Closures/Makros auf Argumente.

use super::{canon, evaluate, special_forms::quoted, EvalStep};
use crate::{Closure, Environment, ErrorKind, Expr, ExprKind, LanguageError, Span, Value};
use std::{collections::HashSet, rc::Rc};

/// Parses a lambda-list, which comes in three shapes shared across the Lisp
/// family (not one dialect's `&rest` keyword): `(a b)` — exactly two fixed
/// parameters, no rest; `(a b . rest)` — a dotted list, `rest` bound to
/// every argument past `a`/`b`; and a bare symbol `args` — zero fixed
/// parameters, every argument bound to `args`. The third shape reads as an
/// ordinary `ExprKind::Symbol`, the second as nested `ExprKind::Pair` (the
/// same dotted-pair reader support added earlier for data literals),
/// exactly the shapes `parser.rs` already produces — no new parser syntax.
/// Rozbyraie lambda-list, shcho maie try formy, spilni dlia rodyny Lisp (ne
/// kliuchove slovo `&rest` odnoho dialektu): `(a b)` — tochno dva fiksovani
/// parametry, bez rest; `(a b . rest)` — dotted-spysok, `rest` zviazuietsia
/// z usima arhumentamy ponad `a`/`b`; holyi symvol `args` — nul fiksovanykh
/// parametriv, kozhen arhument zviazuietsia z `args`. Tretia forma chytaietsia yak
/// zvychainyi `ExprKind::Symbol`, druha — yak vkladenyi `ExprKind::Pair` (ta
/// sama pidtrymka dotted-pair readera, dodana ranishe dlia literaliv danykh) —
/// same ti formy, yaki `parser.rs` uzhe y tak vyrobliaie, bez novoho syntaksysu.
fn parse_lambda_list(expr: &Expr) -> LambdaListResult {
    parse_lambda_list_inner(expr)
}

type LambdaList = (Vec<Rc<str>>, Option<Rc<str>>);
type LambdaListResult = Result<LambdaList, LanguageError>;

fn parse_lambda_list_inner(expr: &Expr) -> LambdaListResult {
    match &expr.kind {
        ExprKind::Symbol(name) => {
            canon::ensure_bindable(name, expr.span)?;
            Ok((Vec::new(), Some(name.clone())))
        }
        ExprKind::List(parameter_forms) => {
            let mut parameters = Vec::with_capacity(parameter_forms.len());
            let mut unique = HashSet::new();
            for parameter in parameter_forms.iter() {
                let ExprKind::Symbol(name) = &parameter.kind else {
                    return Err(LanguageError::new(
                        ErrorKind::InvalidForm,
                        "lambda parameter must be a symbol · parametr lambda maie buty symvolom · lambda-Parameter muss ein Symbol sein",
                        parameter.span,
                    ));
                };
                canon::ensure_bindable(name, parameter.span)?;
                if !unique.insert(name.clone()) {
                    return Err(LanguageError::new(
                        ErrorKind::InvalidForm,
                        format!("duplicate lambda parameter · povtornyi parametr lambda · doppelter lambda-Parameter: {name}"),
                        parameter.span,
                    ));
                }
                parameters.push(name.clone());
            }
            Ok((parameters, None))
        }
        ExprKind::Pair(_, _) => {
            let mut parameters = Vec::new();
            let mut unique = HashSet::new();
            let mut current: &Expr = expr;
            let rest = loop {
                match &current.kind {
                    ExprKind::Pair(head, tail) => {
                        let ExprKind::Symbol(name) = &head.kind else {
                            return Err(LanguageError::new(
                                ErrorKind::InvalidForm,
                                "lambda parameter must be a symbol · parametr lambda maie buty symvolom · lambda-Parameter muss ein Symbol sein",
                                head.span,
                            ));
                        };
                        canon::ensure_bindable(name, head.span)?;
                        if !unique.insert(name.clone()) {
                            return Err(LanguageError::new(
                                ErrorKind::InvalidForm,
                                format!("duplicate lambda parameter · povtornyi parametr lambda · doppelter lambda-Parameter: {name}"),
                                head.span,
                            ));
                        }
                        parameters.push(name.clone());
                        current = tail;
                    }
                    ExprKind::Symbol(name) => {
                        canon::ensure_bindable(name, current.span)?;
                        if !unique.insert(name.clone()) {
                            return Err(LanguageError::new(
                                ErrorKind::InvalidForm,
                                format!("duplicate lambda parameter · povtornyi parametr lambda · doppelter lambda-Parameter: {name}"),
                                current.span,
                            ));
                        }
                        break name.clone();
                    }
                    _ => {
                        return Err(LanguageError::new(
                            ErrorKind::InvalidForm,
                            "rest parameter must be a symbol · rest-parametr maie buty symvolom · Rest-Parameter muss ein Symbol sein",
                            current.span,
                        ))
                    }
                }
            };
            Ok((parameters, Some(rest)))
        }
        _ => Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "lambda parameters must be a list, dotted list, or symbol · parametry lambda maiut buty spyskom, dotted-spyskom abo symvolom · lambda-Parameter müssen eine Liste, Dotted-Liste oder ein Symbol sein",
            expr.span,
        )),
    }
}

pub(super) fn create_lambda(
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if arguments.len() < 2 {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            "lambda expects parameters and a body · lambda ochikuie parametry y tilo · lambda erwartet Parameter und einen Rumpf",
            span,
        ));
    }
    let (parameters, rest) = parse_lambda_list(&arguments[0])?;
    Ok(Value::Closure(Rc::new(Closure {
        parameters,
        rest,
        body: arguments[1..].into(),
        environment: environment.clone(),
    })))
}

/// Shared by `apply`/`apply_macro`: exact arity when there's no rest
/// parameter, "at least this many" when there is.
/// Spilne dlia `apply`/`apply_macro`: tochna arnist, yakshcho nema rest-
/// parametra, "shchonaimenshe stilky" — yakshcho ye.
fn check_arity(
    label: &str,
    fixed: usize,
    has_rest: bool,
    received: usize,
    span: Span,
) -> Result<(), LanguageError> {
    let arity_ok = if has_rest {
        received >= fixed
    } else {
        received == fixed
    };
    if arity_ok {
        return Ok(());
    }
    let expected = if has_rest {
        format!("at least / shchonaimenshe / mindestens {fixed}")
    } else {
        fixed.to_string()
    };
    Err(LanguageError::new(
        ErrorKind::Arity,
        format!(
            "{label}: expected / ochikuvalosia / erwartet {expected}; received / otrymano / erhalten {received}"
        ),
        span,
    ))
}

pub(super) fn apply(
    function: Value,
    arguments: &[Expr],
    calling_environment: &Environment,
    span: Span,
) -> Result<EvalStep, LanguageError> {
    let Value::Closure(ref closure) = function else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "expression is not callable · vyraz ne mozhna vyklykaty · Ausdruck ist nicht aufrufbar",
            span,
        ));
    };
    check_arity(
        "lambda",
        closure.parameters.len(),
        closure.rest.is_some(),
        arguments.len(),
        span,
    )?;

    // Arguments belong to the caller; parameters belong to the captured lexical frame.
    // Arhumenty nalezhat vyklyku, a parametry — zakhoplenomu leksychnomu freimu.
    // Argumente gehören zum Aufrufer, Parameter zum erfassten lexikalischen Frame.
    let local_environment = closure.environment.child();
    for (parameter, argument) in closure.parameters.iter().zip(arguments.iter()) {
        let value = evaluate(argument, calling_environment)?;
        local_environment.define(parameter.clone(), value);
    }
    if let Some(rest_name) = &closure.rest {
        let mut rest_values = Vec::with_capacity(arguments.len() - closure.parameters.len());
        for argument in &arguments[closure.parameters.len()..] {
            rest_values.push(evaluate(argument, calling_environment)?);
        }
        local_environment.define(rest_name.clone(), Value::list(rest_values));
    }
    let last = last_body_expression(&closure.body, &local_environment, span)?;
    // Tail positions become data for the evaluator loop instead of recursive Rust calls.
    // Khvostovi pozytsii staiut danymy dlia tsyklu evaluator, a ne rekursyvnymy vyklykamy Rust.
    // Tail-Positionen werden zu Daten für den Evaluator-Schleife statt zu rekursiven Rust-Aufrufen.
    Ok(EvalStep::TailCall {
        expression: last.clone(),
        environment: local_environment,
    })
}

/// Apply an ordinary closure to values that are already evaluated. Bulk
/// primitives use this path so they do not fabricate source expressions or
/// accidentally evaluate an element as code.
pub(super) fn apply_values(
    closure: Rc<Closure>,
    arguments: &[Value],
    span: Span,
) -> Result<Value, LanguageError> {
    check_arity(
        "lambda",
        closure.parameters.len(),
        closure.rest.is_some(),
        arguments.len(),
        span,
    )?;
    let local_environment = closure.environment.child();
    for (parameter, value) in closure.parameters.iter().zip(arguments.iter()) {
        local_environment.define(parameter.clone(), value.clone());
    }
    if let Some(rest_name) = &closure.rest {
        local_environment.define(
            rest_name.clone(),
            Value::list(arguments[closure.parameters.len()..].iter().cloned()),
        );
    }
    let mut result = Value::Nil;
    for expression in closure.body.iter() {
        result = evaluate(expression, &local_environment)?;
    }
    Ok(result)
}

/// Runs every body expression except the last for its side effects, then returns
/// the last one for the caller to evaluate in tail position. `create_lambda` always
/// builds a non-empty body, but this returns a `LanguageError` instead of panicking
/// so a future invariant change degrades gracefully rather than crashing the process.
/// Vykonuie vsi vyrazy tila, krim ostannoho, zarady pobichnykh efektiv, i povertaie
/// ostannii, shchob vyklyk obchyslyv yoho v khvostovii pozytsii. `create_lambda` zavzhdy
/// buduie neporozhnie tilo, ale tut povertaietsia `LanguageError`, a ne panika, shchob
/// maibutnia zmina invariantu dehraduvala plavno, a ne avariino zavershuvala protses.
/// Führt alle Rumpf-Ausdrücke außer dem letzten wegen ihrer Seiteneffekte aus und
/// gibt den letzten für die Auswertung in Tail-Position zurück. `create_lambda` baut
/// stets einen nicht leeren Rumpf, dennoch wird hier ein `LanguageError` statt eines
/// Panics zurückgegeben, damit eine künftige Invariantenänderung sanft statt abstürzend degradiert.
fn last_body_expression<'a>(
    body: &'a [Expr],
    environment: &Environment,
    span: Span,
) -> Result<&'a Expr, LanguageError> {
    let Some((last, leading)) = body.split_last() else {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "lambda body must not be empty · tilo lambda ne mozhe buty porozhnim · lambda-Rumpf darf nicht leer sein",
            span,
        ));
    };
    for expression in leading {
        evaluate(expression, environment)?;
    }
    Ok(last)
}

pub(super) fn apply_macro(
    closure: Rc<Closure>,
    arguments: &[Expr],
    calling_environment: &Environment,
    span: Span,
) -> Result<EvalStep, LanguageError> {
    check_arity(
        "defmacro",
        closure.parameters.len(),
        closure.rest.is_some(),
        arguments.len(),
        span,
    )?;

    let local_environment = closure.environment.child();
    for (parameter, argument) in closure.parameters.iter().zip(arguments.iter()) {
        let value = quoted(argument)?; // Do NOT evaluate arguments
        local_environment.define(parameter.clone(), value);
    }
    if let Some(rest_name) = &closure.rest {
        let mut rest_values: Vec<Value> = Vec::with_capacity(arguments.len());
        for argument in &arguments[closure.parameters.len()..] {
            rest_values.push(quoted(argument)?); // Do NOT evaluate arguments
        }
        local_environment.define(rest_name.clone(), Value::list(rest_values));
    }

    let last = last_body_expression(&closure.body, &local_environment, span)?;

    let expanded_value = evaluate(last, &local_environment)?;
    let expanded_expr = value_to_expr(expanded_value, span)?;

    Ok(EvalStep::TailCall {
        expression: expanded_expr,
        environment: calling_environment.clone(),
    })
}

// `pub(super)`, not private: `special_forms::evaluate_eval` reuses this same
// data->code conversion for `eval`, rather than duplicating the cons-cell
// walk that macro expansion already needed.
// `pub(super)`, ne pryvatna: `special_forms::evaluate_eval` perevykorystovuie
// tse same peretvorennia dani->kod dlia `eval`, zamist dubliuvannia obkhodu
// cons-komirok, yakyi uzhe buv potriben dlia rozhortannia makrosiv.
// `pub(super)`, nicht privat: `special_forms::evaluate_eval` nutzt dieselbe
// Daten->Code-Umwandlung für `eval` wieder, statt den Cons-Zellen-Durchlauf
// zu duplizieren, den die Makro-Expansion bereits brauchte.
pub(super) fn value_to_expr(value: Value, span: Span) -> Result<Expr, LanguageError> {
    fn go(value: &Value, span: Span, depth: u32) -> Result<Expr, LanguageError> {
        if depth > crate::syntax::MAX_STRUCTURE_DEPTH {
            return Err(LanguageError::new(
                ErrorKind::Parse,
                "structure exceeds reader limit · struktura perevyshchuie mezhu chytacha · Struktur überschreitet das Reader-Limit",
                span,
            ));
        }
        go_inner(value, span, depth)
    }

    fn go_inner(value: &Value, span: Span, depth: u32) -> Result<Expr, LanguageError> {
        let kind = match &value {
        Value::Nil => ExprKind::List(Rc::new([])),
        Value::Bool(true) => ExprKind::Symbol("t".into()),
        Value::Bool(false) => ExprKind::List(Rc::new([])),
        Value::Number(number, exactness) => ExprKind::Number(*number, *exactness),
        Value::Rational(rational) => ExprKind::Rational(rational.clone()),
        Value::NumericBuffer(buffer) => ExprKind::NumericBuffer(buffer.clone()),
        Value::String(val) => ExprKind::String(val.clone()),
        // A semantic callable is a runtime identity, not source syntax. It
        // cannot round-trip through eval/macro expansion by inventing a spelling.
        Value::SemanticRef(semantic_id) => {
            return Err(LanguageError::new(
                ErrorKind::Type,
                format!("a semantic callable (SID {semantic_id:08b}) is not executable code"),
                span,
            ));
        }
        // A legacy host builtin is callable but not syntax either.
        Value::Builtin(builtin) => {
            return Err(LanguageError::new(
                ErrorKind::Type,
                format!("a builtin ({}) is not executable code · v budovanyi funktsii ne ye vykonavym kodom", builtin.name),
                span,
            ));
        }
        Value::Symbol(symbol) => ExprKind::Symbol(symbol.clone()),
        Value::Vector(_) => {
            return Err(LanguageError::new(
                crate::ErrorKind::Type,
                "a vector is not executable code",
                span,
            ));
        }
        Value::Pair(_, _) => {
            let mut items = Vec::new();
            let mut current = value.clone();
            loop {
                match &current {
                    Value::Pair(h, t) => {
                        items.push(go(h, span, depth + 1)?);
                        current = (**t).clone();
                    }
                    Value::Nil => break,
                    _ => {
                        return Err(LanguageError::new(
                            ErrorKind::InvalidForm,
                            "macros must return proper lists · makrosy povynni povertaty pravylni spysky · Makros müssen korrekte Listen zurückgeben",
                            span,
                        ))
                    }
                }
            }
            ExprKind::List(items.into())
        }
        Value::Closure(_) | Value::Macro(_) => {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                "macros cannot return closures or macros · makrosy ne mozhut povertaty zamykannia abo makrosy · Makros dürfen keine Closures oder Makros zurückgeben",
                span,
            ))
        }
        // No source syntax represents a live connection/listener — same
        // capability-boundary reasoning as Closure/Macro above, for the
        // same reason: quoting/macro-expanding one would need to fabricate
        // code that could recreate a specific open TCP resource, which
        // isn't a thing this language can express.
        // Zhoden syntaksys ne predstavliaie zhyve ziednannia/listener — ta sama
        // lohika mezhi mozhlyvostei, shcho y dlia Closure/Macro vyshche, z tiiei
        // samoi prychyny: quote/rozhortannia makrosa na tsomu znachenni
        // oznachalo b vyhadaty kod, shcho vidtvoryv by konkretnyi vidkrytyi
        // TCP-resurs, — tse ne te, shcho tsia mova mozhe vyrazyty.
        Value::HostHandle { .. } | Value::TcpConnection(_) | Value::TcpListener(_) => {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                "macros cannot return TCP connections or listeners · makrosy ne mozhut povertaty TCP-ziednannia chy listener · Makros dürfen keine TCP-Verbindungen oder Listener zurückgeben",
                span,
            ))
        }
    };
        Ok(Expr { kind, span })
    }

    go(&value, span, 0)
}
