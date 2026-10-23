//! Rust перевіряє reader/lowering та запускає Lisp-свідок; не дублює таблицю істинності.

use sens::{
    eval_parsed_expressions, load_core_library, lower_program, parse, parse_mixed_exact_domain,
    Session,
};

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

fn evaluate_ukr(
    source: &str,
    session: &mut Session,
) -> Result<sens::EvalResult, sens::LanguageError> {
    // Змішаний читач і lowering — механізм Rust; вердикт мовних законів лишається Lisp.
    let parsed = parse_mixed_exact_domain(source)?;
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
fn бібліотечні_голови_лишаються_українською_проєкцією() {
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

    // Лише reader/lowering contract. Жодної Rust-таблиці очікувань для D1.
    let parsed = parse("(тотожне? (атом? (як-є ())) (хибне? (атом? (як-є ()))))")
        .expect("українська проєкція D1–D4 читається");
    assert_eq!(parsed.len(), 1);
    assert_eq!(lower_program(&parsed).len(), parsed.len());
}

#[test]
fn український_епістемічний_свідок_сам_виносить_вердикт() {
    let source = include_str!("../../../tests/fixtures/epistemic-authority-witness.lisp");
    let parsed = parse(source).expect("український Lisp-свідок розбирається");
    assert_eq!(parsed.len(), 3, "свідок має три визначення");

    let mut session = epistemic_session();
    evaluate_ukr(source, &mut session).expect("визначення Lisp-свідка завантажуються");
    let verdict = evaluate_ukr("(свідок-епістеміки)", &mut session)
        .expect("Lisp-свідок сам перевіряє епістемічні закони");
    assert_eq!(
        verdict.value.to_string(),
        "(epistemic-authority-witness (status pass))",
        "тестовий Rust-адаптер лише спостерігає іменований Lisp-вердикт",
    );
}

#[test]
fn файл_законів_посилань_читається_й_понижується() {
    let source = include_str!("../../../tests/semantic/epistemic-source-ref-d1-law.lisp");
    let parsed = parse(source).expect("українські закони розбираються");
    assert_eq!(parsed.len(), 6, "файл містить шість Lisp-форм");
    let lowered = lower_program(&parsed);
    assert_eq!(lowered.len(), parsed.len(), "кожна форма має механічне lowering-подання");
}
