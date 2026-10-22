//! D11 00000111011: порівняти-два-значення-мета.
//! Справжній SENS виконує наявну бібліотечну композицію з lib/meta-eval.lisp.
//! Дослідна адреса не означає нового D11-примітива або прямого машинного opcode.

use sens::{eval_program, load_core_library, load_meta_evaluator_library, Session};

#[test]
fn d11_мета_порівняння_має_точні_d1_результати() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("завантажити чинне ядро SENS");
    load_meta_evaluator_library(&mut session)
        .expect("завантажити чинні SENS-визначення MetaEval");

    // Очікування задані незалежно; Rust лише перевіряє D1-відповіді
    // викликів, які справді виконує SENS, а не імітує семантику.
    for (id, source, expected) in [
        ("менше-пряме", "(порівняти-два-значення-мета (як-є менше?) 1 2)", true),
        ("менше-зворотне", "(порівняти-два-значення-мета (як-є менше?) 2 1)", false),
        ("менше-рівні", "(порівняти-два-значення-мета (як-є менше?) 2 2)", false),
        ("більше-пряме", "(порівняти-два-значення-мета (як-є більше?) 2 1)", true),
        ("більше-зворотне", "(порівняти-два-значення-мета (як-є більше?) 1 2)", false),
        ("більше-рівні", "(порівняти-два-значення-мета (як-є більше?) 2 2)", false),
        ("однакові-рівні", "(порівняти-два-значення-мета (як-є однакові?) 2 2)", true),
        ("однакові-різні", "(порівняти-два-значення-мета (як-є однакові?) 2 3)", false),
        ("однакові-зворотне", "(порівняти-два-значення-мета (як-є однакові?) 3 2)", false),
        ("невідомий-оператор", "(порівняти-два-значення-мета (як-є невідомий-оператор) 2 2)", false),
    ] {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|error| {
                panic!("test_id=D11-META-COMPARE-{id} layer=SENS input={source} error={error}")
            })
            .value;
        assert_eq!(
            actual.as_predicate_bit(),
            Some(expected),
            "test_id=D11-META-COMPARE-{id} layer=SENS input={source} expected=D1:{expected} actual={actual}"
        );
    }
}
