//! Rust лише завантажує код і запускає SENS-обчислювач.
//! 19 позитивних і 1 негативний мовні закони SRFI-1 описані тільки в .lisp.
use sens::{eval_program, load_core_library, Session};

#[test]
fn rust_runtime_executes_lisp_owned_srfi1_span_break() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("механізм ініціалізації SENS");
    eval_program(include_str!("../../../lib/d11-srfi1-span-break.lisp"), &mut session)
        .expect("завантаження чинних бібліотечних DEFINE");
    let verdict = eval_program(
        include_str!("../../../tests/semantic/d11-srfi1-span-break-laws.lisp"),
        &mut session,
    )
    .expect("SENS сам перевіряє закони SPAN/BREAK")
    .value;
    assert_eq!(
        verdict.as_predicate_bit(),
        Some(true),
        "отримати кінцевий однобітний вердикт програми SENS: {verdict}",
    );
}
