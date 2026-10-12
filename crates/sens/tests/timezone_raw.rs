use sens::{eval_program, load_core_library, load_time_library, Session};

fn time_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    load_time_library(&mut session).unwrap();
    session
}

#[test]
fn exact_d3_time_source_matches_frozen_pre_migration_w8_oracle() {
    let input = "(timezone-raw->observation (quote (timezone-declarations \"Europe/Kyiv\" \"Etc/UTC\")))";
    fn observe(input: &str, migrated: bool) -> Result<String, String> {
        let mut session = Session::default();
        load_core_library(&mut session).map_err(|e| e.to_string())?;
        if migrated {
            load_time_library(&mut session).map_err(|e| e.to_string())?;
        } else {
            eval_program(include_str!("../../../tests/fixtures/time-d3-before.lisp"), &mut session)
                .map_err(|e| e.to_string())?;
        }
        eval_program(input, &mut session)
            .map(|x| x.value.to_string())
            .map_err(|e| e.to_string())
    }
    let baseline = observe(input, false);
    let current = observe(input, true);
    assert_eq!(current, baseline, "migrating call heads must not alter observable time semantics");
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
