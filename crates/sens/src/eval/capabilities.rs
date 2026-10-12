//! capabilities.rs - the registration point for host capabilities.
//!
//! The canonical core ships ZERO host capabilities: no filesystem, no
//! processes, no sockets. What it ships instead is this registry: a host
//! adapter (the `sens-host` crate, a WASM shim, an embedder) may
//! install named special forms at startup. Until something registers a
//! name, evaluating it falls through to ordinary function application
//! and fails `UnknownSymbol` like any other unbound name - the same
//! fail-named discipline as everything else (S2).
//!
//! This makes "capability-free core" physically true rather than a
//! policy statement: the OS-touching code lives outside this crate, and
//! a build that never calls the installer cannot reach it.

use super::EvalStep;
use crate::{DomainIdentity, Environment, ErrorKind, Expr, LanguageError, Sens8, Span, Value};
use std::collections::{BTreeMap, HashMap};
use std::sync::{OnceLock, RwLock};

/// Signature of one installed capability handler. A plain function
/// pointer keeps the registry `Copy`/`Send` and forbids stateful
/// closures - capabilities get their state (allowlists, etc.) through
/// the `Environment`, exactly like every kernel primitive.
pub type HostFn = fn(&[Expr], &Environment, Span) -> Result<Value, LanguageError>;

type EvaluatedHostFn =
    fn(&[(Value, Span)], &Environment, Span) -> Result<Value, LanguageError>;

#[derive(Clone, Copy)]
enum HostHandler {
    Raw(HostFn),
    Evaluated {
        arity: usize,
        handler: EvaluatedHostFn,
    },
}

/// Host mechanism for one already-existing exact SENS function.
/// The key is the eight-bit function itself; this registry owns no function meaning.
/// Точнодоменний механізм хоста. Ключем є вся (ширина, біти) тотожність,
/// а не історичний байт. Реєстрація механізму сама не надає викликаності:
/// виконавець має спершу перевірити чинний закон і допуск координати.
pub(crate) type DomainHostFn =
    fn(DomainIdentity, &[Value], &Environment, Span) -> Result<Value, LanguageError>;

/// Історичний W8-адаптер залишається окремим від доменного реєстру.
pub type SensHostFn =
    fn(Sens8, &[Value], &Environment, Span) -> Result<Value, LanguageError>;

#[derive(Clone, Copy)]
enum CapabilityLookup {
    Present(HostHandler),
    Absent,
    Unreadable,
}

fn lookup_capability(
    source: &RwLock<BTreeMap<String, HostHandler>>,
    name: &str,
) -> CapabilityLookup {
    match source.read() {
        Ok(map) => match map.get(name).copied() {
            Some(handler) => CapabilityLookup::Present(handler),
            None => CapabilityLookup::Absent,
        },
        Err(_) => CapabilityLookup::Unreadable,
    }
}

fn registry() -> &'static RwLock<BTreeMap<String, HostHandler>> {
    static REGISTRY: OnceLock<RwLock<BTreeMap<String, HostHandler>>> = OnceLock::new();
    REGISTRY.get_or_init(|| RwLock::new(BTreeMap::new()))
}

fn domain_registry() -> &'static RwLock<HashMap<DomainIdentity, DomainHostFn>> {
    static REGISTRY: OnceLock<RwLock<HashMap<DomainIdentity, DomainHostFn>>> = OnceLock::new();
    REGISTRY.get_or_init(|| RwLock::new(HashMap::new()))
}

fn sens_registry() -> &'static RwLock<HashMap<Sens8, SensHostFn>> {
    static REGISTRY: OnceLock<RwLock<HashMap<Sens8, SensHostFn>>> = OnceLock::new();
    REGISTRY.get_or_init(|| RwLock::new(HashMap::new()))
}

/// Install one capability under its surface-form name (e.g. "read-file").
/// Re-registering the same name replaces the previous handler, so an
/// embedder can override or withdraw capabilities deliberately.
pub fn register_capability(name: &str, handler: HostFn) {
    registry()
        .write()
        .expect("capability registry poisoned")
        .insert(name.to_string(), HostHandler::Raw(handler));
    super::closures::bump_resolution_epoch();
}

/// #1779 migration seam: evaluator-owned argument evaluation, host receives
/// only ready Values plus their original source spans. The string key remains
/// private mechanism metadata and is not a SENS function identity.
pub fn register_evaluated_capability(name: &str, arity: usize, handler: EvaluatedHostFn) {
    registry()
        .write()
        .expect("capability registry poisoned")
        .insert(name.to_string(), HostHandler::Evaluated { arity, handler });
    super::closures::bump_resolution_epoch();
}

