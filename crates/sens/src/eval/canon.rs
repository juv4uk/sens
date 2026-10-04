//! Evaluator mechanism routing.
//!
//! Contract 11 canonical identity is exact domain + exact bits. Historical
//! Sens8 tables remain a compatibility/backend lane while migrated D3 calls
//! route directly from `CoreDomainIdentity` without reconstructing a byte.

use super::{
    arithmetic, builtins, closures, necessary_forms,
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

pub(crate) fn immutable_domain_binding_error(
    identity: crate::DomainIdentity,
    span: Span,
) -> LanguageError {
    LanguageError::new(
        ErrorKind::InvalidForm,
        format!(
            "canonical name is immutable after exact-domain lowering · канонічне ім'я незмінне після exact-domain lowering · kanonischer Name ist nach Exact-Domain-Lowering unveränderlich: D{} {}",
            identity.width(),
            identity
        ),
        span,
    )
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

/// Canonical value-call mechanism bridge for migrated exact-domain identities.
///
/// The D3 role mapping is explicit and law-shaped; it is intentionally not a
/// numeric projection to the historical Function8 byte axis.
pub(crate) fn has_language_result_boundary(identity: CoreDomainIdentity) -> bool {
    match identity {
        CoreDomainIdentity::D3(word) => matches!(word.word().packed_bits(), 0b010 | 0b111),
        CoreDomainIdentity::D5(word) => word.word().packed_bits() == 0b11101,
        _ => false,
    }
}

fn canonicalize_domain_result(
    identity: CoreDomainIdentity,
    value: Value,
    span: Span,
) -> Result<Value, LanguageError> {
    if !has_language_result_boundary(identity) {
        return Ok(value);
    }

    // Already-canonical D1 passes through.  Transitional compatibility
    // carriers are accepted only at the exact operation boundary that owns
    // their migration; no generic Number/list/NIL -> D1 coercion exists.
    if value.as_predicate_bit().is_some() {
        return Ok(value);
    }

    match identity {
        CoreDomainIdentity::D3(word) => {
            let bits = word.word().packed_bits();

            // The historical D3 primitive mechanism still returns the old
            // one-element exact-number answer carrier.  Exact-domain callers
            // receive only D1.  Legacy SID callers never pass this boundary.
            let legacy_bit = match &value {
                Value::Pair(head, tail) if matches!(tail.as_ref(), Value::Nil) => {
                    match head.as_ref() {
                        Value::Number(number, crate::Exactness::Exact) if *number == 0.0 => {
                            Some(false)
                        }
                        Value::Number(number, crate::Exactness::Exact) if *number == 1.0 => {
                            Some(true)
                        }
                        _ => None,
                    }
                }
                _ => None,
            };
            if let Some(bit) = legacy_bit {
                return Ok(Value::predicate_bit(bit));
            }

            // Exact D3:010 ATOM is total: the legacy NIL/unknown carrier for
            // structural empty is normalized to D1:YES.
            if bits == 0b010 && matches!(value, Value::Nil) {
                return Ok(Value::predicate_bit(true));
            }

            // #3161: exact D3:111 EQ is partial over the admitted atom domain.
            // Structural EMPTY is its canonical no-witness result for inputs
            // outside that domain; it must not be coerced to D1:NO.
            if bits == 0b111 && matches!(value, Value::Nil) {
                return Ok(Value::Nil);
            }

            Err(LanguageError::new(
                ErrorKind::Type,
                format!(
                    "exact D3 predicate must return D1 PredicateBit or its explicitly admitted EMPTY/no-witness result, got {value}"
                ),
                span,
            ))
        }
        CoreDomainIdentity::D5(_) => {
            // #3060: MEMBER search/equality remains Lisp-owned. This boundary
            // upgrades only its transitional t/() carrier into exact D1.
            if matches!(&value, Value::Symbol(symbol) if symbol.as_ref() == "t") {
                return Ok(Value::predicate_bit(true));
            }
            if matches!(&value, Value::Nil) {
                return Ok(Value::predicate_bit(false));
            }

            Err(LanguageError::new(
                ErrorKind::Type,
                format!(
                    "D5 MEMBER must return exact D1 PredicateBit (legacy t/() accepted only at migration boundary), got {value}"
                ),
                span,
            ))
        }
        _ => Ok(value),
    }
}

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
        let value = primitive(args, environment, span)?;
        return canonicalize_domain_result(identity, value, span);
    }

    if let Some(bound) = environment.domain_code_slot(identity) {
        let result = match &bound {
            Value::Closure(closure) => Some(closures::apply_values(closure.clone(), args, span)?),
            Value::Builtin(builtin) => Some((builtin.func)(args, environment, span)?),
            _ => None,
        };
        if let Some(value) = result {
            return canonicalize_domain_result(identity, value, span);
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
    // #1455: примітив Rust → визначення мовою, прив'язане до коду → помилка.
    if let Some(primitive) = PRIMITIVE_TABLE
        .get(sid.packed_byte() as usize)
        .and_then(|function| *function)
    {
        return primitive(args, environment, span);
    }
    match &environment.code_slot(sid) {
        Some(Value::Closure(closure)) => return closures::apply_values(closure.clone(), args, span),
        Some(Value::Builtin(builtin)) => return (builtin.func)(args, environment, span),
        _ => {}
    }

    // Explicit compatibility adapter: once a historical byte has a proven
    // exact-domain successor, the old spelling delegates to that one
    // canonical mechanism. We do not dual-bind the language definition into
    // both legacy and domain slots.
    if let Some(identity) =
        semantic_registry::legacy_domain_identity_from_registry_byte(sid.packed_byte())
    {
        if environment.domain_code_slot(identity).is_some() || domain_primitive(identity).is_some() {
            return invoke_domain_identity(identity, args, environment, span);
        }
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
    PRIMITIVE_TABLE
        .get(sid.packed_byte() as usize)
        .is_some_and(|function| function.is_some())
}

/// #1455: визначення (функція або макрос) верхнього рівня з назвою з таблиці функцій, чий код не
/// має примітиву й не є особливою формою, стає механізмом цього коду. Лише
/// перше визначення; затінення назви пізніше слот не змінює.
pub(crate) fn bind_language_definition(name: &str, value: &Value, environment: &Environment) {
    if !environment.is_root() || !matches!(value, Value::Closure(_) | Value::Builtin(_) | Value::Macro(_)) {
        return;
    }

    if let Some(identity) = semantic_registry::domain_identity_for_surface(name) {
        if domain_primitive(identity).is_some()
            || super::necessary_forms::identity_for_domain_identity(identity).is_some()
        {
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
    // #3070 transitional bootstrap.
    //
    // Canonical storage/routing is the exact D5 slot. The historical code slot
    // is only a mechanism alias to the SAME Value/Rc so recursive legacy Core
    // bodies keep their old shallow dispatch path while source migration is
    // incomplete. It does not mint a second semantic identity, and #3062
    // removes this alias when exact-domain source/registry routing is complete.
    if let Some(identity) =
        semantic_registry::transitional_d5_binding_identity_from_registry_byte(sid.packed_byte())
    {
        if super::necessary_forms::identity_for_domain_identity(identity).is_some() {
            return;
        }

        // QUOTIENT already has an admitted direct D5 arithmetic mechanism.
        // Keep only its historical closure alias for old Core callers; the
        // exact D5 path must continue to select the direct mechanism first.
        if domain_primitive(identity).is_none()
            && !super::d5_arithmetic::has_mechanism(identity)
        {
            environment.bind_domain_code_slot_once(identity, value.clone());
        }
        environment.bind_code_slot_once(sid, value.clone());
        return;
    }

    if has_primitive(sid) || super::necessary_forms::identity_for_semantic_id(sid).is_some() {
        return;
    }
    environment.bind_code_slot_once(sid, value.clone());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn d5_member_result_boundary_accepts_only_predicate_semantics() {
        let member = CoreDomainIdentity::D5(crate::CoreD5::from_word(
            crate::Bit5::new(0b11101).unwrap(),
        ));
        let assoc = CoreDomainIdentity::D5(crate::CoreD5::from_word(
            crate::Bit5::new(0b11100).unwrap(),
        ));
        let span = Span { start: 0, end: 0 };

        let yes = canonicalize_domain_result(
            member,
            Value::Symbol(std::rc::Rc::from("t")),
            span,
        )
        .expect("legacy YES carrier should normalize");
        let no = canonicalize_domain_result(member, Value::Nil, span)
            .expect("legacy NO carrier should normalize");
        assert_eq!(yes.as_predicate_bit(), Some(true));
        assert_eq!(no.as_predicate_bit(), Some(false));

        let already_exact = Value::predicate_bit(true);
        assert_eq!(
            canonicalize_domain_result(member, already_exact.clone(), span).unwrap(),
            already_exact
        );

        let numeric_truth = Value::Number(1.0, crate::Exactness::Exact);
        let error = canonicalize_domain_result(member, numeric_truth, span)
            .expect_err("Number 1 must never collapse into D1 YES");
        assert_eq!(error.kind, ErrorKind::Type);

        let assoc_pair = Value::list([
            Value::Symbol(std::rc::Rc::from("key")),
            Value::Symbol(std::rc::Rc::from("value")),
        ]);
        assert_eq!(
            canonicalize_domain_result(assoc, assoc_pair.clone(), span).unwrap(),
            assoc_pair,
            "non-MEMBER D5 results must pass through unchanged"
        );
    }

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
    fn exact_d3_predicate_results_cross_only_as_d1() {
        let d3 = |bits| {
            CoreDomainIdentity::D3(crate::Bija3::from_word(crate::Bit3::new(bits).unwrap()))
        };
        let span = Span { start: 0, end: 0 };
        let env = Environment::root();

        let atom_yes = invoke_domain_identity(d3(0b010), &[Value::Nil], &env, span)
            .expect("D3:010 must classify structural empty");
        assert_eq!(atom_yes.as_predicate_bit(), Some(true));

        let atom_no = invoke_domain_identity(
            d3(0b010),
            &[Value::list([Value::Number(1.0, crate::Exactness::Exact)])],
            &env,
            span,
        )
        .expect("D3:010 must classify pairs");
        assert_eq!(atom_no.as_predicate_bit(), Some(false));

        let left = Value::Symbol(std::rc::Rc::from("x"));
        let same = Value::Symbol(std::rc::Rc::from("x"));
        let other = Value::Symbol(std::rc::Rc::from("y"));

        let equal = invoke_domain_identity(d3(0b111), &[left.clone(), same], &env, span)
            .expect("D3:111 equal atoms");
        let different = invoke_domain_identity(d3(0b111), &[left, other], &env, span)
            .expect("D3:111 distinct atoms");
        assert_eq!(equal.as_predicate_bit(), Some(true));
        assert_eq!(different.as_predicate_bit(), Some(false));

        assert!(has_language_result_boundary(d3(0b010)));
        assert!(has_language_result_boundary(d3(0b111)));
        assert!(!has_language_result_boundary(d3(0b100)));

        let number = Value::Number(1.0, crate::Exactness::Exact);
        let error = canonicalize_domain_result(d3(0b111), number, span)
            .expect_err("bare Number 1 must not collapse into D1");
        assert_eq!(error.kind, ErrorKind::Type);
    }

    #[test]
    fn d8_non_selector_without_mechanism_fails_closed() {
        let identity = CoreDomainIdentity::D8(crate::CoreD8::from_word(
            crate::Bit8::new(0b00000000).unwrap(),
        ));
        let error = invoke_domain_identity(
            identity,
            &[],
            &Environment::root(),
            Span { start: 0, end: 0 },
        )
        .expect_err("D8 width alone must not grant a value-call mechanism");

        assert_eq!(error.kind, ErrorKind::Type);
        assert!(error
            .message
            .contains("domain identity has no admitted value-call mechanism"));
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
    fn plus_surface_is_not_bindable_after_m8() {
        let span = Span { start: 0, end: 1 };
        assert!(ensure_bindable("+", span).is_err());
        assert!(ensure_bindable("-", span).is_err());
    }
}
