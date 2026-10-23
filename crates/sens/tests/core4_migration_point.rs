use sens::{eval_program, load_core_library, Session, Value};

fn migrated_core() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("migrated Core4 must load");
    session
}

#[test]
fn core4_named_numeric_values_are_exact_and_source_literal_free() {
    let mut session = migrated_core();

    for (name, expected) in [("число-нуль", "0"), ("число-один", "1")] {
        let value = session.environment.get(name).expect("named D24+ root value");
        match value {
            Value::BinaryNumber(number) => {
                assert_eq!(number.numeric_domain_width(), Some(24));
                assert_eq!(number.to_decimal_string(), expected);
            }
            other => panic!("{name} must be a typed D24+ binary value, got {other:?}"),
        }
    }

    let values = eval_program(
        "(список число-нуль число-один число-два число-три число-чотири число-п'ять число-сім число-вісім число-десять число-п'ятнадцять число-сто число-тисяча число-двісті-п'ятдесят-шість число-шістдесят-п'ять-тисяч-п'ятсот-тридцять-шість число-мільйон)",
        &mut session,
    )
    .expect("named exact numeric values must evaluate")
    .value;
    assert_eq!(
        values.to_string(),
        "(0 1 2 3 4 5 7 8 10 15 100 1000 256 65536 1000000)"
    );

    let bytes = eval_program("(т5м3-три-байти число-мільйон)", &mut session)
        .expect("named million must enter the existing T5M3 projection")
        .value;
    assert_eq!(bytes.to_string(), "(64 66 15)");
}

#[test]
fn core4_point_witness_crosses_predicates_strings_macros_and_fresh_symbols() {
    let mut session = migrated_core();

    for (source, expected) in [
        ("(однакові? (як-є (а б)) (як-є (а б)))", true),
        ("(однакові? (як-є (а б)) (як-є (а в)))", false),
        ("(значення-у-списку? (як-є б) (як-є (а б в)))", true),
        ("(значення-у-списку? (як-є з) (як-є (а б в)))", false),
        ("(порожній? (як-є ()))", true),
        ("(порожній? (як-є (а)))", false),
        ("(текст-передує? \"a\" \"b\")", true),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("source={source} error={error}"))
            .value;
        assert_eq!(
            value.as_predicate_bit(),
            Some(expected),
            "{source} -> {value}"
        );
    }

    for (source, expected) in [
        (
            "(знайти-за-ключем (як-є б) (як-є ((а . 1) (б . 2))))",
            "(б . 2)",
        ),
        ("(знайти-за-ключем (як-є з) (як-є ((а . 1) (б . 2))))", "()"),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("source={source} error={error}"))
            .value;
        assert_eq!(value.to_string(), expected, "{source}");
    }

    for (source, expected) in [
        ("(нехай ((значення 7)) значення)", "7"),
        ("(нехай-послідовно ((перше-значення 7) (друге-значення перше-значення)) друге-значення)", "7"),
        ("(-> 3 (список 4))", "(3 4)"),
        ("(->> 3 (список 4))", "(4 3)"),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("source={source} error={error}"))
            .value;
        assert_eq!(value.to_string(), expected, "{source}");
    }

    let fresh = eval_program("(створити-символ \"core4-point-\")", &mut session)
        .expect("створення символу через чинну українську поверхню")
        .value;
    assert!(matches!(fresh, Value::Symbol(_)));
}

#[test]
fn core4_d6_filter_and_reduce_execute_ukrainian_sources() {
    let mut session = migrated_core();
    // Справжній SENS evaluator, а не пошук лексичних шаблонів у файлі.
    // Десяткові аргументи СПИСКУ проходять проєкцію D24+;
    // вміст ЯК-Є зберігається як сирий синтаксис.
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
            "(згорнути (функція (сума число) (додати сума число)) 0 (список 1 2 3 4))",
            "10",
        ),
        (
            "(згорнути (функція (сума число) (додати сума число)) 7 (як-є ()))",
            "7",
        ),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("source={source} error={error}"))
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
        assert_eq!(
            actual, expected,
            "D6 exact SUBLIS whole-tree precedence: {source}"
        );
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
        let result = eval_program(source, &mut session).unwrap_or_else(|error| {
            panic!("test_id=core4-equal-exec layer=SENS input={source} error={error}")
        });
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(expected),
            "test_id=core4-equal-exec layer=SENS input={source} expected={expected} actual={}",
            result.value
        );
    }
}

