//! SID-keyed evaluator mechanism routing.
//!
//! Contract 9 / #1325: function identity is only Sid8. This module may record
//! mechanism shape for an already-selected SID, but it must never invent a
//! second named function identity.

use super::{
    arithmetic,
    profile_mechanisms_generated::{profile_mechanism_route, ProfileMechanismRouteKind},
    special_forms,
};
use crate::{semantic_registry, Environment, ErrorKind, LanguageError, Sid8, Span, Value};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum SidRouteKind {
    ValueCall,
    SpecialForm,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct SidRoute {
    pub sid: Sid8,
    pub kind: SidRouteKind,
}

/// Mechanical route metadata for the historical seven slots that currently
/// need special evaluator handling. The rows are keyed only by Sid8.
pub(crate) const SID_ROUTES: [SidRoute; 7] = [
    SidRoute { sid: crate::sid!(00000001), kind: SidRouteKind::SpecialForm },
    SidRoute { sid: crate::sid!(00000010), kind: SidRouteKind::ValueCall },
    SidRoute { sid: crate::sid!(00000011), kind: SidRouteKind::ValueCall },
    SidRoute { sid: crate::sid!(00000100), kind: SidRouteKind::ValueCall },
    SidRoute { sid: crate::sid!(00000101), kind: SidRouteKind::ValueCall },
    SidRoute { sid: crate::sid!(00000110), kind: SidRouteKind::ValueCall },
    SidRoute { sid: crate::sid!(00000111), kind: SidRouteKind::SpecialForm },
];

pub(crate) fn route_kind_for_sid(sid: Sid8) -> Option<SidRouteKind> {
    let index = sid.packed_byte().checked_sub(1)? as usize;
    let row = SID_ROUTES.get(index)?;
    debug_assert_eq!(
        row.sid, sid,
        "SID route rows must stay aligned with 00000001..00000111"
    );
    Some(row.kind)
}

/// Optional source/UI routing only. The returned value is the function SID;
/// no named meaning is materialized.
pub(crate) fn routed_sid_for_surface(surface: &str) -> Option<Sid8> {
    let sid = semantic_registry::semantic_id_for_surface(surface)?;
    route_kind_for_sid(sid)?;
    Some(sid)
}

pub(crate) fn is_reserved_surface(surface: &str) -> bool {
    routed_sid_for_surface(surface).is_some()
}

pub(crate) fn surface_has_sid(surface: &str, sid: Sid8) -> bool {
    semantic_registry::semantic_id_for_surface(surface) == Some(sid)
}

pub(crate) fn ensure_bindable(surface: &str, span: Span) -> Result<(), LanguageError> {
    let Some(sid) = routed_sid_for_surface(surface) else {
        return Ok(());
    };
    Err(LanguageError::new(
        ErrorKind::InvalidForm,
        format!(
            "surface routes to immutable function SID · surface маршрутизується до незмінного function SID · Surface verweist auf unveränderliche Funktions-SID: {surface} -> {sid}"
        ),
        span,
    ))
}

fn exact_args(
    sid: &'static str,
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
            "{sid}: expected / ochikuvalosia / erwartet {expected}; received / otrymano / erhalten {}",
            args.len()
        ),
        span,
    ))
}

type PrimitiveFn = fn(&[Value], &Environment, Span) -> Result<Value, LanguageError>;

const PRIMITIVE_TABLE: [Option<PrimitiveFn>; 256] = {
    let mut table: [Option<PrimitiveFn>; 256] = [None; 256];
    table[crate::sid!(00000010).packed_byte() as usize] = Some(prim_00000010);
    table[crate::sid!(00000011).packed_byte() as usize] = Some(prim_00000011);
    table[crate::sid!(00000100).packed_byte() as usize] = Some(prim_00000100);
    table[crate::sid!(00000101).packed_byte() as usize] = Some(prim_00000101);
    table[crate::sid!(00000110).packed_byte() as usize] = Some(prim_00000110);
    table[crate::sid!(00001100).packed_byte() as usize] = Some(prim_00001100);
    table[crate::sid!(00001101).packed_byte() as usize] = Some(prim_00001101);
    table[crate::sid!(00001110).packed_byte() as usize] = Some(prim_00001110);
    table[crate::sid!(00001111).packed_byte() as usize] = Some(prim_00001111);
    table[crate::sid!(01001101).packed_byte() as usize] = Some(prim_01001101);
    table
};

fn prim_00000010(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args("00000010", args, 1, span)?;
    Ok(special_forms::atom_value(&args[0]))
}

fn prim_00000011(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args("00000011", args, 2, span)?;
    special_forms::eq_values(args[0].clone(), args[1].clone(), span)
}

fn prim_00000100(
    args: &[Value],
    env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args("00000100", args, 2, span)?;
    special_forms::cons_values(args[0].clone(), args[1].clone(), env, span)
}

