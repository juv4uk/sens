//! Спостерігач #291 точної арифметики величин, що належить Lisp.
//! Rust завантажує мовні бібліотеки й викликає українську назву свідка.
//! Формат відповіді зберігається; математичне значення визначає Lisp.

use my_lisp::{eval_program, Session};

#[test]
fn exact_quantity_product_quotient_round_trip_is_lisp_owned() {
    let mut session = Session::default();
    for library in [
        include_str!("../../../lib/core.lisp"),
        include_str!("../../../lib/quantity.lisp"),
        include_str!("../../../lib/si.lisp"),
        include_str!("../../../tests/fixtures/exact-quantity-round-trip-witness.lisp"),
    ] {
        eval_program(library, &mut session).expect("exact quantity witness dependency must load");
    }

    let verdict = eval_program("(свідок-кругового-обчислення-точних-величин)", &mut session)
        .expect("exact quantity round-trip witness must execute")
        .value
        .to_string();

    assert!(
        verdict.starts_with("(exact-quantity-round-trip-witness (status pass)"),
        "Lisp-owned exact quantity witness rejected runtime semantics: {verdict}"
    );
}
