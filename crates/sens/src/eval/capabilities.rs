//! capabilities.rs - the registration point for host capabilities.
//!
//! The canonical core ships ZERO host capabilities: no filesystem, no
//! processes, no sockets. What it ships instead is this registry: a host
//! adapter (the `sens-host` crate, a WASM shim, an embedder) may
//! install named host mechanisms at startup. Handlers receive already-evaluated
//! values; they are not special forms and cannot call back into raw AST evaluation.
//! Until something registers a name, evaluating it falls through to ordinary function application
//! and fails `UnknownSymbol` like any other unbound name - the same
//! fail-named discipline as everything else (S2).
//!
//! This makes "capability-free core" physically true rather than a
//! policy statement: the OS-touching code lives outside this crate, and
//! a build that never calls the installer cannot reach it.

use crate::{Environment, ErrorKind, LanguageError, Sens8, Span, Value};
use std::collections::{BTreeMap, HashMap};
use std::sync::{OnceLock, RwLock};

/// Signature of one installed host-mechanism handler.
///
/// The evaluator owns argument evaluation. A handler sees only ready values,
/// so the host layer cannot create a second raw-AST evaluator entry path.
/// A plain function pointer keeps the registry `Copy`/`Send`; capability
/// policy/state remains in the shared `Environment`.
pub type HostFn = fn(&[Value], &Environment, Span) -> Result<Value, LanguageError>;

/// Host mechanism for one already-existing exact SENS function.
/// The key is the eight-bit function itself; this registry owns no function meaning.
pub type SensHostFn = fn(Sens8, &[Value], &Environment, Span) -> Result<Value, LanguageError>;

#[derive(Clone, Copy)]
enum CapabilityLookup {
    Present(HostFn),
    Absent,
    Unreadable,
}

fn lookup_capability(source: &RwLock<BTreeMap<String, HostFn>>, name: &str) -> CapabilityLookup {
    match source.read() {
        Ok(map) => match map.get(name).copied() {
            Some(handler) => CapabilityLookup::Present(handler),
            None => CapabilityLookup::Absent,
        },
        Err(_) => CapabilityLookup::Unreadable,
    }
}

fn registry() -> &'static RwLock<BTreeMap<String, HostFn>> {
    static REGISTRY: OnceLock<RwLock<BTreeMap<String, HostFn>>> = OnceLock::new();
    REGISTRY.get_or_init(|| RwLock::new(BTreeMap::new()))
}

fn sens_registry() -> &'static RwLock<HashMap<Sens8, SensHostFn>> {
    static REGISTRY: OnceLock<RwLock<HashMap<Sens8, SensHostFn>>> = OnceLock::new();
    REGISTRY.get_or_init(|| RwLock::new(HashMap::new()))
}

/// Install one host mechanism under its private routing key.
///
/// The string is mechanism metadata, not a SENS function identity. Re-registering
/// the same key replaces the previous handler so an embedder can deliberately
/// override or withdraw the mechanism.
pub fn register_capability(name: &str, handler: HostFn) {
    registry()
        .write()
        .expect("capability registry poisoned")
        .insert(name.to_string(), handler);
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

fn capability_handler_from(
    source: &RwLock<BTreeMap<String, HostFn>>,
    name: &str,
    span: Span,
) -> Result<Option<HostFn>, LanguageError> {
    match lookup_capability(source, name) {
        CapabilityLookup::Present(handler) => Ok(Some(handler)),
        CapabilityLookup::Absent => Ok(None),
        CapabilityLookup::Unreadable => Err(LanguageError::new(
            ErrorKind::MechanismUnavailable,
            format!("capability registry unavailable while resolving: {name}"),
            span,
        )),
    }
}

/// Resolve one named host mechanism before argument evaluation.
///
/// The registry decides only whether a mechanism is installed. The evaluator
/// owns evaluation order and passes ready `Value` arguments to the handler.
pub(crate) fn capability_handler(name: &str, span: Span) -> Result<Option<HostFn>, LanguageError> {
    capability_handler_from(registry(), name, span)
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
        _arguments: &[Value],
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
            .insert("demo".to_string(), dummy_handler as HostFn);

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

        let result = dispatch_sens_capability(sens, &[], &Environment::root(), Span::default())
            .expect("registered SENS mechanism")
            .expect("mechanism succeeds");
        assert_eq!(result.to_string(), "10101000");

        unregister_sens_capability(sens);
        assert!(
            dispatch_sens_capability(sens, &[], &Environment::root(), Span::default(),).is_none()
        );
    }

    fn value_only_handler(
        arguments: &[Value],
        _environment: &Environment,
        _span: Span,
    ) -> Result<Value, LanguageError> {
        let [Value::Symbol(value)] = arguments else {
            panic!("host handler must receive one already-evaluated Symbol value");
        };
        Ok(Value::Symbol(value.clone()))
    }

    #[test]
    fn host_handler_receives_values_after_evaluator_owned_argument_evaluation() {
        const NAME: &str = "value-only-host-probe";
        unregister_capability(NAME);
        register_capability(NAME, value_only_handler);

        let mut session = crate::Session::default();
        let result = crate::eval_program(
            "(value-only-host-probe (00000001 already-evaluated))",
            &mut session,
        )
        .expect("host mechanism should receive the result of QUOTE, not its Expr");

        assert_eq!(result.value.to_string(), "already-evaluated");
        unregister_capability(NAME);
    }

    #[test]
    fn unreadable_registry_dispatch_is_named_mechanism_failure() {
        let lock = RwLock::new(BTreeMap::new());
        let poisoned = std::panic::catch_unwind(|| {
            let _guard = lock.write().expect("lock is readable before poison");
            panic!("poison local test registry");
        });
        assert!(poisoned.is_err());

        let span = Span { start: 0, end: 4 };
        let error = capability_handler_from(&lock, "demo", span)
            .expect_err("unreadable registry is an observed mechanism failure, not absence");

        assert_eq!(error.kind, ErrorKind::MechanismUnavailable);
        assert_ne!(error.kind, ErrorKind::UnknownSymbol);
    }
}
