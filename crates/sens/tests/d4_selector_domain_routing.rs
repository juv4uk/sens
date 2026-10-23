//! Rust перевіряє лише механізм завантаження та виконання програми.
//! Закон селекторів і власний fail-closed самовердикт належать SENS Lisp.
use sens::{eval_program, load_core_library, Session};

#[test]
fn rust_runtime_executes_lisp_owned_d4_selector_witness() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("SENS core must load");

    let source = include_str!("../../../tests/semantic/d4-selector-domain-law.lisp");
    // Хибний закон у цьому Lisp сам переходить до недопустимого CAR NIL.
    // Rust не порівнює мовний результат із власною таблицею істинності.
    let _ = eval_program(source, &mut session)
        .expect("SENS runtime має виконати самоперевірний Lisp-свідок");
}
