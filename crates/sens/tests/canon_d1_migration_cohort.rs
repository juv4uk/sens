//! Регресійна когорта #5029: виконуємо Canon напряму, без історичного
//! witness-runner (він мігрується окремо в #5025).
use sens::{
    eval_parsed_expressions, eval_program, load_core_library, parse_mixed_exact_domain, Session,
};

fn canon_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("current Core library");
    // Existing mixed-domain reader preserves compatibility D1 projections
    // while lifting canonical D3/D4 call heads into exact domain identities.
    let forms = parse_mixed_exact_domain(include_str!("../../../lib/canon.lisp"))
        .expect("Canon current D3/D4 source must parse");
    eval_parsed_expressions(&forms, &mut session).expect("Canon source must load");
    session
}

#[test]
fn canon_constitutive_laws_use_current_predicate_results() {
    let mut session = canon_session();
    let cases: [(&str, &str); 13] = [
        ("канон-порожній-список", "()"),
        (
            "(канон-закон-порожній-список)",
            "(канон-закон-результат порожній-список виконано)",
        ),
        (
            "(канон-закон-атом-пара (quote left) (quote right))",
            "(канон-закон-результат атом-пара виконано)",
        ),
        (
            "(канон-закон-перше-пара (quote left) (quote right))",
            "(канон-закон-результат перше-пара виконано)",
        ),
        (
            "(канон-закон-решта-пара (quote left) (quote right))",
            "(канон-закон-результат решта-пара виконано)",
        ),
        (
            "(канон-закон-рівність-рефлексивний-атом (quote left))",
            "(канон-закон-результат тотожність-рефлексивний-атом виконано)",
        ),
        (
            "(канон-закон-решта-крапковий)",
            "(канон-закон-результат решта-крапковий виконано)",
        ),
        (
            "(канон-закон-решта-правильний)",
            "(канон-закон-результат решта-правильний виконано)",
        ),
        (
            "(канон-закон-решта-неправильний)",
            "(канон-закон-результат решта-неправильний виконано)",
        ),
        (
            "(канон-закон-цитування-пригнічує-обчислення)",
            "(канон-закон-результат цитування-пригнічує-обчислення виконано)",
        ),
        (
            "(канон-закон-умова-перший-збіг-короткий-ланцюг)",
            "(канон-закон-результат умова-перший-збіг-короткий-ланцюг виконано)",
        ),
        (
            "(канон-закон-символьний-поверхня)",
            "(канон-закон-результат символьна-поверхня виконано)",
        ),
        ("(канон-відповідає?)", "(канон-відповідність виконано)"),
    ];
    for (expr, expected) in cases {
        let actual = eval_program(expr, &mut session)
            .unwrap_or_else(|error| panic!("Canon evaluation failed: {expr}: {error}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "Canon law {expr}");
    }
}

#[test]
fn canon_negative_predicate_polarity_and_exhaustion_are_not_truthiness() {
    let mut session = canon_session();
    // Пара не є атомом: YES і NO тут не взаємозамінні.
    let cases: [(&str, &str); 3] = [
        (
            "(канон-закон-рівність-рефлексивний-атом (quote (left right)))",
            "(канон-закон-результат тотожність-рефлексивний-атом порушено)",
        ),
        (
            "(канон-відповідність-з (quote ()))",
            "(канон-відповідність виконано)",
        ),
        (
            "(канон-відповідність-з (quote ((канон-закон-результат приклад порушено))))",
            "(канон-відповідність порушено)",
        ),
    ];
    for (expr, expected) in cases {
        let actual = eval_program(expr, &mut session)
            .unwrap_or_else(|error| panic!("Canon negative law failed: {expr}: {error}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "Canon branch polarity {expr}");
    }
}


/// #1968/#2012: the typed empty-ground action over ATOM is executable in
/// SENS itself. A YES from ATOM is the guard allowing atomic D3 EQ; the
/// action does not acquire a new D4 word or a host-owned boolean meaning.
#[test]
fn atom_empty_refinement_is_typed_strict_and_idempotent_on_live_sens_values() {
    let mut session = Session::default();
    eval_program(
        r#"
        (визначити уточнити-атом-до-порожнього?
          (функція (значення)
            (за-умовою
              ((атом? значення) (тотожне? значення (як-є ())))
              (так ні))))
        (визначити уточнити-порожній-повторно?
          (функція (значення)
            (за-умовою
              ((уточнити-атом-до-порожнього? значення)
               (тотожне? значення (як-є ())))
              (так ні))))
        "#,
        &mut session,
    )
    .expect("живі українські DEFINE і D3 COND/ATOM/EQ");

    let cases: [(&str, bool, bool); 5] = [
        ("(як-є ())", true, true),
        ("(як-є знак)", true, false),
        ("(як-є інший)", true, false),
        ("(як-є (знак))", false, false),
        ("(сполучити (як-є знак) (як-є ()))", false, false),
    ];
    for (input, expected_atom, expected_empty) in cases {
        for (name, expected) in [
            ("атом?", expected_atom),
            ("уточнити-атом-до-порожнього?", expected_empty),
            ("уточнити-порожній-повторно?", expected_empty),
        ] {
            let program = format!("({name} {input})");
            let actual = eval_program(&program, &mut session)
                .unwrap_or_else(|error| panic!(
                    "test_id=1968-ATOM-EMPTY layer=SENS input={program} actual_error={error}"
                ))
                .value;
            assert_eq!(
                actual.as_predicate_bit(),
                Some(expected),
                "test_id=1968-ATOM-EMPTY layer=SENS input={program} expected=D1:{expected} actual={actual}"
            );
        }
    }

    // The wrong generator that merely returns ATOM must be distinguished by
    // a nonempty atom: ATOM=YES, the empty-ground refinement=NO.
    let source = "(атом? (як-є знак))";
    let mutant = eval_program(source, &mut session).expect("живий негатив").value;
    let actual = eval_program(
        "(уточнити-атом-до-порожнього? (як-є знак))",
        &mut session,
    )
    .expect("живе уточнення")
    .value;
    assert_eq!(mutant.as_predicate_bit(), Some(true));
    assert_eq!(actual.as_predicate_bit(), Some(false));
    // This is bounded idempotence, not evidence of an open ATOM prefix tree.
}

/// #1968/#2014: a CONS pair carries two independent SENS values.
/// These are D3 construction witnesses, not a claim that suffix bits alone
/// can synthesize unknown payloads or that new D4 slots are allocated.
#[test]
fn cons_preserves_independent_payloads_without_fabricating_generator_children() {
    let mut session = Session::default();
    for (left, right) in [("ліве", "праве"), ("перше", "решта"), ("знак", "інший")] {
        for (selector, expected) in [("перше", left), ("решта", right)] {
            let program = format!(
                "(тотожне? ({selector} (сполучити (як-є {left}) (як-є {right}))) (як-є {expected}))"
            );
            let value = eval_program(&program, &mut session)
                .unwrap_or_else(|error| panic!(
                    "test_id=1968-CONS-PAYLOAD layer=SENS input={program} actual_error={error}"
                ))
                .value;
            assert_eq!(
                value.as_predicate_bit(), Some(true),
                "test_id=1968-CONS-PAYLOAD layer=SENS input={program} expected=D1:true actual={value}"
            );
        }
    }
    // A wrong, payload-independent replacement cannot satisfy right-side
    // reconstruction for two distinct atomic tails.
    let negative = "(тотожне? (решта (сполучити (як-є ліве) (як-є праве))) (як-є інший))";
    let value = eval_program(negative, &mut session)
        .expect("сам SENS виконує негативну підміну")
        .value;
    assert_eq!(
        value.as_predicate_bit(), Some(false),
        "test_id=1968-CONS-PAYLOAD layer=SENS case=mutant expected=D1:false actual={value}"
    );
}


/// #1968/#2011: quoting preserves a structural datum without evaluating its
/// head. A second QUOTE written inside a quoted list is DATA, not automatically
/// the next executable child of a hypothetical D3 prefix generator.
#[test]
fn quote_depth_is_structural_data_not_an_invented_generator_opcode() {
    let mut session = Session::default();
    let cases = [
        (
            "(тотожне? (перше (як-є (неозначений))) (як-є неозначений))",
            true,
        ),
        (
            "(тотожне? (перше (перше (як-є ((неозначений))))) (як-є неозначений))",
            true,
        ),
        (
            "(тотожне? (перше (як-є (як-є неозначений))) (як-є як-є))",
            true,
        ),
        (
            "(тотожне? (перше (як-є (як-є неозначений))) (як-є неозначений))",
            false,
        ),
    ];
    for (source, expected) in cases {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=1968-QUOTE-DATA layer=SENS input={source} actual_error={error}"
            ))
            .value;
        assert_eq!(
            value.as_predicate_bit(), Some(expected),
            "test_id=1968-QUOTE-DATA layer=SENS input={source} expected=D1:{expected} actual={value}"
        );
    }
    // Distinct from QUOTE: evaluating the same unbound head cannot succeed.
    let unquoted = eval_program("(неозначений)", &mut session);
    assert!(
        unquoted.is_err(),
        "test_id=1968-QUOTE-DATA layer=SENS case=unquoted-mutant expected=unbound-head-error actual={unquoted:?}"
    );
}


/// #1968/#2013: D3 EQ is a typed atomic relation. Comparing freshly built
/// pairs is not rescued by pointer identity or by a pretend local EQ child;
/// a composed CAR+EQ law explicitly imports the selector root.
#[test]
fn eq_atomic_law_does_not_silently_gain_structural_pair_equality() {
    let mut session = Session::default();
    for (source, expected) in [
        ("(тотожне? (як-є знак) (як-є знак))", true),
        ("(тотожне? (як-є знак) (як-є інший))", false),
        ("(тотожне? (як-є ()) (як-є ()))", true),
        (
            "(тотожне? (перше (сполучити (як-є знак) (як-є ()))) (як-є знак))",
            true,
        ),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=1968-EQ-ATOMS layer=SENS input={source} actual_error={error}"
            ))
            .value;
        assert_eq!(
            value.as_predicate_bit(), Some(expected),
            "test_id=1968-EQ-ATOMS layer=SENS input={source} expected=D1:{expected} actual={value}"
        );
    }
    let invalid = "(тотожне? (сполучити (як-є знак) (як-є ())) (сполучити (як-є знак) (як-є ())))";
    // Contract 11.8 після CURRENT FOUNDATION SUPERSESSION (#3161):
    // позадоменна пара не є предикатом, EQ відхиляє її Type-помилкою.
    let error = eval_program(invalid, &mut session)
        .expect_err("EQ-пара має бути відхилена виконавцем SENS");
    assert_eq!(
        error.kind,
        sens::ErrorKind::Type,
        "test_id=1968-EQ-PAIR layer=SENS expected=Type actual={error}"
    );
}

