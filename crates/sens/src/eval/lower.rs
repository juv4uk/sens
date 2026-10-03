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

use super::{canon, lower_domain, necessary_forms_legacy};
use crate::semantic_registry;
use crate::syntax::{Expr, ExprKind, MAX_STRUCTURE_DEPTH};
use crate::Sens8;
use std::rc::Rc;

const QUOTE: Sens8 = crate::sens!(00000001);
const COND: Sens8 = crate::sens!(00000111);

/// Звести всі виклики програми. Ідемпотентно: `Call` лишається `Call`.
pub fn lower_program(expressions: &[Expr]) -> Vec<Expr> {
    expressions.iter().map(|expression| lower(expression, 0)).collect()
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

pub(super) fn lower(expression: &Expr, depth: u32) -> Expr {
    if depth > MAX_STRUCTURE_DEPTH {
        return expression.clone();
    }
    let kind = match &expression.kind {
        ExprKind::Call(sid, arguments) => ExprKind::Call(*sid, arguments.clone()),
        ExprKind::DomainCall(identity, arguments) => {
            ExprKind::DomainCall(*identity, arguments.clone())
        }
        ExprKind::List(items) if !items.is_empty() => {
            if let Some(domain_call) = lower_domain::try_lower_necessary_form(items, depth) {
                domain_call
            } else {
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
                    Some(sid)
                        if necessary_forms_legacy::identity_for_semantic_id(sid).is_some() =>
                    {
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
    fn lambda_surface_lowers_to_domain_call() {
        let expr = lower_one("(lambda (x) x)");
        match expr.kind {
            ExprKind::DomainCall(identity, args) => {
                assert_eq!((identity.width(), identity.packed_bits()), (4, 0b0010));
                assert_eq!(args.len(), 2);
            }
            other => panic!("expected DomainCall, got {other:?}"),
        }
    }

    #[test]
    fn define_surface_lowers_to_domain_call_and_nested_lambda_is_domain_call() {
        let expr = lower_one("(define id (lambda (x) x))");
        let ExprKind::DomainCall(identity, args) = expr.kind else {
            panic!("expected DEFINE DomainCall");
        };
        assert_eq!((identity.width(), identity.packed_bits()), (4, 0b0011));
        assert!(matches!(args[1].kind, ExprKind::DomainCall(_, _)));
    }

    #[test]
    fn compatibility_def_normalizes_to_canonical_d4_define() {
        let expr = lower_one("(def id (lambda (x) x))");
        let ExprKind::DomainCall(identity, _) = expr.kind else {
            panic!("expected DEFINE DomainCall");
        };
        assert_eq!((identity.width(), identity.packed_bits()), (4, 0b0011));
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
