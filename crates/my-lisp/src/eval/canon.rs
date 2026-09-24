//! Immutable evaluator meaning for Canon 0 + McCarthy7.
//!
//! Canon is deliberately *not* an `Environment`. Stable human/symbolic
//! spellings live in `lib/surface/semantic-registry.wsm` and are projected to
//! opaque runtime projections by the shared registry module. This module owns
//! only the finite mapping from exact eight-bit SID identities to canonical
//! evaluator meaning, plus Canon 0.
//!
//! Primitive dispatch may pack a Sid8 into one byte to index a 256-entry table,
//! but that byte is mechanism only; the identity remains the exact bit spelling. Special forms (quote, cond,
//! lambda, define, defmacro, def) are handled before this table in evaluate_list.

use super::special_forms::{atom_value, car_value, cdr_value, cons_values, eq_values};
use super::arithmetic;
use crate::{semantic_registry, Environment, ErrorKind, LanguageError, Sid8, Span, Value};

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

/// The SID is the primary key. `identity` is a human-readable label carried
/// *over* that SID for the rest of this module to match on, not a separate
/// identity SID happens to also have — Canon is a named subset of the SID
/// space, not the other way around.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct CanonEntry {
    pub semantic_id: Sid8,
    pub kind: CanonicalKind,
    pub identity: CanonicalIdentity,
}

pub(crate) const EMPTY_LIST_SEMANTIC_ID: Sid8 = crate::sid!(00000000);
pub(crate) const QUOTE_SEMANTIC_ID: Sid8 = crate::sid!(00000001);
pub(crate) const ATOM_SEMANTIC_ID: Sid8 = crate::sid!(00000010);
pub(crate) const EQ_SEMANTIC_ID: Sid8 = crate::sid!(00000011);
pub(crate) const CONS_SEMANTIC_ID: Sid8 = crate::sid!(00000100);
pub(crate) const CAR_SEMANTIC_ID: Sid8 = crate::sid!(00000101);
pub(crate) const CDR_SEMANTIC_ID: Sid8 = crate::sid!(00000110);
pub(crate) const COND_SEMANTIC_ID: Sid8 = crate::sid!(00000111);

/// Arithmetic primitives (admitted via semantic registry, not Canon 0).
/// Their canonical identities are the exact bit spellings themselves.
pub(crate) const ADD_SEMANTIC_ID: Sid8 = crate::sid!(00001100);
pub(crate) const SUB_SEMANTIC_ID: Sid8 = crate::sid!(00001101);
pub(crate) const MUL_SEMANTIC_ID: Sid8 = crate::sid!(00001110);
pub(crate) const DIV_SEMANTIC_ID: Sid8 = crate::sid!(00001111);

/// Declared in ascending SID order (00000000..00000111) — `identity_for_semantic_id`
/// indexes this array directly by SID byte, so that order is load-bearing,
/// not incidental.
pub(crate) const CANON: [CanonEntry; 8] = [
    CanonEntry {
        semantic_id: EMPTY_LIST_SEMANTIC_ID,
        kind: CanonicalKind::GroundValue,
        identity: CanonicalIdentity::EmptyList,
    },
    CanonEntry {
        semantic_id: QUOTE_SEMANTIC_ID,
        kind: CanonicalKind::SpecialForm,
        identity: CanonicalIdentity::Quote,
    },
    CanonEntry {
        semantic_id: ATOM_SEMANTIC_ID,
        kind: CanonicalKind::ValuePrimitive,
        identity: CanonicalIdentity::Atom,
    },
    CanonEntry {
        semantic_id: EQ_SEMANTIC_ID,
        kind: CanonicalKind::ValuePrimitive,
        identity: CanonicalIdentity::Eq,
    },
    CanonEntry {
        semantic_id: CONS_SEMANTIC_ID,
        kind: CanonicalKind::ValuePrimitive,
        identity: CanonicalIdentity::Cons,
    },
    CanonEntry {
        semantic_id: CAR_SEMANTIC_ID,
        kind: CanonicalKind::ValuePrimitive,
        identity: CanonicalIdentity::Car,
    },
    CanonEntry {
        semantic_id: CDR_SEMANTIC_ID,
        kind: CanonicalKind::ValuePrimitive,
        identity: CanonicalIdentity::Cdr,
    },
    CanonEntry {
        semantic_id: COND_SEMANTIC_ID,
        kind: CanonicalKind::SpecialForm,
        identity: CanonicalIdentity::Cond,
    },
];

