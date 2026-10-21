use sens::{eval_program, load_core_library, Session, Value};

fn migrated_core() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("migrated Core4 must load");
    session
}

#[test]
fn core4_point_witness_crosses_predicates_strings_macros_and_fresh_symbols() {
    let mut session = migrated_core();

    for (source, expected) in [
        ("(equal? (quote (a b)) (quote (a b)))", true),
        ("(equal? (quote (a b)) (quote (a c)))", false),
        ("(member? (quote b) (quote (a b c)))", true),
        ("(member? (quote z) (quote (a b c)))", false),
        ("(null? (quote ()))", true),
        ("(null? (quote (a)))", false),
        ("(string<? \"a\" \"b\")", true),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|e| panic!("{source} failed: {e:?}"))
            .value;
        assert_eq!(value.as_predicate_bit(), Some(expected), "{source} -> {value}");
    }

    for (source, expected) in [
        ("(assoc (quote b) (quote ((a . 1) (b . 2))))", "(b . 2)"),
        ("(assoc (quote z) (quote ((a . 1) (b . 2))))", "()"),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|e| panic!("{source} failed: {e:?}"))
            .value;
        assert_eq!(value.to_string(), expected, "{source}");
    }

    for (source, expected) in [
        ("(let ((x 7)) x)", "7"),
        ("(let* ((x 7) (y x)) y)", "7"),
        ("(-> 3 (list 4))", "(3 4)"),
        ("(->> 3 (list 4))", "(4 3)"),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|e| panic!("{source} failed: {e:?}"))
            .value;
        assert_eq!(value.to_string(), expected, "{source}");
    }

    let fresh = eval_program("(gensym \"core4-point-\")", &mut session)
        .expect("GENSYM mechanism boundary")
        .value;
    assert!(matches!(fresh, Value::Symbol(_)));
}

#[test]
fn core4_d6_filter_and_reduce_execute_ukrainian_sources() {
    let mut session = migrated_core();
    // Справжній SENS evaluator, а не пошук лексичних шаблонів у файлі.
    for (source, expected) in [
        (
            "(відсіяти (функція (елемент) (тотожне? елемент (як-є б))) (як-є (а б в б)))",
            "(б б)",
        ),
        (
            "(відсіяти (функція (елемент) (тотожне? елемент (як-є б))) (як-є (а в)))",
            "()",
        ),
        (
            "(відсіяти (функція (елемент) (тотожне? елемент (як-є б))) (як-є ()))",
            "()",
        ),
        (
            "(згорнути (функція (сума число) (додати сума число)) 0 (як-є (1 2 3 4)))",
            "10",
        ),
        (
            "(згорнути (функція (сума число) (додати сума число)) 7 (як-є ()))",
            "7",
        ),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("SENS Core4 failed for {source}: {error:?}"))
            .value;
        assert_eq!(value.to_string(), expected, "{source}");
    }
}

#[test]
fn core4_d6_sublis_prioritizes_complete_tree_before_descending() {
    let mut session = migrated_core();
    // Повне завантаження Core4 та реальне виконання у SENS, а не симуляція.
    for (source, expected) in [
        (
            "(підставити-пари (список (сполучити (як-є а) (як-є б))) (як-є (а в а)))",
            "(б в б)",
        ),
        (
            "(підставити-пари (список (сполучити (як-є (а в)) (як-є ціле))) (як-є (а в)))",
            "ціле",
        ),
        (
            "(підставити-пари (список (сполучити (як-є ()) (як-є порожнє))) (як-є ()))",
            "порожнє",
        ),
    ] {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("SENS SUBLIS {source}: {error:?}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "D6 exact SUBLIS whole-tree precedence: {source}");
    }
}

#[test]
fn core4_ukrainian_structural_equality_executes_both_d1_bits() {
    // Реальний SENS Core4: ні символи «так»/«ні» без прив'язки,
    // ні host-рівність не підміняють мовний закон.
    let mut session = migrated_core();
    for (source, expected) in [
        ("(однакові? (як-є (а б)) (як-є (а б)))", true),
        ("(однакові? (як-є (а б)) (як-є (а в)))", false),
        ("(однакові? (як-є ()) (як-є ()))", true),
        ("(однакові? (як-є ()) (як-є (а)))", false),
        ("(однакові? (як-є (а)) (як-є ()))", false),
        ("(однакові? (як-є а) (як-є (а)))", false),
        ("(однакові? (як-є (а)) (як-є (а б)))", false),
    ] {
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=core4-equal-exec layer=SENS input={source} error={error}"
            ));
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(expected),
            "test_id=core4-equal-exec layer=SENS input={source} expected={expected} actual={}",
            result.value
        );
    }
}
