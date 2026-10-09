//! The McCarthy primitives (`eq`, `car`, `cdr`, `cons`, `cond`, `quote`'s
//! helper), plus the compatibility `def` surface. Language-owned `defmacro`
//! is bootstrapped from `lib/macro.lisp`; the Rust kernel no longer implements it.

use crate::eval::canon;
use crate::eval::{evaluate, evaluate_step, EvalStep};
use crate::environment::{CondClauseMode, CoreProfile};
use crate::{Environment, ErrorKind, Expr, ExprKind, LanguageError, Span, Value};

use std::rc::Rc;

/// Відповідь 15-станної шкали Core4 (#1391): список двійкових бітів.
/// `(1)` — «так» ступеня 1, `(0)` — «ні» ступеня 1, `()` — невідомо.
fn answer(bit: Option<u8>) -> Value {
    match bit {
        Some(bit) => Value::list([Value::Number(f64::from(bit), crate::Exactness::Exact)]),
        None => Value::Nil,
    }
}

/// atom? відповіддю шкали (contracts/core4-predicate-answer-scale.lisp /3):
/// атом `(1)`, пара `(0)`. `()` стоїть вище розрізнення атом/пара, тож у Core4
/// (і Core3, що стоїть на ньому) відповідь `()`. Core1–2 мають лише ступінь 1,
/// тож там `()` — атом, як у Маккарті 1960: `(1)`.
pub(crate) fn atom_value(value: &Value, environment: &Environment) -> Value {
    match value {
        Value::Pair(_, _) => answer(Some(0)),
        Value::Nil => match environment.selected_core_profile() {
            Some(CoreProfile::Core1 | CoreProfile::Core2) => answer(Some(1)),
            _ => answer(None),
        },
        _ => answer(Some(1)),
    }
}

/// Напрям відповіді шкали: `Some(true)` для 1^n, `Some(false)` для 0^n
/// (n = 1..7); `None`, якщо значення не є відповіддю зі стрілкою.
fn answer_direction(value: &Value) -> Option<bool> {
    let mut bits = Vec::new();
    let mut cursor = value;
    while let Value::Pair(head, tail) = cursor {
        match head.as_ref() {
            Value::Number(number, crate::Exactness::Exact) if *number == 0.0 || *number == 1.0 => {
                bits.push(*number == 1.0)
            }
            _ => return None,
        }
        cursor = tail.as_ref();
    }
    if !matches!(cursor, Value::Nil) || bits.is_empty() || bits.len() > 7 {
        return None;
    }
    let first = bits[0];
    bits.iter().all(|bit| *bit == first).then_some(first)
}

/// Двочастинна клауза `cond` `(перевірка вираз)` за новою логікою (#1391):
/// клауза обирається лише відповіддю «так» (1^n). «Ні» (0^n) і невідомо `()`
/// її не обирають. Значення, що не є відповіддю шкали, лишаються за
/// історичною істинністю (лише () і false хибні).
fn migration_only_cond_truthy(value: &Value) -> bool {
    if let Some(bit) = value.as_predicate_bit() {
        return bit;
    }
    match answer_direction(value) {
        Some(direction) => direction,
        None => value.is_truthy(),
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum ExactD3CondControl {
    Select,
    SkipNo,
}

/// Canonical D3:110 control projection.
///
/// Contract 11.8: only exact D1 PredicateBit answers may control COND.
/// D1:1 selects and D1:0 skips. Structural (), Number 0/1, T/NIL and
/// every other non-D1 value are wrong-domain control inputs and fail closed.
fn exact_d3_cond_control(value: &Value, span: Span) -> Result<ExactD3CondControl, LanguageError> {
    match value.as_predicate_bit() {
        Some(true) => Ok(ExactD3CondControl::Select),
        Some(false) => Ok(ExactD3CondControl::SkipNo),
        None => Err(LanguageError::new(
            ErrorKind::Type,
            format!("D3:110 COND expects exact D1:1 / D1:0; got {value}"),
            span,
        )),
    }
}

/// Exact-domain D3:110 COND.
///
/// This path is deliberately separate from historical Sens8/profile COND.
/// It is two-part only and never consults host/Lisp truthiness.
pub(crate) fn evaluate_domain_cond(
    clauses: &[Expr],
    environment: &Environment,
    _span: Span,
) -> Result<EvalStep, LanguageError> {
    for clause in clauses {
        let ExprKind::List(parts) = &clause.kind else {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                "D3:110 COND expects list clauses",
                clause.span,
            ));
        };
        // Contract 11.8: canonical D3 COND has exactly two fields.
        // Reject old explicit-result clauses *before* evaluating their query:
        // evaluating a malformed clause would produce observable side effects.
        if parts.len() != 2 {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                "D3:110 COND requires exactly (test expression); three-part compatibility is forbidden",
                clause.span,
            ));
        }
        let value = evaluate(&parts[0], environment)?;
        match exact_d3_cond_control(&value, parts[0].span)? {
            ExactD3CondControl::Select => return evaluate_step(&parts[1], environment),
            ExactD3CondControl::SkipNo => {}
        }
    }

    Ok(EvalStep::Value(Value::Nil))
}

