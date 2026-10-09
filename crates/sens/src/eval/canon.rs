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

/// Сумісний transport не містить власної таблиці семантичних ролей.
/// Координата береться лише з чинної ратифікованої драбини D3.
pub(crate) fn route_kind_for_sid(sid: Sens8) -> Option<SidRouteKind> {
    let CoreDomainIdentity::D3(word) =
        semantic_registry::compatibility_d3_route_from_ratified_domains(sid)?
    else {
        return None;
    };
    match word.word().packed_bits() {
        0b001 | 0b110 => Some(SidRouteKind::SpecialForm),
        0b010 | 0b011 | 0b100 | 0b101 | 0b111 => Some(SidRouteKind::ValueCall),
        _ => None,
    }
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

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum DomainPrimitiveKind {
    Equal,
    AtomPredicate,
    AtomEquality,
    PairConstruct,
}

/// Backend-neutral classification of current exact-domain value primitives.
///
/// This is the single D3 value-primitive classification shared by evaluator
/// mechanism routing and compiler-role projection. It is not a backend opcode
/// table and does not project onto historical Sens8/Function8 identity.
pub(crate) fn domain_primitive_kind(
    identity: CoreDomainIdentity,
) -> Option<DomainPrimitiveKind> {
    match identity {
        CoreDomainIdentity::D3(word) => match word.word().packed_bits() {
            0b010 => Some(DomainPrimitiveKind::AtomPredicate),
            0b101 => Some(DomainPrimitiveKind::AtomEquality),
            0b111 => Some(DomainPrimitiveKind::PairConstruct),
            0b100 | 0b011 => None,
            _ => None, // QUOTE/COND are syntax routes, 000 is structural empty
        },
        CoreDomainIdentity::D8(word) => match word.word().packed_bits() {
            0b11110111 => Some(DomainPrimitiveKind::Equal),
            _ => None,
        },
        _ => None,
    }
}

/// Exact-domain primitive execution never reconstructs an historical SID8.
/// The domain and its exact binary word select the already-admitted mechanism;
/// historical byte dispatch is confined to invoke_semantic_ref below.
fn invoke_domain_primitive(
    identity: CoreDomainIdentity,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    let kind = domain_primitive_kind(identity)?;
    Some((|| {
        let expected = match kind {
            DomainPrimitiveKind::AtomPredicate => 1,
            DomainPrimitiveKind::AtomEquality => 2,
            DomainPrimitiveKind::PairConstruct => 2,
            DomainPrimitiveKind::Equal => 2,
        };
        if args.len() != expected {
            return Err(LanguageError::new(
                ErrorKind::Arity,
                format!(
                    "{identity}: expected {expected} arguments; received {}",
                    args.len()
                ),
                span,
            ));
        }
        match kind {
            DomainPrimitiveKind::AtomPredicate => {
                Ok(special_forms::atom_value(&args[0], environment))
            }
            DomainPrimitiveKind::AtomEquality => {
                special_forms::eq_values(args[0].clone(), args[1].clone(), span)
            }
            DomainPrimitiveKind::PairConstruct => {
                special_forms::cons_values(args[0].clone(), args[1].clone(), environment, span)
            }
            DomainPrimitiveKind::Equal => Ok(Value::predicate_bit(args[0] == args[1])),
        }
    })())
}

/// Canonical value-call mechanism bridge for migrated exact-domain identities.
///
/// The D3 role mapping is explicit and law-shaped; it is intentionally not a
/// numeric projection to the historical Function8 byte axis.
pub(crate) fn has_language_result_boundary(identity: CoreDomainIdentity) -> bool {
    match identity {
        CoreDomainIdentity::D3(word) => matches!(word.word().packed_bits(), 0b010 | 0b101),
        CoreDomainIdentity::D5(word) => matches!(
            word.word().packed_bits(),
            0b01000 | 0b01001 | 0b11010 | 0b11011 | 0b11101
        ),
        CoreDomainIdentity::D8(word) => matches!(word.word().packed_bits(), 0b11110111),
        _ => false,
    }
}

fn canonicalize_domain_result(
    identity: CoreDomainIdentity,
    value: Value,
    span: Span,
) -> Result<Value, LanguageError> {
    if !has_language_result_boundary(identity) || value.as_predicate_bit().is_some() {
        return Ok(value);
    }

    // Контракт 11.8: Rust перевіряє тільки тип межі D1.
    // Старі t/(), числові й спискові відповіді не перетворюються на предикат.
    Err(LanguageError::new(
        ErrorKind::Type,
        format!("exact domain predicate must return D1 PredicateBit; got {value}"),
        span,
    ))
}

/// Compact-derived bootstrap law ratified at D4:1110 LIST / D4:1111 APPEND.
///
/// This is a bounded reference value-call mechanism expressed solely in the
/// D3 pair/empty value algebra; not a host effect, new resident, historical
/// W8 alias, or licence to promote arbitrary D4 identities into builtins.
/// A language-defined closure may replace the reference once independent
/// Lisp↔Rust parity has been established.
fn invoke_compact_derived_d4_lists(
    identity: CoreDomainIdentity,
    args: &[Value],
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    let CoreDomainIdentity::D4(word) = identity else {
        return None;
    };
    match word.word().packed_bits() {
        // Ratified D4 LIST: collect evaluated values into a proper list.
        0b1110 => Some(Ok(Value::list(args.iter().cloned()))),
        // Ratified D4 APPEND: combine only proper lists, left to right.
        // Never coerce a D1 predicate, Text7 datum, symbol, or dotted tail
        // into a proper-list carrier. Each pair is observed, not mutated.
        0b1111 => {
            let mut items = Vec::new();
            for value in args {
                let mut cursor = value;
                loop {
                    match cursor {
                        Value::Nil => break,
                        Value::Pair(head, tail) => {
                            items.push(head.as_ref().clone());
                            cursor = tail.as_ref();
                        }
                        _ => {
                            return Some(Err(LanguageError::new(
                                ErrorKind::Type,
                                "D4:1111 APPEND requires proper lists; no implicit tail or D1 coercion",
                                span,
                            )));
                        }
                    }
                }
            }
            Some(Ok(Value::list(items)))
        }
        _ => None,
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

    if let Some(result) = invoke_compact_derived_d4_lists(identity, args, span) {
        return result;
    }

    if let Some(result) = super::d5_arithmetic::invoke(identity, args, environment, span) {
        let value = result?;
        return canonicalize_domain_result(identity, value, span);
    }

    if let Some(result) = super::d6_arithmetic::invoke(identity, args, environment, span) {
        return result;
    }

    if let Some(result) = invoke_domain_primitive(identity, args, environment, span) {
        return canonicalize_domain_result(identity, result?, span);
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

    let direct_d5_binding = semantic_registry::d5_binding_identity_for_definition(name);
    if let Some(identity) = direct_d5_binding {
        if super::necessary_forms::identity_for_domain_identity(identity).is_none()
            && domain_primitive_kind(identity).is_none()
            && !super::d5_arithmetic::has_mechanism(identity)
        {
            environment.bind_domain_code_slot_once(identity, value.clone());
        }
    }

    if let Some(identity) = semantic_registry::domain_identity_for_surface(name) {
        if domain_primitive_kind(identity).is_some()
            || super::necessary_forms::identity_for_domain_identity(identity).is_some()
        {
            return;
        }
        environment.bind_domain_code_slot_once(identity, value.clone());

        // D3/D4 direct-domain definitions are fully migrated and stop here.
        // Lisp-owned D5 definitions still have historical callers inside the
        // compatibility Core/library corpus, so they must continue below long
        // enough to install the temporary alias to this same Value/Rc.
        if direct_d5_binding.is_none() {
            return;
        }
    }

    // Compatibility-only lane for registry rows that do not yet have a
    // canonical domain identity.
    let Some(sid) = semantic_registry::admitted_semantic_id_for_surface(name) else {
        return;
    };
    // No byte-to-domain lookup is permitted here. The only D5 identity
    // originates in the generated, domain-qualified Lisp definition bindings
    // above; the SID slot is merely a temporary alias for unmigrated callers.
    if let Some(identity) = direct_d5_binding {
        if super::necessary_forms::identity_for_domain_identity(identity).is_some() {
            return;
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
mod exact_domain_primitive_tests {
    use super::*;

    fn d3(bits: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D3(crate::Bija3::from_word(
            crate::Bit3::new(bits).expect("D3 word"),
        ))
    }

    #[test]
    fn domain_primitive_arity_diagnostic_carries_domain_not_historical_sid() {
        let environment = Environment::root();
        let span = Span { start: 0, end: 0 };
        let identity = d3(0b010);
        let error = invoke_domain_primitive(identity, &[], &environment, span)
            .expect("D3 ATOM admitted")
            .expect_err("arity mismatch must fail");
        assert_eq!(error.kind, ErrorKind::Arity);
        assert!(error.message.contains(&identity.to_string()));
        assert!(!error.message.contains("00000010"));
    }
}