/// #1968/#2015: COND is control with an exact D1 selection rule.
/// Exhaustion produces structural NIL, not predicate NO; NIL in *test*
/// position is rejected by Contract 11.8, not accepted as a third answer.
#[test]
fn cond_exhaustion_and_false_answer_are_distinct_live_sens_values() {
    let mut session = Session::default();
    let no = eval_program("ні", &mut session).expect("D1 ні").value;
    let selected_no = eval_program("(за-умовою (так ні))", &mut session)
        .expect("вибрана D1-відповідь ні")
        .value;
    let exhausted = eval_program("(за-умовою (ні (як-є неможливе)))", &mut session)
        .expect("вичерпання COND без вибраної гілки")
        .value;
    assert_eq!(no.as_predicate_bit(), Some(false));
    assert_eq!(selected_no.as_predicate_bit(), Some(false));
    assert!(
        matches!(exhausted, sens::Value::Nil),
        "test_id=1968-COND-EXHAUST layer=SENS expected=structural-NIL actual={exhausted}"
    );
    assert_ne!(
        exhausted, selected_no,
        "test_id=1968-COND-EXHAUST layer=SENS expected=structural-NIL-not-D1-NO"
    );

    // D1:0 справді пропускає гілку; його не можна підміняти на D3:000.
    let program = "(тотожне? (за-умовою (ні (перше (як-є ()))) (так (як-є правильно))) (як-є правильно))";
    let value = eval_program(program, &mut session)
        .unwrap_or_else(|error| panic!(
            "test_id=1968-COND-D1-NO layer=SENS input={program} actual_error={error}"
        ))
        .value;
    assert_eq!(
        value.as_predicate_bit(), Some(true),
        "test_id=1968-COND-D1-NO layer=SENS expected=D1:true actual={value}"
    );

    // Структурне NIL лишається відмінним від D1:NO, але не допустиме
    // в позиції COND test: іменована помилка Type.
    let empty_test = "(за-умовою ((як-є ()) (як-є не-має-виконатися)) (так (як-є правильно)))";
    let error = eval_program(empty_test, &mut session)
        .expect_err("COND з NIL як тестом має відхилитися");
    assert_eq!(
        error.kind,
        sens::ErrorKind::Type,
        "test_id=1968-COND-EMPTY layer=SENS expected=Type actual={error}"
    );

    // Символ не належить ані D1, ані D3:000: його відхиляє сам SENS.
    let invalid = "(за-умовою ((як-є сторонній) (як-є неможливе)) (так (як-є правильно)))";
    let error = eval_program(invalid, &mut session)
        .expect_err("SENS COND має відхилити символ як керівне значення");
    assert_eq!(
        error.kind,
        sens::ErrorKind::Type,
        "test_id=1968-COND-WRONG-DOMAIN layer=SENS input={invalid} expected=Type actual={error}"
    );

    // Позадоменний EQ не породжує фальшивий D1:NO або D3:000 для COND;
    // Type-помилка виникає до будь-якої наступної гілки.
    let composed = "(за-умовою ((тотожне? (сполучити (як-є ліве) (як-є ())) (як-є ліве)) (як-є хибна-гілка)) (так (як-є правильна-гілка)))";
    let error = eval_program(composed, &mut session)
        .expect_err("EQ-пара в COND не має перетворюватися на NO");
    assert_eq!(
        error.kind,
        sens::ErrorKind::Type,
        "test_id=1968-EQ-COND-COMPOSITION layer=SENS expected=Type actual={error}"
    );
}


