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
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=core4-assoc-exec layer=SENS input={source} error={error}"
            ));
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
        ("(значення-у-списку? (як-є (а б)) (як-є ((в г) (а б))))", true),
        ("(значення-у-списку? (як-є (а б)) (як-є ((в г) (а в))))", false),
    ] {
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=core4-member-exec layer=SENS input={source} error={error}"
            ));
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
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("test_id=d10-mklist-sens layer=SENS input={source} error={error}"));
        assert_eq!(result.value.to_string(), expected,
            "test_id=d10-mklist-sens layer=SENS input={source} expected={expected} actual={}", result.value);
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
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("test_id=d10-listp-sens layer=SENS input={source} error={error}"));
        assert_eq!(result.value.as_predicate_bit(), Some(expected),
            "test_id=d10-listp-sens layer=SENS input={source} expected={expected} actual={}", result.value);
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
        ("(відобразити-й-додати (функція (x) (список x)) (як-є (а б в)))", "(а б в)"),
        ("(відобразити-й-додати (функція (x) (список x)) (як-є ()))", "()"),
        ("(сплющити (як-є ((а б) (в г))))", "(а б в г)"),
        ("(сплющити (як-є (((а б) в))) )", "((а б) в)"),
    ] {
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("test_id=d10-mappend-sens layer=SENS input={source} error={error}"));
        assert_eq!(result.value.to_string(), expected,
            "test_id=d10-mappend-sens layer=SENS input={source} expected={expected} actual={}", result.value);
    }
    let invalid = "(відобразити-й-додати (функція (x) (список x)) (як-є а))";
    let error = eval_program(invalid, &mut session)
        .expect_err("test_id=d10-mappend-invalid layer=SENS atom must fail closed");
    assert_eq!(error.kind, sens::ErrorKind::Type,
        "test_id=d10-mappend-invalid layer=SENS input={invalid} expected=Type actual={error:?}");
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
