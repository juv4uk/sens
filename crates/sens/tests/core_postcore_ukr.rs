//! Живе виконання виправлених post-core функцій через справжній SENS evaluator.
//! Не підмінює семантику Rust або Python; Rust лише викликає SENS та звіряє результат.
use sens::{eval_program, Session};

fn core_session() -> Session {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session)
    .expect("чинний core має завантажуватися реальним SENS reader/evaluator");
    session
}

fn execute(session: &mut Session, source: &str) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("SENS відхилив {source}: {error}"))
        .value
        .to_string()
}

#[test]
fn core_peer_lookup_returns_first_matching_group_or_empty() {
    let mut session = core_session();
    assert_eq!(
        execute(&mut session,
            "(my-postcore-peer-group (як-є другий) (як-є ((перший альфа) (другий бета))))"),
        "(другий бета)"
    );
    assert_eq!(
        execute(&mut session,
            "(my-postcore-peer-group (як-є невідомий) (як-є ((перший альфа) (другий бета))))"),
        "()"
    );
}

#[test]
fn core_peer_binding_presence_and_absence_are_observable() {
    let mut session = core_session();
    let bindings = "(як-є ((\"перший\" альфа) (\"другий\" бета)))";
    assert_eq!(
        execute(&mut session,
            &format!("(my-postcore-binding-status (як-є другий) {bindings})")),
        "present"
    );
    assert_eq!(
        execute(&mut session,
            &format!("(my-postcore-binding-status (як-є третій) {bindings})")),
        "absent"
    );
}

#[test]
fn core_missing_peers_skip_existing_and_retain_source_order() {
    let mut session = core_session();
    assert_eq!(
        execute(&mut session,
            "(my-postcore-missing-peers (як-є джерело) (як-є (джерело перший другий третій)) (як-є ((\"перший\" привязка))))"),
        "(другий третій)"
    );
}

#[test]
fn core_constructs_only_ukrainian_d4_define_expressions() {
    let mut session = core_session();
    assert_eq!(
        execute(&mut session,
            "(my-postcore-build-definitions (як-є джерело) (як-є (перший другий)))"),
        "(визначити перший (визначити другий джерело))"
    );
}

// Справжній evaluator читає увесь core, а не окремі скопійовані форми.
#[test]
fn core_nth_member_follow_current_d6_d5_semantics() {
    let mut session = core_session();
    assert_eq!(
        execute(&mut session, "(елемент-списку-за-індексом 1 (як-є (а б)))"),
        execute(&mut session, "(як-є б)")
    );
    assert_eq!(
        execute(&mut session, "(елемент-списку-за-індексом 2 (як-є (а б)))"),
        execute(&mut session, "(як-є ())")
    );
    assert_eq!(
        execute(&mut session, "(значення-у-списку? (як-є б) (як-є (а б)))"),
        execute(&mut session, "так")
    );
    assert_eq!(
        execute(&mut session, "(значення-у-списку? (як-є в) (як-є (а б)))"),
        execute(&mut session, "ні")
    );
}

#[test]
fn core_sublis_and_maplist_execute_in_sens_without_host_oracle() {
    let mut session = core_session();
    assert_eq!(
        execute(&mut session,
            "(підставити-пари (список (сполучити (як-є а) (як-є б))) (як-є (а в а)))"),
        execute(&mut session, "(як-є (б в б))")
    );
    assert_eq!(
        execute(&mut session,
            "(підставити-пари (список (сполучити (як-є (а в)) (як-є ціле))) (як-є (а в)))"),
        execute(&mut session, "(як-є ціле)")
    );
    assert_eq!(
        execute(&mut session,
            "(відобразити-залишки (як-є (а б)) (функція (хвіст) (перше хвіст)))"),
        execute(&mut session, "(як-є (а б))")
    );
}
