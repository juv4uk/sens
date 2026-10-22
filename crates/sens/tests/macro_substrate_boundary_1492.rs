use sens::{eval_program, Session};

const MACRO_SOURCE: &str = include_str!("../../../lib/macro.lisp");

#[test]
fn українське_визначення_макроса_зберігає_необчислені_аргументи() {
    let mut session = Session::default();
    let result = eval_program(
        r#"
        (визначити-макрос перша-форма (а б) а)
        (перша-форма (як-є гаразд) невідоме-імя)
        "#,
        &mut session,
    )
    .expect("D5 макрос має розгорнути перший аргумент без обчислення другого");

    assert_eq!(result.value.to_string(), "гаразд");
}

#[test]
fn звичайне_середовище_не_має_англійського_псевдоніма_конструктора() {
    let mut session = Session::default();
    assert!(
        session.environment.get("make-macro").is_none(),
        "тимчасове англійське ім'я не може бути звичайним викличним словом"
    );
    assert!(
        eval_program("(make-macro (функція (х) х))", &mut session).is_err(),
        "старе ім'я має бути недоступним для виконання"
    );
}

#[test]
fn бібліотека_макросів_не_викликає_англійський_конструктор_чи_сирі_голови() {
    assert!(
        !MACRO_SOURCE.contains("make-macro"),
        "живе макровизначення має користуватися лише D5 «макрос»"
    );
    assert!(
        !MACRO_SOURCE.lines().any(|line| {
            let line = line.trim_start();
            line.starts_with("(000")
                || line.starts_with("(001")
                || line.starts_with("(010")
                || line.starts_with("(011")
                || line.starts_with("(100")
                || line.starts_with("(101")
                || line.starts_with("(110")
                || line.starts_with("(111")
        }),
        "lib/macro.lisp не повинен мати сирих бітових викличних голів"
    );
}
