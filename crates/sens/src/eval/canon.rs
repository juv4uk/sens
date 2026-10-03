//! SID-keyed evaluator mechanism routing.
//!
//! Transitional registry/mechanism bridge for historical exact-eight anchors. This module may record
//! mechanism shape for an already-selected SID, but it must never invent a
//! second named function identity.

use super::{
    arithmetic, builtins, closures, necessary_forms,
    profile_mechanisms_generated::{profile_mechanism_route, ProfileMechanismRouteKind},
    special_forms,
};
use crate::{semantic_registry, CallableIdentity, Environment, ErrorKind, LanguageError, Sens8, Span, Value};

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

pub(crate) fn route_kind_for_legacy8_bits(bits: u8) -> Option<SidRouteKind> {
    let index = bits.checked_sub(1)? as usize;
    let row = SID_ROUTES.get(index)?;
    debug_assert_eq!(
        row.sid.packed_byte(),
        bits,
        "legacy route rows must stay aligned with 00000001..00000111"
    );
    Some(row.kind)
}

pub(crate) fn route_kind_for_sid(sid: Sens8) -> Option<SidRouteKind> {
    route_kind_for_legacy8_bits(sid.packed_byte())
}

/// Optional source/UI routing only. The returned value is the function SID;
/// no named meaning is materialized.
pub(crate) fn routed_legacy8_bits_for_surface(surface: &str) -> Option<u8> {
    let sid = semantic_registry::semantic_id_for_surface(surface)?;
    let bits = sid.packed_byte();
    route_kind_for_legacy8_bits(bits)?;
    Some(bits)
}

pub(crate) fn routed_sid_for_surface(surface: &str) -> Option<Sens8> {
    let bits = routed_legacy8_bits_for_surface(surface)?;
    Some(Sens8::from_packed_byte(bits))
}

pub(crate) fn is_reserved_surface(surface: &str) -> bool {
    routed_sid_for_surface(surface).is_some()
}

pub(crate) fn surface_has_sid(surface: &str, sid: Sens8) -> bool {
    semantic_registry::semantic_id_for_surface(surface) == Some(sid)
}

pub(crate) fn surface_has_legacy8_bits(surface: &str, bits: u8) -> bool {
    semantic_registry::semantic_id_for_surface(surface)
        .is_some_and(|sid| sid.packed_byte() == bits)
}

