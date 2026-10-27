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
use std::rc::Rc;

#[derive(Clone, Copy, Eq, PartialEq)]
enum LowerMode {
    Historical,
    ExactDomain,
}

/// Legacy source only: W8 compatibility does not confer canonical D8 identity.
pub fn lower_program(expressions: &[Expr]) -> Vec<Expr> {
    expressions
        .iter()
        .map(|expression| lower(expression, 0, LowerMode::Historical))
        .collect()
}

/// Exact D1–D9 source: no W8 fallback from bytes or historical surfaces.
pub(crate) fn lower_exact_domain_program(expressions: &[Expr]) -> Vec<Expr> {
    expressions
        .iter()
        .map(|expression| lower(expression, 0, LowerMode::ExactDomain))
        .collect()
}

fn head_domain_identity(head: &Expr, mode: LowerMode) -> Option<CoreDomainIdentity> {
    match &head.kind {
        ExprKind::DomainIdentity(identity) => identity.core_operation(),
        ExprKind::Symbol(name) if mode == LowerMode::ExactDomain => {
            source_head_domain_identity(name)
        }
        ExprKind::Symbol(name) => source_head_domain_identity(name),
        _ => None,
    }
}

/// Resolve a *call head* through the exact Ukrainian source projection first.
/// This is deliberately separate from immutable-binding checks: choosing the
/// exact call route must not silently change which Lisp definitions are bindable.
fn source_head_domain_identity(name: &str) -> Option<CoreDomainIdentity> {
    // Reject non-Ukrainian D6 metadata before all other resolvers. In particular,
    // necessary-form lookup must not re-admit the English `let*` peer ahead of
    // the D6-specific `ук`/`укр` source-head contract.
    if semantic_registry::d6_non_uk_peer_source_name(name) {
        return None;
    }
    necessary_forms::domain_identity_for_symbol(name)
        .or_else(|| {
            // D6 Lisp-owned definitions may be source heads when their exact
            // canonical Ukrainian name is present in the generated D6 binding
            // table. Do this before the primitive-callable index, which does
            // not itself enumerate all Lisp-owned D6 closures.
            semantic_registry::d6_uk_source_identity(name).and_then(|identity| match identity {
                // Convert the explicit D6 coordinate, not the wrapper
                // DomainIdentity. Only this exact width has a CoreD6
                // representation; other variants stay non-routable here.
                crate::DomainIdentity::D6(word) => Some(CoreDomainIdentity::D6(word)),
                _ => None,
            })
        })
        .or_else(|| {
            let identity = semantic_registry::exact_uk_callable_for_source_head(name)?;
            // Lisp-owned D6 bindings are handled by the explicit canonical
            // Ukrainian route above. This index admits only concrete core
            // operations or selector routes that already expose one.
            identity.core_operation()
        })
        .or_else(|| {
            let identity = semantic_registry::domain_identity_for_surface(name)?;
            // D6 source heads are restricted to the exact Ukrainian uk/ukr
            // spelling admitted by the generated Lisp-owned binding table.
            // Otherwise this broad surface fallback would undo the negative
            // alias checks above for English and Sanskrit D6 metadata.
            if matches!(identity, CoreDomainIdentity::D6(_))
                && semantic_registry::d6_uk_source_identity(name).is_none()
            {
                return None;
            }
            Some(identity)
        })
}

/// Binding identity is intentionally unchanged by the source-head routing fix.
/// Never reconstruct an historical eight-bit ID.
pub(crate) fn immutable_surface_domain_identity(name: &str) -> Option<CoreDomainIdentity> {
    necessary_forms::domain_identity_for_symbol(name)
        .or_else(|| semantic_registry::domain_identity_for_surface(name))
}

fn head_sid(head: &Expr) -> Option<CoreDomainIdentity> {
    match &head.kind {
        ExprKind::Sid(sid) => Some(*sid),
        ExprKind::Symbol(name) => immutable_surface_sid(name),
        _ => None,
    }
}