/// Remove one previously installed capability.
pub fn unregister_capability(name: &str) {
    if let Ok(mut map) = registry().write() {
        map.remove(name);
    }
}

/// Встановити механізм для перевіреної доменної координати. Цей запис —
/// лише доступність механізму; семантичний допуск належить оракулу/виконавцю.
pub(crate) fn register_domain_capability(identity: DomainIdentity, handler: DomainHostFn) {
    domain_registry()
        .write()
        .expect("domain host registry poisoned")
        .insert(identity, handler);
    super::closures::bump_resolution_epoch();
}

pub(crate) fn unregister_domain_capability(identity: DomainIdentity) {
    if let Ok(mut map) = domain_registry().write() {
        map.remove(&identity);
    }
}

/// Compatibility only: the historical W8 registry is never indexed by a
/// current D8 payload, even when the eight bits are visually identical.
/// Attach a host mechanism to one historical W8 function.
/// Re-registering replaces only the mechanism; it cannot mint current SENS.
pub fn register_sens_capability(sens: Sens8, handler: SensHostFn) {
    sens_registry()
        .write()
        .expect("SENS capability registry poisoned")
        .insert(sens, handler);
    super::closures::bump_resolution_epoch();
}

/// Detach a host mechanism without changing the function itself.
pub fn unregister_sens_capability(sens: Sens8) {
    if let Ok(mut map) = sens_registry().write() {
        map.remove(&sens);
    }
}

/// Compatibility projection: true only when the richer lookup observes the
/// capability as present. An unreadable registry is deliberately not treated
/// as canonical evidence of absence; evaluator dispatch handles that state
/// separately.
pub fn capability_installed(name: &str) -> bool {
    matches!(
        lookup_capability(registry(), name),
        CapabilityLookup::Present(_)
    )
}

/// Compatibility diagnostics projection. This legacy list-only API cannot
/// represent an unreadable registry, so it retains its empty-list fallback.
/// Canonical evaluator dispatch does not use this projection.
pub fn installed_capabilities() -> Vec<String> {
    registry()
        .read()
        .map(|map| map.keys().cloned().collect())
        .unwrap_or_default()
}