pub(crate) fn evaluate_definition(
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_sens_arity(crate::sens!(00001011), arguments, 2, span)?;

    match &arguments[0].kind {
        ExprKind::Symbol(name) => {
            canon::ensure_bindable(name, arguments[0].span)?;
            let value = evaluate(&arguments[1], environment)?;
            // The shared lexical frame makes recursive definitions visible to their closure after binding.
            // Spilnyi leksychnyi freim robyt rekursyvne vyznachennia vydymym zamykanniu pislia zv’yazuvannia.
            // Der gemeinsame lexikalische Frame macht rekursive Definitionen nach der Bindung für ihre Closure sichtbar.
            canon::bind_language_definition(name, &value, environment);
            environment.define(name.clone(), value.clone());
            Ok(value)
        }
        ExprKind::DomainIdentity(identity) => {
            let Some(identity) = identity.core_operation() else {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    "exact DEFINE target must be a callable D3/D4/D5/D6 DomainIdentity",
                    arguments[0].span,
                ));
            };

            if !environment.is_root() {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    "exact DEFINE target may install a language-owned mechanism only at the root frame",
                    arguments[0].span,
                ));
            }

            if environment.domain_code_slot(identity).is_some() {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    format!("exact DEFINE target already has a language-owned binding: {identity}"),
                    arguments[0].span,
                ));
            }

            let value = evaluate(&arguments[1], environment)?;
            if !matches!(value, Value::Closure(_) | Value::Builtin(_)) {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "exact DEFINE target requires a callable closure or builtin mechanism",
                    arguments[1].span,
                ));
            }

            if !environment.bind_domain_code_slot_once(identity, value.clone()) {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    format!("exact DEFINE target was concurrently bound: {identity}"),
                    arguments[0].span,
                ));
            }

            Ok(value)
        }
        _ => Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "def expects a symbol name or exact callable DomainIdentity · def ochikuie nazvu-symvol abo tochnyi vyklychnyi DomainIdentity · def erwartet einen Symbolnamen oder eine exakte aufrufbare DomainIdentity",
            arguments[0].span,
        )),
    }
}

pub(crate) fn evaluate_cond(
    clauses: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<EvalStep, LanguageError> {
    let mode = environment.cond_clause_mode();
    let mut migration_compatibility_seen = false;

    for clause in clauses {
        let ExprKind::List(parts) = &clause.kind else {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                "cond expects list clauses · cond ochikuie spysky-umovy · cond erwartet Listenklauseln",
                clause.span,
            ));
        };

        match mode {
            CondClauseMode::Core2LegacyTwoPart => {
                if parts.len() != 2 {
                    return Err(LanguageError::new(
                        ErrorKind::InvalidForm,
                        "Core2 cond expects historical (test expression) clauses",
                        clause.span,
                    ));
                }
                let value = evaluate(&parts[0], environment)?;
                if migration_only_cond_truthy(&value) {
                    return evaluate_step(&parts[1], environment);
                }
            }
            CondClauseMode::CurrentMigration => match parts.len() {
                // #217 canonical path: the clause explicitly names the domain
                // result that selects it. The expected form is data, not code.
                // No Value -> bool conversion occurs on this path.
                3 => {
                    let actual = evaluate(&parts[0], environment)?;
                    let expected = quoted(&parts[1])?;
                    if actual == expected {
                        return evaluate_step(&parts[2], environment);
                    }
                }
                // Migration-only compatibility path for callers not yet moved
                // to the canonical three-part form.
                2 => {
                    migration_compatibility_seen = true;
                    let value = evaluate(&parts[0], environment)?;
                    if migration_only_cond_truthy(&value) {
                        return evaluate_step(&parts[1], environment);
                    }
                }
                _ => {
                    return Err(LanguageError::new(
                        ErrorKind::InvalidForm,
                        "cond expects canonical (query expected-result expression) clauses or migration-only (test expression) clauses · cond ochikuie kanonichni (zapyt ochikuvanyi-rezultat vyraz) abo tymchasovi (perevirka vyraz) · cond erwartet kanonische (Abfrage erwartetes-Ergebnis Ausdruck)- oder voruebergehende (Test Ausdruck)-Klauseln",
                        clause.span,
                    ));
                }
            },
        }
    }

    if mode == CondClauseMode::Core2LegacyTwoPart || migration_compatibility_seen {
        return Ok(EvalStep::Value(Value::Nil));
    }

    Err(LanguageError::new(
        ErrorKind::UnsatisfiedConditional,
        "канонічний cond: жоден query не збігся з expected-result · canonical cond: no query matched its expected result · kanonisches cond: keine Abfrage entsprach ihrem erwarteten Ergebnis",
        span,
    ))
}

pub fn exact_arity(
    operator: &str,
    arguments: &[Expr],
    expected: usize,
    span: Span,
) -> Result<(), LanguageError> {
    if arguments.len() == expected {
        return Ok(());
    }
    Err(LanguageError::new(
        ErrorKind::Arity,
        format!(
            "{operator}: expected / ochikuvalosia / erwartet {expected}; received / otrymano / erhalten {}",
            arguments.len()
        ),
        span,
    ))
}

