//! Shared Rust adapter for the SENS-owned Guard schema.
//! Bootstrap enters as exact T5M domain words; SENS executes the policy and
//! Rust validates only the returned outer protocol shape.

#[cfg(feature = "zig-source")]
use sens::ExactDomainWord;
use sens::{eval_program, PhysicalT5Program, Session, Value};

// Zig decodes the physical T5M carrier into exact width + 0/1 bit records.
// Rust resolves those records through SENS's ratified domain identities.
#[cfg(feature = "zig-source")]
#[link(name = "sens_zig_guard_sources", kind = "static")]
unsafe extern "C" {
    fn sens_zig_guard_t5m_words_copy(id: u32, output: *mut u8, capacity: usize) -> isize;
}

#[cfg(feature = "zig-source")]
fn exact_words(id: u32, label: &str) -> Result<Vec<ExactDomainWord>, String> {
    let required = unsafe {
        sens_zig_guard_t5m_words_copy(id, std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err(format!(
            "ZIG_GUARD_T5M_INVALID label={label} size={required}"
        ));
    }
    let len =
        usize::try_from(required).map_err(|_| format!("ZIG_GUARD_T5M_OVERFLOW label={label}"))?;
    // Host allocation bound only; it is not a SENS word-width limit.
    if len > 8 * 1024 * 1024 {
        return Err(format!("ZIG_GUARD_T5M_HOST_CAP label={label} size={len}"));
    }
    let mut records = vec![0u8; len];
    let copied = unsafe { sens_zig_guard_t5m_words_copy(id, records.as_mut_ptr(), records.len()) };
    if copied != required {
        return Err(format!(
            "ZIG_GUARD_T5M_COPY_MISMATCH label={label} expected={required} actual={copied}"
        ));
    }

    let mut words = Vec::new();
    let mut offset = 0usize;
    while offset < records.len() {
        let header_end = offset
            .checked_add(4)
            .filter(|end| *end <= records.len())
            .ok_or_else(|| format!("ZIG_GUARD_T5M_TRUNCATED_WIDTH label={label}"))?;
        let width = u32::from_be_bytes(records[offset..header_end].try_into().unwrap()) as usize;
        let bits_end = header_end
            .checked_add(width)
            .filter(|end| width > 0 && *end <= records.len())
            .ok_or_else(|| format!("ZIG_GUARD_T5M_TRUNCATED_WORD label={label} width={width}"))?;
        let bits = &records[header_end..bits_end];
        let word = ExactDomainWord::from_physical_width_bits(width, bits)
            .map_err(|error| format!("ZIG_GUARD_T5M_DOMAIN_WORD label={label}: {error}"))?;
        words.push(word);
        offset = bits_end;
    }
    if words.is_empty() {
        return Err(format!("ZIG_GUARD_T5M_EMPTY label={label}"));
    }
    Ok(words)
}

#[cfg(feature = "zig-source")]
fn t5m_program(id: u32, label: &str) -> Result<PhysicalT5Program, String> {
    let words = exact_words(id, label)?;
    PhysicalT5Program::from_exact_domain_words_owned(words)
        .map_err(|error| format!("ZIG_GUARD_T5M_REJECTED label={label}: {error}"))
}

#[cfg(feature = "zig-source")]
fn core_program() -> Result<PhysicalT5Program, String> {
    t5m_program(0, "core")
}

#[cfg(feature = "zig-source")]
fn unify_program() -> Result<PhysicalT5Program, String> {
    t5m_program(1, "unify")
}

#[cfg(feature = "zig-source")]
fn guard_program() -> Result<PhysicalT5Program, String> {
    t5m_program(2, "guard")
}

// An explicit no-Zig compatibility build must fail closed.
#[cfg(not(feature = "zig-source"))]
fn core_program() -> Result<PhysicalT5Program, String> {
    Err("RUST_ZIG_ONLY: Guard core T5M requires the Zig corridor".into())
}

#[cfg(not(feature = "zig-source"))]
fn unify_program() -> Result<PhysicalT5Program, String> {
    Err("RUST_ZIG_ONLY: Guard unify T5M requires the Zig corridor".into())
}

#[cfg(not(feature = "zig-source"))]
fn guard_program() -> Result<PhysicalT5Program, String> {
    Err("RUST_ZIG_ONLY: Guard policy T5M requires the Zig corridor".into())
}

/// Execute the shared physical Guard T5M asset in an existing SENS session.
pub fn load_guard_into(session: &mut Session) -> Result<(), String> {
    guard_program()?
        .execute(session)
        .map(|_| ())
        .map_err(|error| format!("guard: {error}"))
}

pub fn load_session() -> Result<Session, String> {
    let mut session = Session::default();
    core_program()?
        .execute(&mut session)
        .map_err(|error| format!("core: {error}"))?;
    unify_program()?
        .execute(&mut session)
        .map_err(|error| format!("unify: {error}"))?;
    load_guard_into(&mut session)?;
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
    fn zig_decodes_guard_t5m_into_exact_word_records() {
        for (label, id) in [("core", 0u32), ("unify", 1u32), ("guard", 2u32)] {
            let length = unsafe {
                sens_zig_guard_t5m_words_copy(id, std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
            };
            assert!(length > 1, "invalid Zig {label} T5M record length={length}");
            let mut short = [0xa5u8];
            assert_eq!(
                unsafe { sens_zig_guard_t5m_words_copy(id, short.as_mut_ptr(), short.len()) },
                -2,
                "short {label} T5M buffer must be rejected"
            );
            assert_eq!(short, [0xa5u8], "short {label} buffer was mutated");
            let first = exact_words(id, label).expect("Zig exact T5M words");
            let second = exact_words(id, label).expect("Zig repeat T5M words");
            assert!(!first.is_empty(), "{label} T5M words empty");
            assert_eq!(
                first, second,
                "{label} exact T5M word transport changed between calls"
            );
        }
    }

    const ALLOW_POLICY: &str = r#"
      (визначити guard-evaluate
        (функція (kind subject evidence)
          (список
            (як-є guard-finding)
            (список (як-є schema) (як-є guard-1))
            (список (як-є decision) kind)
            (список (як-є evidence-status) (як-є confirmed))
            (список (як-є subject) subject)
            (список (як-є state) (як-є read))
            (список (як-є contract) (як-є test-contract))
            (список (як-є difference) (як-є ()))
            (список (як-є impact) (як-є no-impact))
            (список (як-є guidance) (як-є no-action))
            (список (як-є evidence) (список evidence))
            (список (як-є unknown-routes) (як-є ())))))"#;

    #[test]
    fn evaluates_a_real_policy_against_the_shared_core_and_guard_library() {
        let result = evaluate(
            ALLOW_POLICY,
            "(guard-evaluate (як-є allow) (як-є docs) (як-є confirmed))",
        )
        .unwrap();
        assert!(result.contains("(decision allow)"));
        assert!(result.contains("(schema guard-1)"));
    }

    #[test]
    fn rejects_a_policy_result_without_a_valid_decision_shape() {
        let bad_policy = r#"
          (визначити guard-evaluate
            (функція (kind subject evidence) (як-є not-a-decision)))"#;
        let error = evaluate(
            bad_policy,
            "(guard-evaluate (як-є allow) (як-є docs) (як-є confirmed))",
        )
        .unwrap_err();
        assert_eq!(error, "policy-result-without-valid-guard-finding");
    }

    #[test]
    fn nested_decision_text_cannot_spoof_the_guard_protocol() {
        let spoof = r#"
          (визначити guard-evaluate
            (функція (kind subject evidence)
              (як-є (not-a-guard-finding (decision allow)))))"#;
        let error = evaluate(
            spoof,
            "(guard-evaluate (як-є allow) (як-є docs) (як-є confirmed))",
        )
        .unwrap_err();
        assert_eq!(error, "policy-result-without-valid-guard-finding");
    }

    #[test]
    fn wrong_schema_is_rejected_even_with_a_valid_decision() {
        let wrong_schema = r#"
          (визначити guard-evaluate
            (функція (kind subject evidence)
              (як-є
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
            "(guard-evaluate (як-є allow) (як-є docs) (як-є confirmed))",
        )
        .unwrap_err();
        assert_eq!(error, "policy-result-without-valid-guard-finding");
    }

    #[test]
    fn policy_reload_changes_decision_without_recompiling_rust() {
        let allow = evaluate(
            ALLOW_POLICY,
            "(guard-evaluate (як-є allow) (як-є docs) (як-є confirmed))",
        )
        .unwrap();
        let warn = evaluate(
            ALLOW_POLICY,
            "(guard-evaluate (як-є warn) (як-є docs) (як-є confirmed))",
        )
        .unwrap();
        assert!(allow.contains("(decision allow)"));
        assert!(warn.contains("(decision warn)"));
    }

    #[test]
    fn load_session_alone_leaves_guard_wsm_functions_ready_to_call() {
        let session = load_session().unwrap();
        let name = sens::encode_text7("захист-рішення?", sens::Text7Layout::Uk)
            .unwrap()
            .to_canonical_wire_token();
        assert!(session.environment.get(&name).is_some());
    }

    #[test]
    fn guard_bootstrap_assets_restore_as_physical_t5m_programs() {
        for (label, program) in [
            ("core", core_program()),
            ("unify", unify_program()),
            ("guard", guard_program()),
        ] {
            let program = program.unwrap_or_else(|error| panic!("{label}: {error}"));
            assert!(program.form_count() > 0, "{label} has no T5M forms");
        }

        let session = load_session().expect("T5M Guard bootstrap");
        let name = sens::encode_text7("захист-рішення?", sens::Text7Layout::Uk)
            .unwrap()
            .to_canonical_wire_token();
        assert!(session.environment.get(&name).is_some());
    }
}

#[cfg(all(test, not(feature = "zig-source")))]
mod no_zig_transport_tests {
    #[test]
    fn guard_without_zig_refuses_all_programs_instead_of_falling_back() {
        for unavailable in [
            super::core_program(),
            super::unify_program(),
            super::guard_program(),
        ] {
            let error = match unavailable {
                Err(error) => error,
                Ok(_) => panic!("no-Zig Guard T5M unexpectedly loaded"),
            };
            assert!(error.starts_with("RUST_ZIG_ONLY:"), "{error}");
        }
    }
}
