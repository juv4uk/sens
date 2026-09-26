use sens::{eval_program, load_core_library, load_time_library, Session};

fn time_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    load_time_library(&mut session).unwrap();
    session
}

#[test]
fn raw_timezone_declarations_are_interpreted_by_lisp() {
    let mut session = time_session();

    assert_eq!(
        eval_program(
            "(timezone-raw->observation (quote (timezone-declarations \"Europe/Kyiv\" \"Etc/UTC\")))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(detected \"Europe/Kyiv\" TZ)"
    );

    assert_eq!(
        eval_program(
            "(timezone-raw->observation (quote (timezone-declarations () \"Europe/Kyiv\")))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(detected \"Europe/Kyiv\" etc-timezone)"
    );

    assert_eq!(
        eval_program(
            "(timezone-raw->observation (quote (timezone-declarations () ())))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(unknown host-declaration-unavailable)"
    );

    assert_eq!(
        eval_program(
            "(timezone-raw->observation (quote (not-timezone-declarations () ())))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(rejected invalid-timezone-observation)"
    );
}