// D1-поведінка Core4: порядок перевіряється на ВСЬОМУ хвості, не тільки на першій парі.
// Нативний SENS evaluator обчислює закон; Rust не імітує жодного порівняння.
#[test]
fn core4_ukrainian_order_predicates_recurse_until_empty_tail_in_sens() {
    let mut session = migrated_core();
    for (source, expected) in [
        ("(перевірити-неспадання-значень? 1 (як-є ()))", true),
        ("(перевірити-неспадання-значень? 1 (список 1 2))", true),
        ("(перевірити-неспадання-значень? 1 (список 2 1))", false),
        ("(перевірити-неспадання-значень? 2 (список 1))", false),
        ("(перевірити-незростання-значень? 2 (як-є ()))", true),
        ("(перевірити-незростання-значень? 2 (список 2 1))", true),
        ("(перевірити-незростання-значень? 2 (список 1 2))", false),
        ("(перевірити-незростання-значень? 1 (список 2))", false),
    ] {
        // Числові літерали стають точними D24+ у чинній проєкції мови
        // ДО виконання. Цитований список голих Number не є D24.
        let parsed = sens::parse(source).unwrap_or_else(|error| {
            panic!("test_id=core4-order-d1 parse input={source} error={error}")
        });
        let exact = sens::source_projection::project_ukr_decimal_integer_literals(&parsed, source)
            .unwrap_or_else(|error| {
                panic!("test_id=core4-order-d1 numeric projection input={source} error={error}")
            });
        let result = sens::eval_parsed_expressions(&exact, &mut session)
            .unwrap_or_else(|error| panic!("test_id=core4-order-d1 source={source} error={error}"));
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(expected),
            "test_id=core4-order-d1 input={source} expected={expected} actual={}",
            result.value
        );
    }
}

#[test]
fn core4_ukrainian_association_search_handles_later_and_missing_keys() {
    // SENS проходить усі гілки: перший ключ, наступний ключ і відсутність.
    // Старий (так ...) мав неявне незв'язане ім'я у рекурсивній гілці.
    let mut session = migrated_core();
    for (source, expected) in [
        (
            "(знайти-за-ключем (як-є а) (як-є ((а . перший) (б . другий))))",
            "(а . перший)",
        ),
        (
            "(знайти-за-ключем (як-є б) (як-є ((а . перший) (б . другий))))",
            "(б . другий)",
        ),
        (
            "(знайти-за-ключем (як-є немає) (як-є ((а . перший) (б . другий))))",
            "()",
        ),
        ("(знайти-за-ключем (як-є немає) (як-є ()))", "()"),
    ] {
        let result = eval_program(source, &mut session).unwrap_or_else(|error| {
            panic!("test_id=core4-assoc-exec layer=SENS input={source} error={error}")
        });
        assert_eq!(
            result.value.to_string(),
            expected,
            "test_id=core4-assoc-exec layer=SENS input={source} expected={expected} actual={}",
            result.value
        );
    }
}

#[test]
fn core4_ukrainian_member_executes_positive_negative_and_recursive_d1() {
    // Справжній SENS, а не лексичний oracle: член першого, останнього,
    // відсутнього, порожнього списку й структурного вкладеного елемента.
    let mut session = migrated_core();
    for (source, expected) in [
        ("(значення-у-списку? (як-є а) (як-є (а б в)))", true),
        ("(значення-у-списку? (як-є в) (як-є (а б в)))", true),
        ("(значення-у-списку? (як-є г) (як-є (а б в)))", false),
        ("(значення-у-списку? (як-є а) (як-є ()))", false),
        (
            "(значення-у-списку? (як-є (а б)) (як-є ((в г) (а б))))",
            true,
        ),
        (
            "(значення-у-списку? (як-є (а б)) (як-є ((в г) (а в))))",
            false,
        ),
    ] {
        let result = eval_program(source, &mut session).unwrap_or_else(|error| {
            panic!("test_id=core4-member-exec layer=SENS input={source} error={error}")
        });
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(expected),
            "test_id=core4-member-exec layer=SENS input={source} expected={expected} actual={}",
            result.value
        );
    }
}

#[test]
fn core4_ukrainian_d10_mklist_preserves_empty_atom_and_existing_pair() {
    // D10 MKLIST лишається SENS-визначенням; 3 гілки виконуються в SENS.
    let mut session = migrated_core();
    for (source, expected) in [
        ("(утворити-список (як-є ()))", "()"),
        ("(утворити-список (як-є а))", "(а)"),
        ("(утворити-список (як-є (а б)))", "(а б)"),
        ("(утворити-список (сполучити (як-є а) (як-є б)))", "(а . б)"),
    ] {
        let result = eval_program(source, &mut session).unwrap_or_else(|error| {
            panic!("test_id=d10-mklist-sens layer=SENS input={source} error={error}")
        });
        assert_eq!(
            result.value.to_string(),
            expected,
            "test_id=d10-mklist-sens layer=SENS input={source} expected={expected} actual={}",
            result.value
        );
    }
}

