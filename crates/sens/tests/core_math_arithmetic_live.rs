//! Rust перевіряє механізм завантаження та класифікацію помилок виконання.
//! Арифметичні рівності й самовердикт належать Lisp у tests/semantic.
use sens::{eval_program, load_core_library, Session};

fn core_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("SENS core must load");
    session
}

#[test]
fn exact_arithmetic_laws_are_judged_by_lisp() {
    let source = include_str!("../../../tests/semantic/exact-arithmetic-laws.lisp");
    // Lisp має власні негативні гілки з недопустимим CAR порожнього списку.
    // Тут Rust перевіряє лише, що його механізм виконав програму без помилки.
    let _ = eval_program(source, &mut core_session())
        .expect("SENS runtime має виконати арифметичний Lisp-свідок");
}

