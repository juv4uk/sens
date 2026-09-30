//! Одноразове зведення голови виклику до функції СЕНС (1 байт).
//!
//! Після розбору `(atom x)`, `(атом? x)`, `(aṇu x)` і `(00000010 x)` стають
//! одним і тим самим вузлом `ExprKind::Call(00000010, [x])`: функція
//! займає 1 байт, а виконання більше не шукає ім'я на кожному виклику.
//!
//! M8 (#1590): зводяться **усі** admitted surface з реєстру, не лише Canon
//! і necessary forms. Написання (`+`, `-`, `додати`, …) — маршрутизація до
//! фіксованого SENS, не окрема identity, яку можна перевизначити й тим
//! самим змусити runtime шукати ім'я на кожному виклику (#1413).
//!
//! Дані лишаються даними: аргумент `quote`, клаузи `cond` (самі клаузи — не
//! виклики), параметри `lambda` та ім'я в `def`/`define`.

use super::{canon, necessary_forms};
use crate::semantic_registry;
use crate::syntax::{Expr, ExprKind, MAX_STRUCTURE_DEPTH};
use crate::{ErrorKind, LanguageError, Sens8};
use std::rc::Rc;

const QUOTE: Sens8 = crate::sens!(00000001);
const COND: Sens8 = crate::sens!(00000111);

/// Звести всі виклики програми. Ідемпотентно: `Call` лишається `Call`.
pub fn lower_program(expressions: &[Expr]) -> Vec<Expr> {
    expressions.iter().map(|expression| lower(expression, 0)).collect()
}

/// Fail-closed boundary for the default binary SENS entry mode (#1879).
///
/// This is intentionally narrower than the full Symbol/lexical migration
/// (#1696/#1697): it proves that an executable *function* head entering
/// canonical SENS is already exact Function8. Human spellings remain valid
/// only when an explicit human surface frontend is selected.
///
/// Quoted data is not executable and is therefore not inspected. Binder/data
/// positions of exact necessary forms are skipped for the same reason.
pub fn require_binary_function_heads(expressions: &[Expr]) -> Result<(), LanguageError> {
    for expression in expressions {
        require_binary_function_head(expression, 0)?;
    }
    Ok(())
}

fn require_binary_function_head(expression: &Expr, depth: u32) -> Result<(), LanguageError> {
    if depth > MAX_STRUCTURE_DEPTH {
        return Ok(());
    }

    let ExprKind::List(items) = &expression.kind else {
        return Ok(());
    };
    if items.is_empty() {
        return Ok(());
    }

    let head = &items[0];
    match &head.kind {
        ExprKind::Symbol(name) => {
            if immutable_surface_sid(name).is_some() {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    format!(
                        "default SENS mode requires exact Function8 in executable head; human surface spelling '{name}' requires explicit en/ук/укр/sa surface"
                    ),
                    head.span,
                ));
            }
            for argument in &items[1..] {
                require_binary_function_head(argument, depth + 1)?;
            }
        }
        ExprKind::Sid(sid) if *sid == QUOTE => {
            // QUOTE payload is data, not executable source.
        }
        ExprKind::Sid(sid) if *sid == COND => {
            for clause in &items[1..] {
                if let ExprKind::List(parts) = &clause.kind {
                    for part in parts.iter() {
                        require_binary_function_head(part, depth + 1)?;
                    }
                }
            }
        }
        ExprKind::Sid(sid) if necessary_forms::identity_for_semantic_id(*sid).is_some() => {
            // DEFINE target / LAMBDA parameter list is data/binding structure.
            for argument in items[1..].iter().skip(1) {
                require_binary_function_head(argument, depth + 1)?;
            }
        }
        _ => {
            for argument in &items[1..] {
                require_binary_function_head(argument, depth + 1)?;
            }
        }
    }
    Ok(())
}

fn head_sid(head: &Expr) -> Option<Sens8> {
    match &head.kind {
        ExprKind::Sid(sid) => Some(*sid),
        ExprKind::Symbol(name) => immutable_surface_sid(name),
        _ => None,
    }
}

