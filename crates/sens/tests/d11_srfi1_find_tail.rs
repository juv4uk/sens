//! Rust володіє лише механізмом завантаження та виконання SENS.
//! Усі семантичні твердження FIND-TAIL, зокрема перенесені бібліотечні перевірки, — в Lisp.
use sens::{eval_program, load_core_library, Session};

#[test]
fn rust_mechanism_runs_lisp_owned_find_tail_laws() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("завантажити ядро SENS");
    eval_program(include_str!("../../../lib/d11-srfi1-find-tail.lisp"), &mut session)
        .expect("чинні DEFINE знайти-хвіст мають завантажитися");
    // Порушення кожного Lisp-закону потрапляє в недопущений CAR порожнього
    // списку. Rust тут доводить лише, що механізм виконав увесь свідок.
    // Кінцевий D1-вердикт визначає мова, не хостовий тест.
    eval_program(
        include_str!("../../../tests/semantic/d11-srfi1-find-tail-laws.lisp"),
        &mut session,
    )
    .expect("SENS перевіряє мовні закони й відхиляє хибні тези");
}
