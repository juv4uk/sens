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
    // The frozen W8 witness is a negative historical oracle: its LIST-shaped
    // construction invoked old CONS with three arguments. It must stay frozen,
    // not be silently relabelled as a successful parity check.
    let old_error = baseline.expect_err("frozen pre-migration source must preserve its arity bug");
    assert!(old_error.contains("expected 2") && old_error.contains("received 3"),
            "unexpected change in frozen arity error: {old_error}");
    let current = observe(input, true);
    assert_eq!(
        current.as_deref(),
        Ok("(detected \"Europe/Kyiv\" TZ)"),
        "exact-D3 CONS construction must repair the positive timezone witness"
    );
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
