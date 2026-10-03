//! Одноразове зведення голови виклику до канонічної доменної identity.
//!
//! Surface-и, для яких уже ратифіковано exact domain identity, стають
//! `ExprKind::DomainCall`. Старий точний 8-бітний token лишається окремим
//! compatibility-шляхом `ExprKind::Call` зі старим байтом: lower ніколи не
//! виводить домен із історичного байта.
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
use crate::CoreDomainIdentity;
use crate::Sens8;
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
        ExprKind::Symbol(name) => immutable_surface_domain_identity(name),
        _ => None,
    }
}

fn immutable_surface_domain_identity(name: &str) -> Option<CoreDomainIdentity> {
    necessary_forms::domain_identity_for_symbol(name)
        .or_else(|| semantic_registry::domain_identity_for_surface(name))
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
    // Once a surface has an exact domain identity, the legacy byte route is no
    // longer allowed to win. Unmigrated registry rows keep the old path.
    if immutable_surface_domain_identity(name).is_some() {
        return None;
    }
    if let Some(sid) = canon::routed_sid_for_surface(name) {
        return Some(sid);
    }
    semantic_registry::admitted_semantic_id_for_surface(name)
}

fn is_d3(identity: CoreDomainIdentity, bits: u8) -> bool {
    matches!(
        identity,
        CoreDomainIdentity::D3(word) if word.word().packed_bits() == bits
    )
}

fn lower_all(items: &[Expr], depth: u32) -> Rc<[Expr]> {
    items.iter().map(|item| lower(item, depth + 1)).collect()
}

fn lower_domain_call(
    identity: CoreDomainIdentity,
    arguments: &[Expr],
    depth: u32,
) -> ExprKind {
    if is_d3(identity, 0b001) {
        ExprKind::DomainCall(identity, arguments.into())
    } else if is_d3(identity, 0b011) {
        ExprKind::DomainCall(
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
        )
    } else if necessary_forms::identity_for_domain_identity(identity).is_some() {
        ExprKind::DomainCall(
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
        )
    } else {
        ExprKind::DomainCall(identity, lower_all(arguments, depth))
    }
}

fn lower_legacy_call(sid: Sens8, arguments: &[Expr], depth: u32) -> ExprKind {
    if sid == QUOTE {
        ExprKind::Call(sid, arguments.into())
    } else if sid == COND {
        ExprKind::Call(
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
        )
    } else if necessary_forms::identity_for_semantic_id(sid).is_some() {
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
    } else {
        ExprKind::Call(sid, lower_all(arguments, depth))
    }
}

fn lower(expression: &Expr, depth: u32) -> Expr {
    if depth > MAX_STRUCTURE_DEPTH {
        return expression.clone();
    }
    let kind = match &expression.kind {
        // A compatibility head stays compatibility, but its executable
        // descendants must keep moving toward exact-domain identity.
        ExprKind::Call(sid, arguments) => lower_legacy_call(*sid, arguments, depth),
        // Domain calls are already canonical at the head. Recurse only through
        // positions that are executable under that domain form's law.
        ExprKind::DomainCall(identity, arguments) => {
            lower_domain_call(*identity, arguments, depth)
        }
        ExprKind::List(items) if !items.is_empty() => {
            let arguments = &items[1..];

            if let Some(identity) = head_domain_identity(&items[0]) {
                return Expr {
                    kind: lower_domain_call(identity, arguments, depth),
                    span: expression.span,
                };
            }

            match head_sid(&items[0]) {
                Some(sid) => lower_legacy_call(sid, arguments, depth),
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

    fn assert_domain_call(source: &str, width: usize, bits: u8) {
        let expr = lower_one(source);
        match expr.kind {
            ExprKind::DomainCall(identity, _) => {
                assert_eq!(identity.width(), width);
                assert_eq!(identity.packed_bits(), bits);
            }
            other => panic!("expected DomainCall, got {other:?}"),
        }
    }

    #[test]
    fn migrated_d3_surfaces_lower_to_exact_domain_calls() {
        // Use already-admitted Ukrainian projections so this witness proves
        // domain routing without reinstalling an English spelling as identity.
        assert_domain_call("(як-є x)", 3, 0b001);
        assert_domain_call("(атом? x)", 3, 0b010);
        assert_domain_call("(за-умовою (x y))", 3, 0b011);
        assert_domain_call("(сполучити 1 2)", 3, 0b100);
        assert_domain_call("(перше x)", 3, 0b101);
        assert_domain_call("(решта x)", 3, 0b110);
        assert_domain_call("(тотожне? x y)", 3, 0b111);
    }

    #[test]
    fn necessary_forms_lower_to_exact_d4_calls() {
        assert_domain_call("(lambda (x) x)", 4, 0b0010);
        assert_domain_call("(define x 1)", 4, 0b0011);
        assert_domain_call("(def x 1)", 4, 0b0011);
    }

    #[test]
    fn legacy_define_and_lambda_heads_do_not_freeze_migrated_body_calls() {
        let expr = lower_one(
            "(00001001 selector (00001000 (values) (cadr values)))",
        );

        let ExprKind::Call(define_sid, define_args) = expr.kind else {
            panic!("historical DEFINE head must remain compatibility Call");
        };
        assert_eq!(define_sid, crate::sens!(00001001));

        let ExprKind::Call(lambda_sid, lambda_args) = &define_args[1].kind else {
            panic!("historical LAMBDA head must remain compatibility Call");
        };
        assert_eq!(*lambda_sid, crate::sens!(00001000));

        let ExprKind::DomainCall(identity, _) = &lambda_args[1].kind else {
            panic!("migrated CADR body call must become exact DomainCall");
        };
        assert_eq!((identity.width(), identity.packed_bits()), (4, 0b1011));
    }

    #[test]
    fn recursive_legacy_lowering_still_respects_quote_data_boundary() {
        let expr = lower_one(
            "(00001001 quoted (00000001 (cadr values)))",
        );

        let ExprKind::Call(_, define_args) = expr.kind else {
            panic!("historical DEFINE head must remain compatibility Call");
        };
        let ExprKind::Call(quote_sid, quote_args) = &define_args[1].kind else {
            panic!("historical QUOTE head must remain compatibility Call");
        };
        assert_eq!(*quote_sid, crate::sens!(00000001));

        let ExprKind::List(quoted) = &quote_args[0].kind else {
            panic!("quoted form must remain list data");
        };
        assert!(matches!(quoted[0].kind, ExprKind::Symbol(ref name) if name.as_ref() == "cadr"));
    }

    #[test]
    fn explicit_legacy_byte_does_not_infer_a_domain() {
        let expr = lower_one("(00000010 1)");
        match expr.kind {
            ExprKind::Call(sid, _) => assert_eq!(sid.packed_byte(), 0b0000_0010),
            other => panic!("legacy byte must remain compatibility Call, got {other:?}"),
        }
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
