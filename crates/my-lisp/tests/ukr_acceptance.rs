use my_lisp::{eval_program, load_core_library, Session};

const UKR_ACCEPTANCE: &str = include_str!("../../../lib/surface/ukr-acceptance.lisp");

#[test]
fn ukr_acceptance_program_needs_no_latin_keyboard_layout() {
    assert!(
        !UKR_ACCEPTANCE
            .chars()
            .any(|character| character.is_ascii_alphabetic()),
        "ukr acceptance source must contain no ASCII Latin letters"
    );
}

#[test]
fn ukr_acceptance_program_executes_through_real_runtime() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core bootstrap must install stable surface peers");
    let result = eval_program(UKR_ACCEPTANCE, &mut session)
        .expect("ukr acceptance program must evaluate through the real runtime");
    assert_eq!(result.value.to_string(), "успіх");
}

#[test]
fn shadowing_ukr_peer_does_not_retarget_english_peer() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core bootstrap must install stable surface peers");

    let result = eval_program(
        "(визначити порожній-текст? (функція (значення) (як-є затінено)))\n(string-empty? \"\")",
        &mut session,
    )
    .expect("ordinary ukr peer must remain independently shadowable");

    assert_eq!(result.value.to_string(), "(identity-relation same)");
}
