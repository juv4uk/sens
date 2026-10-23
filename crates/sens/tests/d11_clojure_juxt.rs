//! Rust перевіряє тільки механізм завантаження й виконання SENS.
//! Усі двадцять чотири позитивні й негативні закони juxt визначено в Lisp.
//! Жодної таблиці очікувань, логіки EQ або симулятора замикань у Rust немає.
use sens::{eval_program, load_core_library, Session};

#[test]
fn rust_executor_runs_language_owned_d11_juxt_laws() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("реальне ядро SENS має завантажитись");
    eval_program(include_str!("../../../lib/d11-clojure-juxt.lisp"), &mut session)
        .expect("механізм завантаження чинних Lisp-визначень D11");

    let verdict = eval_program(
        include_str!("../../../tests/semantic/d11-clojure-juxt-laws.lisp"),
        &mut session,
    )
    .expect("SENS сам відхиляє порушений мовний закон")
    .value;
    assert_eq!(
        verdict.as_predicate_bit(),
        Some(true),
        "виконавець має повернути завершальний точний D1-вердикт Lisp: {verdict}",
    );
}
