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
    let програма = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/../../benchmarks/recursion.lisp"));
    assert_eq!(запустити_джерело(програма, &mut сеанс), "завершено",
               "повний список повинен завершитися точно");
    assert_eq!(запустити_джерело("(обійти (як-є пошкоджений-хвіст))", &mut сеанс),
               "помилка-не-список",
               "непорожній атом не може повертати той самий успіх");
    assert_eq!(запустити_джерело("(обійти (як-є ()))", &mut сеанс),
               "завершено", "порожній список — єдина базова умова");
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
        assert_eq!(результат.value.as_predicate_bit(), Some(очікуване),
                   "test_id=d1-not source={вираз} expected={очікуване}");
    }
    assert!(eval_program("(хибне? (як-є ()))", &mut сеанс).is_err(),
            "test_id=d1-not-type expected=fail-closed for structural nil");
}

#[test]
fn замикання_зберігає_обидва_лексичні_зв_язування() {
    let mut сеанс = Session::default();
    load_core_library(&mut сеанс).expect("завантаження ядра SENS");
    let програма = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/../../benchmarks/closures.lisp"));
    assert_eq!(запустити_джерело(програма, &mut сеанс), "(радіо антена)");
    assert_eq!(
        запустити_джерело("((створити-пару (як-є радіо)) (як-є сигнал))", &mut сеанс),
        "(радіо сигнал)", "зміна внутрішнього аргумента не змінює захоплений зовнішній");
}
