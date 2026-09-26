use sens::{eval_program, Session};

const УКРАЇНСЬКА_ПОВЕРХНЯ: &str = include_str!("../../../lib/surface/uk.lisp");

#[test]
fn українська_поверхня_не_переводить_необхідні_форми_через_англійську() {
    assert!(
        !УКРАЇНСЬКА_ПОВЕРХНЯ.contains("(defmacro функція"),
        "функція не повинна перевизначатися макросом поверх lambda"
    );
    assert!(
        !УКРАЇНСЬКА_ПОВЕРХНЯ.contains("(defmacro визначити"),
        "визначити не повинно перевизначатися макросом поверх define"
    );
}

#[test]
fn необхідні_українські_форми_працюють_без_environment_binding() {
    let mut сесія = Session::default();

    assert!(
        сесія.environment.get("функція").is_none(),
        "функція має розпізнаватися evaluator-ом, а не environment binding"
    );
    assert!(
        сесія.environment.get("визначити").is_none(),
        "визначити має розпізнаватися evaluator-ом, а не environment binding"
    );

    let результат = eval_program(
        "(визначити подвоїти (функція (число) (додати число число))) (подвоїти 21)",
        &mut сесія,
    )
    .expect("прямі українські necessary-form spellings повинні виконуватися")
    .value
    .to_string();

    assert_eq!(результат, "42");
    assert!(сесія.environment.get("функція").is_none());
    assert!(сесія.environment.get("визначити").is_none());
}
