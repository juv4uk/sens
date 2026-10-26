use sens::{
    eval_parsed_expressions, eval_program, load_core_library, load_time_library, DomainIdentity,
    Expr, ExprKind, Session, Span, Value,
};

#[test]
fn time_library_bootstraps_from_exact_t5m_and_d10_functions_execute() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("Core4 bootstrap");
    load_time_library(&mut session).expect("time bootstrap from Zig-restored T5M words");

    let invoke = |bits: u16, argument: u32, session: &mut Session| {
        let identity = DomainIdentity::from_coordinate(
            sens::domain_ladder::DomainCoordinate::new(10, bits)
                .expect("the time function is an exact D10 word"),
        );
        let argument_bits = (0..24)
            .rev()
            .map(|shift| ((argument >> shift) & 1) as u8)
            .collect::<Vec<_>>();
        let call = Expr {
            kind: ExprKind::List(
                vec![
                    Expr {
                        kind: ExprKind::DomainIdentity(identity),
                        span: Span::default(),
                    },
                    Expr {
                        kind: ExprKind::BinaryNumber(
                            sens::BinaryNumber::from_numeric_domain_bits(24, &argument_bits)
                                .expect("test argument is an exact D24+ value"),
                        ),
                        span: Span::default(),
                    },
                ]
                .into(),
            ),
            span: Span::default(),
        };
        eval_parsed_expressions(&[call], session)
            .unwrap_or_else(|error| panic!("exact T5M-loaded D10 {bits:010b}: {error}"))
    };

    for (bits, argument, expected) in [
        (0b1011101010, 4, true),
        (0b1011101010, 3, false),
        (0b1011101011, 15, true),
        (0b1011101011, 16, false),
    ] {
        let result = invoke(bits, argument, &mut session);
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(expected),
            "D10:{bits:010b} must return the exact D1 result; got {:?}",
            result.value
        );
    }
}

/// Назва з таблиці функцій веде до коду, що має примітив (хостовий механізм).
fn is_raw_primitive(name: &str) -> bool {
    sens::semantic_registry_export::semantic_id_for_admitted_surface(name)
        .and_then(sens::semantic_registry_export::function_role)
        == Some("primitive")
}

#[test]
fn raw_host_time_surface_is_small_and_semantic_names_are_absent() {
    let session = Session::default();

    for name in [
        "mono-ns",
        "unix-time-now",
        "ntp-query-raw",
        "timezone-declarations-raw",
    ] {
        // Після #1477 сирі хостові механізми — примітиви за кодом СЕНС,
        // а не прив'язки Value::Builtin за назвою.
        assert!(
            is_raw_primitive(name),
            "{name} must remain a raw host primitive"
        );
    }

    for name in [
        "mono-ms",
        "utc-now",
        "internet-time-sync",
        "timezone-detect",
    ] {
        assert!(
            session.environment.get(name).is_none(),
            "{name} is semantic policy and must not reappear in the root host surface"
        );
    }
}

#[test]
fn time_library_builds_public_meanings_over_raw_host_observations() {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    load_time_library(&mut session).unwrap();

    for name in [
        "mono-ms",
        "utc-now",
        "internet-time-sync",
        "timezone-detect",
    ] {
        assert!(
            matches!(session.environment.get(name), Some(Value::Closure(_))),
            "{name} must be language-owned after lib/time.my loads"
        );
    }

    for name in [
        "mono-ns",
        "unix-time-now",
        "ntp-query-raw",
        "timezone-declarations-raw",
    ] {
        assert!(
            is_raw_primitive(name),
            "{name} must stay the underlying raw host mechanism"
        );
    }
}

#[test]
fn raw_time_primitives_are_not_redefined_as_self_recursive_lisp_functions() {
    let source = include_str!("../../../lib/time.lisp");
    for (raw_surface, english_peer) in [
        ("мережевий-протокол-часу-запит-сирий", "ntp-query-raw"),
        ("часовий-пояс-оголошення-сирий", "timezone-declarations-raw"),
        ("юнікс-час-зараз", "unix-time-now"),
    ] {
        assert!(
            is_raw_primitive(english_peer),
            "{english_peer}: сирий механізм має залишатися ратифікованим примітивом"
        );
        let rebound = source.lines().any(|line| {
            line.trim_start()
                .strip_prefix("(визначити ")
                .and_then(|rest| rest.split_whitespace().next())
                == Some(raw_surface)
        });
        assert!(
            !rebound,
            "{raw_surface}: заборонено замінювати машинний примітив саморекурсивним Lisp-замиканням"
        );
    }
}

