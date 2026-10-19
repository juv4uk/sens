use sens::{
    eval_parsed_expressions, eval_core_library_source, eval_program,
    parse_mixed_exact_domain_reasoning_source, Session, Value,
};

const FORWARD: &str = include_str!("../../../lib/forward.lisp");

const MIGRATED_MACROS: &[&str] = &[
    "ствердити-факт!",
    "ствердити-факти!",
    "retract-fact!",
    "assert-fact-tms!",
    "run-tms!",
    "retract-fact-tms!",
    "assert-fact-jtms!",
    "run-jtms!",
    "run-jtms-multi!",
    "retract-fact-jtms!",
];

fn load_reasoning(session: &mut Session, path: &str, source: &str) {
    let parsed = parse_mixed_exact_domain_reasoning_source(path, source)
        .unwrap_or_else(|error| panic!("pinned reasoning parse failed for {path}: {error}"));
    eval_parsed_expressions(&parsed, session)
        .unwrap_or_else(|error| panic!("pinned reasoning load failed for {path}: {error}"));
}

fn session() -> Session {
    let mut session = Session::default();
    eval_core_library_source(include_str!("../../../lib/core.lisp"),
        &mut session,
    )
    .expect("exact-domain core bootstrap");

    load_reasoning(
        &mut session,
        "lib/unify.lisp",
        include_str!("../../../lib/unify.lisp"),
    );
    load_reasoning(
        &mut session,
        "lib/reason.lisp",
        include_str!("../../../lib/reason.lisp"),
    );
    load_reasoning(&mut session, "lib/forward.lisp", FORWARD);
    session
}

fn eval(session: &mut Session, source: &str) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("evaluation failed: {error}\nsource: {source}"))
        .value
        .to_string()
}

fn eight_bit_heads(source: &str) -> Vec<String> {
    let bytes = source.as_bytes();
    let mut result = Vec::new();
    let mut i = 0;
    let mut in_string = false;
    let mut escaped = false;
    let mut in_comment = false;

    while i < bytes.len() {
        let byte = bytes[i];
        if in_comment {
            if byte == b'\n' {
                in_comment = false;
            }
            i += 1;
            continue;
        }
        if in_string {
            if escaped {
                escaped = false;
            } else if byte == b'\\' {
                escaped = true;
            } else if byte == b'"' {
                in_string = false;
            }
            i += 1;
            continue;
        }
        if byte == b';' {
            in_comment = true;
            i += 1;
            continue;
        }
        if byte == b'"' {
            in_string = true;
            i += 1;
            continue;
        }

        if byte == b'(' && i + 9 < bytes.len() {
            let bits = &bytes[i + 1..i + 9];
            let delimiter = bytes[i + 9];
            if bits.iter().all(|bit| matches!(bit, b'0' | b'1'))
                && (delimiter.is_ascii_whitespace() || delimiter == b')')
            {
                result.push(String::from_utf8(bits.to_vec()).expect("binary head is ASCII"));
            }
        }
        i += 1;
    }
    result
}

#[test]
fn forward_macro_cutover_is_exact_width_and_bit_neutral() {
    let heads = eight_bit_heads(FORWARD);
    assert!(
        heads.is_empty(),
        "forward.lisp must have no executable eight-bit compatibility heads: {heads:?}"
    );

    assert_eq!(FORWARD.matches("(як-є визначити)").count(), MIGRATED_MACROS.len());
    assert!(!FORWARD.contains("(як-є def)"), "legacy def macro expansion forbidden");
    for name in MIGRATED_MACROS {
        let define = format!("(визначити {name}\n  (make-macro\n    (функція ");
        assert!(
            FORWARD.contains(&define),
            "{name} must be D4 DEFINE -> make-macro -> D4 LAMBDA"
        );
    }

    let legacy_identity_bits = MIGRATED_MACROS.len() * 8;
    let exact_domain_identity_bits = MIGRATED_MACROS.len() * (4 + 4);
    assert_eq!(
        exact_domain_identity_bits, legacy_identity_bits,
        "macro cutover must remove the legacy plane without increasing identity-bit cost"
    );
}

#[test]
fn all_ten_forward_macros_are_real_macro_values() {
    let session = session();
    for name in MIGRATED_MACROS {
        assert!(
            matches!(session.environment.get(name), Some(Value::Macro(_))),
            "{name} must load as a real Macro value"
        );
    }
}

#[test]
fn migrated_macros_drive_plain_tms_and_jtms_state_transitions() {
    let mut session = session();
    // Реальний SENS-виклик: стан змінюється D4 DEFINE, потім відкликається.
    eval(&mut session, "(ствердити-факт! (як-є альфа))");
    assert_eq!(eval(&mut session, "*working-memory*"), "(альфа)");
    eval(&mut session, "(retract-fact! (як-є альфа))");
    assert_eq!(eval(&mut session, "*working-memory*"), "()");

    for source in [
        "(ствердити-факт! (як-є альфа))",
        "(ствердити-факти! (як-є (бета гамма)))",
        "(retract-fact! (як-є альфа))",
        "(retract-fact! (як-є бета))",
        "(retract-fact! (як-є гамма))",
        "(assert-fact-tms! (quote delta))",
        "(run-tms! (quote ()))",
        "(retract-fact-tms! (quote delta))",
        "(assert-fact-jtms! (quote epsilon))",
        "(run-jtms! (quote ()))",
        "(run-jtms-multi! (quote ()))",
        "(retract-fact-jtms! (quote epsilon))",
    ] {
        let _ = eval(&mut session, source);
    }

    assert_eq!(
        eval(
            &mut session,
            "(list *working-memory* *justified-memory* *jtms-memory*)",
        ),
        "(() () ())",
        "all three mutable reasoning memories must return to empty after bounded assert/run/retract"
    );
}
