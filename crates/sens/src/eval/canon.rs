//! Evaluator mechanism routing.
//!
//! Contract 11 canonical identity is exact domain + exact bits. Executable
//! routes are selected by ratified domain identity and concrete mechanisms;
//! historical flat W8 slots never supply callability.

use super::{
    builtins, closures, necessary_forms,
    profile_mechanisms_generated::{profile_mechanism_route, ProfileMechanismRouteKind},
    special_forms,
};
use crate::{
    semantic_registry, CoreDomainIdentity, Environment, ErrorKind, LanguageError, Span, Value,
};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum SidRouteKind {
    ValueCall,
    SpecialForm,
}

/// Сумісний transport не містить власної таблиці семантичних ролей.
/// Координата береться лише з чинної ратифікованої драбини D3.
pub(crate) fn route_kind_for_sid(sid: CoreDomainIdentity) -> Option<SidRouteKind> {
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
pub(crate) fn routed_sid_for_surface(surface: &str) -> Option<CoreDomainIdentity> {
    let sid = semantic_registry::semantic_id_for_surface(surface)?;
    route_kind_for_sid(sid)?;
    Some(sid)
}

/// Admit immutable source surfaces from the ratified exact-domain route first.
/// D5 definitions without admitted mechanisms remain bindable by the language;
/// mere residency is never sufficient to freeze a binding or grant callability.
fn immutable_exact_surface_identity(surface: &str) -> Option<CoreDomainIdentity> {
    let identity = super::lower::immutable_surface_domain_identity(surface)?;
    (matches!(identity, CoreDomainIdentity::D3(_))
        || domain_primitive_kind(identity).is_some()
        || necessary_forms::identity_for_domain_identity(identity).is_some())
    .then_some(identity)
}

pub(crate) fn is_reserved_surface(surface: &str) -> bool {
    if immutable_exact_surface_identity(surface).is_some() {
        return true;
    }
    routed_sid_for_surface(surface).is_some()
}

/// Surface, яку не можна перевизначити: Canon, necessary form, або примітив.
/// Exact domain + exact bits own the canonical diagnostic. The old eight-bit
/// compatibility route is only consulted for unmigrated source surfaces.
pub(crate) fn ensure_bindable(surface: &str, span: Span) -> Result<(), LanguageError> {
    if let Some(identity) = immutable_exact_surface_identity(surface) {
        return Err(immutable_domain_binding_error(identity.into(), span));
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

fn immutable_surface_error(surface: &str, sid: CoreDomainIdentity, span: Span) -> LanguageError {
    LanguageError::new(
        ErrorKind::InvalidForm,
        format!(
            "surface routes to immutable function SID · surface маршрутизується до незмінного function SID · Surface verweist auf unveränderliche Funktions-SID: {surface} -> {sid}"
        ),
        span,
    )
}

pub(crate) fn ensure_bindable_sid(
    sid: CoreDomainIdentity,
    span: Span,
) -> Result<(), LanguageError> {
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
    sid: crate::CoreDomainIdentity,
    args: &[Value],
    expected: usize,
    span: Span,
) -> Result<(), LanguageError> {
    if args.len() == expected {
        return Ok(());
    }
    let width = sid.width();
    let qualified_identity = format!("D{width}:{:0width$b}", sid.packed_bits(), width = width);
    Err(LanguageError::new(
        ErrorKind::Arity,
        format!(
            "{qualified_identity}: expected / ochikuvalosia / erwartet {expected}; received / otrymano / erhalten {}",
            args.len()
        ),
        span,
    ))
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum DomainPrimitiveKind {
    StringToSymbol,
    SymbolToString,
    CharCode,
    CodeChar,
    Read,
    WriteToString,
    Equal,
    AtomPredicate,
    AtomEquality,
    PairConstruct,
    EnvironmentReflection,
}

/// Backend-neutral classification of current exact-domain value primitives.
///
/// Exact domain + exact word select an explicit mechanism; this table never
/// projects a current identity onto historical CoreDomainIdentity/Function8 bytes. The four
/// D9 string operations below are a bounded mechanism cut, not general D9
/// callability: every other D9 resident remains fail-closed.
pub(crate) fn domain_primitive_kind(identity: CoreDomainIdentity) -> Option<DomainPrimitiveKind> {
    match identity {
        CoreDomainIdentity::D3(word) => match word.word().packed_bits() {
            0b010 => Some(DomainPrimitiveKind::AtomPredicate),
            0b101 => Some(DomainPrimitiveKind::AtomEquality),
            0b111 => Some(DomainPrimitiveKind::PairConstruct),
            0b100 | 0b011 => None,
            _ => None, // QUOTE/COND are syntax routes, 000 is structural empty
        },
        CoreDomainIdentity::D8(word) => match word.word().packed_bits() {
            // D8:00000000 CODE-CHAR (укр `символ-за-кодом`) is the exact
            // inverse of D8:11100000 CHAR-CODE. It is the identity the domain
            // table (lib/domains/d8.lisp), the projection catalog and the
            // semantic registry already ratify for that surface, and the one
            // the CLI string projection lowers every string literal into.
            0b00000000 => Some(DomainPrimitiveKind::CodeChar),
            0b11100000 => Some(DomainPrimitiveKind::CharCode),
            0b11101101 => Some(DomainPrimitiveKind::StringToSymbol),
            0b11101110 => Some(DomainPrimitiveKind::SymbolToString),
            0b11101010 => Some(DomainPrimitiveKind::Read),
            0b11110100 => Some(DomainPrimitiveKind::WriteToString),
            0b11110111 => Some(DomainPrimitiveKind::Equal),
            0b11100111 => Some(DomainPrimitiveKind::EnvironmentReflection),
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
            DomainPrimitiveKind::StringToSymbol | DomainPrimitiveKind::SymbolToString => 1,
            DomainPrimitiveKind::CharCode => 1,
            DomainPrimitiveKind::CodeChar => 1,
            DomainPrimitiveKind::Read => args.len(),
            DomainPrimitiveKind::WriteToString => 1,
            DomainPrimitiveKind::AtomPredicate => 1,
            DomainPrimitiveKind::AtomEquality => 2,
            DomainPrimitiveKind::PairConstruct => 2,
            DomainPrimitiveKind::Equal => 2,
            DomainPrimitiveKind::EnvironmentReflection => 0,
        };
        if matches!(kind, DomainPrimitiveKind::Read) && args.len() > 1 {
            return Err(LanguageError::new(
                ErrorKind::Arity,
                format!(
                    "{identity}: expected at most 1 argument; received {}",
                    args.len()
                ),
                span,
            ));
        }
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
            DomainPrimitiveKind::EnvironmentReflection => {
                builtins::environment_reflection(args, environment, span)
            }
            DomainPrimitiveKind::StringToSymbol => {
                // D8:11101101, direct scalar/string mechanism, no byte fallback.
                special_forms::string_to_symbol_values(args, span)
            }
            DomainPrimitiveKind::SymbolToString => {
                // D8:11101110, exact inverse carrier with the existing string
                // mechanism. No historical byte/alias is ever consulted.
                special_forms::symbol_to_string_values(args, span)
            }
            DomainPrimitiveKind::CharCode => {
                // D8:11100000 is the explicit Unicode scalar -> D24 boundary.
                // Temporary lower helpers may already return D24 or an exact
                // unqualified scalar; neither escapes this canonical route.
                let scalar = builtins::string_to_codepoint(args, environment, span)?;
                match &scalar {
                    Value::BinaryNumber(numeric) if numeric.numeric_domain_width() == Some(24) => {
                        Ok(scalar.clone())
                    }
                    Value::Number(codepoint, crate::Exactness::Exact)
                        if codepoint.is_finite()
                            && codepoint.fract() == 0.0
                            && (0.0..=0x10ffff as f64).contains(codepoint) =>
                    {
                        let scalar = *codepoint as u32;
                        let word = (0u32..24)
                            .rev()
                            .map(|shift| ((scalar >> shift) & 1) as u8)
                            .collect::<Vec<_>>();
                        let numeric = crate::BinaryNumber::from_numeric_domain_bits(24, &word)
                            .expect("one Unicode scalar fits exact D24");
                        Ok(Value::BinaryNumber(numeric))
                    }
                    _ => Err(LanguageError::new(
                        ErrorKind::Type,
                        "D8 CHAR-CODE must produce one exact D24 Unicode scalar",
                        span,
                    )),
                }
            }
            DomainPrimitiveKind::CodeChar => {
                // D8:00000000 CODE-CHAR: one already-interpreted Unicode scalar
                // becomes the language's immutable one-character string.
                // Unicode/UTF-8 policy stays in Lisp; this only materializes a
                // scalar, exactly like the admitted D8:11100000 CHAR-CODE does
                // in the opposite direction. No historical byte is consulted.
                special_forms::codepoint_to_string_values(args, span)
            }
            DomainPrimitiveKind::Read => {
                // D8:11101010 owns canonical READ, not the historical SID.
                special_forms::read_values(args, environment, span)
            }
            DomainPrimitiveKind::WriteToString => {
                // D8:11110100 owns WRITE-TO-STRING; call the existing
                // serializer directly, never reconstitute a historical byte.
                special_forms::write_to_string_values(args, environment, span)
            }
        }
    })())
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum D9PrimitiveKind {
    Append,
    Empty,
    Rest,
    Prefix,
    First,
    StringP,
    ReadAll,
}

fn d9_primitive_kind(identity: crate::DomainIdentity) -> Option<D9PrimitiveKind> {
    let crate::DomainIdentity::D9(word) = identity else {
        return None;
    };
    match word.word().packed_bits() {
        0b110011110 => Some(D9PrimitiveKind::Append),
        0b110011100 => Some(D9PrimitiveKind::Empty),
        0b110011101 => Some(D9PrimitiveKind::Rest),
        0b110101010 => Some(D9PrimitiveKind::Prefix),
        0b110101011 => Some(D9PrimitiveKind::First),
        0b110100110 => Some(D9PrimitiveKind::StringP),
        0b110101001 => Some(D9PrimitiveKind::ReadAll),
        _ => None,
    }
}

/// True only for the seven ratified D9 value mechanisms required by the
/// machine-admission wire checker. This is deliberately outside
/// CoreDomainIdentity: D9 identity remains universal-domain identity, not Core.
pub(crate) fn has_d9_mechanism(identity: crate::DomainIdentity) -> bool {
    d9_primitive_kind(identity).is_some()
}

/// Execute the bounded D9 string mechanism cut. Routing is selected from the
/// full nine-bit D9 identity; the called functions are reused implementation
/// bodies only, never looked up or invoked through a historical SID8.
pub(crate) fn invoke_d9_mechanism(
    identity: crate::DomainIdentity,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    let kind = d9_primitive_kind(identity)?;
    Some((|| {
        let expected = match kind {
            D9PrimitiveKind::Append | D9PrimitiveKind::Prefix => 2,
            D9PrimitiveKind::Empty
            | D9PrimitiveKind::Rest
            | D9PrimitiveKind::First
            | D9PrimitiveKind::StringP
            | D9PrimitiveKind::ReadAll => 1,
        };
        if args.len() != expected {
            return Err(LanguageError::new(
                ErrorKind::Arity,
                format!(
                    "D9 {identity}: expected {expected} arguments; received {}",
                    args.len()
                ),
                span,
            ));
        }
        let value = match kind {
            D9PrimitiveKind::Append => super::special_forms::string_append_values(args, span)?,
            D9PrimitiveKind::Empty => super::builtins::string_empty(args, environment, span)?,
            D9PrimitiveKind::Rest => super::builtins::string_rest(args, environment, span)?,
            D9PrimitiveKind::Prefix => super::builtins::string_prefix(args, environment, span)?,
            D9PrimitiveKind::First => super::builtins::string_first(args, environment, span)?,
            D9PrimitiveKind::StringP => Value::predicate_bit(matches!(&args[0], Value::String(_))),
            D9PrimitiveKind::ReadAll => {
                super::special_forms::read_all_values(args, environment, span)?
            }
        };
        if matches!(
            kind,
            D9PrimitiveKind::Empty | D9PrimitiveKind::Prefix | D9PrimitiveKind::StringP
        ) && value.as_predicate_bit().is_none()
        {
            return Err(LanguageError::new(
                ErrorKind::Type,
                format!("D9 {identity} must return an exact D1 PredicateBit; got {value}"),
                span,
            ));
        }
        Ok(value)
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

/// Compact-derived bootstrap laws ratified by Contract D4: NOT, NULL, LIST, APPEND.
///
/// These are bounded reference value-call mechanisms. NOT consumes and returns
/// only exact D1 PredicateBit values; NULL checks structural EMPTY (Value::Nil).
/// Neither law coerces Number 0/1, host Bool, historical truth, or EMPTY into a
/// predicate. LIST/APPEND use the D3 pair/empty value algebra. These mechanisms
/// do not add residents, host effects, or historical W8 aliases.
fn require_exactly_one_d4_argument(
    coordinate: u8,
    args: &[Value],
    span: Span,
) -> Result<(), LanguageError> {
    if args.len() == 1 {
        return Ok(());
    }
    Err(LanguageError::new(
        ErrorKind::Arity,
        format!(
            "D4:{coordinate:04b} expects exactly one argument / потребує рівно один аргумент; отримано {}",
            args.len()
        ),
        span,
    ))
}

/// Exact D4:0001 EVAL mechanism. The argument arrives as a value; the
/// existing SENS evaluator converts that represented datum back into an
/// expression and evaluates it in the current environment. Identity and width
/// select this route; an equal payload in another domain cannot inherit it.
fn invoke_d4_eval(
    identity: CoreDomainIdentity,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    let CoreDomainIdentity::D4(word) = identity else {
        return None;
    };
    if word.word().packed_bits() != 0b0001 {
        return None;
    }
    Some((|| {
        exact_args(identity, args, 1, span)?;
        special_forms::eval_values(args, environment, span)
    })())
}

/// Точний механізм D4:0000: викликає функцію елементами правильного списку
/// аргументів. Список є даними, а його елементи вже обчислені.
fn invoke_d4_apply(
    identity: CoreDomainIdentity,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    let CoreDomainIdentity::D4(word) = identity else {
        return None;
    };
    if word.word().packed_bits() != 0b0000 {
        return None;
    }
    Some((|| {
        exact_args(identity, args, 2, span)?;
        let mut applied_arguments = Vec::new();
        let mut cursor = &args[1];
        loop {
            match cursor {
                Value::Nil => break,
                Value::Pair(pair) => {
                    applied_arguments.push(pair.head.clone());
                    cursor = &pair.tail;
                }
                _ => {
                    return Err(LanguageError::new(
                        ErrorKind::Type,
                        "D4:0000 застосувати очікує правильний список аргументів",
                        span,
                    ));
                }
            }
        }
        apply_callable_value(&args[0], &applied_arguments, environment, span)
    })())
}

/// Викликає лише вже обчислене значення з наявним механізмом SENS.
fn apply_callable_value(
    function: &Value,
    arguments: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    match function {
        Value::Closure(closure) => closures::apply_values(closure.clone(), arguments, span),
        Value::Builtin(builtin) => (builtin.func)(arguments, environment, span),
        Value::DomainIdentity(identity) => {
            if let Some(core_identity) = identity.core_operation() {
                return invoke_domain_identity(core_identity, arguments, environment, span);
            }
            match environment.domain_code_slot(*identity) {
                Some(Value::Closure(ref closure)) => {
                    closures::apply_values(closure.clone(), arguments, span)
                }
                Some(Value::Builtin(ref builtin)) => {
                    (builtin.func)(arguments, environment, span)
                }
                _ => Err(LanguageError::new(
                    ErrorKind::Type,
                    format!(
                        "D4:0000 застосувати: D{} {} не має допущеного механізму виклику",
                        identity.width(),
                        identity
                    ),
                    span,
                )),
            }
        }
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "D4:0000 застосувати очікує значення функції з допущеним механізмом",
            span,
        )),
    }
}

fn invoke_compact_derived_d4(
    identity: CoreDomainIdentity,
    args: &[Value],
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    let CoreDomainIdentity::D4(word) = identity else {
        return None;
    };
    match word.word().packed_bits() {
        // Ratified D4 NOT: exact D1 NO/YES is negated without host truthiness.
        0b0100 => Some((|| {
            require_exactly_one_d4_argument(0b0100, args, span)?;
            let value = args[0].as_predicate_bit().ok_or_else(|| {
                LanguageError::new(
                    ErrorKind::Type,
                    "D4:0100 NOT requires an exact D1 PredicateBit; Number, host Bool, and structural EMPTY are not predicates",
                    span,
                )
            })?;
            Ok(Value::predicate_bit(!value))
        })()),
        // Ratified D4 NULL: only structural empty list is empty; D1 NO is data.
        0b0101 => Some((|| {
            require_exactly_one_d4_argument(0b0101, args, span)?;
            Ok(Value::predicate_bit(matches!(args[0], Value::Nil)))
        })()),
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
                        Value::Pair(node) => {
                            items.push(node.head.clone());
                            cursor = &node.tail;
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
    if let CoreDomainIdentity::D9(_) = identity {
        if let Some(result) = super::selector_law::invoke(identity.into(), args, span) {
            return result;
        }
        let domain_identity = crate::DomainIdentity::from(identity);
        // A concrete language-owned definition bound to this exact D9 identity
        // takes precedence. Residency alone still grants nothing: the slot is
        // populated only by an actual callable definition.
        if let Some(bound) = environment.domain_code_slot(domain_identity) {
            let result = match &bound {
                Value::Closure(closure) => {
                    Some(closures::apply_values(closure.clone(), args, span)?)
                }
                Value::Builtin(builtin) => Some((builtin.func)(args, environment, span)?),
                _ => None,
            };
            if let Some(value) = result {
                return canonicalize_domain_result(identity, value, span);
            }
        }

        return invoke_d9_mechanism(domain_identity, args, environment, span).unwrap_or_else(
            || {
                Err(LanguageError::new(
                    ErrorKind::Type,
                    format!("D9 identity has no admitted value-call mechanism: {identity}"),
                    span,
                ))
            },
        );
    }

    if let Some(result) = invoke_d4_apply(identity, args, environment, span) {
        return result;
    }
    if let Some(result) = invoke_d4_eval(identity, args, environment, span) {
        return result;
    }
    if let Some(result) = super::selector_law::invoke(identity.into(), args, span) {
        return result;
    }

    if let Some(result) = invoke_compact_derived_d4(identity, args, span) {
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

/// Compatibility/backend mechanism bridge selected by historical CoreDomainIdentity.
pub(crate) fn invoke_semantic_ref(
    sid: CoreDomainIdentity,
    args: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    // Transitional input adapter only: the five historical Canon value calls
    // now execute the ratified D3 mechanism, never duplicate Rust SID8 bodies.
    // No historical byte gains placement authority; an unmapped SID fails closed.
    if let Some(identity) = semantic_registry::compatibility_d3_route_from_ratified_domains(sid) {
        if matches!(route_kind_for_sid(sid), Some(SidRouteKind::ValueCall)) {
            return invoke_domain_identity(identity, args, environment, span);
        }
    }
    // Execution requires an exact current mechanism or a concrete callable
    // bound to this domain-qualified identity. No historical W8 dispatch.
    match &environment.code_slot(sid) {
        Some(Value::Closure(closure)) => {
            return closures::apply_values(closure.clone(), args, span)
        }
        Some(Value::Builtin(builtin)) => return (builtin.func)(args, environment, span),
        _ => {}
    }

    if let Some(profile) = environment.selected_core_profile() {
        if matches!(
            profile_mechanism_route(profile, sid),
            Some(ProfileMechanismRouteKind::RegisteredHostMechanism)
        ) {
            return match super::capabilities::dispatch_sens_capability(sid, args, environment, span)
            {
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
pub(crate) fn has_primitive(identity: CoreDomainIdentity) -> bool {
    matches!(route_kind_for_sid(identity), Some(SidRouteKind::ValueCall))
}

/// #1455: визначення (функція або макрос) верхнього рівня з назвою з таблиці функцій, чий код не
/// має примітиву й не є особливою формою, стає механізмом цього коду. Лише
/// перше визначення; затінення назви пізніше слот не змінює.
pub(crate) fn bind_language_definition(name: &str, value: &Value, environment: &Environment) {
    if !environment.is_root()
        || !matches!(
            value,
            Value::Closure(_) | Value::Builtin(_) | Value::Macro(_)
        )
    {
        return;
    }

    if let Some(identity) = semantic_registry::d9_binding_identity_for_definition(name) {
        // Concrete Lisp implementation only; D9 itself remains non-Core.
        environment.bind_domain_code_slot_once(identity, value.clone());
    }

    if let Some(identity) = semantic_registry::d10_binding_identity_for_definition(name) {
        // D10 width/residency is not callability: this exact slot exists only
        // because a concrete Core4 root callable was evaluated above.
        environment.bind_domain_code_slot_once(identity, value.clone());
    }

    if let Some(identity) = semantic_registry::d6_binding_identity_for_definition(name) {
        // D6 residency remains separate from execution. Only an actual
        // language-owned callable definition can populate this exact slot.
        if identity.core_operation().is_none() {
            environment.bind_domain_code_slot_once(identity, value.clone());
        }
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
