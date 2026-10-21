//! Чинні D1/D3 перевірки української бібліотеки наукових констант.
//! Тестує справжній SENS; не закріплює старі англійські DEFINE, #d1 або SID8.
use sens::{eval_parsed_expressions, eval_program, load_core_library, parse, Session, Value};

const SOURCE: &str = include_str!("../../../lib/quantity.lisp");

fn admitted_source() -> &'static str {
    let from = SOURCE.find("(визначити науковий-константа-стан-чинний?")
        .expect("чинна українська функція стану");
    let to = SOURCE[from..].find("\n(визначити створити-науковий-константа")
        .map(|i| from + i).expect("наступна функція після двох предикатів");
    &SOURCE[from..to]
}

fn setup(source: &str) -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("чинний Core4 SENS");
    let parsed = parse(source).expect("українські DEFINE");
    assert_eq!(parsed.len(), 2, "два чинні SENS-предикати");
    eval_parsed_expressions(&parsed, &mut session).expect("SENS DEFINE працює");
    session
}

fn run(session: &mut Session, function: &str, data: &str) -> Value {
    let call = format!("({function} (як-є {data}))");
    eval_program(&call, session)
        .unwrap_or_else(|error| panic!("SENS test_id=quantity-D1 input={call} error={error}"))
        .value
}

#[test]
fn current_ukrainian_status_kind_truth_is_exact_d1_not_legacy_t() {
    let source = admitted_source();
    assert!(!source.contains("(так"), "голе T не є D1-предикатом SENS");
    assert!(!source.contains("#d1:"), "історичний тег не є канонічним законом");
    let mut session = setup(source);
    for (function, valid, invalid) in [
        (
            "науковий-константа-стан-чинний?",
            &["exact-by-definition", "measured"][..],
            &["unknown", "exact-derived", "physical-defining"][..],
        ),
        (
            "науковий-константа-вид-чинний?",
            &["physical-defining", "physical-derived"][..],
            &["unknown", "mathematical", "measured"][..],
        ),
    ] {
        for candidate in valid {
            let got = run(&mut session, function, candidate);
            assert_eq!(got.as_predicate_bit(), Some(true),
                "SENS D1:YES {function}/{candidate} actual={got}");
        }
        for candidate in invalid {
            let got = run(&mut session, function, candidate);
            assert!(matches!(got, Value::Nil),
                "відсутній допуск є D3 NIL, не вигаданий D1:NO: {function}/{candidate}: {got}");
            assert_eq!(got.as_predicate_bit(), None);
        }
    }
}

#[test]
fn mutated_status_law_changes_a_real_sens_result() {
    let source = admitted_source();
    let witness = "(тотожне? стан (як-є measured))";
    assert!(source.contains(witness), "чинний закон measured");
    let mutant = source.replacen(witness, "(тотожне? стан (як-є unknown))", 1);
    let mut real = setup(source);
    let mut altered = setup(&mutant);
    let name = "науковий-константа-стан-чинний?";
    assert_eq!(run(&mut real, name, "measured").as_predicate_bit(), Some(true));
    assert!(matches!(run(&mut altered, name, "measured"), Value::Nil));
    assert!(matches!(run(&mut real, name, "unknown"), Value::Nil));
    assert_eq!(run(&mut altered, name, "unknown").as_predicate_bit(), Some(true));
}

#[test]
fn d1_false_and_d3_nil_are_distinct_in_sens() {
    let mut session = setup(admitted_source());
    let no = eval_program("(хибне? (атом? (як-є ())))", &mut session)
        .expect("SENS computes exact D1 false").value;
    let absent = run(&mut session, "науковий-константа-вид-чинний?", "unknown");
    assert_eq!(no.as_predicate_bit(), Some(false));
    assert!(matches!(absent, Value::Nil));
    assert_eq!(absent.as_predicate_bit(), None);
}

