//! #1774 slice C — Surface execution bypass debt test
//!
//! This test DOCUMENTS the transition debt at evaluate_step lines 179-180:
//! any admitted English surface name (e.g., '+', 'car', 'cons') executes
//! via name lookup instead of requiring a binary SID.
//!
//! EXPECTED BEHAVIOUR TODAY: passes (transition debt active)
//! EXPECTED BEHAVIOUR AFTER C1: fails with UnknownSymbol for English names
//!
//! When lowering (#1714) is complete and C1 deletion lands, this test
//! must be flipped to assert UnknownSymbol for English names.

use sens::{
    eval_program, load_core_library, Environment, Session, LanguageError, ErrorKind, Value,
};

#[test]
fn surface_bypass_is_transition_debt_today() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");

    // English name '+' executes via semantic_registry name lookup (transition debt)
    // Binary SID form would be: (00001100 1 2)  -- 00001100 = plus/+
    let result = eval_program("(+ 1 2)", &mut session);

    // TODAY: this PASSES because '+' resolves via semantic_registry name lookup
    // AFTER C1: should be Err(LanguageError { kind: ErrorKind::UnknownSymbol, ... })
    assert!(
        result.is_ok(),
        "surface bypass active: '+' executes via name lookup — transition debt"
    );

    // Verify it returns the correct value (1+2=3)
    let eval_result = result.unwrap();
    match eval_result.value {
        Value::Number(n, _) => assert!((n - 3.0).abs() < f64::EPSILON),
        other => panic!("expected Number, got {other:?}"),
    }
}

#[test]
fn binary_sid_form_works() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");

    // Binary SID form: 00001100 = plus/+
    let result = eval_program("(00001100 1 2)", &mut session);
    assert!(result.is_ok(), "binary SID form must work");

    let eval_result = result.unwrap();
    match eval_result.value {
        Value::Number(n, _) => assert!((n - 3.0).abs() < f64::EPSILON),
        other => panic!("expected Number, got {other:?}"),
    }
}

#[test]
fn unknown_english_name_fails_today() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");

    // A name that is NOT in the semantic registry
    let result = eval_program("(not-a-real-function 1 2)", &mut session);
    assert!(result.is_err(), "unknown name must fail");

    match result.unwrap_err().kind {
        ErrorKind::UnknownSymbol => {}
        other => panic!("expected UnknownSymbol, got {other:?}"),
    }
}
