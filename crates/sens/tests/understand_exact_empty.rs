//! Реальний Rust-оракул мігрованого Advice Taker Lisp джерела.
//! Без обхідних host-макетів: завантажуємо source-pinned ядро й справжній
//! `lib/understand.lisp` через точнодоменний D3/D4 reader.
use sens::{
    eval_parsed_expressions, load_core_library, lower_program, parse_mixed_exact_domain, Session,
};

fn loaded() -> Session {
    let mut session = Session::default();
    // Канонічне ядро SENS завантажується своїм чинним механізмом:
    // окреме обчислення core.lisp не має всіх його залежностей.
    load_core_library(&mut session).expect("точнодоменне ядро SENS має завантажитись");
    let forms = parse_mixed_exact_domain(include_str!("../../../lib/understand.lisp"))
        .expect("D3/D4 заголовки мають розпізнаватися без W8-підміни");
    // Лексичні українські D1 значення потрібні у виконуваній
    // двійковій формі; цитати залишаються незмінними даними.
    let lowered = lower_program(&forms);
    eval_parsed_expressions(&lowered, &mut session)
        .expect("реальний understand-модуль повинен завантажитися");
    session
}

fn run(session: &mut Session, source: &str) -> String {
    let forms = parse_mixed_exact_domain(source).expect("правильне D3 джерело");
    let lowered = lower_program(&forms);
    eval_parsed_expressions(&lowered, session)
        .unwrap_or_else(|error| panic!("виконання {source} не пройшло: {error:?}"))
        .value
        .to_string()
}

#[test]
fn empty_word_lists_never_evaluate_car() {
    let mut session = loaded();
    for name in ["прибрати-артикль", "розібрати", "розібрати-запит"]
    {
        let program = format!("({name} (001 ()))");
        assert_eq!(run(&mut session, &program), "()", "{name}");
    }
}

#[test]
fn incomplete_word_lists_do_not_reach_second_or_third_selectors() {
    let mut session = loaded();
    for program in [
        "(розібрати (001 (mars)))",
        "(розібрати (001 (mars orbits)))",
        "(розібрати-запит (001 (is)))",
        "(розібрати-запит (001 (is mars)))",
        "(розібрати-запит (001 (does mars)))",
        "(розібрати (001 (all planets have)))",
        "(розібрати-запит (001 (does mars orbit)))",
        "(розібрати-загальний (001 (all planets have)))",
        "(розібрати-запит-відношення (001 (does mars orbit)))",
        "(розібрати (001 (all planets have . хвіст)))",
        "(розібрати-запит (001 (does mars orbit . хвіст)))",
        "(розібрати-загальний (001 ()))",
        "(розібрати-запит-відношення (001 ()))",
    ] {
        assert_eq!(run(&mut session, program), "()", "{program}");
    }
}

#[test]
fn ordinary_nonempty_words_preserve_exact_advice_taker_laws() {
    let mut session = loaded();
    for (program, expected) in [
        ("(прибрати-артикль (001 (a mars)))", "(mars)"),
        ("(прибрати-артикль (001 (an mars)))", "(mars)"),
        ("(прибрати-артикль (001 (mars)))", "(mars)"),
        ("(розібрати (001 (mars orbits sun)))", "((orbits mars sun))"),
        (
            "(розібрати-запит (001 (is mars a planet)))",
            "(planet mars)",
        ),
        (
            "(розібрати (001 (all planets have mass)))",
            "((has (var w) mass) (planets (var w)))",
        ),
        (
            "(розібрати-запит (001 (does mars orbit sun)))",
            "(orbit mars sun)",
        ),
        (
            "(розібрати-загальний (001 (all planets have mass)))",
            "((has (var w) mass) (planets (var w)))",
        ),
        (
            "(розібрати-запит-відношення (001 (does mars orbit sun)))",
            "(orbit mars sun)",
        ),
    ] {
        assert_eq!(run(&mut session, program), expected, "{program}");
    }
}
