use sens::{eval_program, load_core_library, ErrorKind, Session};

#[test]
fn ukrainian_canon_surface_is_reserved_but_ordinary_binding_is_lexical() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("чинне ядро має завантажуватися");
    let error = eval_program(
        "(визначити перше (функція (x) (як-є затінено)))",
        &mut session,
    )
    .expect_err("Contract 6.0 must reject shadowing a Ukrainian Canon spelling");
    assert_eq!(error.kind, ErrorKind::InvalidForm);

    let ordinary = eval_program(
        "(визначити локальна-функція (функція (x y) (як-є локально))) (локальна-функція (як-є перший) (як-є другий))",
        &mut session,
    )
    .expect("ordinary non-registry bindings must remain lexical values");
    assert_eq!(ordinary.value.to_string(), "локально");
}
