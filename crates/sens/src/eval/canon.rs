//! Evaluator mechanism routing.
//!
//! Contract 11 canonical identity is exact domain + exact bits. Historical
//! Sens8 tables remain a compatibility/backend lane while migrated D3 calls
//! route directly from `CoreDomainIdentity` without reconstructing a byte.

use super::{
    closures, necessary_forms,
    profile_mechanisms_generated::{profile_mechanism_route, ProfileMechanismRouteKind},
    special_forms,
};
use crate::{semantic_registry, Environment, ErrorKind, LanguageError, Sens8, Span, Value};
use crate::CoreDomainIdentity;

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

/// Surface, яку не можна перевизначити: Canon, necessary form, або примітив.
/// M8 (#1590): після lower admitted surface → SENS, біндинг `+` не змінює Call.
pub(crate) fn ensure_bindable(surface: &str, span: Span) -> Result<(), LanguageError> {
    if let Some(identity) = semantic_registry::domain_identity_for_surface(surface) {
        if domain_has_native_mechanism(identity) {
            return Err(LanguageError::new(
                ErrorKind::InvalidForm,
                format!("surface routes to immutable exact domain identity: {surface} -> {identity}"),
                span,
            ));
        }
    }
    if let Some(sid) = routed_sid_for_surface(surface) {
        return Err(immutable_surface_error(surface, sid, span));
    }
    if let Some(sid) = semantic_registry::admitted_semantic_id_for_surface(surface) {
        if has_primitive(sid) || necessary_forms::identity_for_semantic_id(sid).is_some() {
            return Err(immutable_surface_error(surface, sid, span));
        }
    }
    Ok(())
}

