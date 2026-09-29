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
use crate::{Environment, ErrorKind, Expr, LanguageError, Sens8, Span, Value};
use std::collections::{BTreeMap, HashMap};
use std::sync::{OnceLock, RwLock};

/// Signature of one installed capability handler. A plain function
/// pointer keeps the registry `Copy`/`Send` and forbids stateful
/// closures - capabilities get their state (allowlists, etc.) through
/// the `Environment`, exactly like every kernel primitive.
pub type HostFn = fn(&[Expr], &Environment, Span) -> Result<Value, LanguageError>;

/// Тимчасова межа міграції #1779: значення вже обчислене evaluator-ом,
/// а Span лишається суто діагностичною метаданою механізму.
#[derive(Clone, Debug)]
pub struct EvaluatedArg {
    pub value: Value,
    pub span: Span,
}

pub type EvaluatedHostFn =
    fn(&[EvaluatedArg], &Environment, Span) -> Result<Value, LanguageError>;

#[derive(Clone, Copy)]
enum HostHandler {
    Raw(HostFn),
    Evaluated(EvaluatedHostFn),
}

/// Host mechanism for one already-existing exact SENS function.
/// The key is the eight-bit function itself; this registry owns no function meaning.
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
pub fn register_evaluated_capability(name: &str, handler: EvaluatedHostFn) {
    registry()
        .write()
        .expect("capability registry poisoned")
        .insert(name.to_string(), HostHandler::Evaluated(handler));
    super::closures::bump_resolution_epoch();
}

/// Remove one previously installed capability.
pub fn unregister_capability(name: &str) {
    if let Ok(mut map) = registry().write() {
        map.remove(name);
    }
}

/// Attach a host mechanism to one exact SENS function.
/// Re-registering replaces only the mechanism; it cannot mint or reinterpret SENS.
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
        CapabilityLookup::Present(HostHandler::Evaluated(handler)) => {
            let result = (|| {
                let mut evaluated = Vec::with_capacity(arguments.len());
                for argument in arguments {
                    evaluated.push(EvaluatedArg {
                        value: super::evaluate(argument, environment)?,
                        span: argument.span,
                    });
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

/// Mechanical lookup/execution seam for one already-registered exact SENS function.
///
/// #1406: production has no caller until #1411 supplies an explicit SENS-owned
/// raw-invoke mechanism admission. The direct seam exists only for its mechanical
/// unit witness in this slice; registration/storage remain production availability.
#[cfg(test)]
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
