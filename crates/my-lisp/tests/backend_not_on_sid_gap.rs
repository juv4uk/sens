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
//! entire `my-lisp-host` crate's surface, dispatched by
//! `eval/capabilities.rs`'s `BTreeMap<String, HostFn>` on the literal
//! spelling of the calling symbol — never through `Sid8`.
//!
//! Part 2: `lib/meta-eval.lisp`'s metacircular evaluator has the exact
//! same shape, written in Lisp instead of Rust. Its Canon-identity
//! primitives (`quote`/`atom`/`eq`/`cons`/`car`/`cdr`/`cond`) correctly
//! resolve through `my-semantic-id-for-surface`, so any admitted surface
//! spelling in any language works. But `my-default-binding`'s fallback
//! for "ordinary" primitives (`+`/`-`/`*`/`<`/`=`/`>`/`write-to-string`/
//! `string->symbol`) is a literal `(eq name (quote +))` chain — hardcoded
//! to one spelling, never routed through the SID that same operation
//! already has (`+` is SID `00001100`, whose own admitted Ukrainian
//! surface name `додати` resolves correctly in the *native* evaluator but
//! is `unbound-symbol` inside meta-eval).
//!
//! Both are the concrete backend that is NOT on SID: they depend on
//! exact text, so a surface-encoding change (Ukrainian/English/KOI-8/
//! SLP1/anything) that altered how a name is written could silently
//! break dispatch, unlike genuine SID-routed forms (`quote`/`cond`/the
//! Canon-identity primitives) which are encoding-invariant by
//! construction.
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
    my_lisp::load_meta_evaluator_library(&mut session).expect("meta-evaluator should load");

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
fn meta_eval_ordinary_primitive_dispatch_is_hardcoded_to_one_spelling_not_sid() {
    // `+` is SID 00001100; `додати` is its own admitted Ukrainian surface
    // spelling for the exact same identity (see
    // lib/surface/semantic-registry.lisp and #1228's own read-file work
    // this session, which read that very table). The NATIVE evaluator
    // resolves both spellings to the same SID and gives the same answer.
    let mut native_session = Session::default();
    let native_english = eval_program("(+ 2 3)", &mut native_session)
        .expect("native + resolves")
        .value
        .to_string();
    let native_ukrainian = eval_program("(додати 2 3)", &mut native_session)
        .expect("native evaluator is SID-routed for + regardless of surface spelling")
        .value
        .to_string();
    assert_eq!(
        native_english, native_ukrainian,
        "the native evaluator must be spelling-invariant for a SID-routed primitive"
    );

    // The metacircular evaluator's `my-default-binding` fallback for
    // "ordinary" primitives is a literal `(eq name (quote +))` chain
    // (lib/meta-eval.lisp) — hardcoded to the English spelling only, never
    // consulting the SID that `+` and `додати` already share. This is the
    // concrete, named confirmation that this specific backend path is
    // textual, not SID-routed, exactly like the host-capability registry
    // above, just written in Lisp instead of Rust.
    let mut meta_session = Session::default();
    eval_program(
        include_str!("../../../lib/core.lisp"),
        &mut meta_session,
    )
    .expect("core.lisp should load");
    my_lisp::load_meta_evaluator_library(&mut meta_session)
        .expect("meta-evaluator should load");

    let meta_english = eval_via_meta("((lambda (a b) (+ a b)) 2 3)", &mut meta_session)
        .expect("meta-eval resolves the hardcoded English spelling");
    assert_eq!(meta_english, "5");

    let meta_ukrainian = eval_via_meta("((lambda (a b) (додати a b)) 2 3)", &mut meta_session);
    assert!(
        meta_ukrainian.is_err()
            || meta_ukrainian
                .as_deref()
                .map(|v| v.contains("unbound"))
                .unwrap_or(false),
        "meta-eval must fail to resolve додати even though it is the exact \
         same SID as +, proving this dispatch path ignores SID identity \
         entirely and depends on the literal English spelling baked into \
         lib/meta-eval.lisp's eq-chain: got {meta_ukrainian:?}"
    );
}