#[test]
fn core4_ukrainian_d10_listp_returns_exact_d1_for_nil_atom_and_cons() {
    // D10 LISTP відмінний від PROPER-LIST: крапкова CONS-пара теж є парою.
    let mut session = migrated_core();
    for (source, expected) in [
        ("(список? (як-є ()))", true),
        ("(список? (як-є а))", false),
        ("(список? (як-є (а б)))", true),
        ("(список? (сполучити (як-є а) (як-є б)))", true),
    ] {
        let result = eval_program(source, &mut session).unwrap_or_else(|error| {
            panic!("test_id=d10-listp-sens layer=SENS input={source} error={error}")
        });
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(expected),
            "test_id=d10-listp-sens layer=SENS input={source} expected={expected} actual={}",
            result.value
        );
    }
}

#[test]
fn core4_ukrainian_d10_find_leaf_evaluates_real_predicate_with_d1() {
    // SENS рекурсія D10: на атомі й вкладеній парі обидва D1 виходи,
    // на NIL предикат обчислюється, а не підмінюється truthiness Rust.
    let mut session = migrated_core();
    for (source, expected) in [
        ("(є-листок-дерева-що-задовольняє-предикат? (функція (x) (тотожне? x (як-є б))) (як-є б))", true),
        ("(є-листок-дерева-що-задовольняє-предикат? (функція (x) (тотожне? x (як-є б))) (як-є а))", false),
        ("(є-листок-дерева-що-задовольняє-предикат? (функція (x) (тотожне? x (як-є б))) (як-є ((а в) (г б))))", true),
        ("(є-листок-дерева-що-задовольняє-предикат? (функція (x) (тотожне? x (як-є б))) (як-є ((а в) (г д))))", false),
        ("(є-листок-дерева-що-задовольняє-предикат? (функція (x) (тотожне? x (як-є ()))) (як-є ()))", true),
    ] {
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("test_id=d10-find-leaf-sens layer=SENS input={source} error={error}"));
        assert_eq!(result.value.as_predicate_bit(), Some(expected),
            "test_id=d10-find-leaf-sens layer=SENS input={source} expected={expected} actual={}", result.value);
    }
}

#[test]
fn core4_ukrainian_d10_mappend_and_one_level_flatten_execute_in_sens() {
    // Мовні D10 MAPPEND/FLATTEN: порядок, порожній вхід,
    // рівно один рівень вкладеності та fail-closed атомарний вхід.
    let mut session = migrated_core();
    for (source, expected) in [
        (
            "(відобразити-й-додати (функція (x) (список x)) (як-є (а б в)))",
            "(а б в)",
        ),
        (
            "(відобразити-й-додати (функція (x) (список x)) (як-є ()))",
            "()",
        ),
        ("(сплющити (як-є ((а б) (в г))))", "(а б в г)"),
        ("(сплющити (як-є (((а б) в))) )", "((а б) в)"),
    ] {
        let result = eval_program(source, &mut session).unwrap_or_else(|error| {
            panic!("test_id=d10-mappend-sens layer=SENS input={source} error={error}")
        });
        assert_eq!(
            result.value.to_string(),
            expected,
            "test_id=d10-mappend-sens layer=SENS input={source} expected={expected} actual={}",
            result.value
        );
    }
    let invalid = "(відобразити-й-додати (функція (x) (список x)) (як-є а))";
    let error = eval_program(invalid, &mut session)
        .expect_err("test_id=d10-mappend-invalid layer=SENS atom must fail closed");
    assert_eq!(
        error.kind,
        sens::ErrorKind::Type,
        "test_id=d10-mappend-invalid layer=SENS input={invalid} expected=Type actual={error:?}"
    );
}

