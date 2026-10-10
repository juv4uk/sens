//! Shared Rust adapter for the Lisp-owned Guard schema.
//! Rust loads the executable WSM policy and validates the returned value's
//! outer protocol shape. Meaning and policy remain in lib/guard.lisp.

use sens::{eval_program, Session, Value};

pub const CORE: &str = include_str!("../../../lib/core.lisp");
pub const GUARD: &str = include_str!("../../../lib/guard.lisp");

pub fn load_session() -> Result<Session, String> {
    let mut session = Session::default();
    eval_program(CORE, &mut session).map_err(|error| format!("core: {error}"))?;
    eval_program(GUARD, &mut session).map_err(|error| format!("guard: {error}"))?;
    Ok(session)
}

fn proper_list(value: &Value) -> Option<Vec<&Value>> {
    let mut items = Vec::new();
    let mut cursor = value;
    loop {
        match cursor {
            Value::Nil => return Some(items),
            Value::Pair(head, tail) => {
                items.push(head.as_ref());
                cursor = tail.as_ref();
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
/// `(guard-finding (schema guard/1) (decision ...) ... (unknown-routes ...))`.
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

    if symbol(values[0]) != Some("guard/1") {
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
/// guard/1 value. The rendered string is returned only after structure has
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

#[cfg(test)]
mod tests {
    use super::*;

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
        assert!(result.contains("(schema guard/1)"));
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
                  (schema guard/999)
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
    fn migrated_guard_classifiers_return_only_exact_d1_predicate_bits() {
        let mut session = load_session().expect("load Lisp-owned guard classifiers");
        for (name, admitted) in [
            ("guard-decision?", &["allow", "warn", "reject", "unknown"][..]),
            ("guard-evidence-status?", &["confirmed", "partial", "unresolved", "broken"][..]),
        ] {
            for symbol in admitted {
                let source = format!("({name} (quote {symbol}))");
                let result = eval_program(&source, &mut session)
                    .unwrap_or_else(|error| panic!("{source}: {error:?}"));
                assert_eq!(
                    result.value.as_predicate_bit(),
                    Some(true),
                    "{source} must return exact D1:YES, not historical t"
                );
            }
            for symbol in ["unexpected-value", "allow-invalid", "absent"] {
                let source = format!("({name} (quote {symbol}))");
                let result = eval_program(&source, &mut session)
                    .unwrap_or_else(|error| panic!("{source}: {error:?}"));
                assert_eq!(
                    result.value.as_predicate_bit(),
                    Some(false),
                    "{source} must return exact D1:NO, not structural ()"
                );
            }
        }
    }

    #[test]
    fn load_session_alone_leaves_guard_wsm_functions_ready_to_call() {
        let mut session = load_session().unwrap();
        let result = eval_program("(guard-decision? (quote allow))", &mut session);
        assert!(result.is_ok(), "{result:?}");
    }
}