/// Arity check for a SENS form inside the core: the form is named by its
/// 8-bit code, never by a surface spelling. `exact_arity` stays for host
/// capabilities, which are not SENS identities.
pub fn exact_sens_arity(
    operator: crate::Sens8,
    arguments: &[Expr],
    expected: usize,
    span: Span,
) -> Result<(), LanguageError> {
    if arguments.len() == expected {
        return Ok(());
    }
    Err(LanguageError::new(
        ErrorKind::Arity,
        format!(
            "{operator}: expected / ochikuvalosia / erwartet {expected}; received / otrymano / erhalten {}",
            arguments.len()
        ),
        span,
    ))
}

pub(crate) fn quoted(expression: &Expr) -> Result<Value, LanguageError> {
    fn go(expression: &Expr, depth: u32) -> Result<Value, LanguageError> {
        if depth > crate::syntax::MAX_STRUCTURE_DEPTH {
            return Err(LanguageError::new(
                ErrorKind::Parse,
                "quoted structure exceeds reader limit · struktura perevyshchuie mezhu chytacha · zitierte Struktur überschreitet das Reader-Limit",
                Span { start: 0, end: 0 },
            ));
        }
        Ok(match &expression.kind {
            ExprKind::Number(number, exactness) => Value::Number(*number, *exactness),
            ExprKind::Rational(rational) => Value::Rational(rational.clone()),
            ExprKind::BinaryNumber(number) => Value::BinaryNumber(number.clone()),
            ExprKind::Sid(sid) => Value::Sid(*sid),
            ExprKind::DomainIdentity(identity) => Value::DomainIdentity(*identity),
            ExprKind::NumericBuffer(buffer) => Value::NumericBuffer(buffer.clone()),
            ExprKind::String(value) => Value::String(value.clone()),
            ExprKind::Symbol(symbol) => Value::Symbol(symbol.clone()),
            // Слот — координата виконання, не дані: у quote-позиції його не буває
            // (розв'язувач її не чіпає), тож така поява — порушення інваріанта.
            ExprKind::Local { .. } => {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    "a lexical slot has no source datum · leksychnyi slot ne maie danykh dzherela · ein lexikalischer Slot hat kein Quelldatum",
                    expression.span,
                ));
            }
            ExprKind::List(items) => {
                let mut out = Vec::with_capacity(items.len());
                for item in items.iter() {
                    out.push(go(item, depth + 1)?);
                }
                Value::list(out)
            }
            ExprKind::Pair(head, tail) => {
                Value::Pair(Rc::new(go(head, depth + 1)?), Rc::new(go(tail, depth + 1)?))
            }
            // Зведений виклик як дані — список із функцією СЕНС у голові.
            ExprKind::Call(sid, arguments) => {
                let mut out = Vec::with_capacity(arguments.len() + 1);
                out.push(Value::Sid(*sid));
                for argument in arguments.iter() {
                    out.push(go(argument, depth + 1)?);
                }
                Value::list(out)
            }
            ExprKind::DomainCall(identity, arguments) => {
                let mut out = Vec::with_capacity(arguments.len() + 1);
                out.push(Value::DomainIdentity((*identity).into()));
                for argument in arguments.iter() {
                    out.push(go(argument, depth + 1)?);
                }
                Value::list(out)
            }
        })
    }
    go(expression, 0)
}

// ── contract 2.1: value-level entry points (first-class builtins) ──
// Same compute as the expr-handlers above; arguments arrive
// pre-evaluated. The expr-handlers delegate here after evaluating.

pub(crate) fn car_value(value: &Value, span: Span) -> Result<Value, LanguageError> {
    match value {
        Value::Pair(ref head, _) => Ok((**head).clone()),
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "car expects a non-empty list · car ochikuie neporozhnii spysok · car erwartet eine nicht leere Liste",
            span,
        )),
    }
}

pub(crate) fn cdr_value(value: &Value, span: Span) -> Result<Value, LanguageError> {
    match value {
        Value::Pair(_, ref tail) => Ok((**tail).clone()),
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "cdr expects a non-empty list · cdr ochikuie neporozhnii spysok · cdr erwartet eine nicht leere Liste",
            span,
        )),
    }
}

pub(crate) fn cons_values(
    head: Value,
    tail: Value,
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if environment.try_alloc_cons().is_err() {
        return Err(LanguageError::new(
            ErrorKind::OutOfMemory,
            "cons: resource limit reached · cons: dosiahnuto mezhi resursu · cons: Ressourcengrenze erreicht",
            span,
        ));
    }
    Ok(Value::Pair(std::rc::Rc::new(head), std::rc::Rc::new(tail)))
}

pub(crate) fn eq_values(left: Value, right: Value, span: Span) -> Result<Value, LanguageError> {
    if !left.is_atom() || !right.is_atom() {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "eq expects two atoms · eq ochikuie dva atomy · eq erwartet zwei Atome",
            span,
        ));
    }
    Ok(answer(Some(u8::from(left == right))))
}
