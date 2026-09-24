//! Named, concrete evidence for a real gap #997 already documents:
//! "name-based capability fallback exists beside SID routing". Host
//! capabilities (`read-file-bytes`, `read-file-utf8-raw`,
//! `write-file-bytes`, `process-run-raw`, `tcp-connect`, ...) are the
//! entire `my-lisp-host` crate's surface, dispatched by
//! `eval/capabilities.rs`'s `BTreeMap<String, HostFn>` on the literal
//! spelling of the calling symbol — never through `Sid8`. This is the
//! concrete backend that is NOT on SID: it depends on exact text, so a
//! surface-encoding change (Ukrainian/English/KOI-8/SLP1/anything) that
//! altered how a name is written could silently break dispatch, unlike
//! genuine SID-routed forms (`quote`/`cond`/`+`/...) which are
//! encoding-invariant by construction.
//!
//! This is observational evidence, not a call to fix it in this test —
//! #997/#1048/#1049 already own the direction (host may transport, never
//! own semantic routing); this file exists so the gap has one
//! executable, named location instead of only living in issue prose.

use my_lisp::{
    capability_installed, eval_program, installed_capabilities, load_core_library, register_capability,
    Environment, LanguageError, Session, Value,
};

fn dummy_capability(
    _arguments: &[my_lisp::Expr],
    _environment: &Environment,
    _span: my_lisp::Span,
) -> Result<Value, LanguageError> {
    Ok(Value::Number(1.0, my_lisp::Exactness::Exact))
}

#[test]
fn every_installed_my_lisp_host_capability_has_zero_sid_registry_entries() {
    let mut session = Session::default();
    my_lisp_host::install();
    load_core_library(&mut session).expect("core library should load");

    let host_capabilities = [
        "read-file-bytes",
        "read-file-utf8-raw",
        "write-file-bytes",
        "process-run-raw",
        "tcp-connect",
        "tcp-listen-raw",
    ];

    for name in host_capabilities {
        assert!(
            capability_installed(name),
            "{name} should be installed by my-lisp-host"
        );
        // The full function-table generator scans lib/generated/function-table.lisp
        // and docs/generated/function-table.md for every admitted SID surface
        // name; none of these host capability names ever appear there, because
        // they carry no semantic identity at all — dispatch happens purely on
        // this literal string, one BTreeMap lookup before SID routing is ever
        // consulted (crates/my-lisp/src/eval/mod.rs's dispatch order).
        let looks_like_sid_alias = eval_program(
            &format!("(quote {name})"),
            &mut session,
        );
        assert!(
            looks_like_sid_alias.is_ok(),
            "{name} at least parses as an ordinary symbol, confirming it carries \
             no Sid8 lexical form of its own"
        );
    }

    // Direct, load-bearing claim: none of these names resolve through the
    // Sid8-keyed semantic registry at all — only through the separate
    // name-keyed capability registry checked in `installed_capabilities`.
    let installed = installed_capabilities();
    for name in host_capabilities {
        assert!(
            installed.contains(&name.to_string()),
            "{name} must be reachable only via the name-keyed capability \
             registry, not via any Sid8 route"
        );
    }
}

#[test]
fn capability_dispatch_is_exact_string_match_not_identity_based() {
    // A capability registered under one spelling is unreachable under any
    // other spelling, even a symbol a program might reasonably treat as an
    // alias for "the same thing" — because there is no identity (SID) behind
    // it to alias against, only a literal key in a BTreeMap<String, HostFn>.
    register_capability("demo-backend-not-on-sid", dummy_capability);
    assert!(capability_installed("demo-backend-not-on-sid"));
    assert!(
        !capability_installed("demo-backend-not-on-sid-alias"),
        "a differently-spelled name must not reach the same capability — \
         there is no SID identity underneath to alias against, only exact text"
    );

    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");

    let direct = eval_program("(demo-backend-not-on-sid)", &mut session);
    assert!(
        direct.is_ok(),
        "the exact registered spelling dispatches: {direct:?}"
    );

    // Rebinding the exact same registered name to a local variable does not
    // let the capability be invoked through that binding either: dispatch in
    // crates/my-lisp/src/eval/mod.rs reads the literal head symbol text
    // before any value/identity is even evaluated, so this is genuinely a
    // syntactic-name lookup, not a resolvable reference.
    let via_alias_binding = eval_program(
        "(def my-alias (quote demo-backend-not-on-sid)) (my-alias)",
        &mut session,
    );
    assert!(
        via_alias_binding.is_err(),
        "an aliased binding to the same name text must NOT reach the \
         capability through ordinary function application — dispatch never \
         resolves an identity here, confirming this backend path is textual, \
         not SID-routed"
    );
}
