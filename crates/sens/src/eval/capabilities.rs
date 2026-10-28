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
use crate::{CoreDomainIdentity, Environment, ErrorKind, Expr, LanguageError, Span, Value};
use std::collections::{BTreeMap, HashMap};
use std::sync::{OnceLock, RwLock};

/// Signature of one installed capability handler. A plain function
/// pointer keeps the registry `Copy`/`Send` and forbids stateful
/// closures - capabilities get their state (allowlists, etc.) through
/// the `Environment`, exactly like every kernel primitive.
pub type HostFn = fn(&[Expr], &Environment, Span) -> Result<Value, LanguageError>;

type EvaluatedHostFn = fn(&[(Value, Span)], &Environment, Span) -> Result<Value, LanguageError>;

#[derive(Clone, Copy)]
enum HostHandler {
    Raw(HostFn),
    Evaluated {
        arity: usize,
        handler: EvaluatedHostFn,
    },
}

/// Host mechanism for one already-existing exact SENS function.
/// The key is the exact-domain function identity; this registry owns no function meaning.
pub type SensHostFn =
    fn(CoreDomainIdentity, &[Value], &Environment, Span) -> Result<Value, LanguageError>;

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

fn sens_registry() -> &'static RwLock<HashMap<CoreDomainIdentity, SensHostFn>> {
    static REGISTRY: OnceLock<RwLock<HashMap<CoreDomainIdentity, SensHostFn>>> = OnceLock::new();
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

/// Attach a host mechanism to one exact SENS function.
/// Re-registering replaces only the mechanism; it cannot mint or reinterpret SENS.
pub fn register_sens_capability(sens: CoreDomainIdentity, handler: SensHostFn) {
    sens_registry()
        .write()
        .expect("SENS capability registry poisoned")
        .insert(sens, handler);
    super::closures::bump_resolution_epoch();
}

/// Detach a host mechanism without changing the function itself.
pub fn unregister_sens_capability(sens: CoreDomainIdentity) {
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
        CapabilityLookup::Present(_) if !environment.is_host_capability_allowed(name) => {
            Some(Err(LanguageError::new(
                ErrorKind::MechanismUnavailable,
                format!("host capability forbidden by session policy: {name}"),
                span,
            )))
        }
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

/// Mechanical lookup/execution seam for one already-registered exact SENS function.
///
/// #1422: production may call this seam only downstream of the generated
/// SENS-owned profile-mechanism admission gate. Registration/storage remain
/// availability; this function cannot mint callability by itself.
pub(crate) fn dispatch_sens_capability(
    sens: CoreDomainIdentity,
    arguments: &[Value],
    environment: &Environment,
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    match sens_registry().read() {
        Ok(map) => map.get(&sens).copied().map(|handler| {
            if !environment.are_exact_host_capabilities_allowed() {
                Err(LanguageError::new(
                    ErrorKind::MechanismUnavailable,
                    format!("exact host capability forbidden by session policy: {sens}"),
                    span,
                ))
            } else {
                handler(sens, arguments, environment, span)
            }
        }),
        Err(_) => Some(Err(LanguageError::new(
            ErrorKind::MechanismUnavailable,
            format!("SENS capability registry unavailable while resolving: {sens}"),
            span,
        ))),
    }
}

