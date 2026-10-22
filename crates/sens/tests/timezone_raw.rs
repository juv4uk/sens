use sens::{eval_program, load_core_library, load_time_library, Session};

fn time_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    load_time_library(&mut session).unwrap();
    session
}

#[test]
fn current_d3_time_observation_and_cons_arity_are_executed_by_sens() {
    let mut session = time_session();

    // Чинний Lisp/укр виконує спостереження; застарілий англійський
    // псевдонім не повертаємо в мовну таблицю чи runtime.
    let observed = eval_program(
        "(часовий-пояс-сирий-до-спостереження (як-є (timezone-declarations \"Europe/Kyiv\" \"Etc/UTC\")))",
        &mut session,
    )
    .expect("SENS виконує українське визначення часової бібліотеки");
    assert_eq!(observed.value.to_string(), "(detected \"Europe/Kyiv\" TZ)");

    // Замість старого W8/fixture — живий негативний закон D3 CONS.
    let error = eval_program("(сполучити (як-є а) (як-є б) (як-є в))", &mut session)
        .expect_err("D3 CONS повинен відхилити третій аргумент");
    assert!(
        error
            .to_string()
            .contains("expected 2 arguments; received 3"),
        "D3 CONS повернув неочікувану помилку: {error}"
    );
}

#[test]
fn raw_timezone_declarations_are_interpreted_by_lisp() {
    let mut session = time_session();

    assert_eq!(
        eval_program(
            "(часовий-пояс-сирий-до-спостереження (як-є (timezone-declarations \"Europe/Kyiv\" \"Etc/UTC\")))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(detected \"Europe/Kyiv\" TZ)"
    );

    assert_eq!(
        eval_program(
            "(часовий-пояс-сирий-до-спостереження (як-є (timezone-declarations () \"Europe/Kyiv\")))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(detected \"Europe/Kyiv\" etc-timezone)"
    );

    assert_eq!(
        eval_program(
            "(часовий-пояс-сирий-до-спостереження (як-є (timezone-declarations () ())))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(unknown host-declaration-unavailable)"
    );

    // Empty strings are absent declarations too; timezone precedence must
    // remain language-owned and D3:110 must stay exactly two-clause.
    for (source, expected) in [
        (
            "(часовий-пояс-сирий-до-спостереження (як-є (timezone-declarations \"\" \"Etc/UTC\")))",
            "(detected \"Etc/UTC\" etc-timezone)",
        ),
        (
            "(часовий-пояс-сирий-до-спостереження (як-є (timezone-declarations \"\" \"\")))",
            "(unknown host-declaration-unavailable)",
        ),
        (
            "(часовий-пояс-сирий-до-спостереження (як-є (timezone-declarations \"Europe/Kyiv\" \"\")))",
            "(detected \"Europe/Kyiv\" TZ)",
        ),
        (
            "(часовий-пояс-сирий-до-спостереження (як-є (timezone-declarations () \"\")))",
            "(unknown host-declaration-unavailable)",
        ),
    ] {
        assert_eq!(
            eval_program(source, &mut session)
                .unwrap_or_else(|error| panic!("{source}: {error}"))
                .value
                .to_string(),
            expected,
            "{source}"
        );
    }

    assert_eq!(
        eval_program(
            "(часовий-пояс-сирий-до-спостереження (як-є (not-timezone-declarations () ())))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(rejected invalid-timezone-observation)"
    );
}
