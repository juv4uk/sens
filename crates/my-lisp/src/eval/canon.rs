//! Immutable evaluator meaning for Canon 0 + McCarthy7.
//!
//! Canon is deliberately *not* an `Environment`. Stable human/symbolic
//! spellings live in the semantic registry and SID-to-operation classification
//! lives in `lib/evaluator-dispatch.lisp`. This Rust module only maps the
//! Lisp-selected operation class onto concrete evaluator mechanisms.

use super::{
    evaluator_dispatch_generated::{self as dispatch, EvaluatorMechanism},
    special_forms::{atom_value, car_value, cdr_value, cons_values, eq_values},
};
use crate::{semantic_registry, Environment, ErrorKind, LanguageError, Span, Value};
use crate::semantic_registry::SemanticId;

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub(crate) enum CanonicalIdentity {
    EmptyList,
    Quote,
    Atom,
    Eq,
    Cons,
    Car,
    Cdr,
    Cond,
}

fn canonical_identity_for_mechanism(
    mechanism: EvaluatorMechanism,
) -> Option<CanonicalIdentity> {
    match mechanism {
        EvaluatorMechanism::EmptyListGround => Some(CanonicalIdentity::EmptyList),
        EvaluatorMechanism::QuoteForm => Some(CanonicalIdentity::Quote),
        EvaluatorMechanism::AtomPrimitive => Some(CanonicalIdentity::Atom),
        EvaluatorMechanism::EqPrimitive => Some(CanonicalIdentity::Eq),
        EvaluatorMechanism::ConsPrimitive => Some(CanonicalIdentity::Cons),
        EvaluatorMechanism::CarPrimitive => Some(CanonicalIdentity::Car),
        EvaluatorMechanism::CdrPrimitive => Some(CanonicalIdentity::Cdr),
        EvaluatorMechanism::CondForm => Some(CanonicalIdentity::Cond),
        EvaluatorMechanism::LambdaForm | EvaluatorMechanism::DefineForm => None,
    }
}

fn mechanism_for_identity(identity: CanonicalIdentity) -> EvaluatorMechanism {
    match identity {
        CanonicalIdentity::EmptyList => EvaluatorMechanism::EmptyListGround,
        CanonicalIdentity::Quote => EvaluatorMechanism::QuoteForm,
        CanonicalIdentity::Atom => EvaluatorMechanism::AtomPrimitive,
        CanonicalIdentity::Eq => EvaluatorMechanism::EqPrimitive,
        CanonicalIdentity::Cons => EvaluatorMechanism::ConsPrimitive,
        CanonicalIdentity::Car => EvaluatorMechanism::CarPrimitive,
        CanonicalIdentity::Cdr => EvaluatorMechanism::CdrPrimitive,
        CanonicalIdentity::Cond => EvaluatorMechanism::CondForm,
    }
}

fn identity_for_semantic_id(semantic_id: SemanticId) -> Option<CanonicalIdentity> {
    dispatch::EVALUATOR_DISPATCH
        .iter()
        .find(|row| row.semantic_id == semantic_id)
        .and_then(|row| canonical_identity_for_mechanism(row.mechanism))
}

fn semantic_id_for_identity(identity: CanonicalIdentity) -> SemanticId {
    let mechanism = mechanism_for_identity(identity);
    dispatch::EVALUATOR_DISPATCH
        .iter()
        .find(|row| row.mechanism == mechanism)
        .map(|row| row.semantic_id)
        .expect("every Canon mechanism must be projected from Lisp-owned evaluator dispatch")
}

pub(crate) fn identity_for_surface(name: &str) -> Option<CanonicalIdentity> {
    semantic_registry::semantic_id_for_surface(name).and_then(identity_for_semantic_id)
}

pub(crate) fn is_reserved_surface(name: &str) -> bool {
    identity_for_surface(name).is_some()
}

/// True for any admitted surface of `quote` specifically (semantic ID 1) —
/// `quote`/`як-є`/`svarūpa`/`'`, not just the English spelling.
/// Exposed narrowly via `crate::is_quote_surface_name` for tooling that
/// must distinguish "this list's head is quote" from "this list's head is
/// some other Canon identity," per the same routing every surface already
/// shares.
pub(crate) fn is_quote_identity(name: &str) -> bool {
    identity_for_surface(name) == Some(CanonicalIdentity::Quote)
}