/// Написання, що маршрутизується до фіксованого SENS (не окрема identity).
fn immutable_surface_sid(name: &str) -> Option<CoreDomainIdentity> {
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

/// Сумісна голова W8 одержує закон лише через доказову D3-проєкцію.
fn historical_head_has_d3_law(sid: CoreDomainIdentity, bits: u8) -> bool {
    semantic_registry::compatibility_d3_route_from_ratified_domains(sid)
        .is_some_and(|identity| is_d3(identity, bits))
}

fn lower_all(items: &[Expr], depth: u32, mode: LowerMode) -> Rc<[Expr]> {
    items
        .iter()
        .map(|item| lower(item, depth + 1, mode))
        .collect()
}

/// Lower an already typed or newly discovered domain call in exactly the
/// same way. A quoted datum and a D4 binder are not executable call heads.
fn lower_domain_arguments(
    identity: CoreDomainIdentity,
    arguments: &[Expr],
    depth: u32,
    mode: LowerMode,
) -> Rc<[Expr]> {
    if is_d3(identity, 0b001) {
        return arguments.into();
    }
    if is_d3(identity, 0b110) {
        return arguments
            .iter()
            .map(|clause| match &clause.kind {
                ExprKind::List(parts) => Expr {
                    kind: ExprKind::List(lower_all(parts, depth + 1, mode)),
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
                    lower(argument, depth + 1, mode)
                }
            })
            .collect();
    }
    lower_all(arguments, depth, mode)
}

/// Preserve historical QUOTE/COND/binder argument shape while continuing
/// staged lowering inside an already-typed legacy call. This is a compatibility
/// mechanism only: no W8 word is promoted to current D8 or admitted by payload.
fn lower_historical_arguments(
    sid: CoreDomainIdentity,
    arguments: &[Expr],
    depth: u32,
    mode: LowerMode,
) -> Rc<[Expr]> {
    if historical_head_has_d3_law(sid, 0b001) {
        return arguments.into();
    }
    if historical_head_has_d3_law(sid, 0b110) {
        return arguments
            .iter()
            .map(|clause| match &clause.kind {
                ExprKind::List(parts) => Expr {
                    kind: ExprKind::List(lower_all(parts, depth + 1, mode)),
                    span: clause.span,
                },
                _ => clause.clone(),
            })
            .collect();
    }
    if necessary_forms::identity_for_semantic_id(sid).is_some() {
        return arguments
            .iter()
            .enumerate()
            .map(|(index, argument)| {
                if index == 0 {
                    argument.clone()
                } else {
                    lower(argument, depth + 1, mode)
                }
            })
            .collect();
    }
    lower_all(arguments, depth, mode)
}

fn lower(expression: &Expr, depth: u32, mode: LowerMode) -> Expr {
    if depth > MAX_STRUCTURE_DEPTH {
        return expression.clone();
    }
    let kind = match &expression.kind {
        ExprKind::Call(sid, arguments) if mode == LowerMode::Historical => ExprKind::Call(
            *sid,
            lower_historical_arguments(*sid, arguments, depth, mode),
        ),
        // Exact-domain lowering never interprets a pre-existing historical
        // Call as an admitted current-domain operation.
        ExprKind::Call(sid, arguments) => ExprKind::Call(*sid, arguments.clone()),
        ExprKind::DomainCall(identity, arguments) => ExprKind::DomainCall(
            *identity,
            lower_domain_arguments(*identity, arguments, depth, mode),
        ),
        // In exact-domain source a D2/W7 Text7 identifier is an atomic name,
        // not a call whose first D7 glyph becomes executable. Preserve the
        // framed token for the evaluator's contextual binding lookup.
        ExprKind::List(items)
            if !items.is_empty()
                && mode == LowerMode::ExactDomain
                && crate::canonical_reader::text7_binding_key(expression).is_some() =>
        {
            expression.kind.clone()
        }
        ExprKind::List(items) if !items.is_empty() => {
            let arguments = &items[1..];

            if let Some(identity) = head_domain_identity(&items[0], mode) {
                return Expr {
                    kind: ExprKind::DomainCall(
                        identity,
                        lower_domain_arguments(identity, arguments, depth, mode),
                    ),
                    span: expression.span,
                };
            }

            // Canonical D9 string mechanism is not CoreDomainIdentity
            // (D3-D6). Qualify *only* the ratified Ukrainian head and
            // *only* if its exact D9 law has an installed evaluator mechanism.
            // The text remains a projection, never an historical W8 byte.
            if let ExprKind::Symbol(head) = &items[0].kind {
                if let Some(identity) = semantic_registry::d9_uk_source_identity(head)
                    .filter(|identity| canon::has_d9_mechanism(*identity))
                {
                    // D9 here has an explicitly admitted resident mechanism.
                    // Lower once to its typed call, not to an intermediate
                    // List(D9 head) that changes on a second lowering pass.
                    let core = identity
                        .core_operation()
                        .expect("admitted D9 string identity keeps its exact core carrier");
                    return Expr {
                        kind: ExprKind::DomainCall(
                            core,
                            lower_domain_arguments(core, arguments, depth, mode),
                        ),
                        span: expression.span,
                    };
                }
            }

            // Exact source must not consult a flat historical W8 registry.
            if mode == LowerMode::ExactDomain {
                return Expr {
                    kind: ExprKind::List(lower_all(items, depth, mode)),
                    span: expression.span,
                };
            }

            match head_sid(&items[0]) {
                Some(sid) => {
                    ExprKind::Call(sid, lower_historical_arguments(sid, arguments, depth, mode))
                }
                None => ExprKind::List(lower_all(items, depth, mode)),
            }
        }
        ExprKind::Symbol(name) if mode == LowerMode::ExactDomain => {
            let Some(text) = crate::encode_text7(name, crate::Text7Layout::Uk).ok() else {
                return expression.clone();
            };
            let mut glyphs = Vec::with_capacity(text.cells().len());
            for cell in text.cells() {
                let bits = format!("{:07b}", cell);
                let Ok(words) = crate::parse_binary_source_words(&bits) else {
                    return expression.clone();
                };
                let Some(word) = words.first() else {
                    return expression.clone();
                };
                glyphs.push(Expr {
                    kind: ExprKind::DomainIdentity(crate::DomainIdentity::from_source_word(
                        word.word,
                    )),
                    span: expression.span,
                });
            }
            ExprKind::List(Rc::from(glyphs.into_boxed_slice()))
        }
        _ => return expression.clone(),
    };
    Expr {
        kind,
        span: expression.span,
    }
}