/// #2014: both binary growth shapes are executable SENS constructions.
/// The same CONS root can hold independent left/right payloads; suffix bits
/// cannot synthesize either unknown payload, so no D4 child is allocated.
/// Every traversal below is evaluated by SENS, not a host Lisp simulator.
#[test]
fn cons_left_and_right_growth_remain_payload_dependent_in_live_sens() {
    let mut session = Session::default();
    for (a, b, c) in [
        ("лівий-атом", "середній-атом", "правий-атом"),
        ("перший-атом", "другий-атом", "третій-атом"),
    ] {
        let left = format!(
            "(сполучити (сполучити (як-є {a}) (як-є {b})) (як-є {c}))"
        );
        let right = format!(
            "(сполучити (як-є {a}) (сполучити (як-є {b}) (як-є {c})))"
        );
        let paths = [
            (format!("(перше (перше {left}))"), a),
            (format!("(решта (перше {left}))"), b),
            (format!("(решта {left})"), c),
            (format!("(перше {right})"), a),
            (format!("(перше (решта {right}))"), b),
            (format!("(решта (решта {right}))"), c),
        ];
        for (path, expected_atom) in paths {
            let source = format!("(тотожне? {path} (як-є {expected_atom}))");
            let value = eval_program(&source, &mut session)
                .unwrap_or_else(|error| panic!(
                    "test_id=2014-CONS-GROWTH layer=SENS input={source} actual_error={error}"
                ))
                .value;
            assert_eq!(
                value.as_predicate_bit(),
                Some(true),
                "test_id=2014-CONS-GROWTH layer=SENS input={source} expected=D1:YES actual={value}"
            );
        }
        for source in [
            format!("(тотожне? (перше (перше {left})) (як-є {b}))"),
            format!("(тотожне? (перше (решта {right})) (як-є {c}))"),
        ] {
            let value = eval_program(&source, &mut session)
                .unwrap_or_else(|error| panic!(
                    "test_id=2014-CONS-MUTANT layer=SENS input={source} actual_error={error}"
                ))
                .value;
            assert_eq!(
                value.as_predicate_bit(),
                Some(false),
                "test_id=2014-CONS-MUTANT layer=SENS input={source} expected=D1:NO actual={value}"
            );
        }
    }
}