#[test]
fn nil_returning_validators_use_d4_null_not_d4_not() {
    // У D4 NOT є лише домен D1, D3 NIL не допускається.
    // Невірний стан/вид повертає NIL згідно з реальною SENS-евалюацією.
    let mut session = setup(admitted_source());
    for (function, good) in [
        ("науковий-константа-стан-чинний?", "measured"),
        ("науковий-константа-вид-чинний?", "physical-derived"),
    ] {
        let admitted = format!("(порожній? ({function} (як-є {good})))");
        let unadmitted = format!("(порожній? ({function} (як-є unknown)))");
        let positive = eval_program(&admitted, &mut session)
            .expect("SENS D4 NULL для допущеного результату").value;
        let negative = eval_program(&unadmitted, &mut session)
            .expect("SENS D4 NULL для відсутнього результату").value;
        assert_eq!(positive.as_predicate_bit(), Some(false),
            "test_id=quantity-nil-good input={admitted} expected=D1:NO actual={positive}");
        assert_eq!(negative.as_predicate_bit(), Some(true),
            "test_id=quantity-nil-bad input={unadmitted} expected=D1:YES actual={negative}");

        let illegal = format!("(хибне? ({function} (як-є unknown)))");
        let error = eval_program(&illegal, &mut session)
            .expect_err("SENS D4 NOT не може прийняти структурне NIL");
        // Для похідного хибне? чинний SENS відмовляє на внутрішньому
        // D3 COND раніше, ніж буде досягнуто D4 NOT. Обидва шляхи
        // забороняють перетворення D3 NIL на D1 без явного закону.
        let message = error.to_string();
        assert!(
            message.contains("COND expects exact D1:1 / D1:0")
                || message.contains("NOT requires an exact D1 PredicateBit"),
            "test_id=quantity-not-nil input={illegal} expected=EXACT_D1_REQUIRED actual={error}"
        );
    }

    for guard in [
        "(порожній? (величина? (третє значення)))",
        "(порожній? (науковий-константа-стан-чинний? (четверте значення)))",
        "(порожній? (науковий-константа-вид-чинний? (п'ятий значення)))",
        "(порожній? (наука-джерело? (науковий-сьомий значення)))",
        "(порожній? (науковий-константа? константа))",
    ] {
        assert!(SOURCE.contains(guard),
            "виконувана бібліотека втратила потрібну перевірку D3 NIL: {guard}");
    }
}

#[test]
fn quantity_symbol_guard_executes_real_sens_and_rejects_non_symbols() {
    // Завантажуємо рівно чинне Lisp-визначення, а не Python-емуляцію D9.
    let start = SOURCE.find("(визначити науковий-внутрішній-символ?")
        .expect("потрібен виконуваний D1-закон символу");
    let end = SOURCE[start..].find("\n(визначити науковий-список-правильний?")
        .map(|i| start + i).expect("завершення D1-закону");
    let current = &SOURCE[start..end];
    let key = "(тотожне? значення (текст-у-символ (значення-у-текст значення)))";
    assert!(current.contains(key), "закон має точно відрізняти символ від інших атомів");
    for name in ["(символ? (друге значення))",
                 "(символ? (науковий-шостий значення))"] {
        assert!(!SOURCE.contains(name), "старий невиконуваний D9 виклик: {name}");
    }

    let launch = |source: &str| {
        let mut session = Session::default();
        load_core_library(&mut session).expect("живий SENS Core");
        eval_parsed_expressions(&parse(source).expect("чинний Lisp"), &mut session)
            .expect("справжнє SENS DEFINE");
        session
    };
    let mut real = launch(current);
    let mutant = current.replacen(key, "(атом? значення)", 1);
    assert_ne!(mutant, current);
    let mut altered = launch(&mutant);

    for (case, expression, expected) in [
        ("uk-symbol", "(науковий-внутрішній-символ? (як-є метр))", true),
        ("protocol-symbol", "(науковий-внутрішній-символ? (як-є dimension/1))", true),
        ("nil", "(науковий-внутрішній-символ? (як-є ()))", false),
        ("pair", "(науковий-внутрішній-символ? (як-є (метр)))", false),
        ("d1-value", "(науковий-внутрішній-символ? (атом? (як-є ())))", false),
    ] {
        let actual = eval_program(expression, &mut real)
            .unwrap_or_else(|err| panic!("test_id=quantity-symbol case={case} input={expression} error={err}")).value;
        assert_eq!(actual.as_predicate_bit(), Some(expected),
            "test_id=quantity-symbol layer=real-SENS case={case} input={expression} expected=D1:{expected} actual={actual}");
    }
    let probe = "(науковий-внутрішній-символ? (атом? (як-є ())))";
    let broken = eval_program(probe, &mut altered)
        .expect("старе ATOM-only правило має дати неправильну відповідь").value;
    assert_eq!(broken.as_predicate_bit(), Some(true),
        "test_id=quantity-symbol-mutant expected=D1:YES actual={broken}");
}