/// Написання, що маршрутизується до фіксованого SENS (не окрема identity).
fn immutable_surface_sid(name: &str) -> Option<Sens8> {
    if let Some(sid) = canon::routed_sid_for_surface(name) {
        return Some(sid);
    }
    // M8: будь-яка admitted surface → SENS. Необхідні форми лишаються
    // підмножиною; раніше лише вони зводились, тож `+`/`-` шукались у runtime.
    semantic_registry::admitted_semantic_id_for_surface(name)
}

fn lower_all(items: &[Expr], depth: u32) -> Rc<[Expr]> {
    items.iter().map(|item| lower(item, depth + 1)).collect()
}

fn lower(expression: &Expr, depth: u32) -> Expr {
    if depth > MAX_STRUCTURE_DEPTH {
        return expression.clone();
    }
    let kind = match &expression.kind {
        ExprKind::Call(sid, arguments) => ExprKind::Call(*sid, arguments.clone()),
        ExprKind::List(items) if !items.is_empty() => {
            let arguments = &items[1..];
            match head_sid(&items[0]) {
                Some(sid) if sid == QUOTE => ExprKind::Call(sid, arguments.into()),
                Some(sid) if sid == COND => ExprKind::Call(
                    sid,
                    arguments
                        .iter()
                        .map(|clause| match &clause.kind {
                            ExprKind::List(parts) => Expr {
                                kind: ExprKind::List(lower_all(parts, depth + 1)),
                                span: clause.span,
                            },
                            _ => clause.clone(),
                        })
                        .collect(),
                ),
                Some(sid) if necessary_forms::identity_for_semantic_id(sid).is_some() => {
                    ExprKind::Call(
                        sid,
                        arguments
                            .iter()
                            .enumerate()
                            .map(|(index, argument)| {
                                if index == 0 {
                                    argument.clone()
                                } else {
                                    lower(argument, depth + 1)
                                }
                            })
                            .collect(),
                    )
                }
                Some(sid) => ExprKind::Call(sid, lower_all(arguments, depth)),
                None => ExprKind::List(lower_all(items, depth)),
            }
        }
        _ => return expression.clone(),
    };
    Expr {
        kind,
        span: expression.span,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::parser;

    fn lower_one(source: &str) -> Expr {
        let program = parser::parse(source).expect("parse");
        let lowered = lower_program(&program);
        assert_eq!(lowered.len(), 1);
        lowered.into_iter().next().expect("one form")
    }

    #[test]
    fn plus_surface_lowers_to_sens_call() {
        let expr = lower_one("(+ 1 2)");
        match expr.kind {
            ExprKind::Call(sid, args) => {
                assert_eq!(sid, crate::sens!(00001100));
                assert_eq!(args.len(), 2);
            }
            other => panic!("expected Call, got {other:?}"),
        }
    }

    #[test]
    fn minus_surface_lowers_to_sens_call() {
        let expr = lower_one("(- 5 3)");
        match expr.kind {
            ExprKind::Call(sid, _) => assert_eq!(sid, crate::sens!(00001101)),
            other => panic!("expected Call, got {other:?}"),
        }
    }

    #[test]
    fn user_symbol_is_not_lowered() {
        let expr = lower_one("(my-fn 1)");
        match expr.kind {
            ExprKind::List(_) => {}
            other => panic!("user head must stay List, got {other:?}"),
        }
    }

    #[test]
    fn binary_entry_accepts_exact_function8_and_rejects_human_heads() {
        for source in [
            "(00001100 2 3)",
            "(00000111 ((00000011 1 1) (00001100 2 3)))",
            "(00000001 (+ додати atom?))",
        ] {
            let parsed = parser::parse(source).expect("parse");
            require_binary_function_heads(&parsed)
                .unwrap_or_else(|error| panic!("{source}: {error}"));
        }

        for source in ["(+ 2 3)", "(додати 2 3)", "(atom? (00000001 x))"] {
            let parsed = parser::parse(source).expect("parse");
            let error = require_binary_function_heads(&parsed)
                .expect_err("human function head must be explicit-surface only");
            assert_eq!(error.kind, ErrorKind::InvalidForm);
            assert!(error.to_string().contains("exact Function8"), "{error}");
        }
    }

    #[test]
    fn binary_entry_does_not_treat_exact_binders_as_executable_heads() {
        let source = "(00001000 (+ x) (00001100 x 1))";
        let parsed = parser::parse(source).expect("parse");
        require_binary_function_heads(&parsed).expect("binder list is not executable");
    }
}