pub(crate) fn ensure_bindable(name: &str, span: Span) -> Result<(), LanguageError> {
    let Some(identity) = identity_for_surface(name) else {
        return Ok(());
    };
    Err(LanguageError::new(
        ErrorKind::InvalidForm,
        format!(
            "canonical name is immutable · канонічне ім'я незмінне · kanonischer Name ist unveränderlich: {name} -> {identity:?}"
        ),
        span,
    ))
}

pub(crate) fn ground_value(identity: CanonicalIdentity) -> Option<Value> {
    match identity {
        CanonicalIdentity::EmptyList => Some(Value::Nil),
        _ => None,
    }
}

fn exact_args(
    identity: &'static str,
    args: &[Value],
    expected: usize,
    span: Span,
) -> Result<(), LanguageError> {
    if args.len() == expected {
        return Ok(());
    }
    Err(LanguageError::new(
        ErrorKind::Arity,
        format!(
            "{identity}: expected / ochikuvalosia / erwartet {expected}; received / otrymano / erhalten {}",
            args.len()
        ),
        span,
    ))
}

/// Invoke the current implementation projection for a semantic callable.
///
/// The semantic ID is the language identity. This function is only the
/// execution bridge from that identity to today's Rust mechanism; another
/// backend may replace the projection without changing the value identity.
pub(crate) fn invoke_semantic_ref(
    semantic_id: SemanticId,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    let Some(identity) = identity_for_semantic_id(semantic_id) else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            format!("unknown semantic callable SID: {}", semantic_registry::semantic_id_bits(semantic_id)),
            span,
        ));
    };

    match identity {
        CanonicalIdentity::Atom => {
            exact_args("PRIM_ATOM", args, 1, span)?;
            Ok(atom_value(&args[0]))
        }
        CanonicalIdentity::Eq => {
            exact_args("PRIM_EQ", args, 2, span)?;
            eq_values(args[0].clone(), args[1].clone(), span)
        }
        CanonicalIdentity::Cons => {
            exact_args("PRIM_CONS", args, 2, span)?;
            cons_values(args[0].clone(), args[1].clone(), environment, span)
        }
        CanonicalIdentity::Car => {
            exact_args("PRIM_CAR", args, 1, span)?;
            car_value(&args[0], span)
        }
        CanonicalIdentity::Cdr => {
            exact_args("PRIM_CDR", args, 1, span)?;
            cdr_value(&args[0], span)
        }
        CanonicalIdentity::EmptyList | CanonicalIdentity::Quote | CanonicalIdentity::Cond => {
            Err(LanguageError::new(
                ErrorKind::Type,
                format!("semantic identity is not a callable value: {}", semantic_registry::semantic_id_bits(semantic_id)),
                span,
            ))
        }
    }
}

/// Return the first-class semantic value for a canonical identity. Special
/// forms deliberately have no value representation; they remain syntax-only.
pub(crate) fn value(identity: CanonicalIdentity) -> Option<Value> {
    match identity {
        CanonicalIdentity::EmptyList => Some(Value::Nil),
        CanonicalIdentity::Atom
        | CanonicalIdentity::Eq
        | CanonicalIdentity::Cons
        | CanonicalIdentity::Car
        | CanonicalIdentity::Cdr => Some(Value::SemanticRef(semantic_id_for_identity(identity))),
        CanonicalIdentity::Quote | CanonicalIdentity::Cond => None,
    }
}

