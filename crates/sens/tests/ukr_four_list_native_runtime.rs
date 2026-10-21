//! Живі українські D3/D4 програми: виконання, а не підрахунок назв чи Python-oracle.
//! Обидва вихідні Lisp є власними композиціями ратифікованих CAR/CDR/CONS.
//! Позитив і адресна помилка мутації перевіряються в справжній SENS-сесії.
use sens::{eval_program, Session};

fn execute_with_negative(
    source_name: &str,
    source: &str,
    original: &str,
    changed: &str,
) {
    assert_eq!(
        source.matches(original).count(),
        1,
        "test_id=ukr-four-list layer=fixture source={source_name} expected=unique-mutation-site"
    );
    // D3/D4 та DEFINE/FUNCTION вже є в чинному SENS; повний історичний
    // Core4 не потрібен для цих самостійних виконуваних програм.
    let mut session = Session::default();
    let expected = eval_program("(атом? (як-є ()))", &mut session)
        .expect("native D1:так").value;
    let actual = eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!(
            "test_id=ukr-four-list layer=SENS source={source_name} case=positive error={error}"
        )).value;
    assert_eq!(
        actual, expected,
        "test_id=ukr-four-list layer=SENS source={source_name} case=positive expected=D1:так"
    );

    // Псуємо саме закон перестановки, не синтаксис, не доменні таблиці.
    // Негатив запускається іншою реальною SENS-сесією, не Rust-інтерпретатором.
    let mutant = source.replacen(original, changed, 1);
    let mut negative_session = Session::default();
    match eval_program(&mutant, &mut negative_session) {
        Ok(value) => assert_ne!(
            value.value, expected,
            "test_id=ukr-four-list layer=SENS source={source_name} case=mutant expected=non-true actual=D1:так"
        ),
        Err(_) => {} // Дозволене семантичне відхилення хибної гілки, а не PASS мутації.
    }
}

#[test]
fn replace_third_preserves_first_second_fourth_and_rejects_old_third() {
    execute_with_negative(
        "lib/замінити-третій-в-четвірці.lisp",
        include_str!("../../../lib/замінити-третій-в-четвірці.lisp"),
        "(сполучити новий (решта (решта (решта елементи))))",
        "(сполучити (як-є решта) (решта (решта (решта елементи))))",
    );
}

#[test]
fn swap_second_third_preserves_outer_positions_and_rejects_identity_swap() {
    execute_with_negative(
        "lib/поміняти-другий-і-третій.lisp",
        include_str!("../../../lib/поміняти-другий-і-третій.lisp"),
        "(перше (решта (решта четвірка)))",
        "(перше (решта четвірка))",
    );
}
