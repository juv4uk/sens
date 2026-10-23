//! Реальне виконання українських Lisp-програм, у яких ще немає
//! незалежно підтвердженої фізичної T5M-пари.
//! Ці тести не створюють .sens і не надають релізного допуску.
use sens::{eval_program, load_core_library, Session};

fn запустити_джерело(джерело: &str, сеанс: &mut Session) -> String {
    eval_program(джерело, сеанс)
        .unwrap_or_else(|помилка| panic!("SENS runtime відхилив програму: {помилка}"))
        .value
        .to_string()
}

// Семантику рекурсивного обходу перенесено в українські Lisp-закони.
// Rust не визначає очікувані результати функції «обійти».
// Негативна семантика D4 NOT тепер у Lisp/SENS:
// tests/semantic/d4-not-nonpredicate-type-negative.lisp.
// Rust не видає самостійного мовного Type-вердикту.
// Мовний закон списку перенесено в tests/semantic/ukr-lists-d24-language-law.lisp.
// Rust тут перевіряє лише API/reader/transport, не значення Lisp-функцій.
// Перевірку полінома перенесено в українські Lisp-закон і мутант Д24.
#[test]
fn український_читач_виконує_цитовані_дані_й_точний_d24_дріб() {
    // Непарний benchmarks/parser.lisp виконується реальним SENS;
    // це ще не доказ фізичного T5M roundtrip.
    let mut сеанс = Session::default();
    load_core_library(&mut сеанс).expect("чинний SENS Core4");
    let програма = include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../benchmarks/parser.lisp"
    ));
    assert_eq!(
        запустити_джерело(програма, &mut сеанс),
        "5/336",
        "SENS має обчислити вкладені D24+ частки, а не друкувати літерал"
    );
    assert_eq!(
        запустити_джерело(
            "(повернути-значення (як-є (українська абетка ґрунт їжак)))",
            &mut сеанс,
        ),
        "(українська абетка ґрунт їжак)",
        "цитовані D7 імена мають залишатися точними"
    );
    assert!(
        eval_program("(повернути-значення (частка 5 0))", &mut сеанс).is_err(),
        "test_id=parser-fraction-zero layer=eval expected=division-by-zero"
    );
}

#[test]
fn незалежне_виконання_аккермана_та_фібоначчі_у_sens() {
    // В обліку корпусу обидва джерела наразі без фізичних .sens.
    // Доведено лише виконання самих Lisp-програм через SENS; ні Zig/T5M,
    // ні оберненість від цих тверджень не стають автоматично PASS.
    let mut сеанс = Session::default();
    load_core_library(&mut сеанс).expect("чинний Core4 SENS");
    let аккерман = include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../benchmarks/cross-language/sens-vs-python/sens/ackermann.setup.lisp"
    ));
    let аккерман_виклик = include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../benchmarks/cross-language/sens-vs-python/sens/ackermann.call.lisp"
    ));
    eval_program(аккерман, &mut сеанс)
        .expect("визначення Аккермана — справжня виконувана D4 форма SENS");
    assert_eq!(
        запустити_джерело("(аккерман 0 3)", &mut сеанс),
        "4",
        "перший базовий випадок D24+"
    );
    assert_eq!(
        запустити_джерело("(аккерман 1 2)", &mut сеанс),
        "4",
        "другий базовий випадок D24+"
    );
    assert_eq!(
        запустити_джерело(аккерман_виклик, &mut сеанс),
        "61",
        "вкладена рекурсія не замінена Python або host-оракулом"
    );

    let фібоначчі = include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../benchmarks/cross-language/sens-vs-python/sens/fib.setup.lisp"
    ));
    let фібоначчі_виклик = include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../benchmarks/cross-language/sens-vs-python/sens/fib.call.lisp"
    ));
    eval_program(фібоначчі, &mut сеанс)
        .expect("визначення Фібоначчі — справжня виконувана D4 форма SENS");
    for (вхід, вихід) in [
        ("(фібоначчі 0)", "0"),
        ("(фібоначчі 1)", "1"),
        ("(фібоначчі 2)", "1"),
        (фібоначчі_виклик, "987"),
    ] {
        assert_eq!(
            запустити_джерело(вхід, &mut сеанс),
            вихід,
            "test_id=unpaired-fib-d24 layer=real-sens input={вхід} expected={вихід}"
        );
    }
}