pub(crate) fn value_for_surface(name: &str) -> Option<Value> {
    identity_for_surface(name).and_then(value)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn canon_identities() -> [CanonicalIdentity; 8] {
        [
            CanonicalIdentity::EmptyList,
            CanonicalIdentity::Quote,
            CanonicalIdentity::Atom,
            CanonicalIdentity::Eq,
            CanonicalIdentity::Cons,
            CanonicalIdentity::Car,
            CanonicalIdentity::Cdr,
            CanonicalIdentity::Cond,
        ]
    }

    #[test]
    fn canon_has_exactly_ground_plus_seven_in_lisp_owned_dispatch() {
        let projected = dispatch::EVALUATOR_DISPATCH
            .iter()
            .filter_map(|row| {
                canonical_identity_for_mechanism(row.mechanism)
                    .map(|identity| (row.semantic_id, identity))
            })
            .collect::<Vec<_>>();

        assert_eq!(projected.len(), 8);
        for identity in canon_identities() {
            assert!(
                projected.iter().any(|(_, candidate)| *candidate == identity),
                "Lisp-owned evaluator dispatch must project every Canon identity: {identity:?}"
            );
        }
    }

    #[test]
    fn canon_meanings_are_selected_only_by_projected_semantic_identity() {
        for identity in canon_identities() {
            let semantic_id = semantic_id_for_identity(identity);
            assert_eq!(identity_for_semantic_id(semantic_id), Some(identity));
        }

        let lambda_id = semantic_registry::semantic_id_for_surface("lambda")
            .expect("lambda must remain a registry identity");
        assert_eq!(identity_for_semantic_id(lambda_id), None);
    }

    #[test]
    fn every_admitted_surface_for_car_resolves_to_projected_identity() {
        let car_id = semantic_id_for_identity(CanonicalIdentity::Car);
        let surfaces = semantic_registry::admitted_surfaces_for_semantic_id(car_id);
        assert!(
            surfaces.len() >= 2,
            "car should admit peer surfaces for this invariant to be meaningful, got {surfaces:?}"
        );
        for surface in &surfaces {
            assert_eq!(
                identity_for_surface(surface),
                Some(CanonicalIdentity::Car),
                "registry-admitted surface {surface:?} did not route to projected Car mechanism"
            );
        }
    }

    #[test]
    fn projected_canon_identity_is_the_runtime_value_identity() {
        let car_id = semantic_id_for_identity(CanonicalIdentity::Car);
        let human_surface = semantic_registry::admitted_surfaces_for_semantic_id(car_id)
            .into_iter()
            .next()
            .expect("projected car identity should admit at least one human surface");
        let direct = value(CanonicalIdentity::Car).expect("projected Canon identity");
        let human = value_for_surface(human_surface).expect("registry-admitted Canon surface");

        assert_eq!(direct, Value::SemanticRef(car_id));
        assert_eq!(human, Value::SemanticRef(car_id));
        assert_eq!(direct, human);
    }

    #[test]
    fn every_admitted_surface_materializes_one_projected_semantic_reference() {
        let car_id = semantic_id_for_identity(CanonicalIdentity::Car);
        let surfaces = semantic_registry::admitted_surfaces_for_semantic_id(car_id);

        for surface in &surfaces {
            assert_eq!(
                value_for_surface(surface),
                Some(Value::SemanticRef(car_id)),
                "registry-admitted surface {surface:?} must materialize its projected Binary SID"
            );
        }
    }

    #[test]
    fn unrelated_registry_rows_do_not_gain_canon_meaning() {
        let plus_id = semantic_registry::semantic_id_for_surface("+")
            .expect("+ must remain an admitted registry surface");
        assert_eq!(identity_for_semantic_id(plus_id), None);
        assert_eq!(identity_for_surface("+"), None);
    }

    #[test]
    fn all_registry_surfaces_of_projected_canon_identities_are_reserved() {
        for identity in canon_identities().into_iter().filter(|identity| {
            *identity != CanonicalIdentity::EmptyList
        }) {
            let semantic_id = semantic_id_for_identity(identity);
            let surfaces = semantic_registry::admitted_surfaces_for_semantic_id(semantic_id);
            assert!(
                !surfaces.is_empty(),
                "projected Canon identity {identity:?} should have admitted registry surfaces"
            );
            for surface in surfaces {
                assert!(
                    is_reserved_surface(surface),
                    "registry surface {surface:?} for {identity:?} must stay immutable"
                );
            }
        }

        assert!(!is_reserved_surface("map"));
    }

    #[test]
    fn empty_list_is_a_value_not_a_primitive_operation() {
        assert_eq!(ground_value(CanonicalIdentity::EmptyList), Some(Value::Nil));
        assert!(value(CanonicalIdentity::Quote).is_none());
        assert!(value(CanonicalIdentity::Cond).is_none());
    }
}
