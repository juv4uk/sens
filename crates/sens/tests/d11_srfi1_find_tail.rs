//! Rust володіє лише механізмом завантаження та виконання SENS.
//! Усі 20 позитивних і негативних семантичних законів FIND-TAIL — в Lisp.
use sens::{eval_program, load_core_library, Session};

#[test]
fn rust_mechanism_runs_lisp_owned_find_tail_laws() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("завантажити ядро SENS");
    eval_program(include_str!("../../../lib/d11-srfi1-find-tail.lisp"), &mut session)
        .expect("чинні DEFINE знайти-хвіст мають завантажитися");
    let verdict = eval_program(
        include_str!("../../../tests/semantic/d11-srfi1-find-tail-laws.lisp"),
        &mut session,
    )
    .expect("SENS перевіряє мовні закони")
    .value;
    assert_eq!(verdict.as_predicate_bit(), Some(true),
        "механізм повернув мовний D1-вердикт: {verdict}");
}
