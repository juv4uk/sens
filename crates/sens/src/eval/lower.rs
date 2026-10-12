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

/// Звести всі виклики програми. Ідемпотентно: `Call` лишається `Call`.
pub fn lower_program(expressions: &[Expr]) -> Vec<Expr> {
    expressions.iter().map(|expression| lower(expression, 0)).collect()
}

fn head_domain_identity(head: &Expr) -> Option<CoreDomainIdentity> {
    match &head.kind {
        ExprKind::DomainIdentity(identity) => identity.core_operation(),
        ExprKind::Symbol(name) => immutable_surface_domain_identity(name),
        _ => None,
    }
}

/// The source-surface → exact-domain projection boundary, shared by lowering
/// and immutable-binding checks. Never reconstruct an historical eight-bit ID.
pub(crate) fn immutable_surface_domain_identity(name: &str) -> Option<CoreDomainIdentity> {
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

/// Історичний W8 не є D8. Лише явно доведена в реєстрі відповідність
/// людської поверхні до ратифікованої D3 дозволяє сумісну спеціальну форму.
fn historical_head_has_d3_law(sid: Sens8, bits: u8) -> bool {
    semantic_registry::compatibility_d3_route_from_ratified_domains(sid)
        .is_some_and(|identity| is_d3(identity, bits))
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
                return Expr {
                    kind: if is_d3(identity, 0b001) {
                        ExprKind::DomainCall(identity, arguments.into())
                    } else if is_d3(identity, 0b110) {
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
                    },
                    span: expression.span,
                };
            }

            match head_sid(&items[0]) {
                Some(sid) if historical_head_has_d3_law(sid, 0b001) => ExprKind::Call(sid, arguments.into()),
                Some(sid) if historical_head_has_d3_law(sid, 0b110) => ExprKind::Call(
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
mod domain_ladder_lowering_migration_tests {
    use super::*;

    fn lowered_one(source: &str) -> Expr {
        let parsed = crate::parse(source).expect("чинний читач");
        let lowered = lower_program(&parsed);
        assert_eq!(lowered.len(), 1);
        lowered.into_iter().next().expect("одна форма")
    }

    #[test]
    fn historical_quote_uses_ratified_d3_law_and_preserves_quoted_data() {
        let lowered = lowered_one("(00000001 (00000101 x))");
        let ExprKind::Call(_, args) = lowered.kind else {
            panic!("історична сумісна форма QUOTE має залишатися явно W8");
        };
        assert_eq!(args.len(), 1);
        let ExprKind::List(items) = &args[0].kind else {
            panic!("дані після QUOTE не виконуються");
        };
        assert!(matches!(items[0].kind, ExprKind::Sid(_)));
    }

    #[test]
    fn historical_cond_uses_ratified_d3_law_only_for_clause_expressions() {
        let lowered = lowered_one("(00000111 ((00000101 x) (00000001 (00000101 y))))");
        let ExprKind::Call(_, clauses) = lowered.kind else {
            panic!("історична сумісна форма COND залишається явно W8");
        };
        let ExprKind::List(parts) = &clauses[0].kind else {
            panic!("клаузи COND є структурними");
        };
        assert!(matches!(parts[0].kind, ExprKind::Call(_, _)));
        let ExprKind::Call(_, quoted) = &parts[1].kind else {
            panic!("QUOTE усередині клаузи зберігається");
        };
        assert!(matches!(quoted[0].kind, ExprKind::List(_)));
    }

    #[test]
    fn unrelated_legacy_head_never_becomes_a_d3_quote_or_cond() {
        for source in ["(00001000 x)", "(10101000 x)"] {
            let lowered = lowered_one(source);
            let ExprKind::Call(_, _) = lowered.kind else {
                panic!("старий байт не отримує новий домен за збігом значення");
            };
        }
    }
}
