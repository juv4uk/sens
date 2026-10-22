use sens::{eval_program, load_core_library, Session, Value};

#[test]
fn canonical_core_loader_installs_language_owned_defmacro_before_core() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("macro.my then core.my should bootstrap cleanly");

    assert!(
        matches!(
            session.environment.get("визначити-макрос"),
            Some(Value::Macro(_))
        ),
        "українська поверхня макросу має бути завантажена до ядра"
    );

    let value = eval_program(
        r#"
        (визначити-макрос вибрати-перше (ліве праве) ліве)
        (вибрати-перше (як-є гаразд) невизначене)
        "#,
        &mut session,
    )
    .expect("макрос мови має зберігати необчислені аргументи")
    .value;
    assert_eq!(value.to_string(), "гаразд");
}

#[test]
fn core_macros_work_after_canonical_macro_first_bootstrap() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("macro.my then core.my should bootstrap cleanly");

    let value = eval_program("(та так 42)", &mut session)
        .expect("український макрос та доступний після канонічного завантаження")
        .value;
    assert_eq!(value.to_string(), "42");

    // D3 empty list is data, not D1:NO. Explicit false must carry one bit.
    let value = eval_program("(або ні (як-є запасне))", &mut session)
        .expect("український макрос або доступний після канонічного завантаження")
        .value;
    assert_eq!(value.to_string(), "запасне");
}