fn immutable_surface_error(surface: &str, sid: Sens8, span: Span) -> LanguageError {
    LanguageError::new(
        ErrorKind::InvalidForm,
        format!(
            "surface routes to immutable function SID · surface маршрутизується до незмінного function SID · Surface verweist auf unveränderliche Funktions-SID: {surface} -> {sid}"
        ),
        span,
    )
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
    sid: crate::Sens8,
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

fn prim_00000010(
    args: &[Value],
    env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args(crate::sens!(00000010), args, 1, span)?;
    Ok(special_forms::atom_value(&args[0], env))
}

fn prim_00000011(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args(crate::sens!(00000011), args, 2, span)?;
    special_forms::eq_values(args[0].clone(), args[1].clone(), span)
}

fn prim_00000100(
    args: &[Value],
    env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args(crate::sens!(00000100), args, 2, span)?;
    special_forms::cons_values(args[0].clone(), args[1].clone(), env, span)
}

fn domain_primitive(identity: CoreDomainIdentity) -> Option<PrimitiveFn> {
    let CoreDomainIdentity::D3(word) = identity else {
        return None;
    };
    match word.word().packed_bits() {
        0b010 => Some(prim_00000010), // ATOM
        0b111 => Some(prim_00000011), // EQ
        0b100 => Some(prim_00000100), // CONS
        // CAR/CDR and all proven descendants are executed by selector_law.
        0b101 | 0b110 => None,
        _ => None, // QUOTE/COND are syntax routes, 000 is structural empty
    }
}

fn domain_has_native_mechanism(identity: CoreDomainIdentity) -> bool {
    domain_primitive(identity).is_some()
        || super::selector_law::supports(identity)
        || super::d5_arithmetic::supports(identity)
        || necessary_forms::identity_for_domain_identity(identity).is_some()
}

/// Canonical value-call mechanism bridge for migrated exact-domain identities.
///
/// The D3 role mapping is explicit and law-shaped; it is intentionally not a
/// numeric projection to the historical Function8 byte axis.
pub(crate) fn invoke_domain_identity(
    identity: CoreDomainIdentity,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if let Some(result) = super::selector_law::invoke(identity, args, span) {
        return result;
    }

    if let Some(result) = super::d5_arithmetic::invoke(identity, args, environment, span) {
        return result;
    }

    if let Some(primitive) = domain_primitive(identity) {
        return primitive(args, environment, span);
    }

    if let Some(bound) = environment.domain_code_slot(identity) {
        match &bound {
            Value::Closure(closure) => {
                return closures::apply_values(closure.clone(), args, span);
            }
            Value::Builtin(builtin) => return (builtin.func)(args, environment, span),
            _ => {}
        }
    }

    Err(LanguageError::new(
        ErrorKind::Type,
        format!("domain identity has no admitted value-call mechanism: {identity}"),
        span,
    ))
}

/// Compatibility/backend mechanism bridge selected by historical Sens8.
pub(crate) fn invoke_semantic_ref(
    sid: Sens8,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    // One-way compatibility adapter. Once a historical byte has a proven
    // exact-domain successor, it delegates before any legacy primitive or code
    // slot can participate. The old coordinate cannot shadow canonical domain
    // meaning.
    if let Some(identity) =
        semantic_registry::legacy_domain_identity_from_registry_byte(sid.packed_byte())
    {
        if environment.domain_code_slot(identity).is_some() || domain_has_native_mechanism(identity) {
            return invoke_domain_identity(identity, args, environment, span);
        }
    }

    // Unmigrated compatibility-only mechanisms.
    if let Some(result) = super::legacy_primitives::invoke(sid, args, environment, span) {
        return result;
    }
    match &environment.code_slot(sid) {
        Some(Value::Closure(closure)) => return closures::apply_values(closure.clone(), args, span),
        Some(Value::Builtin(builtin)) => return (builtin.func)(args, environment, span),
        _ => {}
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
                    format!("admitted host mechanism is unavailable for SENS function: {sid}"),
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

/// #1455: чи має код примітив Rust.
pub(crate) fn has_primitive(sid: Sens8) -> bool {
    super::legacy_primitives::has(sid)
        || semantic_registry::legacy_domain_identity_from_registry_byte(sid.packed_byte())
            .is_some_and(domain_has_native_mechanism)
}

/// #1455: визначення (функція або макрос) верхнього рівня з назвою з таблиці функцій, чий код не
/// має примітиву й не є особливою формою, стає механізмом цього коду. Лише
/// перше визначення; затінення назви пізніше слот не змінює.
pub(crate) fn bind_language_definition(name: &str, value: &Value, environment: &Environment) {
    if !environment.is_root() || !matches!(value, Value::Closure(_) | Value::Builtin(_) | Value::Macro(_)) {
        return;
    }

    if let Some(identity) = semantic_registry::domain_identity_for_surface(name) {
        if domain_has_native_mechanism(identity) {
            return;
        }
        environment.bind_domain_code_slot_once(identity, value.clone());
        return;
    }

    // Compatibility-only lane for registry rows that do not yet have a
    // canonical domain identity.
    let Some(sid) = semantic_registry::admitted_semantic_id_for_surface(name) else {
        return;
    };
    if has_primitive(sid) || super::necessary_forms::identity_for_semantic_id(sid).is_some() {
        return;
    }
    environment.bind_code_slot_once(sid, value.clone());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_d3_primitive_route_is_role_aware_not_numeric_projection() {
        let d3 = |bits| {
            CoreDomainIdentity::D3(crate::Bija3::from_word(crate::Bit3::new(bits).unwrap()))
        };

        assert!(domain_primitive(d3(0b010)).is_some()); // ATOM
        assert!(domain_primitive(d3(0b111)).is_some()); // EQ
        assert!(domain_primitive(d3(0b100)).is_some()); // CONS
        assert!(domain_primitive(d3(0b101)).is_none()); // CAR -> selector law
        assert!(domain_primitive(d3(0b110)).is_none()); // CDR -> selector law
        assert!(domain_primitive(d3(0b001)).is_none()); // QUOTE syntax
        assert!(domain_primitive(d3(0b011)).is_none()); // COND syntax

        let d4_same_payload = CoreDomainIdentity::D4(crate::CoreD4::from_word(
            crate::Bit4::new(0b0010).unwrap(),
        ));
        assert!(domain_primitive(d4_same_payload).is_none());
    }

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
    fn exact_d5_numeric_surfaces_are_not_bindable() {
        let span = Span { start: 0, end: 1 };
        assert!(ensure_bindable("+", span).is_err());
        assert!(ensure_bindable("-", span).is_err());
    }
}
