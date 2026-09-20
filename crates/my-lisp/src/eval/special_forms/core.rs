//! The McCarthy primitives (`eq`, `car`, `cdr`, `cons`, `cond`, `quote`'s
//! helper), plus the compatibility `def` surface. Language-owned `defmacro`
//! is bootstrapped from `lib/macro.my`; the Rust kernel no longer implements it.

use crate::eval::canon;
use crate::eval::{evaluate, evaluate_step, EvalStep};
use crate::{Environment, ErrorKind, Exactness, Expr, ExprKind, LanguageError, Span, Value};
use std::rc::Rc;

fn semantic_record(kind: &str, state: &str) -> Value {
    Value::list([
        Value::Symbol(Rc::from(kind)),
        Value::Symbol(Rc::from(state)),
    ])
}

pub(crate) fn atom_value(value: &Value) -> Value {
    let state = match value {
        Value::Nil => "empty-list",
        Value::Pair(_, _) => "pair",
        _ => "atom",
    };
    semantic_record("structural-kind", state)
}

fn two_symbol_record(value: &Value) -> Option<(&str, &str)> {
    let Value::Pair(kind, tail) = value else {
        return None;
    };
    let Value::Symbol(kind) = kind.as_ref() else {
        return None;
    };
    let Value::Pair(state, end) = tail.as_ref() else {
        return None;
    };
    let Value::Symbol(state) = state.as_ref() else {
        return None;
    };
    if !matches!(end.as_ref(), Value::Nil) {
        return None;
    }
    Some((kind.as_ref(), state.as_ref()))
}

/// Temporary bridge for historical two-part `cond` only.
///
/// Canonical three-part #217 dispatch never calls this function. The mapping
/// preserves the old branching behavior of the migrated #218 structural
/// observations and #216 exact-Q decisions while their callers move to
/// explicit domain-result matching. Once two-part `cond` is retired, this
/// adapter disappears with it.
fn migration_only_cond_truthy(value: &Value) -> bool {
    match value {
        // #216 exact comparison answers are mathematical data, not general
        // truth values. This mapping exists only so historical two-part cond
        // callers survive until they are rewritten to explicit three-part
        // result matching; canonical #217 control never passes through here.
        Value::Number(number, Exactness::Exact) if *number == 0.0 => false,
        Value::Number(number, Exactness::Exact) if *number == 1.0 => true,
        _ => match two_symbol_record(value) {
            Some(("structural-kind", "empty-list" | "atom")) => true,
            Some(("structural-kind", "pair")) => false,
            Some(("identity-relation", "same")) => true,
            Some(("identity-relation", "distinct")) => false,
            Some(("structural-relation", "same")) => true,
            Some(("structural-relation", "distinct")) => false,
            _ => value.is_truthy(),
        },
    }
}

pub(crate) fn evaluate_definition(
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_arity("def", arguments, 2, span)?;
    let ExprKind::Symbol(name) = &arguments[0].kind else {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "def expects a symbol name · def ochikuie nazvu-symvol · def erwartet einen Symbolnamen",
            arguments[0].span,
        ));
    };
    canon::ensure_bindable(name, arguments[0].span)?;
    let value = evaluate(&arguments[1], environment)?;
    // The shared lexical frame makes recursive definitions visible to their closure after binding.
    // Spilnyi leksychnyi freim robyt rekursyvne vyznachennia vydymym zamykanniu pislia zv’yazuvannia.
    // Der gemeinsame lexikalische Frame macht rekursive Definitionen nach der Bindung für ihre Closure sichtbar.
    environment.define(name.clone(), value.clone());
    Ok(value)
}

pub(crate) fn evaluate_cond(
    clauses: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<EvalStep, LanguageError> {
    let mut migration_compatibility_seen = false;
    for clause in clauses {
        let ExprKind::List(parts) = &clause.kind else {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                "cond expects list clauses · cond ochikuie spysky-umovy · cond erwartet Listenklauseln",
                clause.span,
            ));
        };
        match parts.len() {
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
            // Migration-only compatibility path for the existing library
            // bootstrap. It understands the new #218 structural records only
            // to preserve historical callers while source migrates to the
            // canonical three-part form. This path owns no language semantics.
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
        }
    }
    if migration_compatibility_seen {
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
            ExprKind::Binary(binary) => Value::Binary(*binary),
            ExprKind::NumericBuffer(buffer) => Value::NumericBuffer(buffer.clone()),
            ExprKind::String(value) => Value::String(value.clone()),
            ExprKind::Symbol(symbol) => Value::Symbol(symbol.clone()),
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
    Ok(semantic_record(
        "identity-relation",
        if left == right { "same" } else { "distinct" },
    ))
}
