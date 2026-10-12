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

fn lower_all(items: &[Expr], depth: u32) -> Rc<[Expr]> {
    items.iter().map(|item| lower(item, depth + 1)).collect()
}

/// Lower an already typed or newly discovered domain call in exactly the
/// same way. A quoted datum and a D4 binder are not executable call heads.
fn lower_domain_arguments(
    identity: CoreDomainIdentity,
    arguments: &[Expr],
    depth: u32,
) -> Rc<[Expr]> {
    if is_d3(identity, 0b001) {
        return arguments.into();
    }
    if is_d3(identity, 0b110) {
        return arguments
            .iter()
            .map(|clause| match &clause.kind {
                ExprKind::List(parts) => Expr {
                    kind: ExprKind::List(lower_all(parts, depth + 1)),
                    span: clause.span,
                },
                _ => clause.clone(),
            })
            .collect();
    }
    if necessary_forms::identity_for_domain_identity(identity).is_some() {
        return arguments
            .iter()
            .enumerate()
            .map(|(index, argument)| {
                if index == 0 {
                    argument.clone()
                } else {
                    lower(argument, depth + 1)
                }
            })
            .collect();
    }
    lower_all(arguments, depth)
}

fn lower(expression: &Expr, depth: u32) -> Expr {
    if depth > MAX_STRUCTURE_DEPTH {
        return expression.clone();
    }
    let kind = match &expression.kind {
        ExprKind::Call(sid, arguments) => ExprKind::Call(*sid, arguments.clone()),
        ExprKind::DomainCall(identity, arguments) => {
            ExprKind::DomainCall(*identity, lower_domain_arguments(*identity, arguments, depth))
        }
        ExprKind::List(items) if !items.is_empty() => {
            let arguments = &items[1..];

            if let Some(identity) = head_domain_identity(&items[0]) {
                return Expr {
                    kind: ExprKind::DomainCall(
                        identity,
                        lower_domain_arguments(identity, arguments, depth),
                    ),
                    span: expression.span,
                };
            }

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
mod exact_domain_lowering_tests {
    use super::*;

    /// A partially lowered AST is a valid compiler input. Typed call heads
    /// must not shield their nested domain calls from lowering.
    fn compare_partial_and_source(source: &str) {
        let parsed = crate::parser::parse_exact_domain_source(source)
            .expect("valid current exact-domain source");
        let ExprKind::List(items) = &parsed[0].kind else {
            panic!("top-level call required");
        };
        let ExprKind::DomainIdentity(domain) = items[0].kind else {
            panic!("current domain head required");
        };
        let identity = domain.core_operation().expect("admitted callable domain");
        let partial = Expr {
            kind: ExprKind::DomainCall(identity, items[1..].into()),
            span: parsed[0].span,
        };
        let canonical = lower_program(&parsed);
        let lowered = lower_program(&[partial]);
        assert_eq!(lowered, canonical, "typed and source heads must lower alike");
        assert_eq!(lower_program(&lowered), lowered, "lowering must be idempotent");
    }

    #[test]
    fn nested_d3_calls_are_lowered_under_an_already_typed_head() {
        compare_partial_and_source("(111 (100 (001 000)) (011 (001 000)))");
    }

    #[test]
    fn quote_data_is_not_rewritten_as_executable_domain_calls() {
        compare_partial_and_source("(001 (010 (001 11110111)))");
    }

    #[test]
    fn lambda_binder_stays_data_while_its_body_is_lowered() {
        compare_partial_and_source("(0010 (x) (010 (001 x)))");
    }

    #[test]
    fn cond_clause_structure_and_nested_calls_survive_lowering() {
        compare_partial_and_source("(110 ((001 1) (010 (001 000))))");
    }
}
