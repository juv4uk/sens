//! Виконуваний SENS-свідок української Lisp-проєкції епістемічних законів.

use sens::{eval_parsed_expressions, load_core_library, lower_program, parse, Session};

const SOURCES: &[&str] = &[
    include_str!("../../../lib/unify.lisp"),
    include_str!("../../../lib/reason.lisp"),
    include_str!("../../../lib/forward.lisp"),
    include_str!("../../../lib/knowledge.lisp"),
    include_str!("../../../lib/persistent-map.lisp"),
    include_str!("../../../lib/persistent-vector.lisp"),
    include_str!("../../../lib/time.lisp"),
    include_str!("../../../lib/epistemic.lisp"),
];

fn evaluate_ukr(source: &str, session: &mut Session) -> Result<sens::EvalResult, sens::LanguageError> {
    let parsed = parse(source)?;
    let projected = lower_program(&parsed);
    eval_parsed_expressions(&projected, session)
}

fn epistemic_session() -> Session {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("ядро SENS завантажується");
    for source in SOURCES {
        evaluate_ukr(source, &mut session).expect("бібліотечне джерело завантажується");
    }
    session
}

#[test]
fn бібліотечні_голови_не_повертаються_до_історичних_англійських_імен() {
    let source = include_str!("../../../lib/epistemic.lisp");
    for obsolete in [
        "(визначити source-ref?",
        "(визначити supporting-evidence",
        "(визначити claim-statement",
        "(визначити evidence-outcome",
        "(визначити intent-capabilities-satisfied?",
    ] {
        assert!(!source.contains(obsolete), "застаріла голова: {obsolete}");
    }

    let parsed = parse("(тотожне? (атом? (як-є ())) (хибне? (атом? (як-є ()))))")
        .expect("українська проєкція D1–D4 читається");
    let projected = lower_program(&parsed);
    let result = eval_parsed_expressions(&projected, &mut epistemic_session())
        .expect("предикатні операції повертають точний D1");
    assert_eq!(result.value.as_predicate_bit(), Some(false));
}

#[test]
fn український_свідок_епістеміки_розбирається_як_lisp() {
    let source = include_str!("../../../tests/fixtures/epistemic-authority-witness.lisp");
    let parsed = parse(source).expect("український Lisp-свідок розбирається");
    assert_eq!(parsed.len(), 3, "свідок зберігає три визначення");
}

#[test]
fn посилання_на_джерело_повертає_точні_значення_d1() {
    let mut session = epistemic_session();
    for (source, expected) in [
        ("(це-належне-посилання-на-джерело? (як-є (digest packet)))", true),
        ("(це-належне-посилання-на-джерело? (як-є (proof packet)))", true),
        ("(це-належне-посилання-на-джерело? (як-є (unknown packet)))", false),
        ("(це-належне-посилання-на-джерело? (як-є ((digest) packet)))", false),
        ("(це-належне-посилання-на-джерело? (як-є ()))", false),
        ("(це-належне-посилання-на-джерело? (як-є (digest packet extra)))", false),
    ] {
        let result = evaluate_ukr(source, &mut session)
            .unwrap_or_else(|error| panic!("{source}: {error}"));
        assert_eq!(result.value.as_predicate_bit(), Some(expected), "{source}");
    }

    for (source, expected) in [
        ("(епістеміка--посилання-на-твердження? (як-є (claim-ref packet)))", true),
        ("(епістеміка--посилання-на-твердження? (як-є (other-ref packet)))", false),
        ("(епістеміка--посилання-на-твердження? (як-є (claim-ref packet extra)))", false),
        ("(епістеміка--посилання-на-твердження? (як-є (claim-ref)))", false),
    ] {
        let result = evaluate_ukr(source, &mut session)
            .unwrap_or_else(|error| panic!("{source}: {error}"));
        assert_eq!(result.value.as_predicate_bit(), Some(expected), "{source}");
    }
}

#[test]
fn український_файл_законів_посилання_повертає_точний_d1() {
    let mut session = epistemic_session();
    let source = include_str!("../../../tests/semantic/epistemic-source-ref-d1-law.lisp");
    let parsed = parse(source).expect("українські закони розбираються");
    assert_eq!(parsed.len(), 6, "файл містить п'ять законів і відмовний випадок");

    for (index, form) in parsed.iter().enumerate() {
        let projected = lower_program(std::slice::from_ref(form));
        let result = eval_parsed_expressions(&projected, &mut session)
            .unwrap_or_else(|error| panic!("закон посилання {index}: {error}"));
        assert_eq!(result.value.as_predicate_bit(), Some(true), "закон {index}");
    }
}

#[test]
fn неправильний_хвіст_вимог_не_створює_хибної_істини() {
    // Справжній SENS обчислює D1, не Python-симуляція.
    // Пошкоджені атомні та крапкові хвости не дорівнюють порожньому списку.
    let mut session = epistemic_session();
    for (source, expected) in [
        ("(епістеміка--усі-вимоги-наявні? (як-є ()) (як-є ()))", true),
        ("(епістеміка--усі-вимоги-наявні? (як-є (читання)) (як-є (читання)))", true),
        ("(епістеміка--усі-вимоги-наявні? (як-є (читання)) (як-є (запис)))", false),
        ("(епістеміка--усі-вимоги-наявні? (як-є хибний-хвіст) (як-є (читання)))", false),
        ("(епістеміка--усі-вимоги-наявні? (як-є (читання . хибний-хвіст)) (як-є (читання)))", false),
    ] {
        let result = evaluate_ukr(source, &mut session)
            .unwrap_or_else(|error| panic!("{source}: {error}"));
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(expected),
            "повинно бути точне D1, джерело: {source}",
        );
    }
}

#[test]
fn рівність_вкладених_посилань_розрізняє_форму_та_значення() {
    let mut session = epistemic_session();
    for (source, expected) in [
        ("(епістеміка--рівні-посилання? (як-є (а (б в))) (як-є (а (б в))))", true),
        ("(епістеміка--рівні-посилання? (як-є (а (б в))) (як-є (а (б г))))", false),
        ("(епістеміка--рівні-посилання? (як-є (а (б))) (як-є (а б)))", false),
        ("(епістеміка--рівні-посилання? (як-є ()) (як-є ()))", true),
    ] {
        let result = evaluate_ukr(source, &mut session)
            .unwrap_or_else(|error| panic!("{source}: {error}"));
        assert_eq!(result.value.as_predicate_bit(), Some(expected), "{source}");
    }
}
