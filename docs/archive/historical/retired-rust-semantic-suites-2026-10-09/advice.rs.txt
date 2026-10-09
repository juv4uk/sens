//! End-to-end Advice Taker boundary: controlled words become validated
//! knowledge, inference proves an answer, and narration explains it.
//! Naskrizna mezha Advice Taker: kontrolovani slova staiut perevirenym
//! znanniam, inference dovodyt vidpovid, a narration poiasniuie yii.
//! Durchgängige Advice-Taker-Grenze: kontrollierte Wörter werden zu
//! geprüftem Wissen, Inferenz beweist eine Antwort und Narration erklärt sie.

use sens::{eval_program, Session};

fn eval_advice(source: &str) -> String {
    let mut session = Session::default();
    for library in [
        include_str!("../../../lib/core.lisp"),
        include_str!("../../../lib/unify.lisp"),
        include_str!("../../../lib/reason.lisp"),
        include_str!("../../../lib/forward.lisp"),
        include_str!("../../../lib/knowledge.lisp"),
        include_str!("../../../lib/understand.lisp"),
        include_str!("../../../lib/narrate.lisp"),
    ] {
        eval_program(library, &mut session).unwrap();
    }
    eval_program(source, &mut session)
        .unwrap()
        .value
        .to_string()
}

#[test]
fn controlled_words_flow_through_advice_reason_and_narration() {
    let source = r#"
        (advise astronomy (understand (quote (earth is a planet))))
        (advise astronomy (understand (quote (all planet have mass))))
        (def goal (quote (has earth mass)))
        (def proof (second (car (reason-in (quote astronomy) goal))))
        (narrate-answer goal proof)
    "#;
    assert_eq!(
        eval_advice(source),
        "(earth has mass because earth is a planet)"
    );
}

#[test]
fn rejected_translation_cannot_leak_into_the_knowledge_module() {
    let source = r#"
        (def result (advise astronomy (quote (planet earth))))
        (list (car result) (reason-in (quote astronomy) (quote (planet earth))))
    "#;
    assert_eq!(eval_advice(source), "(rejected Module-not-found)");
}
