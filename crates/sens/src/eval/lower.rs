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
            semantic_registry::d6_uk_source_identity(name)
                .and_then(|identity| match identity {
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
                    kind: ExprKind::DomainIdentity(crate::DomainIdentity::from_source_word(word.word)),
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

#[cfg(test)]
mod ratified_d9_string_surface_tests {
    use super::*;

    #[test]
    fn ukr_string_append_uses_real_d9_110011110_not_legacy_w8() {
        let source = "(рядок-додати \"Привіт, \" \"світе\")";
        let parsed = crate::parse(source).expect("канонічна українська Lisp-форма");
        let lowered = lower_program(&parsed);
        assert!(
            matches!(&lowered[0].kind,
                ExprKind::DomainCall(crate::CoreDomainIdentity::D9(word), args)
                    if word.word().packed_bits() == 0b110011110 && args.len() == 2
            ),
            "D9 call must have exact nine-bit identity without an old SID8 row"
        );
        assert_eq!(
            lower_program(&lowered),
            lowered,
            "D9 source lowering is idempotent"
        );

        let result = crate::eval_parsed_expressions(&parsed, &mut crate::Session::default())
            .expect("реальний D9 механізм складає обидва Unicode рядки");
        assert_eq!(result.value, crate::Value::String("Привіт, світе".into()));
    }

    #[test]
    fn nested_canonical_d9_append_keeps_both_editor_selection_fragments() {
        let source = "(рядок-додати \"[\" (рядок-додати \"їжак\" \"]\"))";
        let parsed = crate::parse(source).expect("два вкладені D9 виклики");
        let result = crate::eval_parsed_expressions(&parsed, &mut crate::Session::default())
            .expect("вкладений D9 рядок-додати реально виконується");
        assert_eq!(result.value, crate::Value::String("[їжак]".into()));

        let short = crate::parse("(рядок-додати \"тільки один\")").unwrap();
        assert!(
            crate::eval_parsed_expressions(&short, &mut crate::Session::default()).is_err(),
            "не підміняти D9 виклик мовчазним поверненням останнього аргументу"
        );
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
        assert_eq!(
            lowered, canonical,
            "typed and source heads must lower alike"
        );
        assert_eq!(
            lower_program(&lowered),
            lowered,
            "lowering must be idempotent"
        );
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

#[cfg(test)]
mod domain_ladder_lowering_migration_tests {
    use super::*;

    fn lowered_one(source: &str) -> Expr {
        let parsed = crate::parse(source).expect("сумісний читач");
        lower_program(&parsed)
            .into_iter()
            .next()
            .expect("одна форма")
    }

    #[test]
    fn ukr_equal_source_head_keeps_its_ratified_d8_identity() {
        let identity = source_head_domain_identity("однакові?")
            .expect("ratified Ukrainian D8 EQUAL source route");
        assert_eq!(identity.width(), 8, "D8 must not collapse to D3 EQ");
        assert_eq!(identity.packed_bits(), 0b11110111, "exact D8 EQUAL word");
    }

    #[test]
    fn source_heads_preserve_exact_d6_identity_for_lisp_owned_definitions() {
        for (name, bits) in [
            ("довжина", 0b000000u16),
            ("довжина-до", 0b000001u16),
            ("нехай*", 0b001001u16),
            ("нехай-послідовно", 0b001001u16),
        ] {
            let identity = source_head_domain_identity(name)
                .unwrap_or_else(|| panic!("ratified Ukrainian D6 binding must lower: {name}"));
            assert_eq!(identity.width(), 6, "{name} must retain D6 width");
            assert_eq!(identity.packed_bits(), bits, "{name} exact D6 coordinate");
        }

        // Non-Ukrainian peer names are metadata, not Ukrainian source heads.
        for name in ["length", "let*", "krama-sthānika-bandha"] {
            assert!(source_head_domain_identity(name).is_none(), "{name} is not a Ukrainian source head");
        }
    }

    #[test]
    fn raw_eight_bit_tokens_do_not_gain_historical_callability() {
        for source in [
            "(00000001 x)",
            "(00000111 x)",
            "(00001000 x)",
            "(10101000 x)",
        ] {
            let lowered = lowered_one(source);
            assert!(
                !matches!(lowered.kind, ExprKind::Call(_, _)),
                "raw token unexpectedly became a call head: {source}"
            );
        }
    }
}

#[cfg(test)]
mod exact_lowering_isolation_tests {
    use super::*;

    fn lower_current(source: &str) -> Expr {
        let parsed =
            crate::parser::parse_exact_domain_source(source).expect("explicit exact-width source");
        lower_exact_domain_program(&parsed)
            .into_iter()
            .next()
            .expect("one expression")
    }

    #[test]
    fn exact_def_compatibility_surface_lowers_to_ratified_d4_binder() {
        let current = lower_current("(визначити x (001 1))");
        let ExprKind::DomainCall(CoreDomainIdentity::D4(word), arguments) = current.kind else {
            panic!("Lisp-owned def compatibility surface must lower to D4 DEFINE");
        };
        assert_eq!(word.word().packed_bits(), 0b0011);
        assert!(matches!(
            &arguments[1].kind,
            ExprKind::DomainCall(CoreDomainIdentity::D3(_), _)
        ));
    }

    #[test]
    fn exact_lowering_preserves_text7_references_instead_of_calling_the_first_glyph() {
        let current = lower_current("(визначити кодування-число-нуль число-нуль)");
        let ExprKind::DomainCall(CoreDomainIdentity::D4(word), arguments) = current.kind else {
            panic!("the exact Ukrainian DEFINE head must remain D4");
        };
        assert_eq!(word.word().packed_bits(), 0b0011);
        let ExprKind::List(glyphs) = &arguments[1].kind else {
            panic!("a Text7 name reference must remain a framed D2 list");
        };
        assert!(!glyphs.is_empty());
        assert!(
            glyphs.iter().all(|glyph| matches!(
                &glyph.kind,
                ExprKind::DomainIdentity(crate::DomainIdentity::D7(_))
            )),
            "the symbol's characters must remain D7 data, not a D7 DomainCall"
        );

        let call = lower_current("(число-нуль)");
        let ExprKind::List(items) = call.kind else {
            panic!("a D2 Text7 call head must remain a contextual list");
        };
        assert!(
            matches!(
                items.first().map(|head| &head.kind),
                Some(ExprKind::List(glyphs))
                    if !glyphs.is_empty()
                        && glyphs.iter().all(|glyph| matches!(
                &glyph.kind,
                            ExprKind::DomainIdentity(crate::DomainIdentity::D7(_))
                        ))
            ),
            "the full identifier, not its first D7 glyph, selects the binding"
        );
    }

    #[test]
    fn exact_d4_lambda_and_d3_quote_preserve_their_widths() {
        let current = lower_current("(0010 (x) (001 (00000001 x)))");
        let ExprKind::DomainCall(CoreDomainIdentity::D4(word), arguments) = current.kind else {
            panic!("exact D4 lambda");
        };
        assert_eq!(word.word().packed_bits(), 0b0010);
        let ExprKind::DomainCall(CoreDomainIdentity::D3(quote), quoted) = &arguments[1].kind else {
            panic!("D3 quote");
        };
        assert_eq!(quote.word().packed_bits(), 0b001);
        assert!(matches!(&quoted[0].kind, ExprKind::List(items)
            if matches!(&items[0].kind, ExprKind::DomainIdentity(identity)
                if identity.width() == 8 && identity.packed_bits() == 0b00000001)));
    }

    #[test]
    fn exact_lowering_remains_idempotent_with_nested_calls() {
        let parsed =
            crate::parser::parse_exact_domain_source("(111 (100 (001 000)) (011 (001 000)))")
                .unwrap();
        let lowered = lower_exact_domain_program(&parsed);
        assert_eq!(lower_exact_domain_program(&lowered), lowered);
    }
}
