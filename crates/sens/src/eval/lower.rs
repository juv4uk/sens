//! Одноразове зведення голови виклику до функції СЕНС (1 байт).
//!
//! Після розбору `(atom x)`, `(атом? x)`, `(aṇu x)` і `(00000010 x)` стають
//! одним і тим самим вузлом `ExprKind::LegacyCall(00000010, [x])`: функція
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
use crate::Sens8;
use std::rc::Rc;

const QUOTE: Sens8 = crate::sens!(00000001);
const COND: Sens8 = crate::sens!(00000111);

/// Звести legacy surface-виклики. Канонічні domain Call лишаються незмінними.
pub fn lower_program(expressions: &[Expr]) -> Vec<Expr> {
    expressions.iter().map(|expression| lower(expression, 0)).collect()
}

fn head_sid(head: &Expr) -> Option<Sens8> {
    match &head.kind {
        ExprKind::LegacySid(sid) => Some(*sid),
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
        ExprKind::Call(identity, arguments) => ExprKind::Call(*identity, arguments.clone()),
        ExprKind::LegacyCall(sid, arguments) => ExprKind::LegacyCall(*sid, arguments.clone()),
        ExprKind::List(items) if !items.is_empty() => {
            let arguments = &items[1..];
            match head_sid(&items[0]) {
                Some(sid) if sid == QUOTE => ExprKind::LegacyCall(sid, arguments.into()),
                Some(sid) if sid == COND => ExprKind::LegacyCall(
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
                    ExprKind::LegacyCall(
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
                Some(sid) => ExprKind::LegacyCall(sid, lower_all(arguments, depth)),
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
            ExprKind::LegacyCall(sid, args) => {
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
            ExprKind::LegacyCall(sid, _) => assert_eq!(sid, crate::sens!(00001101)),
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
}
