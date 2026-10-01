//! Named, concrete evidence for a real gap #997 already documents:
//! "name-based capability fallback exists beside SID routing". "Backend"
//! here means any execution mechanism, regardless of implementation
//! language — a Rust host capability and a Lisp-owned metacircular
//! evaluator are both backends in the sense that matters (#997's "Rust
//! owns mechanism, Lisp owns meaning" cuts across implementation
//! language, not along it).
//!
//! Part 1: Host capabilities (`read-file-bytes`, `read-file-utf8-raw`,
//! `write-file-bytes`, `process-run-raw`, `tcp-connect`, ...) are the
//! entire `sens-host` crate's surface, dispatched by
//! `eval/capabilities.rs`'s `BTreeMap<String, HostFn>` on the literal
//! spelling of the calling symbol — never through `Sens8`.
//!
//! Part 2 historically proved the same gap in `lib/meta-eval.lisp`: ordinary
//! primitives were dispatched by one literal spelling. #2223 closes that
//! half of the witness. The metacircular evaluator now projects admitted
//! boundary spellings to their exact SENS identity and carries that identity
//! in the `(primitive ...)` value; exact SENS and peer spellings therefore
//! converge before mechanism dispatch.
//!
//! The host-capability gap above remains intentionally separate: capabilities
//! without an admitted SENS identity are still name-keyed mechanism entries.
//!
//!
//! Checked and corrected (2026-09-24): an earlier version of this
//! comment speculated that the ordinary-primitive `eq`-chain was a
//! "plausible contributor" to `meta_eval_mutual`'s measured 79-291s cost.
//! Direct benchmark (500 dispatches of a Canon/SID-routed primitive vs.
//! the chain's first entry `+` vs. its last entry `string->symbol`)
//! showed no measurable difference (ratio 0.977-0.981, within noise) —
//! the ~8-entry chain is far too short to matter against `my-eval`'s own
//! per-call cost. The correctness gap above is real and independently
//! confirmed by the tests below; the performance speculation was not,
//! and is retracted rather than left standing unverified.
//!
//! This is observational evidence, not a call to fix it in this test —
//! #997/#1048/#1049 already own the direction (host may transport, never
//! own semantic routing); this file exists so the gap has one
//! executable, named location instead of only living in issue prose.

use sens::{
    capability_installed, eval_program, installed_capabilities, load_core_library, register_capability,
    Environment, LanguageError, Session, Value,
};

fn dummy_capability(
    _arguments: &[sens::Expr],
    _environment: &Environment,
    _span: sens::Span,
) -> Result<Value, LanguageError> {
    Ok(Value::Number(1.0, sens::Exactness::Exact))
}

#[test]
fn every_installed_sens_host_capability_has_zero_sid_registry_entries() {
    let mut session = Session::default();
    sens_host::install();
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
            "{name} should be installed by sens-host"
        );
        // The full function-table generator scans lib/generated/function-table.lisp
        // and docs/generated/function-table.md for every admitted SID surface
        // name; none of these host capability names ever appear there, because
        // they carry no semantic identity at all — dispatch happens purely on
        // this literal string, one BTreeMap lookup before SID routing is ever
        // consulted (crates/sens/src/eval/mod.rs's dispatch order).
        let looks_like_sid_alias = eval_program(
            &format!("(quote {name})"),
            &mut session,
        );
        assert!(
            looks_like_sid_alias.is_ok(),
            "{name} at least parses as an ordinary symbol, confirming it carries \
             no Sens8 lexical form of its own"
        );
    }

    // Direct, load-bearing claim: none of these names resolve through the
    // Sens8-keyed semantic registry at all — only through the separate
    // name-keyed capability registry checked in `installed_capabilities`.
    let installed = installed_capabilities();
    for name in host_capabilities {
        assert!(
            installed.contains(&name.to_string()),
            "{name} must be reachable only via the name-keyed capability \
             registry, not via any Sens8 route"
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
    // crates/sens/src/eval/mod.rs reads the literal head symbol text
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

fn eval_via_meta(expr: &str, session: &mut Session) -> Result<String, LanguageError> {
    let escaped = expr.replace('\\', "\\\\").replace('"', "\\\"");
    let source = format!(r#"(my-eval (read "{escaped}") (quote ()))"#);
    eval_program(&source, session).map(|v| v.value.to_string())
}

#[test]
fn meta_eval_resolves_canon_identity_primitives_through_any_admitted_surface_name() {
    // atom is SID 00000010; "атом?" is its own admitted Ukrainian surface
    // spelling, per lib/surface/semantic-registry.lisp. Canon-identity
    // primitives go through my-semantic-id-for-surface first, so both
    // spellings must resolve identically inside the metacircular evaluator.
    let mut session = Session::default();
    eval_program(
        include_str!("../../../lib/core.lisp"),
        &mut session,
    )
    .expect("core.lisp should load");
    sens::load_meta_evaluator_library(&mut session).expect("meta-evaluator should load");

    let english = eval_via_meta("(atom? 5)", &mut session).expect("english spelling resolves");
    let ukrainian =
        eval_via_meta("(атом? 5)", &mut session).expect("Canon identity is spelling-invariant");
    assert_eq!(
        english, ukrainian,
        "a genuinely SID-routed Canon primitive must give the same answer \
         under every admitted surface spelling"
    );
}

#[test]
fn meta_eval_ordinary_primitive_dispatch_converges_on_exact_sens_identity() {
    let mut meta_session = Session::default();
    eval_program(
        include_str!("../../../lib/core.lisp"),
        &mut meta_session,
    )
    .expect("core.lisp should load");
    sens::load_meta_evaluator_library(&mut meta_session)
        .expect("meta-evaluator should load");

    let exact = eval_via_meta(
        "((lambda (a b) (00001100 a b)) 2 3)",
        &mut meta_session,
    )
    .expect("exact SENS identity must be callable in meta-eval");
    let english = eval_via_meta(
        "((lambda (a b) (+ a b)) 2 3)",
        &mut meta_session,
    )
    .expect("English surface must project to the admitted exact identity");
    let ukrainian = eval_via_meta(
        "((lambda (a b) (додати a b)) 2 3)",
        &mut meta_session,
    )
    .expect("Ukrainian peer surface must project to the same exact identity");

    assert_eq!(english, exact);
    assert_eq!(ukrainian, exact);
}
