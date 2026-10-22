//! Shared Rust adapter for the Lisp-owned Guard schema.
//! Rust loads the executable WSM policy and validates the returned value's
//! outer protocol shape. Meaning and policy remain in lib/guard.lisp.

use sens::{
    Session, Value, eval_parsed_expressions, eval_pinned_reasoning_source, eval_program,
    parse_mixed_exact_domain,
};

// Three exact source byte transfers. Zig copies bytes and never decides
// what a SENS word, Guard policy or executable function means.
#[cfg(feature = "zig-source")]
#[link(name = "sens_zig_guard_sources", kind = "static")]
unsafe extern "C" {
    fn sens_zig_guard_core_source_copy(output: *mut u8, capacity: usize) -> isize;
    fn sens_zig_guard_unify_source_copy(output: *mut u8, capacity: usize) -> isize;
    fn sens_zig_guard_policy_source_copy(output: *mut u8, capacity: usize) -> isize;
}

#[cfg(feature = "zig-source")]
type ZigSourceCopy = unsafe extern "C" fn(*mut u8, usize) -> isize;

#[cfg(feature = "zig-source")]
fn exact_source_copy(copy: ZigSourceCopy, label: &str) -> Result<String, String> {
    // Size probe: the Zig carrier must not touch a zero-capacity destination.
    let required = unsafe { copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0) };
    if required <= 0 {
        return Err(format!(
            "ZIG_GUARD_SOURCE_INVALID label={label} size={required}"
        ));
    }
    let len = usize::try_from(required)
        .map_err(|_| format!("ZIG_GUARD_SOURCE_OVERFLOW label={label}"))?;
    // This is a host allocation bound, NOT a SENS domain or semantic limit.
    if len > 8 * 1024 * 1024 {
        return Err(format!(
            "ZIG_GUARD_SOURCE_HOST_CAP label={label} size={len}"
        ));
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!(
            "ZIG_GUARD_SOURCE_COPY_MISMATCH label={label} expected={required} actual={copied}"
        ));
    }
    String::from_utf8(bytes)
        .map_err(|error| format!("ZIG_GUARD_SOURCE_UTF8 label={label}: {error}"))
}

#[cfg(feature = "zig-source")]
fn core_source() -> Result<String, String> {
    exact_source_copy(sens_zig_guard_core_source_copy, "core")
}

#[cfg(feature = "zig-source")]
fn unify_source() -> Result<String, String> {
    exact_source_copy(sens_zig_guard_unify_source_copy, "unify")
}

/// The very same exact Guard bootstrap bytes used by both Guard and CLI.
/// This is a physical adapter, never a Rust semantic oracle.
#[cfg(feature = "zig-source")]
pub fn guard_source() -> Result<String, String> {
    exact_source_copy(sens_zig_guard_policy_source_copy, "guard")
}

// An explicit no-Zig compatibility build must not secretly load files from
// the Rust filesystem or claim the source was carried by Zig.
#[cfg(not(feature = "zig-source"))]
fn core_source() -> Result<String, String> {
    Err("RUST_ZIG_ONLY: Guard core source requires Zig byte transport".into())
}

#[cfg(not(feature = "zig-source"))]
fn unify_source() -> Result<String, String> {
    Err("RUST_ZIG_ONLY: Guard unify source requires Zig byte transport".into())
}

#[cfg(not(feature = "zig-source"))]
pub fn guard_source() -> Result<String, String> {
    Err("RUST_ZIG_ONLY: Guard policy source requires Zig byte transport".into())
}