/// Surface, яку не можна перевизначити: Canon, necessary form, або примітив.
/// M8 (#1590): після lower admitted surface → SENS, біндинг `+` не змінює Call.
pub(crate) fn ensure_bindable(surface: &str, span: Span) -> Result<(), LanguageError> {
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

pub(crate) fn ensure_bindable_legacy8_bits(bits: u8, span: Span) -> Result<(), LanguageError> {
    Err(LanguageError::new(
        ErrorKind::InvalidForm,
        format!(
            "surface routes to immutable historical exact-eight identity: {bits:08b} -> {bits:08b}"
        ),
        span,
    ))
}

pub(crate) fn ensure_bindable_sid(sid: Sens8, span: Span) -> Result<(), LanguageError> {
    ensure_bindable_legacy8_bits(sid.packed_byte(), span)
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
    table[crate::sens!(00111011).packed_byte() as usize] = Some(builtins::prim_00111011); // string-length
    table[crate::sens!(00111100).packed_byte() as usize] = Some(builtins::prim_00111100); // string-empty?
    table[crate::sens!(00111101).packed_byte() as usize] = Some(builtins::prim_00111101); // string-prefix?
    table[crate::sens!(00111110).packed_byte() as usize] = Some(builtins::prim_00111110); // string-contains?
    table[crate::sens!(01010000).packed_byte() as usize] = Some(builtins::prim_01010000); // make-vector
    table[crate::sens!(01001111).packed_byte() as usize] = Some(builtins::prim_01001111); // vector
    table[crate::sens!(01011010).packed_byte() as usize] = Some(builtins::prim_01011010); // mono-ns
    table[crate::sens!(01011011).packed_byte() as usize] = Some(builtins::prim_01011011); // unix-time-now
    table[crate::sens!(01011100).packed_byte() as usize] = Some(builtins::prim_01011100); // ntp-query-raw
    table[crate::sens!(01011101).packed_byte() as usize] = Some(builtins::prim_01011101); // timezone-declarations-raw
    table[crate::sens!(01010001).packed_byte() as usize] = Some(builtins::prim_01010001); // vector-length
    table[crate::sens!(01010010).packed_byte() as usize] = Some(builtins::prim_01010010); // vector-ref
    table[crate::sens!(01010011).packed_byte() as usize] = Some(builtins::prim_01010011); // vector-set!
    table[crate::sens!(01010100).packed_byte() as usize] = Some(builtins::prim_01010100); // i32-buffer
    table[crate::sens!(01010101).packed_byte() as usize] = Some(builtins::prim_01010101); // f32-buffer
    table[crate::sens!(01000001).packed_byte() as usize] = Some(builtins::prim_01000001); // string-slice
    table[crate::sens!(00111010).packed_byte() as usize] = Some(builtins::prim_00111010); // string-append
    table[crate::sens!(00100100).packed_byte() as usize] = Some(builtins::prim_00100100); // string?
    table[crate::sens!(01000010).packed_byte() as usize] = Some(builtins::prim_01000010); // symbol->string
    table[crate::sens!(01000011).packed_byte() as usize] = Some(builtins::prim_01000011); // string->symbol
    table[crate::sens!(00111111).packed_byte() as usize] = Some(builtins::prim_00111111); // string-first
    table[crate::sens!(01000000).packed_byte() as usize] = Some(builtins::prim_01000000); // string-rest
    table[crate::sens!(01000100).packed_byte() as usize] = Some(builtins::prim_01000100); // codepoint->string
    table[crate::sens!(01000101).packed_byte() as usize] = Some(builtins::prim_01000101); // string->codepoint
    table[crate::sens!(10100001).packed_byte() as usize] = Some(builtins::prim_10100001); // sha256-hex
    table[crate::sens!(10100000).packed_byte() as usize] = Some(builtins::prim_10100000); // json-parse
    table[crate::sens!(01001000).packed_byte() as usize] = Some(builtins::prim_01001000); // print
    table[crate::sens!(01001001).packed_byte() as usize] = Some(builtins::prim_01001001); // princ
    table[crate::sens!(01001100).packed_byte() as usize] = Some(builtins::prim_01001100); // write-to-string
    table[crate::sens!(01001010).packed_byte() as usize] = Some(builtins::prim_01001010); // read
    table[crate::sens!(01001011).packed_byte() as usize] = Some(builtins::prim_01001011); // read-all
    table[crate::sens!(00100110).packed_byte() as usize] = Some(builtins::prim_00100110); // numeric-buffer?
    table[crate::sens!(01010110).packed_byte() as usize] = Some(builtins::prim_01010110); // numeric-buffer-type
    table[crate::sens!(01010111).packed_byte() as usize] = Some(builtins::prim_01010111); // numeric-buffer-length
    table[crate::sens!(01011000).packed_byte() as usize] = Some(builtins::prim_01011000); // numeric-buffer-ref
    table[crate::sens!(01011001).packed_byte() as usize] = Some(builtins::prim_01011001); // numeric-buffer-map
    table[crate::sens!(01001110).packed_byte() as usize] = Some(builtins::prim_01001110); // env
    table
};

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

fn prim_00000101(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args(crate::sens!(00000101), args, 1, span)?;
    special_forms::car_value(&args[0], span)
}

fn prim_00000110(
    args: &[Value],
    _env: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_args(crate::sens!(00000110), args, 1, span)?;
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
    exact_args(crate::sens!(01001101), args, 1, span)?;
    special_forms::eval_values(args, env, span)
}

/// Compatibility mechanism bridge selected by a historical exact-eight anchor.
pub(crate) fn invoke_legacy8_bits(
    bits: u8,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    let sid = Sens8::from_packed_byte(bits);
    // #1455: примітив Rust → визначення мовою, прив'язане до коду → помилка.
    if let Some(primitive) = PRIMITIVE_TABLE
        .get(bits as usize)
        .and_then(|function| *function)
    {
        return primitive(args, environment, span);
    }
    match &environment.code_slot(CallableIdentity::legacy8(bits)) {
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
        format!("historical exact-eight identity has no admitted callable mechanism: {bits:08b}"),
        span,
    ))
}

pub(crate) fn invoke_semantic_ref(
    sid: Sens8,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    invoke_legacy8_bits(sid.packed_byte(), args, environment, span)
}

/// #1455: чи має compatibility-код примітив Rust.
pub(crate) fn has_primitive_legacy8_bits(bits: u8) -> bool {
    PRIMITIVE_TABLE
        .get(bits as usize)
        .is_some_and(|function| function.is_some())
}

pub(crate) fn has_primitive(sid: Sens8) -> bool {
    has_primitive_legacy8_bits(sid.packed_byte())
}

/// #1455: визначення (функція або макрос) верхнього рівня з назвою з таблиці функцій, чий код не
/// має примітиву й не є особливою формою, стає механізмом цього коду. Лише
/// перше визначення; затінення назви пізніше слот не змінює.
pub(crate) fn bind_language_definition(name: &str, value: &Value, environment: &Environment) {
    if !environment.is_root() || !matches!(value, Value::Closure(_) | Value::Builtin(_) | Value::Macro(_)) {
        return;
    }
    let Some(sid) = semantic_registry::admitted_semantic_id_for_surface(name) else {
        return;
    };
    if has_primitive(sid) || super::necessary_forms::identity_for_semantic_id(sid).is_some() {
        return;
    }
    environment.bind_code_slot_once(CallableIdentity::legacy8(bits), value.clone());
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
    fn plus_surface_is_not_bindable_after_m8() {
        let span = Span { start: 0, end: 1 };
        assert!(ensure_bindable("+", span).is_err());
        assert!(ensure_bindable("-", span).is_err());
    }
}
