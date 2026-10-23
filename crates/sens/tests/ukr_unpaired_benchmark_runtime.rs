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

#[test]
fn рекурсія_не_приймає_непорожній_атом_за_завершений_список() {
    let mut сеанс = Session::default();
    load_core_library(&mut сеанс).expect("завантаження ратифікованого ядра SENS");
    let програма = include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../benchmarks/recursion.lisp"
    ));
    assert_eq!(
        запустити_джерело(програма, &mut сеанс),
        "завершено",
        "повний список повинен завершитися точно"
    );
    assert_eq!(
        запустити_джерело("(обійти (як-є пошкоджений-хвіст))", &mut сеанс),
        "помилка-не-список",
        "непорожній атом не може повертати той самий успіх"
    );
    assert_eq!(
        запустити_джерело("(обійти (як-є ()))", &mut сеанс),
        "завершено",
        "порожній список — єдина базова умова"
    );
}

#[test]
fn заперечення_повертає_точний_d1_без_невизначених_так_ні() {
    let mut сеанс = Session::default();
    load_core_library(&mut сеанс).expect("ядро повинно завантажитися");
    for (вираз, очікуване) in [
        ("(хибне? (атом? (як-є ())))", false),
        ("(хибне? (атом? (сполучити (як-є ()) (як-є ()))))", true),
    ] {
        let результат = eval_program(вираз, &mut сеанс)
            .unwrap_or_else(|помилка| panic!("test_id=d1-not source={вираз} actual={помилка}"));
        assert_eq!(
            результат.value.as_predicate_bit(),
            Some(очікуване),
            "test_id=d1-not source={вираз} expected={очікуване}"
        );
    }
    assert!(
        eval_program("(хибне? (як-є ()))", &mut сеанс).is_err(),
        "test_id=d1-not-type expected=fail-closed for structural nil"
    );
}

#[test]
fn довжина_списку_відкидає_пошкоджений_хвіст_і_зберігає_d24_нуль() {
    let mut сеанс = Session::default();
    load_core_library(&mut сеанс).expect("завантаження ядра SENS");
    let програма = include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../benchmarks/lists.lisp"
    ));
    assert_eq!(
        запустити_джерело(програма, &mut сеанс),
        "10",
        "дійсний список із десяти символів має довжину десять"
    );
    assert_eq!(
        запустити_джерело("(порахувати-елементи (як-є ()))", &mut сеанс),
        "0",
        "D3 NIL дає числовий D24+ нуль"
    );
    assert_eq!(
        запустити_джерело(
            "(порахувати-елементи (як-є пошкоджений-хвіст))",
            &mut сеанс
        ),
        "помилка-не-список",
        "непорожній атом не є завершенням списку"
    );
    assert_eq!(
        запустити_джерело(
            "(порахувати-елементи (як-є (радіо антена)))",
            &mut сеанс
        ),
        "2",
        "рекурсія повинна виконати дійсний SENS D24+ ADD"
    );
    assert!(
        eval_program("(порахувати-елементи (як-є (радіо . антена)))", &mut сеанс).is_err(),
        "неправильний хвіст не може дати успішний числовий результат"
    );
}

#[test]
fn арифметика_та_бенчмарки_без_числових_токенів_виконуються_в_sens() {
    // Цей контракт стосується лише живої вихідної проєкції, не коментарів.
    let програми = [
        ("списки", include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/../../benchmarks/lists.lisp"))),
        ("арифметика", include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/../../benchmarks/arithmetic.lisp"))),
        ("читач", include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/../../benchmarks/parser.lisp"))),
    ];
    for (назва, джерело) in програми {
        for (індекс, рядок) in джерело.lines().enumerate() {
            let код = рядок.split(';').next().unwrap_or("");
            for токен in код.split(|знак: char| знак.is_whitespace() || знак == '(' || знак == ')') {
                if токен.is_empty() {
                    continue;
                }
                assert!(
                    !токен.chars().all(|знак| знак.is_ascii_digit())
                        && !токен.starts_with("#d")
                        && !токен.starts_with("#b")
                        && !токен.starts_with("#q2"),
                    "test_id=ukr-no-numeric-token файл={назва} рядок={} токен={токен}",
                    індекс + 1
                );
            }
        }
    }

    let mut сеанс = Session::default();
    load_core_library(&mut сеанс).expect("завантаження ядра SENS");
    let арифметика = include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../benchmarks/arithmetic.lisp"
    ));
    assert_eq!(запустити_джерело(арифметика, &mut сеанс), "15505");
    assert_eq!(
        запустити_джерело("(поліном (довжина (як-є ())))", &mut сеанс),
        "7",
        "нульовий аргумент не потребує цифрового літерала"
    );
}

#[test]
fn замикання_зберігає_обидва_лексичні_зв_язування() {
    let mut сеанс = Session::default();
    load_core_library(&mut сеанс).expect("завантаження ядра SENS");
    let програма = include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../benchmarks/closures.lisp"
    ));
    assert_eq!(запустити_джерело(програма, &mut сеанс), "(радіо антена)");
    assert_eq!(
        запустити_джерело(
            "((створити-пару (як-є радіо)) (як-є сигнал))",
            &mut сеанс
        ),
        "(радіо сигнал)",
        "зміна внутрішнього аргумента не змінює захоплений зовнішній"
    );
}

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