fn dispatch_capability_from(
    source: &RwLock<BTreeMap<String, HostHandler>>,
    name: &str,
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Option<Result<EvalStep, LanguageError>> {
    match lookup_capability(source, name) {
        CapabilityLookup::Present(HostHandler::Raw(handler)) => {
            Some(handler(arguments, environment, span).map(EvalStep::Value))
        }
        CapabilityLookup::Present(HostHandler::Evaluated { arity, handler }) => {
            if arguments.len() != arity {
                return Some(Err(LanguageError::new(
                    ErrorKind::Arity,
                    format!(
                        "{name}: expected / ochikuvalosia / erwartet {arity}; received / otrymano / erhalten {}",
                        arguments.len()
                    ),
                    span,
                )));
            }
            let result = (|| {
                let mut evaluated = Vec::with_capacity(arguments.len());
                for argument in arguments {
                    evaluated.push((super::evaluate(argument, environment)?, argument.span));
                }
                handler(&evaluated, environment, span)
            })();
            Some(result.map(EvalStep::Value))
        }
        CapabilityLookup::Absent => None,
        CapabilityLookup::Unreadable => Some(Err(LanguageError::new(
            ErrorKind::MechanismUnavailable,
            format!("capability registry unavailable while resolving: {name}"),
            span,
        ))),
    }
}

/// Dispatch fallback in the evaluator: consulted after the kernel's own
/// special forms and primitives, before ordinary function application.
/// A readable registry may establish absence; an unreadable registry is a
/// named mechanism failure and must never masquerade as `UnknownSymbol`.
pub(crate) fn dispatch_capability(
    name: &str,
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Option<Result<EvalStep, LanguageError>> {
    dispatch_capability_from(registry(), name, arguments, environment, span)
}

/// Точнодоменна межа виклику: тільки після окремої перевірки викликаності
/// координати. Відсутність запису не означає відсутності семантичного закону.
fn dispatch_domain_capability_from(
    source: &RwLock<HashMap<DomainIdentity, DomainHostFn>>,
    identity: DomainIdentity,
    arguments: &[Value],
    environment: &Environment,
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    match source.read() {
        Ok(map) => map
            .get(&identity)
            .copied()
            .map(|handler| handler(identity, arguments, environment, span)),
        Err(_) => Some(Err(LanguageError::new(
            ErrorKind::MechanismUnavailable,
            format!(
                "доменний механізм хоста недоступний: D{} {}",
                identity.width(), identity
            ),
            span,
        ))),
    }
}

pub(crate) fn dispatch_domain_capability(
    identity: DomainIdentity,
    arguments: &[Value],
    environment: &Environment,
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    dispatch_domain_capability_from(domain_registry(), identity, arguments, environment, span)
}

/// Історична W8-межа, відокремлена від поточного доменного механізму.
///
/// #1422: production may call this seam only downstream of the generated
/// SENS-owned profile-mechanism admission gate. Registration/storage remain
/// availability; this function cannot mint callability by itself.
pub(crate) fn dispatch_sens_capability(
    sens: Sens8,
    arguments: &[Value],
    environment: &Environment,
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    match sens_registry().read() {
        Ok(map) => map
            .get(&sens)
            .copied()
            .map(|handler| handler(sens, arguments, environment, span)),
        Err(_) => Some(Err(LanguageError::new(
            ErrorKind::MechanismUnavailable,
            format!("SENS capability registry unavailable while resolving: {sens}"),
            span,
        ))),
    }
}

#[cfg(test)]
mod honesty_tests {
    use super::*;

    fn dummy_handler(
        _arguments: &[Expr],
        _environment: &Environment,
        _span: Span,
    ) -> Result<Value, LanguageError> {
        Ok(Value::Nil)
    }

    #[test]
    fn lookup_distinguishes_present_absent_and_unreadable_registry() {
        let lock = RwLock::new(BTreeMap::new());
        lock.write()
            .expect("fresh local registry")
            .insert("demo".to_string(), HostHandler::Raw(dummy_handler as HostFn));

        assert!(matches!(
            lookup_capability(&lock, "demo"),
            CapabilityLookup::Present(_)
        ));
        assert!(matches!(
            lookup_capability(&lock, "missing"),
            CapabilityLookup::Absent
        ));

        let poisoned = std::panic::catch_unwind(|| {
            let _guard = lock.write().expect("lock is readable before poison");
            panic!("poison local test registry");
        });
        assert!(poisoned.is_err());
        assert!(matches!(
            lookup_capability(&lock, "demo"),
            CapabilityLookup::Unreadable
        ));
    }

    fn evaluated_handler(
        _arguments: &[(Value, Span)],
        _environment: &Environment,
        _span: Span,
    ) -> Result<Value, LanguageError> {
        Ok(Value::Nil)
    }

    #[test]
    fn evaluated_handler_checks_arity_before_evaluating_arguments() {
        let lock = RwLock::new(BTreeMap::new());
        lock.write()
            .expect("fresh local registry")
            .insert(
                "demo".to_string(),
                HostHandler::Evaluated {
                    arity: 1,
                    handler: evaluated_handler,
                },
            );

        let program = crate::parse("(demo missing extra)").expect("probe parses");
        let crate::ExprKind::List(items) = &program[0].kind else {
            panic!("probe must be a call");
        };
        let span = program[0].span;
        let error = match dispatch_capability_from(
            &lock,
            "demo",
            &items[1..],
            &Environment::root(),
            span,
        )
        .expect("registered evaluated handler")
        {
            Err(error) => error,
            Ok(_) => panic!("wrong arity must fail before callback"),
        };

        assert_eq!(error.kind, ErrorKind::Arity);
        assert_eq!(error.span, span);
    }

    fn d3_nil(
        _identity: DomainIdentity,
        _arguments: &[Value],
        _environment: &Environment,
        _span: Span,
    ) -> Result<Value, LanguageError> {
        Ok(Value::Nil)
    }

    fn d4_marker(
        _identity: DomainIdentity,
        _arguments: &[Value],
        _environment: &Environment,
        _span: Span,
    ) -> Result<Value, LanguageError> {
        Ok(Value::Symbol(std::rc::Rc::from("д4")))
    }

    #[test]
    fn domain_host_registry_distinguishes_same_payload_and_legacy_w8() {
        use crate::{Bija3, Bit3, Bit4, Bit8, CoreD4, CoreD8};
        let d3 = DomainIdentity::D3(Bija3::from_word(Bit3::new(0b101).unwrap()));
        let d4 = DomainIdentity::D4(CoreD4::from_word(Bit4::new(0b0101).unwrap()));
        let d8 = DomainIdentity::D8(CoreD8::from_word(Bit8::new(0b10101000).unwrap()));
        let old = crate::sens!(10101000);
        assert_eq!(d3.packed_bits(), d4.packed_bits());
        assert_eq!(d8.packed_bits(), old.packed_byte() as u64);

        let routes = RwLock::new(HashMap::from([
            (d3, d3_nil as DomainHostFn),
            (d4, d4_marker as DomainHostFn),
        ]));
        let environment = Environment::root();
        let span = Span::default();
        assert_eq!(
            dispatch_domain_capability_from(&routes, d3, &[], &environment, span)
                .expect("D3 installed").expect("D3 mechanism"),
            Value::Nil
        );
        assert_eq!(
            dispatch_domain_capability_from(&routes, d4, &[], &environment, span)
                .expect("D4 installed").expect("D4 mechanism"),
            Value::Symbol(std::rc::Rc::from("д4"))
        );
        assert!(dispatch_domain_capability_from(&routes, d8, &[], &environment, span).is_none());
        // Old W8 INVOKE cannot silently become current D8 ROUND.
        let legacy = HashMap::from([(old, sens_handler as SensHostFn)]);
        assert!(legacy.contains_key(&old));
        assert!(routes.read().unwrap().get(&d8).is_none());
    }

    #[test]
    fn domain_host_registration_does_not_make_missing_domain_callable() {
        use crate::{Bija3, Bit3, Bit4, CoreD4};
        let d3 = DomainIdentity::D3(Bija3::from_word(Bit3::new(0b101).unwrap()));
        let d4 = DomainIdentity::D4(CoreD4::from_word(Bit4::new(0b0101).unwrap()));
        unregister_domain_capability(d3);
        unregister_domain_capability(d4);
        register_domain_capability(d3, d3_nil);
        let environment = Environment::root();
        let span = Span::default();
        assert!(dispatch_domain_capability(d4, &[], &environment, span).is_none());
        assert!(dispatch_domain_capability(d3, &[], &environment, span).is_some());
        unregister_domain_capability(d3);
        assert!(dispatch_domain_capability(d3, &[], &environment, span).is_none());
    }

    #[test]
    fn poisoned_domain_host_registry_fails_closed() {
        use crate::{Bija3, Bit3};
        let d3 = DomainIdentity::D3(Bija3::from_word(Bit3::new(0b101).unwrap()));
        let lock = RwLock::new(HashMap::from([(d3, d3_nil as DomainHostFn)]));
        assert!(std::panic::catch_unwind(|| {
            let _guard = lock.write().unwrap();
            panic!("poison local domain registry");
        }).is_err());
        let error = dispatch_domain_capability_from(
            &lock, d3, &[], &Environment::root(), Span::default()
        ).expect("poisoned registry cannot count as absent")
         .expect_err("poisoned registry must fail");
        assert_eq!(error.kind, ErrorKind::MechanismUnavailable);
        assert!(error.message.contains("D3 101"), "{}", error.message);
    }

    fn sens_handler(
        sens: Sens8,
        _arguments: &[Value],
        _environment: &Environment,
        _span: Span,
    ) -> Result<Value, LanguageError> {
        Ok(Value::Symbol(std::rc::Rc::from(sens.to_string())))
    }

    #[test]
    fn sens_registry_is_keyed_by_exact_identity_without_ordering() {
        let sens = crate::sens!(10101000);
        unregister_sens_capability(sens);
        register_sens_capability(sens, sens_handler);

        let result = dispatch_sens_capability(
            sens,
            &[],
            &Environment::root(),
            Span::default(),
        )
        .expect("registered SENS mechanism")
        .expect("mechanism succeeds");
        assert_eq!(result.to_string(), "10101000");

        unregister_sens_capability(sens);
        assert!(dispatch_sens_capability(
            sens,
            &[],
            &Environment::root(),
            Span::default(),
        )
        .is_none());
    }

    #[test]
    fn unreadable_registry_dispatch_is_named_mechanism_failure() {
        let lock = RwLock::new(BTreeMap::new());
        let poisoned = std::panic::catch_unwind(|| {
            let _guard = lock.write().expect("lock is readable before poison");
            panic!("poison local test registry");
        });
        assert!(poisoned.is_err());

        let environment = Environment::root();
        let span = Span { start: 0, end: 4 };
        let result = dispatch_capability_from(&lock, "demo", &[], &environment, span)
            .expect("unreadable registry is an observed mechanism failure, not absence");

        let result = match result {
            Err(error) => error,
            Ok(_) => panic!("unreadable registry must fail named"),
        };

        assert_eq!(result.kind, ErrorKind::MechanismUnavailable);
        assert_ne!(result.kind, ErrorKind::UnknownSymbol);
    }
}