#[test]
fn core4_ukrainian_rassoc_union_execute_true_d1_branches_in_sens() {
    // SENS виконує реальні D3 CAR/CDR, рекурсію та D1 COND.
    // Ніяка семантика не обчислюється у тестовому Rust-спостерігачі.
    let mut session = migrated_core();
    for (source, expected) in [
        (
            "(знайти-за-значенням (як-є б) (як-є ((а . б) (в . г))))",
            "(а . б)",
        ),
        (
            "(знайти-за-значенням (як-є г) (як-є ((а . б) (в . г))))",
            "(в . г)",
        ),
        (
            "(знайти-за-значенням (як-є д) (як-є ((а . б) (в . г))))",
            "()",
        ),
        ("(знайти-за-значенням (як-є а) (як-є ()))", "()"),
        ("(об'єднання (як-є (а б)) (як-є (б в)))", "(а б в)"),
        ("(об'єднання (як-є (а б)) (як-є (а б)))", "(а б)"),
        ("(об'єднання (як-є ()) (як-є (б в)))", "(б в)"),
        ("(об'єднання (як-є (а)) (як-є (а)))", "(а)"),
    ] {
        let result = eval_program(source, &mut session).unwrap_or_else(|error| {
            panic!("test_id=core4-ukr-rassoc-union layer=SENS input={source} error={error}")
        });
        assert_eq!(
            result.value.to_string(),
            expected,
            "test_id=core4-ukr-rassoc-union layer=SENS input={source} expected={expected} actual={}",
            result.value
        );
    }
}

#[test]
fn core4_ukrainian_answer_algebra_executes_both_sides_of_distinctions() {
    // Закони визначає SENS: тут виконується справжній evaluator.
    let mut session = migrated_core();
    for (source, expected) in [
        ("(відповідь-і (список ні) (список так))", "(0)"),
        ("(відповідь-і (список так) (список ні))", "(0)"),
        ("(відповідь-і (список ні ні) (список ні))", "(0)"),
        ("(відповідь-і (список так) (список так так))", "(1 1)"),
        ("(відповідь-послабити (список так))", "(1 1)"),
        (
            "(відповідь-послабити (список так так так так так так так))",
            "()",
        ),
    ] {
        let result = eval_program(source, &mut session).unwrap_or_else(|error| {
            panic!("test_id=core4-answer-algebra layer=SENS input={source} error={error}")
        });
        assert_eq!(
            result.value.to_string(),
            expected,
            "test_id=core4-answer-algebra layer=SENS input={source} expected={expected} actual={}",
            result.value
        );
    }
}

#[test]
fn core4_ukrainian_rest_args_are_executed_after_d7_dotted_tail_removal() {
    // Варіативні визначення з lib/core4.lisp виконуються в живому SENS.
    // Перевіряємо поведінку, не просто відсутність текстового шаблону.
    let mut session = migrated_core();
    for (program, expected) in [
        ("(повернути-перше (як-є а) (як-є б) (як-є в))", "а"),
        ("(повернути-друге (як-є а) (як-є б) (як-є в))", "б"),
        ("(найменше 8 3 5)", "3"),
        ("(найбільше 8 3 5)", "8"),
    ] {
        let value = eval_program(program, &mut session)
            .unwrap_or_else(|error| {
                panic!("test_id=core4-ukr-varargs layer=SENS input={program} error={error}")
            })
            .value;
        assert_eq!(
            value.to_string(), expected,
            "test_id=core4-ukr-varargs layer=SENS input={program} expected={expected} actual={value}"
        );
    }
}


// Перевірка не текстового шаблону, а результатів виконання чинного Core4:
// D1:0 тепер повертається прямо; жодного CONS/ATOM для штучної хиби.
#[test]
fn core4_ukrainian_clips_shortcut_truth_tables_execute_in_sens() {
    let mut session = migrated_core();
    for (program, expected) in [
        ("(твердження-кліпс? (як-є а))", false),
        ("(твердження-кліпс? (як-є (assert а)))", true),
        ("(твердження-кліпс? (як-є (printout а)))", false),
        ("(виведення-кліпс? (як-є а))", false),
        ("(виведення-кліпс? (як-є (printout а)))", true),
        ("(виведення-кліпс? (як-є (assert а)))", false),
        ("(усі-твердження-кліпс? (як-є ()))", true),
        ("(усі-твердження-кліпс? (як-є ((assert а))))", true),
        ("(усі-твердження-кліпс? (як-є ((printout а))))", false),
    ] {
        let actual = eval_program(program, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=CORE4-CLIPS-D1 layer=SENS input={program} expected=D1:{expected} actual_error={error}"
            ))
            .value;
        assert_eq!(
            actual.as_predicate_bit(),
            Some(expected),
            "test_id=CORE4-CLIPS-D1 layer=SENS input={program} expected=D1:{expected} actual={actual}"
        );
    }
}
