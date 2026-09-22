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
use crate::{Environment, ErrorKind, Expr, LanguageError, Sid8, Span, Value};
use std::collections::BTreeMap;
use std::sync::{OnceLock, RwLock};

/// Signature of one installed capability handler. A plain function
/// pointer keeps the registry `Copy`/`Send` and forbids stateful
/// closures - capabilities get their state (allowlists, etc.) through
/// the `Environment`, exactly like every kernel primitive.
pub type HostFn = fn(&[Expr], &Environment, Span) -> Result<Value, LanguageError>;


/// Host execution mechanism keyed by an already-resolved exact Sid8.
/// This registry cannot define SID meaning; it can only provide an implementation
/// for a semantic identity that already exists in the Lisp-owned function table.
pub type SemanticHostFn =
    fn(Sid8, &[Value], &Environment, Span) -> Result<Value, LanguageError>;

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


fn semantic_registry() -> &'static RwLock<BTreeMap<Sid8, SemanticHostFn>> {
    static REGISTRY: OnceLock<RwLock<BTreeMap<Sid8, SemanticHostFn>>> = OnceLock::new();
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


/// Register a host implementation for one already-resolved semantic identity.
/// The exact Sid8 remains the key; no decimal/u8 identity is introduced here.
pub fn register_semantic_capability(semantic_id: Sid8, handler: SemanticHostFn) {
    semantic_registry()
        .write()
        .expect("semantic capability registry poisoned")
        .insert(semantic_id, handler);
}

/// Remove one host implementation projection without changing the semantic identity.
pub fn unregister_semantic_capability(semantic_id: Sid8) {
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


/// Mechanical host-implementation fallback for an exact semantic identity.
/// Canon/evaluator mechanisms get first chance; this is consulted only when
/// the local semantic callable table has no implementation for that Sid8.
pub(crate) fn dispatch_semantic_capability(
    semantic_id: Sid8,
    arguments: &[Value],
    environment: &Environment,
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    match semantic_registry().read() {
        Ok(map) => map
            .get(&semantic_id)
            .copied()
            .map(|handler| handler(semantic_id, arguments, environment, span)),
        Err(_) => Some(Err(LanguageError::new(
            ErrorKind::MechanismUnavailable,
            format!(
                "semantic capability registry unavailable while resolving SID: {semantic_id}"
            ),
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