/// #2013/#2015, current Contract 11.8: EQ is defined only on atoms.
/// Pair operands fail with a named Type error before COND can select/skip.
/// A valid atomic EQ-negative result is D1:NO and does skip a branch.
#[test]
fn eq_pair_rejects_before_cond_without_implicit_no_witness() {
    let mut session = Session::default();
    let invalid_eq = "(тотожне? (сполучити (як-є а) (як-є б)) (сполучити (як-є а) (як-є б)))";
    let error = eval_program(invalid_eq, &mut session)
        .expect_err("пара в D3 EQ мусить дати Type");
    assert_eq!(
        error.kind, sens::ErrorKind::Type,
        "test_id=2015-EQ-PAIR layer=SENS input={invalid_eq} expected=Type actual={error}"
    );

    let explicit_no = "(тотожне? (як-є а) (як-є б))";
    let no = eval_program(explicit_no, &mut session)
        .expect("атомний EQ двох відмінних атомів").value;
    assert_eq!(no.as_predicate_bit(), Some(false));

    let valid = format!(
        "(за-умовою ({explicit_no} (перше (як-є ()))) (так (як-є правильна-гілка)))"
    );
    let result = eval_program(&valid, &mut session)
        .unwrap_or_else(|error| panic!(
            "test_id=2015-EQ-COND-NO layer=SENS input={valid} actual_error={error}"
        )).value;
    assert_eq!(result, sens::Value::Symbol("правильна-гілка".into()));

    // COND does not swallow a domain error from an earlier EQ call.
    let invalid_cond = format!(
        "(за-умовою ({invalid_eq} (як-є хибна-гілка)) (так (як-є правильна-гілка)))"
    );
    let error = eval_program(&invalid_cond, &mut session)
        .expect_err("помилка EQ в умові COND мусить дійти до користувача");
    assert_eq!(
        error.kind, sens::ErrorKind::Type,
        "test_id=2015-EQ-COND-PAIR layer=SENS input={invalid_cond} expected=Type actual={error}"
    );

    let invalid_control = "(за-умовою ((як-є ()) (як-є хибна-гілка)) (так (як-є правильна-гілка)))";
    let error = eval_program(invalid_control, &mut session)
        .expect_err("структурне NIL не є D1 COND предикатом");
    assert_eq!(error.kind, sens::ErrorKind::Type);
}

