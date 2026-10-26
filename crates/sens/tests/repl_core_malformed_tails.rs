//! Реальне виконання SENS REPL після завантаження чинного core/meta-eval.
//! Незаконні атомарні хвости не мають виглядати як кінець списку.
mod common;

use sens::{
    eval_parsed_expressions, eval_program, load_core_library, parse_mixed_exact_domain, Session,
};

fn repl_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("current Core4 must load");
    common::load_meta_evaluator_library(&mut session).expect("SENS meta-evaluator must load");
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
        assert_eq!(
            result.as_predicate_bit(),
            Some(expected),
            "{source}: {result}"
        );
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
            "(репл-показати-слово-з-таблиці \"0010\" (як-є укр) (як-є (domain-table-1 (\"0010\" (укр функція)))))",
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
    let catalogue = "(як-є ((д4 (domain-table-1 (\"0010\" (укр функція) (ук фк))))))";
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
    let source = "(репл-код-із-каталогу (як-є функція) (як-є укр) (як-є д4) (як-є ((д4 (domain-table-1 (\"0010\" (укр функція)) (\"0011\" (укр функція)))))))";
    let result = eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("SENS D4 ambiguity witness: {error:?}"))
        .value;
    assert_eq!(
        result.to_string(),
        "()",
        "test_id=repl-d4-ambiguous layer=SENS input={source} expected=() actual={result}"
    );
}

#[test]
fn repl_uses_exact_d9_stringp_not_historical_text_alias() {
    // Справжній evaluator: тип рядка — ратифіковане D9:110100110,
    // результат — точне D1, не Python/JSON truthiness і не Unicode-carrier.
    let mut session = repl_session();
    for (source, expected) in [
        ("(рядок? \"0010\")", true),
        ("(рядок? \"\")", true),
        ("(рядок? (як-є ключ))", false),
        ("(рядок? (як-є ()))", false),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("SENS D9 string-type on {source}: {error:?}"))
            .value;
        assert_eq!(
            value.as_predicate_bit(),
            Some(expected),
            "test_id=repl-d9-stringp layer=SENS input={source} expected={expected} actual={value}"
        );
    }
}

#[test]
fn d11_four_repl_library_laws_run_inside_sens() {
    // Four already defined lib/repl-core.lisp functions — SENS evaluates
    // both sides of each compositional law, including a distinct countercase.
    let mut session = repl_session();
    let laws = [
        (
            "репл-форма-функція",
            "(репл-форма-функція (як-є (арг)) (як-є (перше арг)))",
            "(як-є (функція (арг) (перше арг)))",
            "(репл-форма-функція (як-є (арг)) (як-є (решта арг)))",
        ),
        (
            "репл-крок",
            "(репл-крок (як-є (визначити нова (як-є альфа))) (репл-почати (як-є ())))",
            "(обчислити-форму-та-оновити-оточення (як-є (визначити нова (як-є альфа))) (перше (репл-почати (як-є ()))))",
            "(репл-крок (як-є (визначити нова (як-є бета))) (репл-почати (як-є ())))",
        ),
        (
            "репл-визначити",
            "(репл-визначити (як-є нова) (як-є (як-є альфа)) (репл-почати (як-є ())))",
            "(репл-крок (як-є (визначити нова (як-є альфа))) (репл-почати (як-є ())))",
            "(репл-визначити (як-є нова) (як-є (як-є бета)) (репл-почати (як-є ())))",
        ),
        (
            "репл-визначити-функцію",
            "(репл-визначити-функцію (як-є обчислювач) (як-є (арг)) (як-є (перше арг)) (репл-почати (як-є ())))",
            "(репл-визначити (як-є обчислювач) (репл-форма-функція (як-є (арг)) (як-є (перше арг))) (репл-почати (як-є ())))",
            "(репл-визначити-функцію (як-є обчислювач) (як-є (арг)) (як-є (решта арг)) (репл-почати (як-є ())))",
        ),
    ];
    for (name, actual_source, law_source, different_source) in laws {
        let evaluate = |src: &str, session: &mut Session| {
            eval_program(src, session)
                .unwrap_or_else(|error| {
                    panic!("test_id=D11-REPL-{name} layer=SENS input={src} error={error}")
                })
                .value
                .to_string()
        };
        let actual = evaluate(actual_source, &mut session);
        let expected = evaluate(law_source, &mut session);
        assert_eq!(
            actual, expected,
            "test_id=D11-REPL-{name}-LAW expected={expected} actual={actual}"
        );
        let changed = evaluate(different_source, &mut session);
        assert_ne!(
            actual, changed,
            "test_id=D11-REPL-{name}-NEG actual={actual} mutated={changed}"
        );
    }
}

#[test]
fn repl_step_rejects_atomic_state_as_sens_data() {
    let mut session = repl_session();
    let source = "(репл-крок (як-є (визначити нова (як-є альфа))) (як-є битий-стан))";
    let value = eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("SENS REPL should reject an atomic state as data: {error:?}"))
        .value;
    assert_eq!(
        value.to_string(),
        "неправильний-стан-репл",
        "test_id=repl-step-atomic-state layer=SENS expected=explicit-error-data actual={value}"
    );
}
