//! SID-keyed evaluator mechanism routing.
//!
//! Contract 9 / #1325: function identity is only Sens8. This module may record
//! mechanism shape for an already-selected SID, but it must never invent a
//! second named function identity.

use super::{arithmetic, closures, special_forms};
use crate::{semantic_registry, Environment, ErrorKind, LanguageError, Sens8, Span, Value};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum SidRouteKind {
    ValueCall,
    SpecialForm,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct SidRoute {
    pub sid: Sens8,
    pub kind: SidRouteKind,
}

/// Mechanical route metadata for the historical seven slots that currently
/// need special evaluator handling. The rows are keyed only by Sens8.
pub(crate) const SID_ROUTES: [SidRoute; 7] = [
    SidRoute { sid: crate::sens!(00000001), kind: SidRouteKind::SpecialForm },
    SidRoute { sid: crate::sens!(00000010), kind: SidRouteKind::ValueCall },
    SidRoute { sid: crate::sens!(00000011), kind: SidRouteKind::ValueCall },
    SidRoute { sid: crate::sens!(00000100), kind: SidRouteKind::ValueCall },
    SidRoute { sid: crate::sens!(00000101), kind: SidRouteKind::ValueCall },
    SidRoute { sid: crate::sens!(00000110), kind: SidRouteKind::ValueCall },
    SidRoute { sid: crate::sens!(00000111), kind: SidRouteKind::SpecialForm },
];

pub(crate) fn route_kind_for_sid(sid: Sens8) -> Option<SidRouteKind> {
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
pub(crate) fn routed_sid_for_surface(surface: &str) -> Option<Sens8> {
    let sid = semantic_registry::semantic_id_for_surface(surface)?;
    route_kind_for_sid(sid)?;
    Some(sid)
}

pub(crate) fn is_reserved_surface(surface: &str) -> bool {
    routed_sid_for_surface(surface).is_some()
}

pub(crate) fn surface_has_sid(surface: &str, sid: Sens8) -> bool {
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

pub(crate) fn ensure_bindable_sid(sid: Sens8, span: Span) -> Result<(), LanguageError> {
    Err(LanguageError::new(
        ErrorKind::InvalidForm,
        format!(
            "surface routes to immutable function SID · surface маршрутизується до незмінного function SID · Surface verweist auf unveränderliche Funktions-SID: {sid} -> {sid}"
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
    table[crate::sens!(00000010).packed_byte() as usize] = Some(prim_00000010);
    table[crate::sens!(00000011).packed_byte() as usize] = Some(prim_00000011);
    table[crate::sens!(00000100).packed_byte() as usize] = Some(prim_00000100);
    table[crate::sens!(00000101).packed_byte() as usize] = Some(prim_00000101);
    table[crate::sens!(00000110).packed_byte() as usize] = Some(prim_00000110);
    table[crate::sens!(00001100).packed_byte() as usize] = Some(prim_00001100);
    table[crate::sens!(00001101).packed_byte() as usize] = Some(prim_00001101);
    table[crate::sens!(00001110).packed_byte() as usize] = Some(prim_00001110);
    table[crate::sens!(00001111).packed_byte() as usize] = Some(prim_00001111);
    table[crate::sens!(00011010).packed_byte() as usize] = Some(prim_00011010);
    table[crate::sens!(00011011).packed_byte() as usize] = Some(prim_00011011);
    table[crate::sens!(00011100).packed_byte() as usize] = Some(prim_00011100);
    table[crate::sens!(01001101).packed_byte() as usize] = Some(prim_01001101);
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
    // Довільна арність — за контрактом tests/fixtures/conformance.lisp.
    arithmetic::arithmetic_on_values("+", args, env, span)
}

fn prim_00001101(
    args: &[Value],
    env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    // Довільна арність — за контрактом tests/fixtures/conformance.lisp.
    arithmetic::arithmetic_on_values("-", args, env, span)
}

fn prim_00001110(
    args: &[Value],
    env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    // Довільна арність — за контрактом tests/fixtures/conformance.lisp.
    arithmetic::arithmetic_on_values("*", args, env, span)
}

fn prim_00001111(
    args: &[Value],
    env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    // Довільна арність: (/ 5 6 8 7) -> 5/336 (conformance.lisp).
    arithmetic::division_on_values(args, args.len(), env, span)
}

fn prim_00011010(args: &[Value], _env: &Environment, span: Span) -> Result<Value, LanguageError> {
    arithmetic::comparison_on_values("<", args, span)
}

fn prim_00011011(args: &[Value], _env: &Environment, span: Span) -> Result<Value, LanguageError> {
    arithmetic::comparison_on_values(">", args, span)
}

fn prim_00011100(args: &[Value], _env: &Environment, span: Span) -> Result<Value, LanguageError> {
    arithmetic::comparison_on_values("=", args, span)
}

fn prim_01001101(
    args: &[Value],
    env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args("01001101", args, 1, span)?;
    special_forms::eval_values(args, env, span)
}

/// Mechanism bridge selected only by Sens8.
pub(crate) fn invoke_semantic_ref(
    sid: Sens8,
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

    if let Some(value) = environment.get_sens(sid) {
        return match value {
            Value::Closure(closure) => closures::apply_values(closure, args, span),
            _ => Err(LanguageError::new(
                ErrorKind::Type,
                format!("SENS function slot is not callable: {sid}"),
                span,
            )),
        };
    }

    Err(LanguageError::new(
        ErrorKind::Type,
        format!("SENS function has no admitted callable mechanism: {sid}"),
        span,
    ))
}

pub(crate) fn value_for_sid(sid: Sens8) -> Option<Value> {
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
        assert_eq!(route_kind_for_sid(crate::sens!(00000000)), None);
        assert_eq!(SID_ROUTES[0].sid, crate::sens!(00000001));
    }

    #[test]
    fn route_metadata_is_keyed_only_by_exact_sid() {
        assert_eq!(
            route_kind_for_sid(crate::sens!(00000001)),
            Some(SidRouteKind::SpecialForm)
        );
        assert_eq!(
            route_kind_for_sid(crate::sens!(00000101)),
            Some(SidRouteKind::ValueCall)
        );
        assert_eq!(route_kind_for_sid(crate::sens!(00001100)), None);
    }

    #[test]
    fn every_surface_for_sid_00000101_routes_back_to_that_sid() {
        let surfaces =
            semantic_registry::admitted_surfaces_for_semantic_id(crate::sens!(00000101));
        assert!(surfaces.len() >= 2, "expected multiple routing surfaces");
        for surface in &surfaces {
            assert_eq!(
                routed_sid_for_surface(surface),
                Some(crate::sens!(00000101))
            );
        }
    }

    #[test]
    fn routed_value_surface_materializes_only_the_sid() {
        let surface = semantic_registry::admitted_surfaces_for_semantic_id(
            crate::sens!(00000101),
        )
        .into_iter()
        .next()
        .expect("SID 00000101 should have a routing surface");
        assert_eq!(
            value_for_surface(surface),
            Some(Value::Sid(crate::sens!(00000101)))
        );
    }

    #[test]
    fn surfaces_for_sid_routes_are_reserved_mechanically() {
        for sid in [
            crate::sens!(00000001),
            crate::sens!(00000010),
            crate::sens!(00000011),
            crate::sens!(00000100),
            crate::sens!(00000101),
            crate::sens!(00000110),
            crate::sens!(00000111),
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
        assert_eq!(value_for_sid(crate::sens!(00000001)), None);
        assert_eq!(value_for_sid(crate::sens!(00000111)), None);
    }
}