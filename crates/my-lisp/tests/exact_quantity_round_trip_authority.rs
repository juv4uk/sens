//! #291 observer for Lisp-owned exact quantity product/quotient preservation.
//! Rust loads the quantity libraries and witness, then observes only the named
//! pass envelope. Expected quantity shapes and semantic relations stay in Lisp.

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

    let verdict = eval_program("(exact-quantity-round-trip-witness)", &mut session)
        .expect("exact quantity round-trip witness must execute")
        .value
        .to_string();

    assert!(
        verdict.starts_with("(exact-quantity-round-trip-witness (status pass)"),
        "Lisp-owned exact quantity witness rejected runtime semantics: {verdict}"
    );
}
