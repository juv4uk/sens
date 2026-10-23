//! Реальне виконання українських Lisp-програм, у яких ще немає
//! незалежно підтвердженої фізичної T5M-пари.
//! Ці тести не створюють .sens і не надають релізного допуску.
use sens::{eval_program, load_core_library, Session};

// Семантику рекурсивного обходу перенесено в українські Lisp-закони.
// Rust не визначає очікувані результати функції «обійти».
// Негативна семантика D4 NOT тепер у Lisp/SENS:
// tests/semantic/d4-not-nonpredicate-type-negative.lisp.
// Rust не видає самостійного мовного Type-вердикту.
// Мовний закон списку перенесено в tests/semantic/ukr-lists-d24-language-law.lisp.
// Rust тут перевіряє лише API/reader/transport, не значення Lisp-функцій.
// Перевірку полінома перенесено в українські Lisp-закон і мутант Д24.
// Семантику точних дробів, читача та D7 цитат перенесено в Lisp-закони.
// Rust тут не має друкувати очікуваний мовний результат.
// Rust перевіряє лише механізм приймання Lisp-джерела, не його результати.
// Чотири D24-мовні вердикти живуть у tests/semantic/d24-*-language-*.lisp.
#[test]
fn два_українські_рекурсивні_джерела_завантажуються_як_lisp() {
    let mut сеанс = Session::default();
    load_core_library(&mut сеанс).expect("Core4 bootstrap");
    for (назва, джерело) in [
        (
            "ackermann.setup.lisp",
            include_str!(concat!(env!("CARGO_MANIFEST_DIR"),
                "/../../benchmarks/cross-language/sens-vs-python/sens/ackermann.setup.lisp")),
        ),
        (
            "fib.setup.lisp",
            include_str!(concat!(env!("CARGO_MANIFEST_DIR"),
                "/../../benchmarks/cross-language/sens-vs-python/sens/fib.setup.lisp")),
        ),
    ] {
        eval_program(джерело, &mut сеанс).unwrap_or_else(|помилка|
            panic!("test_id=recursive-lisp-load layer=rust-api source={назва} actual={помилка}")
        );
    }
}