/// #1968/#2013/#2015: current D3 EQ admits exactly atomic PredicateBit
/// answers; pair inputs are named Type failures. COND selects/skips only
/// exact D1, never structural NIL or arbitrary symbols.
#[test]
fn eq_atomic_answers_and_pair_errors_drive_cond_without_host_truthiness() {
    let mut session = Session::default();
    let yes = "(тотожне? (як-є ліве) (як-є ліве))";
    let no = "(тотожне? (як-є ліве) (як-є праве))";
    for (id, source, expected) in [("yes", yes, true), ("no", no, false)] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=1968-EQ-{id} layer=SENS input={source} actual_error={error}"
            )).value;
        assert_eq!(
            value.as_predicate_bit(), Some(expected),
            "test_id=1968-EQ-{id} layer=SENS expected=D1:{expected} actual={value}"
        );
    }

    let pairs = [
        "(тотожне? (сполучити (як-є ліве) (як-є ())) (сполучити (як-є ліве) (як-є ())))",
        "(тотожне? (сполучити (як-є ліве) (як-є ())) (як-є ліве))",
    ];
    for (id, source) in pairs.iter().enumerate() {
        let error = eval_program(source, &mut session)
            .expect_err("недопущений EQ не перетворюється на D1:NO");
        assert_eq!(
            error.kind, sens::ErrorKind::Type,
            "test_id=1968-EQ-PAIR-{id} layer=SENS input={source} expected=Type actual={error}"
        );
        let condition = format!(
            "(за-умовою ({source} (перше (як-є ()))) (так (як-є резерв)))"
        );
        let error = eval_program(&condition, &mut session)
            .expect_err("COND не приховує помилку EQ");
        assert_eq!(
            error.kind, sens::ErrorKind::Type,
            "test_id=1968-COND-EQ-PAIR-{id} layer=SENS input={condition} expected=Type actual={error}"
        );
    }

    let skip = format!(
        "(за-умовою ({no} (перше (як-є ()))) (так (як-є резерв)))"
    );
    let result = eval_program(&skip, &mut session)
        .unwrap_or_else(|error| panic!(
            "test_id=1968-COND-D1-NO layer=SENS input={skip} actual_error={error}"
        )).value;
    assert_eq!(result, sens::Value::Symbol("резерв".into()));

    let select = format!(
        "(за-умовою ({yes} (як-є вибрано)) (так (перше (як-є ()))))"
    );
    let result = eval_program(&select, &mut session)
        .unwrap_or_else(|error| panic!(
            "test_id=1968-COND-D1-YES layer=SENS input={select} actual_error={error}"
        )).value;
    assert_eq!(result, sens::Value::Symbol("вибрано".into()));

    for invalid in [
        "(за-умовою ((як-є ()) (як-є недопустимо)))",
        "(за-умовою ((як-є сторонній-символ) (як-є недопустимо)))",
    ] {
        let error = eval_program(invalid, &mut session)
            .expect_err("COND приймає тільки D1:1/D1:0");
        assert_eq!(
            error.kind, sens::ErrorKind::Type,
            "test_id=1968-COND-WRONG-TYPE layer=SENS input={invalid} expected=Type actual={error}"
        );
    }
}


