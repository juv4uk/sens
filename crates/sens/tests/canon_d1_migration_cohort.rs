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
    // Чинний answer-contract (#3161): D3 EQ поза доменом дає
    // структурне () / no-witness, НЕ host-помилку і НЕ D1:0.
    let value = eval_program(invalid, &mut session)
        .expect("SENS EQ поза атомним доменом повертає no-witness")
        .value;
    assert!(
        matches!(value, sens::Value::Nil),
        "test_id=1968-EQ-PAIR layer=SENS expected=D3:000-no-witness actual={value}"
    );
    assert_eq!(
        value.as_predicate_bit(),
        None,
        "test_id=1968-EQ-PAIR layer=SENS expected=non-predicate-not-D1:NO actual={value}"
    );
}

/// #1968/#2015: COND is control with an exact D1 selection rule.
/// Exhaustion produces structural NIL, which is not predicate NO. An empty
/// witness in a condition must continue, not become a made-up YES/NO bit.
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

    let no_witness = "(тотожне? (за-умовою ((як-є ()) (як-є не-має-виконатися)) (так (як-є правильно))) (як-є правильно))";
    let value = eval_program(no_witness, &mut session)
        .unwrap_or_else(|error| panic!(
            "test_id=1968-COND-EMPTY-WITNESS layer=SENS input={no_witness} actual_error={error}"
        ))
        .value;
    assert_eq!(
        value.as_predicate_bit(), Some(true),
        "test_id=1968-COND-EMPTY-WITNESS layer=SENS expected=D1:true actual={value}"
    );

    // Позаобласний EQ має породжувати D3:000; COND продовжує далі.
    // Це наскрізний SENS-закон двох сучасних Д3-механізмів, не host-oracle.
    let composed = "(тотожне? (за-умовою ((тотожне? (сполучити (як-є ліве) (як-є ())) (як-є ліве)) (як-є хибна-гілка)) (так (як-є правильна-гілка))) (як-є правильна-гілка))";
    let answer = eval_program(composed, &mut session)
        .unwrap_or_else(|error| panic!(
            "test_id=1968-EQ-COND-COMPOSITION layer=SENS input={composed} actual_error={error}"
        ))
        .value;
    assert_eq!(
        answer.as_predicate_bit(), Some(true),
        "test_id=1968-EQ-COND-COMPOSITION layer=SENS expected=D1:true actual={answer}"
    );
}