fn prim_00000101(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args("00000101", args, 1, span)?;
    special_forms::car_value(&args[0], span)
}

fn prim_00000110(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args("00000110", args, 1, span)?;
    special_forms::cdr_value(&args[0], span)
}

fn prim_00001100(
    args: &[Value],
    env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args("00001100", args, 2, span)?;
    arithmetic::arithmetic_on_values("+", args, env, span)
}

fn prim_00001101(
    args: &[Value],
    env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args("00001101", args, 2, span)?;
    arithmetic::arithmetic_on_values("-", args, env, span)
}

fn prim_00001110(
    args: &[Value],
    env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args("00001110", args, 2, span)?;
    arithmetic::arithmetic_on_values("*", args, env, span)
}

fn prim_00001111(
    args: &[Value],
    env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args("00001111", args, 2, span)?;
    arithmetic::arithmetic_on_values("/", args, env, span)
}

fn prim_01001101(
    args: &[Value],
    env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args("01001101", args, 1, span)?;
    special_forms::eval_values(args, env, span)
}

/// Mechanism bridge selected only by Sid8.
pub(crate) fn invoke_semantic_ref(
    sid: Sid8,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if let Some(primitive) = PRIMITIVE_TABLE
        .get(sid.packed_byte() as usize)
        .and_then(|function| *function)
    {
        return primitive(args, environment, span);
    }

    if let Some(profile) = environment.selected_core_profile() {
        if matches!(
            profile_mechanism_route(profile, sid),
            Some(ProfileMechanismRouteKind::RegisteredHostMechanism)
        ) {
            return match super::capabilities::dispatch_sens_capability(
                sid,
                args,
                environment,
                span,
            ) {
                Some(result) => result,
                None => Err(LanguageError::new(
                    ErrorKind::MechanismUnavailable,
                    format!(
                        "admitted host mechanism is unavailable for SENS function: {sid}"
                    ),
                    span,
                )),
            };
        }
    }

    Err(LanguageError::new(
        ErrorKind::Type,
        format!("SENS function has no admitted callable mechanism: {sid}"),
        span,
    ))
}

pub(crate) fn value_for_sid(sid: Sid8) -> Option<Value> {
    match route_kind_for_sid(sid)? {
        SidRouteKind::ValueCall => Some(Value::Sid(sid)),
        SidRouteKind::SpecialForm => None,
    }
}

pub(crate) fn value_for_surface(surface: &str) -> Option<Value> {
    routed_sid_for_surface(surface).and_then(value_for_sid)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sid_zero_is_not_owned_by_route_metadata() {
        assert_eq!(route_kind_for_sid(crate::sid!(00000000)), None);
        assert_eq!(SID_ROUTES[0].sid, crate::sid!(00000001));
    }

    #[test]
    fn route_metadata_is_keyed_only_by_exact_sid() {
        assert_eq!(
            route_kind_for_sid(crate::sid!(00000001)),
            Some(SidRouteKind::SpecialForm)
        );
        assert_eq!(
            route_kind_for_sid(crate::sid!(00000101)),
            Some(SidRouteKind::ValueCall)
        );
        assert_eq!(route_kind_for_sid(crate::sid!(00001100)), None);
    }

    #[test]
    fn every_surface_for_sid_00000101_routes_back_to_that_sid() {
        let surfaces =
            semantic_registry::admitted_surfaces_for_semantic_id(crate::sid!(00000101));
        assert!(surfaces.len() >= 2, "expected multiple routing surfaces");
        for surface in &surfaces {
            assert_eq!(
                routed_sid_for_surface(surface),
                Some(crate::sid!(00000101))
            );
        }
    }

    #[test]
    fn routed_value_surface_materializes_only_the_sid() {
        let surface = semantic_registry::admitted_surfaces_for_semantic_id(
            crate::sid!(00000101),
        )
        .into_iter()
        .next()
        .expect("SID 00000101 should have a routing surface");
        assert_eq!(
            value_for_surface(surface),
            Some(Value::Sid(crate::sid!(00000101)))
        );
    }

    #[test]
    fn surfaces_for_sid_routes_are_reserved_mechanically() {
        for sid in [
            crate::sid!(00000001),
            crate::sid!(00000010),
            crate::sid!(00000011),
            crate::sid!(00000100),
            crate::sid!(00000101),
            crate::sid!(00000110),
            crate::sid!(00000111),
        ] {
            for surface in semantic_registry::admitted_surfaces_for_semantic_id(sid) {
                assert!(is_reserved_surface(surface));
                assert!(surface_has_sid(surface, sid));
            }
        }
        assert!(!is_reserved_surface("map"));
    }

    #[test]
    fn special_form_routes_do_not_materialize_callable_values() {
        assert_eq!(value_for_sid(crate::sid!(00000001)), None);
        assert_eq!(value_for_sid(crate::sid!(00000111)), None);
    }
}