/// #2014/#2016: CONS is a binary constructor, not an associative algebra.
/// This is a *bounded structural counterexample*, not a global impossibility
/// result for every possible constructor generator. Both terms contain the
/// same ordered atoms. ATOM with CAR/CDR distinguishes their parenthesization
/// through the real SENS evaluator, without applying partial EQ to pairs.
#[test]
fn cons_tree_growth_is_observably_nonassociative_with_atom_and_selectors() {
    let mut session = Session::default();
    let left = "(сполучити (сполучити (як-є а) (як-є б)) (як-є в))";
    let right = "(сполучити (як-є а) (сполучити (як-є б) (як-є в)))";
    for (shape, tree, left_atom, right_atom) in [
        ("left-nested", left, false, true),
        ("right-nested", right, true, false),
    ] {
        for (selector, expected) in [("перше", left_atom), ("решта", right_atom)] {
            let program = format!("(атом? ({selector} {tree}))");
            let actual = eval_program(&program, &mut session)
                .unwrap_or_else(|error| panic!(
                    "test_id=2014-CONS-NONASSOC layer=SENS shape={shape} input={program} actual_error={error}"
                ))
                .value;
            assert_eq!(
                actual.as_predicate_bit(), Some(expected),
                "test_id=2014-CONS-NONASSOC layer=SENS shape={shape} input={program} expected=D1:{expected} actual={actual}"
            );
        }
    }
}



