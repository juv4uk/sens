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
use crate::{CoreDomainIdentity, Sens8};
use std::rc::Rc;

const QUOTE: Sens8 = crate::sens!(00000001);
const COND: Sens8 = crate::sens!(00000111);

/// Звести всі виклики програми. Ідемпотентно: `Call` лишається `Call`.
pub fn lower_program(expressions: &[Expr]) -> Vec<Expr> {
    expressions.iter().map(|expression| lower(expression, 0)).collect()
}

fn head_domain_identity(head: &Expr) -> Option<CoreDomainIdentity> {
    match &head.kind {
        ExprKind::DomainIdentity(identity) => Some(*identity),
        ExprKind::Symbol(name) => semantic_registry::domain_identity_for_surface(name),
        _ => None,
    }
}

fn is_d3(identity: CoreDomainIdentity, raw: u8) -> bool {
    matches!(
        identity,
        CoreDomainIdentity::D3(word) if word.word().packed_bits() == raw
    )
}

fn lower_domain_call(
    identity: CoreDomainIdentity,
    arguments: &[Expr],
    depth: u32,
) -> ExprKind {
    if is_d3(identity, 0b001) {
        return ExprKind::DomainCall(identity, arguments.into());
    }
    if is_d3(identity, 0b011) {
        return ExprKind::DomainCall(
            identity,
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
        );
    }
    if necessary_forms::identity_for_domain_identity(identity).is_some() {
        return ExprKind::DomainCall(
            identity,
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
        );
    }
    ExprKind::DomainCall(identity, lower_all(arguments, depth))
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
    if semantic_registry::domain_identity_for_surface(name).is_some() {
        return None;
    }
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
        ExprKind::DomainCall(identity, arguments) => {
            ExprKind::DomainCall(*identity, arguments.clone())
        }
        ExprKind::List(items) if !items.is_empty() => {
            let arguments = &items[1..];
            if let Some(identity) = head_domain_identity(&items[0]) {
                lower_domain_call(identity, arguments, depth)
            } else {
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
    fn d3_surface_lowers_to_domain_call() {
        let expr = lower_one("(atom? (quote x))");
        let ExprKind::DomainCall(identity, args) = expr.kind else {
            panic!("expected canonical DomainCall");
        };
        assert_eq!((identity.width(), identity.packed_bits()), (3, 0b010));
        assert!(matches!(
            args[0].kind,
            ExprKind::DomainCall(quote, _) if (quote.width(), quote.packed_bits()) == (3, 0b001)
        ));
    }

    #[test]
    fn d4_lambda_surface_lowers_to_domain_call() {
        let expr = lower_one("(lambda (x) x)");
        let ExprKind::DomainCall(identity, args) = expr.kind else {
            panic!("expected D4 DomainCall");
        };
        assert_eq!((identity.width(), identity.packed_bits()), (4, 0b0010));
        assert_eq!(args.len(), 2);
        assert!(matches!(args[0].kind, ExprKind::List(_)));
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
}