/// CANON is declared in exact SID order (index 0 = 00000000 ... index 7 =
/// 00000111), so resolution indexes directly by the SID byte instead of
/// scanning for an equal field — the same mechanism PRIMITIVE_TABLE already
/// uses, now applied to identity resolution too.
pub(crate) fn identity_for_semantic_id(semantic_id: Sid8) -> Option<CanonicalIdentity> {
    let entry = CANON.get(semantic_id.packed_byte() as usize)?;
    debug_assert_eq!(
        entry.semantic_id, semantic_id,
        "CANON must stay declared in ascending SID order for direct indexing to hold"
    );
    Some(entry.identity)
}

fn semantic_id_for_identity(identity: CanonicalIdentity) -> Sid8 {
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
    table[ATOM_SEMANTIC_ID.packed_byte() as usize] = Some(prim_atom);
    table[EQ_SEMANTIC_ID.packed_byte() as usize] = Some(prim_eq);
    table[CONS_SEMANTIC_ID.packed_byte() as usize] = Some(prim_cons);
    table[CAR_SEMANTIC_ID.packed_byte() as usize] = Some(prim_car);
    table[CDR_SEMANTIC_ID.packed_byte() as usize] = Some(prim_cdr);
    table[ADD_SEMANTIC_ID.packed_byte() as usize] = Some(prim_add);
    table[SUB_SEMANTIC_ID.packed_byte() as usize] = Some(prim_sub);
    table[MUL_SEMANTIC_ID.packed_byte() as usize] = Some(prim_mul);
    table[DIV_SEMANTIC_ID.packed_byte() as usize] = Some(prim_div);
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
    semantic_id: Sid8,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if let Some(primitive) = PRIMITIVE_TABLE
        .get(semantic_id.packed_byte() as usize)
        .and_then(|function| *function)
    {
        return primitive(args, environment, span);
    }

    if let Some(result) =
        super::capabilities::dispatch_semantic_capability(semantic_id, args, environment, span)
    {
        return result;
    }

    Err(LanguageError::new(
        ErrorKind::Type,
        format!("unknown semantic callable SID: {semantic_id}"),
        span,
    ))
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
        | CanonicalIdentity::Cdr => Some(Value::Sid(semantic_id_for_identity(identity))),
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
    fn canon_meanings_are_selected_only_by_exact_binary_semantic_identity() {
        assert_eq!(
            identity_for_semantic_id(QUOTE_SEMANTIC_ID),
            Some(CanonicalIdentity::Quote)
        );
        assert_eq!(
            identity_for_semantic_id(CAR_SEMANTIC_ID),
            Some(CanonicalIdentity::Car)
        );
        assert_eq!(identity_for_semantic_id(crate::sid!(00001100)), None);
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
    fn canon_bit_identity_is_the_runtime_value_identity() {
        assert_eq!(
            identity_for_semantic_id(CAR_SEMANTIC_ID),
            Some(CanonicalIdentity::Car)
        );
        let human_surface = semantic_registry::admitted_surfaces_for_semantic_id(CAR_SEMANTIC_ID)
            .into_iter()
            .next()
            .expect("00000101 (car) should admit at least one human surface");
        let direct = value(CanonicalIdentity::Car).expect("binary Canon identity");
        let human = value_for_surface(human_surface).expect("registry-admitted Canon surface");
        assert_eq!(direct, Value::Sid(CAR_SEMANTIC_ID));
        assert_eq!(human, Value::Sid(CAR_SEMANTIC_ID));
        assert_eq!(direct, human);
    }

    #[test]
    fn every_admitted_surface_for_one_semantic_id_materializes_one_sid8_value() {
        let surfaces = semantic_registry::admitted_surfaces_for_semantic_id(CAR_SEMANTIC_ID);
        assert!(
            surfaces.len() >= 2,
            "0005 (car) should admit at least two surfaces for this invariant to be meaningful, \
             got {surfaces:?}"
        );

        for surface in &surfaces {
            assert_eq!(
                value_for_surface(surface),
                Some(Value::Sid(CAR_SEMANTIC_ID)),
                "registry-admitted surface {surface:?} must materialize SID 00000101"
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
        assert_eq!(identity_for_semantic_id(crate::sid!(00001100)), None);
    }

    #[test]
    fn registry_rows_without_canon_meaning_do_not_become_canon() {
        assert_eq!(semantic_registry::semantic_id_for_surface("+"), Some(ADD_SEMANTIC_ID));
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