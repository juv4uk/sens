//! Українські текстові назви визначаються в SENS до встановлення D9.
 //! Реальне виконання, не Python-оракул і не побайтовий тест коментарів.
use sens::{eval_parsed_expressions, load_core_library, parse_mixed_exact_domain, Session};

const SOURCE: &str = include_str!("../../../lib/string-surface-aliases.lisp");

fn eval_ukr(source: &str, session: &mut Session) -> sens::Value {
    let expressions = parse_mixed_exact_domain(source)
        .unwrap_or_else(|error| panic!("SENS reader {source}: {error}"));
    eval_parsed_expressions(&expressions, session)
        .unwrap_or_else(|error| panic!("SENS evaluator {source}: {error}"))
        .value
}

#[test]
fn українські_текстові_замикання_завантажуються_раніше_d9_без_раннього_звязування() {
    let mut session = Session::bare();

    // Незалежні мовні замикання не читають ще не встановлені механізми.
    let definitions = parse_mixed_exact_domain(SOURCE)
        .expect("поточний український Lisp повинен розбиратися у SENS");
    eval_parsed_expressions(&definitions, &mut session)
        .expect("визначення замикань не повинні вимагати ранній D9");

    // Справжня SENS-реєстрація усіх п'яти замикань, не повторена перевірка
    // текстових регулярних виразів у Python.
    for name in [
        "зчепити", "текст-порожній?", "перший-символ-тексту",
        "решта-символів-тексту", "порожнє?",
    ] {
        assert!(
            matches!(session.environment.get(name), Some(sens::Value::Closure(_))),
            "виконуване українське замикання не встановлено: {name}"
        );
    }

    // Тільки після цього встановлюємо штатний SENS Core4.
    load_core_library(&mut session).expect("штатне ядро визначає виконавчі закони");
    for (expression, expected) in [
        ("(порожнє? (як-є ()))", true),
        ("(порожнє? (як-є (елемент)))", false),
    ] {
        let value = eval_ukr(expression, &mut session);
        assert_eq!(value.as_predicate_bit(), Some(expected), "{expression}");
    }
}
