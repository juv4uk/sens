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