#[test]
fn time_stable_peers_reuse_the_same_lisp_closures() {
    use std::rc::Rc;

    let mut session = Session::default();
    load_core_library(&mut session).expect("основа для часових значень");
    load_time_library(&mut session).expect("часові функції визначає Lisp");

    // Перевірка проєкції без повторного макросу, окремої онтології чи дубля коду.
    for (source, peer) in [
        ("utc-now", "поточний-всч"),
        ("utc-from-unix", "всч-із-юнікс"),
        ("unix-time-observation->utc", "юнікс-спостереження-у-всч"),
        ("milliseconds-from-nanoseconds", "мілісекунди-із-наносекунд"),
        ("mono-ms", "монотонний-мс"),
        ("timezone-name", "назва-часового-поясу"),
        ("timezone-detect", "визначити-часовий-пояс"),
        (
            "timezone-offset-seconds",
            "зміщення-часового-поясу-в-секундах",
        ),
        ("deadline-reached?", "дедлайн-досягнуто?"),
        ("deadline-reached-at?", "дедлайн-досягнуто-на-момент?"),
        ("elapsed-ns", "минуло-нс"),
        ("deadline-from", "дедлайн-від"),
        ("deadline-after-ns", "дедлайн-через-нс"),
        ("internet-time-sync", "запитати-інтернет-час"),
    ] {
        let original = session.environment.get(source);
        let localized = session.environment.get(peer);
        match (&original, &localized) {
            (Some(Value::Closure(left)), Some(Value::Closure(right))) => {
                assert!(
                    Rc::ptr_eq(left, right),
                    "{peer} має бути тим самим Lisp-замиканням, що й {source}"
                );
            }
            (left, right) => {
                panic!("Втрата стабільної часової проєкції {source}/{peer}: {left:?} та {right:?}");
            }
        }
    }
}

fn eval_exact_time_source(
    source: &str,
    session: &mut Session,
) -> Result<Value, sens::LanguageError> {
    let expressions = sens::parse_mixed_exact_domain_time_source("lib/time.lisp", source)?;
    Ok(sens::eval_parsed_expressions(&expressions, session)?.value)
}

#[test]
fn ntp_mode_and_stratum_execute_exact_d1_and_reject_lists() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("основа часу");
    load_time_library(&mut session).expect("чинні часові Lisp-закони");
    for (source, expected) in [
        ("(інтернет-час-режим-припустимий? 4)", true),
        ("(інтернет-час-режим-припустимий? 5)", true),
        ("(інтернет-час-режим-припустимий? 3)", false),
        ("(інтернет-час-режим-припустимий? 6)", false),
        ("(інтернет-час-режим-припустимий? (як-є (4)))", false),
        ("(інтернет-час-рівень-припустимий? 1)", true),
        ("(інтернет-час-рівень-припустимий? 15)", true),
        ("(інтернет-час-рівень-припустимий? 0)", false),
        ("(інтернет-час-рівень-припустимий? 16)", false),
        ("(інтернет-час-рівень-припустимий? (як-є (1)))", false),
    ] {
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| {
                panic!("test_id=ntp-d1 layer=SENS input={source} error={error}")
            })
            .value;
        assert_eq!(
            result.as_predicate_bit(),
            Some(expected),
            "test_id=ntp-d1 layer=SENS input={source} expected=D1:{expected} actual={result}"
        );
    }
}

#[test]
fn time_predicates_use_exact_d1_literals_and_keep_boundary_laws() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("Core functions");
    load_time_library(&mut session).expect("Lisp-owned time functions");

    // Reuse actual existing time-library functions; this is not a synthetic
    // coordinate-only test. Direct D1 values must remain typed predicates.
    for (source, expected) in [
        ("(internet-time-mode-valid? 4)", true),
        ("(internet-time-mode-valid? 5)", true),
        ("(internet-time-mode-valid? 3)", false),
        ("(internet-time-mode-valid? 6)", false),
        ("(internet-time-stratum-valid? 1)", true),
        ("(internet-time-stratum-valid? 15)", true),
        ("(internet-time-stratum-valid? 0)", false),
        ("(internet-time-stratum-valid? 16)", false),
        ("(deadline-reached-at? -1 0)", false),
        ("(deadline-reached-at? 0 0)", true),
        ("(deadline-reached-at? 1 0)", true),
        ("(deadline-reached-at? 9 10)", false),
        ("(deadline-reached-at? 10 10)", true),
        ("(deadline-reached-at? 11 10)", true),
        ("(крайній-час-досягнуто-у? 9 10)", false),
        ("(крайній-час-досягнуто-у? 10 10)", true),
        ("(крайній-час-досягнуто-у? 11 10)", true),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("{source}: {error}"))
            .value;
        assert_eq!(
            value.as_predicate_bit(),
            Some(expected),
            "{source} must return exact D1, not a Number or structural ()"
        );
    }

    for (source, expected) in [("#d1:0", false), ("#d1:1", true)] {
        let value = eval_exact_time_source(source, &mut session).unwrap();
        assert_eq!(value.as_predicate_bit(), Some(expected), "{source}");
    }
    for source in ["0", "1"] {
        let value = eval_program(source, &mut session).unwrap().value;
        assert_eq!(
            value.as_predicate_bit(),
            None,
            "{source} must remain numeric"
        );
    }

    let code: String = include_str!("../../../lib/time.lisp")
        .lines()
        .filter(|line| !line.trim_start().starts_with(';'))
        .collect::<Vec<_>>()
        .join("\n");
    assert_eq!(
        code.matches("(010 (001 ()))").count(),
        0,
        "no redundant ATOM(QUOTE empty) truth constructors"
    );
    assert_eq!(
        code.matches("(101 (001 (0)) (001 (1)))").count(),
        0,
        "no redundant EQ(QUOTE 0, QUOTE 1) false constructors"
    );
    // Текстові теги ширини не належать нинішній українській граматиці.
    // Виконуваний D1 закон вище перевіряємо за типом, а не підрахунком
    // застарілих #d1-літералів у файлі.
    assert!(
        !code.contains("#d1:"),
        "застарілий текстовий D1-тег у lib/time.lisp"
    );
    assert!(
        code.contains("(хибне? (менше? поточні-нс граничні-нс))"),
        "точна D24+ межа повинна лишатися у Lisp без D3 EQ чисел"
    );
}