pub fn load_session() -> Result<Session, String> {
    let mut session = Session::default();
    let core = core_source()?;
    let core_forms =
        parse_mixed_exact_domain(&core).map_err(|error| format!("core-parse: {error}"))?;
    eval_parsed_expressions(&core_forms, &mut session).map_err(|error| format!("core: {error}"))?;
    // Guard reuses the existing exact-D1 structural comparator. Load the
    // domain-aware reasoning source through its pinned reader.
    let unify = unify_source()?;
    eval_pinned_reasoning_source("lib/unify.lisp", &unify, &mut session)
        .map_err(|error| format!("unify: {error}"))?;
    let guard = guard_source()?;
    let guard_forms =
        parse_mixed_exact_domain(&guard).map_err(|error| format!("guard-parse: {error}"))?;
    eval_parsed_expressions(&guard_forms, &mut session)
        .map_err(|error| format!("guard: {error}"))?;
    Ok(session)
}

fn proper_list(value: &Value) -> Option<Vec<&Value>> {
    let mut items = Vec::new();
    let mut cursor = value;
    loop {
        match cursor {
            Value::Nil => return Some(items),
            Value::Pair(node) => {
                items.push(&node.head);
                cursor = &node.tail;
            }
            _ => return None,
        }
    }
}

fn symbol(value: &Value) -> Option<&str> {
    match value {
        Value::Symbol(value) => Some(value.as_ref()),
        _ => None,
    }
}

/// Guard's Rust boundary validates structure, never rendered substrings.
/// A valid finding is exactly:
/// `(guard-finding (schema guard-1) (decision ...) ... (unknown-routes ...))`.
fn valid_guard_finding(value: &Value) -> bool {
    let Some(items) = proper_list(value) else {
        return false;
    };
    if items.len() != 12 || symbol(items[0]) != Some("guard-finding") {
        return false;
    }

    const FIELDS: [&str; 11] = [
        "schema",
        "decision",
        "evidence-status",
        "subject",
        "state",
        "contract",
        "difference",
        "impact",
        "guidance",
        "evidence",
        "unknown-routes",
    ];

    let mut values = Vec::with_capacity(FIELDS.len());
    for (entry, expected_name) in items[1..].iter().zip(FIELDS) {
        let Some(pair) = proper_list(entry) else {
            return false;
        };
        if pair.len() != 2 || symbol(pair[0]) != Some(expected_name) {
            return false;
        }
        values.push(pair[1]);
    }

    if symbol(values[0]) != Some("guard-1") {
        return false;
    }

    if !matches!(
        symbol(values[1]),
        Some("allow" | "warn" | "reject" | "unknown")
    ) {
        return false;
    }

    matches!(
        symbol(values[2]),
        Some("confirmed" | "partial" | "unresolved" | "broken")
    )
}

/// Load CORE + GUARD + policy, evaluate one call, and accept only an exact
/// guard-1 value. The rendered string is returned only after structure has
/// been validated.
pub fn evaluate(policy: &str, call: &str) -> Result<String, String> {
    let mut session = load_session()?;
    eval_program(policy, &mut session).map_err(|error| format!("policy: {error}"))?;
    let result = eval_program(call, &mut session).map_err(|error| format!("evaluate: {error}"))?;

    if !valid_guard_finding(&result.value) {
        return Err("policy-result-without-valid-guard-finding".into());
    }

    Ok(result.value.to_string())
}

#[cfg(all(test, feature = "zig-source"))]
mod tests {
    use super::*;

