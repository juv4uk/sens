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
use crate::CallableIdentity;
use std::rc::Rc;

const QUOTE: CallableIdentity = CallableIdentity::legacy8(0b0000_0001);
const COND: CallableIdentity = CallableIdentity::legacy8(0b0000_0111);

/// Звести всі виклики програми. Ідемпотентно: `Call` лишається `Call`.
pub fn lower_program(expressions: &[Expr]) -> Vec<Expr> {
    expressions.iter().map(|expression| lower(expression, 0)).collect()
}

fn head_sid(head: &Expr) -> Option<CallableIdentity> {
    match &head.kind {
        ExprKind::Sid(sid) => Some(*sid),
        ExprKind::Symbol(name) => immutable_surface_sid(name),
        _ => None,
    }
}

/// Написання, що маршрутизується до фіксованого SENS (не окрема identity).
fn immutable_surface_sid(name: &str) -> Option<CallableIdentity> {
    if let Some(sid) = canon::routed_sid_for_surface(name) {
        return Some(CallableIdentity::legacy8(sid.packed_byte()));
    }
    // M8: будь-яка admitted surface → SENS. Необхідні форми лишаються
    // підмножиною; раніше лише вони зводились, тож `+`/`-` шукались у runtime.
    semantic_registry::admitted_semantic_id_for_surface(name)
        .map(|sid| CallableIdentity::legacy8(sid.packed_byte()))
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
                Some(identity)
                    if identity
                        .legacy8_bits()
                        .map(crate::Sens8::from_packed_byte)
                        .and_then(necessary_forms::identity_for_semantic_id)
                        .is_some() => {
                    let sid = identity;
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
                assert_eq!(sid.legacy8_bits(), Some(0b0000_1100));
                assert_eq!(args.len(), 2);
            }
            other => panic!("expected Call, got {other:?}"),
        }
    }

    #[test]
    fn minus_surface_lowers_to_sens_call() {
        let expr = lower_one("(- 5 3)");
        match expr.kind {
            ExprKind::Call(sid, _) => assert_eq!(sid.legacy8_bits(), Some(0b0000_1101)),
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
