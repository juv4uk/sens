//! Реальне виконання SENS REPL після завантаження чинного core/meta-eval.
//! Незаконні атомарні хвости не мають виглядати як кінець списку.
use sens::{eval_parsed_expressions, eval_program, load_core_library, load_meta_evaluator_library, parse_mixed_exact_domain, Session};

fn repl_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("current Core4 must load");
    load_meta_evaluator_library(&mut session).expect("SENS meta-evaluator must load");
    let source = include_str!("../../../lib/repl-core.lisp");
    let forms = parse_mixed_exact_domain(source).expect("SENS REPL reader");
    eval_parsed_expressions(&forms, &mut session).expect("SENS REPL definitions must evaluate");
    session
}

#[test]
fn repl_bit_and_label_comparisons_reject_improper_tails() {
    let mut session = repl_session();
    for (source, expected) in [
        ("(репл-біти-збігаються? (як-є ()) \"\")", true),
        ("(репл-біти-збігаються? (як-є зайве) \"\")", false),
        ("(репл-біти-збігаються? (як-є (зайве)) \"\")", false),
        ("(репл-мітки-черги? (як-є ()) (як-є ()))", true),
        ("(репл-мітки-черги? (як-є зайве) (як-є ()))", false),
        ("(репл-мітки-черги? (як-є (зайве)) (як-є ()))", false),
    ] {
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("SENS REPL failed on {source}: {error:?}"))
            .value;
        assert_eq!(result.as_predicate_bit(), Some(expected), "{source}: {result}");
    }
}

#[test]
fn repl_named_catalog_lookups_execute_without_d5_value_calls() {
    // Справжня SENS-сесія: D7-рядки є лише поданням ключа.
    // Ідентичність та вибір поверхні залишаються мовними операціями.
    let mut session = repl_session();
    for (source, expected) in [
        (
            "(репл-назва-із-рядка \"0010\" (як-є укр) (як-є ((\"0010\" (укр функція)))) \"0010\")",
            "функція",
        ),
        (
            "(репл-назва-із-рядка \"0010\" (як-є укр) (як-є ((\"0010\" (укр функція)))) \"0020\")",
            "()",
        ),
        (
            "(репл-ключі-із-рядка (як-є функція) (як-є укр) (як-є ((\"0010\" (укр функція)))) (як-є ()) \"0010\")",
            "\"0010\"",
        ),
        (
            "(репл-ключі-із-рядка (як-є функція) (як-є укр) (як-є ((\"0010\" (укр функція)))) (як-є ()) \"0020\")",
            "()",
        ),
        (
            "(репл-код-однозначний (як-є неоднозначно))",
            "()",
        ),
        (
            "(репл-код-однозначний \"0010\")",
            "\"0010\"",
        ),
        (
            "(репл-показати-слово-з-таблиці \"0010\" (як-є укр) (як-є (domain-table/1 (\"0010\" (укр функція)))))",
            "функція",
        ),
        (
            "(репл-показати-слово-з-таблиці \"0010\" (як-є укр) (як-є ()))",
            "()",
        ),
    ] {
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("SENS REPL catalog failed on {source}: {error:?}"))
            .value;
        assert_eq!(
            result.to_string(),
            expected,
            "test_id=repl-named-catalog layer=SENS input={source} expected={expected} actual={result}"
        );
    }
}

#[test]
fn repl_projection_round_trip_uses_named_ukrainian_sens_calls() {
    // Ширина D4 перевіряється самою мовою, не сторонньою таблицею.
    // Один запис каталогу покриває пряме ім'я, інверсію і чужий домен.
    let mut session = repl_session();
    let catalogue = "(як-є ((д4 (domain-table/1 (\"0010\" (укр функція) (ук фк)))))";
    for (call, expected) in [
        (
            "(репл-код-із-каталогу (як-є функція) (як-є укр) (як-є д4)",
            "\"0010\"",
        ),
        (
            "(репл-код-із-каталогу (як-є функція) (як-є укр) (як-є д5)",
            "()",
        ),
        (
            "(репл-проєктувати-ім'я (як-є функція) (як-є укр) (як-є д4) (як-є ук)",
            "фк",
        ),
        (
            "(репл-проєктувати-ім'я (як-є відсутня) (як-є укр) (як-є д4) (як-є ук)",
            "()",
        ),
    ] {
        let source = format!("{call} {catalogue})");
        let result = eval_program(&source, &mut session)
            .unwrap_or_else(|error| panic!("SENS D4 projection failed on {source}: {error:?}"))
            .value;
        assert_eq!(
            result.to_string(),
            expected,
            "test_id=repl-d4-inverse layer=SENS input={source} expected={expected} actual={result}"
        );
    }
}

#[test]
fn repl_duplicate_name_rejects_ambiguous_d4_code() {
    // Дві різні чотирибітні координати з однією укр-проєкцією:
    // SENS не повинен здогадуватися, яку виконувати.
    let mut session = repl_session();
    let source = "(репл-код-із-каталогу (як-є функція) (як-є укр) (як-є д4) (як-є ((д4 (domain-table/1 (\"0010\" (укр функція)) (\"0011\" (укр функція)))))))";
    let result = eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("SENS D4 ambiguity witness: {error:?}"))
        .value;
    assert_eq!(
        result.to_string(), "()",
        "test_id=repl-d4-ambiguous layer=SENS input={source} expected=() actual={result}"
    );
}