    #[test]
    fn zig_static_source_carriers_exact_and_reject_small_buffers() {
        let carriers: [(&str, ZigSourceCopy); 3] = [
            ("core", sens_zig_guard_core_source_copy),
            ("unify", sens_zig_guard_unify_source_copy),
            ("guard", sens_zig_guard_policy_source_copy),
        ];
        for (label, copy) in carriers {
            let length = unsafe { copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0) };
            assert!(length > 1, "invalid Zig {label} source length={length}");
            let mut short = [0xa5u8];
            assert_eq!(
                unsafe { copy(short.as_mut_ptr(), short.len()) },
                -2,
                "short {label} buffer must be rejected"
            );
            assert_eq!(short, [0xa5u8], "short {label} buffer was mutated");
            let first = exact_source_copy(copy, label).expect("Zig exact source");
            let second = exact_source_copy(copy, label).expect("Zig repeat source");
            assert!(!first.is_empty(), "{label} source empty");
            assert_eq!(
                first.as_bytes(),
                second.as_bytes(),
                "{label} source byte transport changed between calls"
            );
        }
    }

    const ALLOW_POLICY: &str = r#"
      (def guard-evaluate
        (lambda (kind subject evidence)
          (make-guard-finding (quote allow) (quote confirmed) subject
            kind (quote test-contract) (quote ()) (quote no-impact)
            (quote no-action) (list evidence))))"#;

    #[test]
    fn evaluates_a_real_policy_against_the_shared_core_and_guard_library() {
        let result = evaluate(
            ALLOW_POLICY,
            "(guard-evaluate (quote read) (quote docs) (quote confirmed))",
        )
        .unwrap();
        assert!(result.contains("(decision allow)"));
        assert!(result.contains("(schema guard-1)"));
    }

    #[test]
    fn rejects_a_policy_result_without_a_valid_decision_shape() {
        let bad_policy = r#"
          (def guard-evaluate
            (lambda (kind subject evidence) (quote not-a-decision)))"#;
        let error = evaluate(
            bad_policy,
            "(guard-evaluate (quote read) (quote docs) (quote confirmed))",
        )
        .unwrap_err();
        assert_eq!(error, "policy-result-without-valid-guard-finding");
    }

    #[test]
    fn nested_decision_text_cannot_spoof_the_guard_protocol() {
        let spoof = r#"
          (def guard-evaluate
            (lambda (kind subject evidence)
              (quote (not-a-guard-finding (decision allow)))))"#;
        let error = evaluate(
            spoof,
            "(guard-evaluate (quote read) (quote docs) (quote confirmed))",
        )
        .unwrap_err();
        assert_eq!(error, "policy-result-without-valid-guard-finding");
    }

    #[test]
    fn wrong_schema_is_rejected_even_with_a_valid_decision() {
        let wrong_schema = r#"
          (def guard-evaluate
            (lambda (kind subject evidence)
              (quote
                (guard-finding
                  (schema guard-999)
                  (decision allow)
                  (evidence-status confirmed)
                  (subject docs)
                  (state read)
                  (contract test)
                  (difference ())
                  (impact no-impact)
                  (guidance no-action)
                  (evidence ())
                  (unknown-routes ())))))"#;
        let error = evaluate(
            wrong_schema,
            "(guard-evaluate (quote read) (quote docs) (quote confirmed))",
        )
        .unwrap_err();
        assert_eq!(error, "policy-result-without-valid-guard-finding");
    }

    #[test]
    fn policy_reload_changes_decision_without_recompiling_rust() {
        let warn_policy = ALLOW_POLICY.replace("(quote allow)", "(quote warn)");
        let allow = evaluate(
            ALLOW_POLICY,
            "(guard-evaluate (quote read) (quote docs) (quote confirmed))",
        )
        .unwrap();
        let warn = evaluate(
            &warn_policy,
            "(guard-evaluate (quote read) (quote docs) (quote confirmed))",
        )
        .unwrap();
        assert!(allow.contains("(decision allow)"));
        assert!(warn.contains("(decision warn)"));
    }

    #[test]
    fn load_session_alone_leaves_guard_wsm_functions_ready_to_call() {
        let mut session = load_session().unwrap();
        let result = eval_program("(guard-decision? (quote allow))", &mut session);
        assert!(result.is_ok(), "{result:?}");
    }
}

#[cfg(all(test, not(feature = "zig-source")))]
mod no_zig_transport_tests {
    #[test]
    fn guard_without_zig_refuses_all_sources_instead_of_falling_back() {
        for unavailable in [
            super::core_source(),
            super::unify_source(),
            super::guard_source(),
        ] {
            let error = unavailable.expect_err("no-Zig guard source may not load");
            assert!(error.starts_with("RUST_ZIG_ONLY:"), "{error}");
        }
    }
}
