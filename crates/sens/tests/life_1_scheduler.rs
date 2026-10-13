//! Тільки механічний провідник: усі позитивні й негативні закони — у SENS.
//! ЖОДНИХ semantic expected cases або host-generated форм тут немає.

use sens::{eval_program, load_core_library, Session};

#[test]
fn виконати_двійковий_свідок_life_1() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("транспорт: завантажити SENS Core");

    let scheduler = include_str!("../../../lib/life-1-scheduler.lisp");
    eval_program(scheduler, &mut session).expect("транспорт: завантажити LIFE-1");

    // Єдиний оракул семантики: сама двійкова SENS-програма.
    let witness = include_str!("../../../tests/fixtures/life-1-exact-d3-semantic.lisp");
    let result = eval_program(witness, &mut session)
        .expect("транспорт: виконати SENS-свідок");

    // Це тільки спостереження вердикту D1:1, не перевірка логіки в Rust.
    assert_eq!(result.value.to_string(), "1", "SENS повернув не D1:YES");
}
