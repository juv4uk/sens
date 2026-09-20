//! capabilities.rs - the registration point for host capabilities.
//!
//! The canonical core ships ZERO host capabilities: no filesystem, no
//! processes, no sockets. What it ships instead is this registry: a host
//! adapter (the `my-lisp-host` crate, a WASM shim, an embedder) may
//! install named special forms at startup. Until something registers a
//! name, evaluating it falls through to ordinary function application
//! and fails `UnknownSymbol` like any other unbound name - the same
//! fail-named discipline as everything else (S2).
//!
//! This makes "capability-free core" physically true rather than a
//! policy statement: the OS-touching code lives outside this crate, and
//! a build that never calls the installer cannot reach it.

use super::EvalStep;
use crate::{Environment, ErrorKind, Expr, LanguageError, Span, Value};
use std::collections::BTreeMap;
use std::sync::{OnceLock, RwLock};

/// Signature of one installed capability handler. A plain function
/// pointer keeps the registry `Copy`/`Send` and forbids stateful
/// closures - capabilities get their state (allowlists, etc.) through
/// the `Environment`, exactly like every kernel primitive.
pub type HostFn = fn(&[Expr], &Environment, Span) -> Result<Value, LanguageError>;

#[derive(Clone, Copy)]
enum CapabilityLookup {
    Present(HostFn),
    Absent,
    Unreadable,
}

fn lookup_capability(
    source: &RwLock<BTreeMap<String, HostFn>>,
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

fn registry() -> &'static RwLock<BTreeMap<String, HostFn>> {
    static REGISTRY: OnceLock<RwLock<BTreeMap<String, HostFn>>> = OnceLock::new();
    REGISTRY.get_or_init(|| RwLock::new(BTreeMap::new()))
}

fn semantic_registry() -> &'static RwLock<BTreeMap<u8, HostFn>> {
    static REGISTRY: OnceLock<RwLock<BTreeMap<u8, HostFn>>> = OnceLock::new();
    REGISTRY.get_or_init(|| RwLock::new(BTreeMap::new()))
}

/// Install one capability under its surface-form name (e.g. "read-file").
/// Re-registering the same name replaces the previous handler, so an
/// embedder can override or withdraw capabilities deliberately.
pub fn register_capability(name: &str, handler: HostFn) {
    registry()
        .write()
        .expect("capability registry poisoned")
        .insert(name.to_string(), handler);
}

/// Remove one previously installed capability.
pub fn unregister_capability(name: &str) {
    if let Ok(mut map) = registry().write() {
        map.remove(name);
    }
}

/** Register a host implementation for one Lisp-owned semantic identity.
 *
 * The evaluator resolves surfaces to the opaque semantic ID first; this
 * registry contains only the implementation projection supplied by an
 * embedder. It never creates or renumbers semantic IDs.
 */
pub fn register_semantic_capability(semantic_id: u8, handler: HostFn) {
    semantic_registry()
        .write()
        .expect("semantic capability registry poisoned")
        .insert(semantic_id, handler);
}

/// Remove one implementation projection previously registered for a semantic ID.
pub fn unregister_semantic_capability(semantic_id: u8) {
    if let Ok(mut map) = semantic_registry().write() {
        map.remove(&semantic_id);
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
    source: &RwLock<BTreeMap<String, HostFn>>,
    name: &str,
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Option<Result<EvalStep, LanguageError>> {
    match lookup_capability(source, name) {
        CapabilityLookup::Present(handler) => {
            Some(handler(arguments, environment, span).map(EvalStep::Value))
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

fn dispatch_semantic_capability(
    semantic_id: u8,
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Option<Result<EvalStep, LanguageError>> {
    match semantic_registry().read() {
        Ok(map) => match map.get(&semantic_id).copied() {
            Some(handler) => Some(handler(arguments, environment, span).map(EvalStep::Value)),
            None => None,
        },
        Err(_) => Some(Err(LanguageError::new(
            ErrorKind::MechanismUnavailable,
            format!(
                "semantic capability registry unavailable while resolving SID: {semantic_id}"
            ),
            span,
        ))),
    }
}

pub(crate) fn dispatch_semantic_capability_for_surface(
    name: &str,
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Option<Result<EvalStep, LanguageError>> {
    let semantic_id = crate::semantic_registry::semantic_id_for_surface(name)?;
    dispatch_semantic_capability(semantic_id, arguments, environment, span)
}

#[cfg(test)]
mod honesty_tests {
    use super::*;

    #[test]
    fn semantic_dispatch_is_keyed_by_id_not_surface_spelling() {
        register_semantic_capability(250, dummy_handler);
        let environment = Environment::root();
        let result = dispatch_semantic_capability(250, &[], &environment, Span { start: 0, end: 0 })
            .expect("semantic capability should be found");
        assert!(result.is_ok());
        unregister_semantic_capability(250);
    }

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
