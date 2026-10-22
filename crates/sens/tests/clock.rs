use sens::{
    eval_program, load_core_library, load_time_library, DomainD10, DomainIdentity, ErrorKind,
    Session, Value,
};

fn time_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    load_time_library(&mut session).unwrap();
    session
}

#[test]
fn core_integer_quotient_and_mod_keep_exact_lisp_laws() {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();

    for (source, expected) in [
        ("(знайти-найбільший-блок-частки 10 3 3 1)", "(6 . 2)"),
        ("(частка-через-подвоєння 10 3)", "3"),
        ("(частка-через-подвоєння 1 3)", "0"),
        ("(модульна-остача 10 3)", "1"),
        ("(модульна-остача 0 7)", "0"),
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

    // D5 ЧАСТКА є точною раціональною операцією; 10/3 не дорівнює
    // цілочисельній FLOOR-частці і не має вдавати такий результат.
    let exact =
        eval_program("(частка 10 3)", &mut session).expect("адмітоване математичне D24+ ділення");
    assert!(
        matches!(exact.value, Value::NumericComposition(_)),
        "дробове D5 ділення не можна підміняти цілочисельною часткою"
    );
}

/// D10 residency alone does not authorize a host or evaluator mechanism.
fn assert_d10_has_no_implicit_core_operation(bits: u16) {
    let word = DomainD10::new(bits).expect("exact ten-bit resident");
    assert!(DomainIdentity::D10(word).core_operation().is_none());
}

#[test]
fn d48_integer_quotient_and_mod_stay_in_the_operand_domain() {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();

    // Дільник обчислюється як D48, а не як окремий D24-літерал.
    let denominator = "(додати 65536 (відняти 1000000000 1000000000))";
    for (operator, expected) in [
        ("частка-через-подвоєння", "65535"),
        ("модульна-остача", "65535"),
    ] {
        let source = format!("({operator} 4294967295 {denominator})");
        let actual = eval_program(&source, &mut session)
            .unwrap_or_else(|error| panic!("{source}: {error}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "{source}");
    }
    let mixed = eval_program("(частка-через-подвоєння 4294967295 65536)", &mut session)
        .expect_err("D48/D24 must not be coerced implicitly");
    assert_eq!(mixed.kind, ErrorKind::Type);
}

#[test]
fn utc_now_fails_closed_without_an_individually_admitted_d10_observation() {
    let mut session = time_session();
    assert_d10_has_no_implicit_core_operation(0b0011110001); // поточний-юнікс-час
    let error = eval_program("(узгоджений-час-зараз)", &mut session)
        .expect_err("D10 residency must not invent a raw host-clock mechanism");
    assert_eq!(error.kind, ErrorKind::UnknownSymbol);
}

#[test]
fn utc_calendar_conversion_is_language_owned() {
    let mut session = time_session();

    assert_eq!(
        eval_program("(узгоджений-час-з-юнікс 0 0)", &mut session)
            .unwrap()
            .value
            .to_string(),
        "(utc 1970 1 1 0 0 0 0)"
    );
    assert_eq!(
        eval_program("(узгоджений-час-з-юнікс 86400 123456789)", &mut session)
            .unwrap()
            .value
            .to_string(),
        "(utc 1970 1 2 0 0 0 123456789)"
    );
    for wide_timestamp in ["946684800", "1709164800"] {
        let error = eval_program(
            &format!("(узгоджений-час-з-юнікс {wide_timestamp} 0)"),
            &mut session,
        )
        .expect_err("D48 input must not be implicitly mixed with D24 calendar constants");
        assert_eq!(error.kind, ErrorKind::Type);
    }
}

#[test]
fn raw_unix_clock_observation_is_interpreted_by_lisp() {
    let mut session = time_session();
    // Числа у quoted-даних не мають D24+; будуємо виконуваний список
    // з точних числових значень, а не арифметику над legacy-number.
    // Цей позитивний свідок використовує D24 для обох полів; ширший
    // перехід D48/D24 не можна мовчки допускати без закону міждоменного
    // приведення (див. окремий негативний свідок нижче).

    assert_eq!(
        eval_program(
            "(юнікс-час-спостереження-узгоджений-час (список (як-є unix-time) 0 42))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(utc 1970 1 1 0 0 0 42)"
    );
    assert_eq!(
        eval_program(
            "(юнікс-час-спостереження-узгоджений-час (список (як-є not-unix-time) 946684800 42))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(rejected invalid-unix-time-observation)"
    );
    let legacy = eval_program(
        "(юнікс-час-спостереження-узгоджений-час (як-є (unix-time 946684800 42)))",
        &mut session,
    )
    .expect_err("quoted legacy-number не може стати математичним D24+");
    assert_eq!(legacy.kind, ErrorKind::Type);

    let mixed_domains = eval_program(
        "(юнікс-час-спостереження-узгоджений-час (список (як-є unix-time) 946684800 42))",
        &mut session,
    )
    .expect_err("міждоменне приведення D48/D24 без закону заборонене");
    assert_eq!(mixed_domains.kind, ErrorKind::Type);
    assert!(mixed_domains.message.contains("same-domain numeric values"));
}

#[test]
fn utc_now_layer_does_not_invent_the_missing_raw_d10_clock_mechanism() {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    assert_d10_has_no_implicit_core_operation(0b0011110001);
    assert_eq!(
        session.environment.get("узгоджений-час-зараз"),
        None,
        "Core4 must not install a lexical placeholder before the time layer"
    );
    let error = eval_program("(узгоджений-час-зараз)", &mut session)
        .expect_err("unloaded time definition must fail closed");
    assert!(matches!(
        error.kind,
        ErrorKind::UnknownSymbol | ErrorKind::Type
    ));

    load_time_library(&mut session).unwrap();
    let error = eval_program("(узгоджений-час-зараз)", &mut session)
        .expect_err("D10 raw clock observation has no individually admitted mechanism");
    assert_eq!(error.kind, ErrorKind::UnknownSymbol);
}

#[test]
fn ntp_field_interpretation_is_language_owned() {
    let mut session = time_session();

    assert_eq!(
        eval_program(
            "(тлумачити-поля-відповіді-часу \"clock.example\" 4 1 2208988800 1073741824)",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(accepted \"clock.example\" 0 250000000)"
    );
    assert_eq!(
        eval_program(
            "(тлумачити-поля-відповіді-часу \"clock.example\" 5 15 2208988801 2147483648)",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(accepted \"clock.example\" 1 500000000)"
    );
    // Гранична частка в D48: точне округлення донизу без D96.
    assert_eq!(
        eval_program(
            "(тлумачити-поля-відповіді-часу \"clock.example\" 4 1 2208988801 4294967295)",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(accepted \"clock.example\" 1 999999999)"
    );
    assert_eq!(
        eval_program(
            "(тлумачити-поля-відповіді-часу \"clock.example\" 3 1 2208988800 0)",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(rejected invalid-response)"
    );
    assert_eq!(
        eval_program(
            "(тлумачити-поля-відповіді-часу \"clock.example\" 4 0 2208988800 0)",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(rejected invalid-response)"
    );
    assert_eq!(
        eval_program(
            "(тлумачити-поля-відповіді-часу \"clock.example\" 4 1 2208988799 0)",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(rejected invalid-epoch)"
    );
}

#[test]
fn raw_ntp_observation_boundary_is_interpreted_by_lisp() {
    let mut session = time_session();

    assert_eq!(
        eval_program(
            "(перетворити-сирі-дані-часу-на-спостереження (список (як-є ntp-fields) \"clock.example\" 4 1 2208988801 2147483648))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(accepted \"clock.example\" 1 500000000)"
    );
    assert_eq!(
        eval_program(
            "(перетворити-сирі-дані-часу-на-спостереження (список (як-є ntp-fields) \"clock.example\" 3 1 2208988800 0))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(rejected invalid-response)"
    );
    assert_eq!(
        eval_program(
            "(перетворити-сирі-дані-часу-на-спостереження (як-є (rejected receive-failed)))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(rejected receive-failed)"
    );
}

#[test]
fn internet_time_sync_fails_closed_without_an_individually_admitted_d10_network_mechanism() {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    assert_d10_has_no_implicit_core_operation(0b0011110000); // сирий мережевий запит часу
    assert_eq!(
        session.environment.get("інтернет-час-синхронізувати"),
        None,
        "Core4 must not install a lexical placeholder before the time layer"
    );
    let error = eval_program(
        "(інтернет-час-синхронізувати \"clock.example\" 1)",
        &mut session,
    )
    .expect_err("unloaded time definition must fail closed");
    assert!(matches!(
        error.kind,
        ErrorKind::UnknownSymbol | ErrorKind::Type
    ));

    load_time_library(&mut session).unwrap();
    let error = eval_program(
        "(інтернет-час-синхронізувати \"clock.example\" 1)",
        &mut session,
    )
    .expect_err("D10 raw network query has no individually admitted mechanism");
    assert_eq!(error.kind, ErrorKind::UnknownSymbol);
}

#[test]
fn internet_time_timestamp_interpretation_is_language_owned() {
    let mut session = time_session();

    assert_eq!(
        eval_program(
            "(дати-календарне-значення-схваленому-часу (список (як-є accepted) \"clock.example\" 86400 123456789))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(accepted \"clock.example\" (utc 1970 1 2 0 0 0 123456789))"
    );
    assert_eq!(
        eval_program(
            "(дати-календарне-значення-схваленому-часу (як-є (rejected receive-failed)))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(rejected receive-failed)"
    );
}

#[test]
fn mono_ms_is_derived_from_nanoseconds_in_lisp() {
    let mut session = time_session();

    assert_eq!(
        eval_program("(мілісекунди-з-наносекунди 0)", &mut session)
            .unwrap()
            .value
            .to_string(),
        "0"
    );
    assert_eq!(
        eval_program("(мілісекунди-з-наносекунди 999999)", &mut session)
            .unwrap()
            .value
            .to_string(),
        "0"
    );
    assert_eq!(
        eval_program("(мілісекунди-з-наносекунди 1000000)", &mut session)
            .unwrap()
            .value
            .to_string(),
        "1"
    );
    assert_eq!(
        eval_program("(мілісекунди-з-наносекунди 1999999)", &mut session)
            .unwrap()
            .value
            .to_string(),
        "1"
    );
}

#[test]
fn mono_ms_binding_is_owned_by_lisp_after_time_library_loads() {
    let mut session = time_session();
    assert_eq!(
        eval_program("(мілісекунди-з-наносекунди 1000000)", &mut session)
            .unwrap()
            .value
            .to_string(),
        "1",
        "language-owned conversion is available without a lexical alias for a D9 identity"
    );
}

#[test]
fn timezone_declaration_policy_is_language_owned() {
    let mut session = time_session();

    assert_eq!(
        eval_program(
            "(обрати-достовірне-джерело-часового-поясу \"Europe/Kyiv\" \"Etc/UTC\")",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(detected \"Europe/Kyiv\" TZ)"
    );
    assert_eq!(
        eval_program(
            "(обрати-достовірне-джерело-часового-поясу (як-є ()) \"Europe/Kyiv\")",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(detected \"Europe/Kyiv\" etc-timezone)"
    );
    assert_eq!(
        eval_program(
            "(обрати-достовірне-джерело-часового-поясу \"\" \"Europe/Kyiv\")",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(detected \"Europe/Kyiv\" etc-timezone)"
    );
    assert_eq!(
        eval_program(
            "(обрати-достовірне-джерело-часового-поясу (як-є ()) (як-є ()))",
            &mut session,
        )
        .unwrap()
        .value
        .to_string(),
        "(unknown host-declaration-unavailable)"
    );
}

#[test]
fn timezone_detection_is_explicit_and_ntp_requires_host_string() {
    let mut session = time_session();
    assert_d10_has_no_implicit_core_operation(0b0011110011); // сирі оголошення часового поясу
    assert!(eval_program("(часовий-пояс-визначити)", &mut session).is_err());
    assert!(eval_program("(інтернет-час-синхронізувати 123 100)", &mut session).is_err());
    assert_eq!(
        eval_program(
            "(створити-перевірене-значення-поясу \"Europe/Kyiv\" 7200)",
            &mut session
        )
        .unwrap()
        .value
        .to_string(),
        "(accepted (timezone \"Europe/Kyiv\" 7200))"
    );

    assert_eq!(
        eval_program(
            "(створити-перевірене-значення-поясу 123 7200)",
            &mut session
        )
        .unwrap()
        .value
        .to_string(),
        "(rejected invalid-name)"
    );
}
