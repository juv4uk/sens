//! Immutable evaluator meaning for Canon 0 + McCarthy7.
//!
//! Canon is deliberately *not* an `Environment`. Stable human/symbolic
//! spellings live in `lib/surface/semantic-registry.wsm` and are projected to
//! opaque numeric IDs by the shared registry module. This module owns only the
//! finite mapping from those IDs to canonical evaluator meaning, plus Canon 0.
//!
//! Primitive dispatch is a direct u8-indexed function table. Each SemanticId
//! (0..255) either has a callable primitive or not. Special forms (quote, cond,
//! lambda, define, defmacro, def) are handled before this table in evaluate_list.

use super::special_forms::{atom_value, car_value, cdr_value, cons_values, eq_values};
use super::arithmetic;
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

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum CanonicalKind {
    GroundValue,
    ValuePrimitive,
    SpecialForm,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct CanonEntry {
    pub identity: CanonicalIdentity,
    pub kind: CanonicalKind,
    pub semantic_id: SemanticId,
}

pub(crate) const EMPTY_LIST_SEMANTIC_ID: SemanticId = 0b00000000;
pub(crate) const QUOTE_SEMANTIC_ID: SemanticId = 0b00000001;
pub(crate) const ATOM_SEMANTIC_ID: SemanticId = 0b00000010;
pub(crate) const EQ_SEMANTIC_ID: SemanticId = 0b00000011;
pub(crate) const CONS_SEMANTIC_ID: SemanticId = 0b00000100;
pub(crate) const CAR_SEMANTIC_ID: SemanticId = 0b00000101;
pub(crate) const CDR_SEMANTIC_ID: SemanticId = 0b00000110;
pub(crate) const COND_SEMANTIC_ID: SemanticId = 0b00000111;

/// Arithmetic primitives (admitted via semantic registry, not Canon 0).
/// SID 00001100 = +, 00001101 = -, 00001110 = *, 00001111 = /
pub(crate) const ADD_SEMANTIC_ID: SemanticId = 0b00001100;
pub(crate) const SUB_SEMANTIC_ID: SemanticId = 0b00001101;
pub(crate) const MUL_SEMANTIC_ID: SemanticId = 0b00001110;
pub(crate) const DIV_SEMANTIC_ID: SemanticId = 0b00001111;

/// Canon 00000000 is the empty-list ground object itself.
/// McCarthy7 follow contiguously through 00000111.
pub(crate) const CANON: [CanonEntry; 8] = [
    CanonEntry {
        identity: CanonicalIdentity::EmptyList,
        kind: CanonicalKind::GroundValue,
        semantic_id: EMPTY_LIST_SEMANTIC_ID,
    },
    CanonEntry {
        identity: CanonicalIdentity::Quote,
        kind: CanonicalKind::SpecialForm,
        semantic_id: QUOTE_SEMANTIC_ID,
    },
    CanonEntry {
        identity: CanonicalIdentity::Atom,
        kind: CanonicalKind::ValuePrimitive,
        semantic_id: ATOM_SEMANTIC_ID,
    },
    CanonEntry {
        identity: CanonicalIdentity::Eq,
        kind: CanonicalKind::ValuePrimitive,
        semantic_id: EQ_SEMANTIC_ID,
    },
    CanonEntry {
        identity: CanonicalIdentity::Cons,
        kind: CanonicalKind::ValuePrimitive,
        semantic_id: CONS_SEMANTIC_ID,
    },
    CanonEntry {
        identity: CanonicalIdentity::Car,
        kind: CanonicalKind::ValuePrimitive,
        semantic_id: CAR_SEMANTIC_ID,
    },
    CanonEntry {
        identity: CanonicalIdentity::Cdr,
        kind: CanonicalKind::ValuePrimitive,
        semantic_id: CDR_SEMANTIC_ID,
    },
    CanonEntry {
        identity: CanonicalIdentity::Cond,
        kind: CanonicalKind::SpecialForm,
        semantic_id: COND_SEMANTIC_ID,
    },
];

pub(crate) fn identity_for_semantic_id(semantic_id: SemanticId) -> Option<CanonicalIdentity> {
    CANON
        .iter()
        .find(|entry| entry.semantic_id == semantic_id)
        .map(|entry| entry.identity)
}

fn semantic_id_for_identity(identity: CanonicalIdentity) -> SemanticId {
    CANON
        .iter()
        .find(|entry| entry.identity == identity)
        .map(|entry| entry.semantic_id)
        .expect("every Canon identity has one byte SID")
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

/// Primitive function signature: pre-evaluated args + env + span -> Value.
type PrimitiveFn = fn(&[Value], &Environment, Span) -> Result<Value, LanguageError>;

/// Direct u8-indexed primitive table. SemanticId -> callable or None.
/// Special forms (quote, cond, lambda, define, defmacro, def) are NOT in this table;
/// they are handled in evaluate_list before reaching here.
const PRIMITIVE_TABLE: [Option<PrimitiveFn>; 256] = {
    let mut table: [Option<PrimitiveFn>; 256] = [None; 256];
    table[ATOM_SEMANTIC_ID as usize] = Some(prim_atom);
    table[EQ_SEMANTIC_ID as usize] = Some(prim_eq);
    table[CONS_SEMANTIC_ID as usize] = Some(prim_cons);
    table[CAR_SEMANTIC_ID as usize] = Some(prim_car);
    table[CDR_SEMANTIC_ID as usize] = Some(prim_cdr);
    table[ADD_SEMANTIC_ID as usize] = Some(prim_add);
    table[SUB_SEMANTIC_ID as usize] = Some(prim_sub);
    table[MUL_SEMANTIC_ID as usize] = Some(prim_mul);
    table[DIV_SEMANTIC_ID as usize] = Some(prim_div);
    table
};

fn prim_atom(args: &[Value], _env: &Environment, span: Span) -> Result<Value, LanguageError> {
    exact_args("atom", args, 1, span)?;
    Ok(atom_value(&args[0]))
}

fn prim_eq(args: &[Value], _env: &Environment, span: Span) -> Result<Value, LanguageError> {
    exact_args("eq", args, 2, span)?;
    eq_values(args[0].clone(), args[1].clone(), span)
}

fn prim_cons(args: &[Value], env: &Environment, span: Span) -> Result<Value, LanguageError> {
    exact_args("cons", args, 2, span)?;
    cons_values(args[0].clone(), args[1].clone(), env, span)
}

fn prim_car(args: &[Value], _env: &Environment, span: Span) -> Result<Value, LanguageError> {
    exact_args("car", args, 1, span)?;
    car_value(&args[0], span)
}

fn prim_cdr(args: &[Value], _env: &Environment, span: Span) -> Result<Value, LanguageError> {
    exact_args("cdr", args, 1, span)?;
    cdr_value(&args[0], span)
}

fn prim_add(args: &[Value], env: &Environment, span: Span) -> Result<Value, LanguageError> {
    exact_args("+", args, 2, span)?;
    arithmetic::arithmetic_on_values("+", args, env, span)
}

fn prim_sub(args: &[Value], env: &Environment, span: Span) -> Result<Value, LanguageError> {
    exact_args("-", args, 2, span)?;
    arithmetic::arithmetic_on_values("-", args, env, span)
}

fn prim_mul(args: &[Value], env: &Environment, span: Span) -> Result<Value, LanguageError> {
    exact_args("*", args, 2, span)?;
    arithmetic::arithmetic_on_values("*", args, env, span)
}

fn prim_div(args: &[Value], env: &Environment, span: Span) -> Result<Value, LanguageError> {
    exact_args("/", args, 2, span)?;
    arithmetic::arithmetic_on_values("/", args, env, span)
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
    let Some(primitive) = PRIMITIVE_TABLE.get(semantic_id as usize).and_then(|f| *f) else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            format!("unknown semantic callable SID: {}", semantic_registry::semantic_id_bits(semantic_id)),
            span,
        ));
    };
    primitive(args, environment, span)
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

    #[test]
    fn canon_has_exactly_ground_plus_seven() {
        assert_eq!(CANON.len(), 8);
        assert_eq!(CANON[0].identity, CanonicalIdentity::EmptyList);
        assert_eq!(CANON[0].kind, CanonicalKind::GroundValue);
        assert_eq!(CANON[0].semantic_id, EMPTY_LIST_SEMANTIC_ID);
    }

    #[test]
    fn canon_meanings_are_selected_only_by_numeric_semantic_identity() {
        assert_eq!(
            identity_for_semantic_id(QUOTE_SEMANTIC_ID),
            Some(CanonicalIdentity::Quote)
        );
        assert_eq!(
            identity_for_semantic_id(CAR_SEMANTIC_ID),
            Some(CanonicalIdentity::Car)
        );
        assert_eq!(identity_for_semantic_id(12), None);
    }

    #[test]
    fn every_admitted_surface_for_one_semantic_id_resolves_to_one_identity() {
        // Which spellings mean "car" is a registry FACT, not a Rust literal
        // to enumerate here -- read them from the registry so this test
        // keeps meaning "Canon routes every admitted surface for 0005 to
        // the same identity" even if the admitted spellings change.
        let surfaces = semantic_registry::admitted_surfaces_for_semantic_id(CAR_SEMANTIC_ID);
        assert!(
            surfaces.len() >= 2,
            "0005 (car) should admit at least two surfaces for this invariant to be meaningful, \
             got {surfaces:?}"
        );
        for surface in &surfaces {
            assert_eq!(
                identity_for_surface(surface),
                Some(CanonicalIdentity::Car),
                "registry-admitted surface {surface:?} did not route to CanonicalIdentity::Car"
            );
        }
    }

    #[test]
    fn numeric_canon_identity_is_the_runtime_value_identity() {
        assert_eq!(
            identity_for_semantic_id(CAR_SEMANTIC_ID),
            Some(CanonicalIdentity::Car)
        );
        let human_surface = semantic_registry::admitted_surfaces_for_semantic_id(CAR_SEMANTIC_ID)
            .into_iter()
            .next()
            .expect("00000101 (car) should admit at least one human surface");
        let direct = value(CanonicalIdentity::Car).expect("numeric Canon identity");
        let human = value_for_surface(human_surface).expect("registry-admitted Canon surface");
        assert_eq!(direct, Value::SemanticRef(CAR_SEMANTIC_ID));
        assert_eq!(human, Value::SemanticRef(CAR_SEMANTIC_ID));
        assert_eq!(direct, human);
    }

    #[test]
    fn every_admitted_surface_for_one_semantic_id_materializes_one_semantic_reference() {
        let surfaces = semantic_registry::admitted_surfaces_for_semantic_id(CAR_SEMANTIC_ID);
        assert!(
            surfaces.len() >= 2,
            "0005 (car) should admit at least two surfaces for this invariant to be meaningful, \
             got {surfaces:?}"
        );

        for surface in &surfaces {
            assert_eq!(
                value_for_surface(surface),
                Some(Value::SemanticRef(CAR_SEMANTIC_ID)),
                "registry-admitted surface {surface:?} must materialize semantic identity 0005"
            );
        }
    }

    #[test]
    fn semantic_ids_control_canon_routing() {
        assert_eq!(
            identity_for_semantic_id(QUOTE_SEMANTIC_ID),
            Some(CanonicalIdentity::Quote)
        );
        assert_eq!(
            identity_for_semantic_id(CAR_SEMANTIC_ID),
            Some(CanonicalIdentity::Car)
        );
        assert_eq!(identity_for_semantic_id(12), None);
    }

    #[test]
    fn registry_rows_without_canon_meaning_do_not_become_canon() {
        assert_eq!(semantic_registry::semantic_id_for_surface("+"), Some(12));
        assert_eq!(identity_for_surface("+"), None);
    }

    #[test]
    fn canonical_surface_names_are_reserved() {
        for name in [
            "quote", "як-є", "svarūpa", "atom", "атом?", "aṇu", "eq", "тотожне?",
            "abheda", "cons", "сполучити", "saṃyuj", "car", "перше", "ādi", "cdr",
            "решта", "śeṣa", "cond", "за-умовою", "anukrama",
        ] {
            assert!(is_reserved_surface(name), "Canon spelling must be reserved: {name}");
        }
        assert!(!is_reserved_surface("map"));
        assert!(!is_reserved_surface("відобразити"));
    }

    #[test]
    fn empty_list_is_a_value_not_a_primitive_operation() {
        assert_eq!(ground_value(CanonicalIdentity::EmptyList), Some(Value::Nil));
        assert!(value(CanonicalIdentity::Quote).is_none());
        assert!(value(CanonicalIdentity::Cond).is_none());
    }
}