/// #1968: тотожність атомних значень не залежить від адреси двох окремих CONS.
/// Rust створює лише вхідні носії; сам EQ/COND виконується рушієм SENS.
/// Це не припущення про інтернування та не дозвіл EQ для складених пар.
#[test]
fn eq_equal_atoms_in_separately_built_pairs_are_value_equal_in_sens() {
    let mut session = Session::default();
    session.environment.define(
        "лівий-носій",
        sens::Value::list([sens::Value::Symbol("спільний-атом".into())]),
    );
    session.environment.define(
        "правий-носій",
        sens::Value::list([sens::Value::Symbol("спільний-атом".into())]),
    );
    session.environment.define(
        "відмінний-носій",
        sens::Value::list([sens::Value::Symbol("інший-атом".into())]),
    );

    for (id, source, expected) in [
        (
            "same-value-other-carrier",
            "(тотожне? (перше лівий-носій) (перше правий-носій))",
            true,
        ),
        (
            "distinct-value-other-carrier",
            "(тотожне? (перше лівий-носій) (перше відмінний-носій))",
            false,
        ),
        (
            "cond-on-separate-carriers",
            "(за-умовою ((тотожне? (перше лівий-носій) (перше правий-носій)) так) (так ні))",
            true,
        ),
    ] {
        let result = eval_program(source, &mut session).unwrap_or_else(|error| panic!(
            "test_id=1968-EQ-CARRIERS-{id} layer=SENS input={source} actual_error={error}"
        )).value;
        assert_eq!(
            result.as_predicate_bit(), Some(expected),
            "test_id=1968-EQ-CARRIERS-{id} layer=SENS input={source} expected=D1:{expected} actual={result}"
        );
    }

    let invalid = "(тотожне? лівий-носій правий-носій)";
    let error = eval_program(invalid, &mut session)
        .expect_err("test_id=1968-EQ-CARRIERS-PAIRS expected=Type");
    assert_eq!(
        error.kind, sens::ErrorKind::Type,
        "test_id=1968-EQ-CARRIERS-PAIRS layer=SENS input={invalid} expected=Type actual={error}"
    );
}
/// #5950 / #1968: SENS constructs two distinct CONS roots with one shared tail.
/// The SENS evaluator must preserve exact D3 CAR/CDR semantics. Rc::ptr_eq is
/// checked only as a *mechanism* invariant (no copy of an existing PairNode),
/// never as language-level EQ or a canonical identity representation.
#[test]
fn cdr_on_shared_sens_tail_preserves_pairnode_allocation() {
    use std::rc::Rc;

    let mut session = Session::default();
    let setup = r#"
        (визначити спільний-хвіст (як-є (а б)))
        (визначити ліва-гілка (сполучити (як-є л) спільний-хвіст))
        (визначити права-гілка (сполучити (як-є п) спільний-хвіст))
    "#;
    eval_program(setup, &mut session).unwrap_or_else(|error| panic!(
        "test_id=5950-SHARED-SETUP layer=SENS input={setup} actual_error={error}"
    ));

    let read = |source: &str, session: &mut Session| {
        eval_program(source, session).unwrap_or_else(|error| panic!(
            "test_id=5950-SHARED-CDR layer=SENS input={source} actual_error={error}"
        )).value
    };

    let tail = read("спільний-хвіст", &mut session);
    let left = read("(решта ліва-гілка)", &mut session);
    let right = read("(решта права-гілка)", &mut session);
    let (sens::Value::Pair(tail_node), sens::Value::Pair(left_node), sens::Value::Pair(right_node)) =
        (&tail, &left, &right)
    else {
        panic!("test_id=5950-SHARED-CDR layer=SENS expected=three-PairNode-tails actual=({tail}, {left}, {right})");
    };

    assert!(
        Rc::ptr_eq(tail_node, left_node) && Rc::ptr_eq(tail_node, right_node),
        "test_id=5950-SHARED-CDR layer=mechanism expected=same-PairNode-allocation after SENS CDR"
    );

    for (id, source, expected) in [
        (
            "same-tail-atom",
            "(тотожне? (перше (решта ліва-гілка)) (перше (решта права-гілка)))",
            true,
        ),
        (
            "distinct-root-heads",
            "(тотожне? (перше ліва-гілка) (перше права-гілка))",
            false,
        ),
    ] {
        let actual = read(source, &mut session);
        assert_eq!(
            actual.as_predicate_bit(),
            Some(expected),
            "test_id=5950-SHARED-{id} layer=SENS input={source} expected=D1:{expected} actual={actual}"
        );
    }

    // Shared physical representation does not widen partial D3 EQ or CDR.
    for (id, source) in [
        ("eq-pairs", "(тотожне? ліва-гілка права-гілка)"),
        ("cdr-nil", "(решта (як-є ()))"),
    ] {
        let error = eval_program(source, &mut session).expect_err(
            "test_id=5950-SHARED-NEGATIVE expected=Type actual=success",
        );
        assert_eq!(
            error.kind,
            sens::ErrorKind::Type,
            "test_id=5950-SHARED-{id} layer=SENS input={source} expected=Type actual={error}"
        );
    }
}
