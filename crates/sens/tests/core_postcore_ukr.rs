//! Живе виконання виправлених post-core функцій через справжній SENS evaluator.
//! Не підмінює семантику Rust або Python; Rust лише викликає SENS та звіряє результат.
mod common;

use sens::{eval_program, Session};

fn core_session() -> Session {
    // Post-core функції визначені в канонічному Core4, тому тест має
    // використовувати штатний bootstrap Core/FASL, а не лише lib/core.lisp.
    // Відсутні механізми лишаються реальними помилками; bootstrap не
    // додає сторонніх адаптерів до виконання SENS.
    let mut session = Session::default();
    sens::load_core_library(&mut session)
        .expect("чинне Core4 має завантажуватися через штатний SENS bootstrap");
    session
}

fn execute(session: &mut Session, source: &str) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("SENS відхилив {source}: {error}"))
        .value
        .to_string()
}

// D1-свідок: непорожній список не може потрапити у незв'язану
// текстову гілку «так/ні». Порівнюємо із результатом реального SENS.
#[test]
fn core_empty_predicate_returns_exact_d1_for_nil_atom_and_pair() {
    let mut session = core_session();
    let yes = execute(&mut session, "(атом? (як-є ()))");
    let no = execute(&mut session, "(атом? (сполучити (як-є ()) (як-є ())))");
    for (source, expected) in [
        ("(порожній? (як-є ()))", yes.as_str()),
        ("(порожній? (як-є атом))", no.as_str()),
        ("(порожній? (як-є (весна літо)))", no.as_str()),
    ] {
        assert_eq!(execute(&mut session, source), expected, "{source}");
    }
}

// Порожні логічні макроси мають повернути точний D1, не символ з цитати.
#[test]
fn core_zero_arity_and_or_return_real_d1_bits() {
    let mut session = Session::default();
    sens::eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("чинне українське ядро повинне виконуватися в SENS");
    for (source, expected) in [("(та)", true), ("(або)", false)] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("SENS відхилив {source}: {error}"))
            .value;
        assert_eq!(
            value.as_predicate_bit(),
            Some(expected),
            "Порожній логічний макрос не може повернути цитований символ: {source}",
        );
    }
}

#[test]
fn core_peer_lookup_returns_first_matching_group_or_empty() {
    let mut session = core_session();
    assert_eq!(
        execute(&mut session,
            "(знайти-групу-відповідників-за-адресою (як-є другий) (як-є ((перший альфа) (другий бета))))"),
        "(другий бета)"
    );
    assert_eq!(
        execute(&mut session,
            "(знайти-групу-відповідників-за-адресою (як-є невідомий) (як-є ((перший альфа) (другий бета))))"),
        "()"
    );
}

#[test]
fn core_peer_binding_presence_and_absence_are_observable() {
    let mut session = core_session();
    let bindings = "(як-є ((\"перший\" альфа) (\"другий\" бета)))";
    assert_eq!(
        execute(
            &mut session,
            &format!("(стан-привязки-відповідника (як-є другий) {bindings})")
        ),
        "present"
    );
    assert_eq!(
        execute(
            &mut session,
            &format!("(стан-привязки-відповідника (як-є третій) {bindings})")
        ),
        "absent"
    );
}

#[test]
fn core_missing_peers_skip_existing_and_retain_source_order() {
    let mut session = core_session();
    assert_eq!(
        execute(&mut session,
            "(відсутні-відповідники (як-є джерело) (як-є (джерело перший другий третій)) (як-є ((\"перший\" привязка))))"),
        "(другий третій)"
    );
}

#[test]
fn core_constructs_only_ukrainian_d4_define_expressions() {
    let mut session = core_session();
    assert_eq!(
        execute(
            &mut session,
            "(побудувати-визначення-відповідників (як-є джерело) (як-є (перший другий)))"
        ),
        "(визначити перший (визначити другий джерело))"
    );
}

// Справжній evaluator читає увесь core, а не окремі скопійовані форми.
#[test]
fn core_nth_member_follow_current_d6_d5_semantics() {
    let mut session = core_session();
    assert_eq!(
        execute(&mut session, "(елемент-списку-за-індексом 1 (як-є (а б)))"),
        execute(&mut session, "(як-є б)")
    );
    assert_eq!(
        execute(&mut session, "(елемент-списку-за-індексом 2 (як-є (а б)))"),
        execute(&mut session, "(як-є ())")
    );
    assert_eq!(
        execute(&mut session, "(значення-у-списку? (як-є б) (як-є (а б)))"),
        execute(&mut session, "(атом? (як-є а))")
    );
    assert_eq!(
        execute(&mut session, "(значення-у-списку? (як-є в) (як-є (а б)))"),
        execute(&mut session, "(тотожне? (як-є а) (як-є б))")
    );
}

#[test]
fn core_sublis_and_maplist_execute_in_sens_without_host_oracle() {
    let mut session = core_session();
    assert_eq!(
        execute(
            &mut session,
            "(підставити-пари (список (сполучити (як-є а) (як-є б))) (як-є (а в а)))"
        ),
        execute(&mut session, "(як-є (б в б))")
    );
    assert_eq!(
        execute(
            &mut session,
            "(підставити-пари (список (сполучити (як-є (а в)) (як-є ціле))) (як-є (а в)))"
        ),
        execute(&mut session, "(як-є ціле)")
    );
    assert_eq!(
        execute(
            &mut session,
            "(відобразити-залишки (як-є (а б)) (функція (хвіст) (перше хвіст)))"
        ),
        execute(&mut session, "(як-є (а б))")
    );
}

// Живий SENS-метаобчислювач: атомарні мітки даних і справжні
// складені замикання мають повертати біт D1, не Lisp-символ "так"/"ні".
#[test]
fn meta_eval_predicates_are_actual_d1_bits() {
    let mut session = core_session();
    common::load_meta_evaluator_library(&mut session)
        .expect("чинний український MetaEval має виконуватися в SENS");
    let cases = [
        ("(ім'я-форми-як-є? (як-є як-є))", true),
        ("(ім'я-форми-як-є? (як-є атом?))", false),
        ("(ім'я-форми-як-є? (як-є за-умовою))", false),
        ("(ім'я-форми-як-є? (як-є невідоме))", false),
        ("(ім'я-форми-за-умовою? (як-є за-умовою))", true),
        ("(ім'я-форми-за-умовою? (як-є як-є))", false),
        ("(ім'я-форми-за-умовою? (як-є функція))", false),
        ("(ім'я-форми-за-умовою? (як-є невідоме))", false),
        ("(ім'я-форми-лямбда? (як-є функція))", true),
        ("(ім'я-форми-лямбда? (як-є визначити))", false),
        ("(ім'я-форми-лямбда? (як-є за-умовою))", false),
        ("(ім'я-форми-лямбда? (як-є невідоме))", false),
        ("(ім'я-форми-визначити? (як-є визначити))", true),
        ("(ім'я-форми-визначити? (як-є функція))", false),
        ("(ім'я-форми-визначити? (як-є визначити-макрос))", false),
        ("(ім'я-форми-визначити? (як-є невідоме))", false),
        ("(ім'я-форми-визначити-макрос? (як-є визначити-макрос))", true),
        ("(ім'я-форми-визначити-макрос? (як-є визначити))", false),
        ("(ім'я-форми-визначити-макрос? (як-є функція))", false),
        ("(ім'я-форми-визначити-макрос? (як-є невідоме))", false),
        ("(канонічне-ім'я-форми? (як-є функція))", true),
        ("(канонічне-ім'я-форми? (як-є визначити))", true),
        ("(канонічне-ім'я-форми? (як-є визначити-макрос))", true),
        ("(канонічне-ім'я-форми? (як-є за-умовою))", true),
        ("(канонічне-ім'я-форми? (як-є невідоме))", false),
        ("(канонічна-виклична-тотожність? (як-є атом?))", true),
        ("(канонічна-виклична-тотожність? (як-є тотожне?))", true),
        ("(канонічна-виклична-тотожність? (як-є сполучити))", true),
        ("(канонічна-виклична-тотожність? (як-є перше))", true),
        ("(канонічна-виклична-тотожність? (як-є решта))", true),
        ("(канонічна-виклична-тотожність? (як-є як-є))", false),
        ("(канонічна-виклична-тотожність? (як-є функція))", false),
        ("(канонічна-виклична-тотожність? (як-є визначити))", false),
        ("(канонічна-виклична-тотожність? (як-є додати))", false),
        ("(канонічна-виклична-тотожність? (як-є невідоме))", false),
        ("(тотожність-відповідає-поверхні? (як-є функція) (як-є функція))", true),
        ("(тотожність-відповідає-поверхні? (як-є визначити) (як-є визначити))", true),
        ("(тотожність-відповідає-поверхні? (як-є визначити-макрос) (як-є визначити-макрос))", true),
        ("(тотожність-відповідає-поверхні? (як-є атом?) (як-є атом?))", true),
        ("(тотожність-відповідає-поверхні? (як-є як-є) (як-є як-є))", true),
        ("(тотожність-відповідає-поверхні? (як-є функція) (як-є визначити))", false),
        ("(тотожність-відповідає-поверхні? (як-є як-є) (як-є за-умовою))", false),
        ("(тотожність-відповідає-поверхні? (як-є невідоме) (як-є функція))", false),
        ("(тотожність-відповідає-поверхні? (як-є визначити-макрос) (як-є визначити))", false),
        ("(тотожність-відповідає-поверхні? (як-є атом?) (як-є сполучити))", false),
        ("(тотожність-відповідає-поверхні? (як-є (а б)) (як-є функція))", false),
        ("(це-макрос? (як-є приклад))", false),
        ("(це-макрос? (як-є (macro приклад)))", true),
        ("(це-замикання? (як-є приклад))", false),
        ("(це-замикання? (як-є (closure приклад)))", true),
        ("(це-рекурсивне-замикання? (як-є приклад))", false),
        (
            "(це-рекурсивне-замикання? (як-є (recursive-closure приклад)))",
            true,
        ),
        ("(лямбда-має-параметр-залишку? (як-є ()))", false),
        ("(лямбда-має-параметр-залишку? (як-є (x y)))", false),
        ("(лямбда-має-параметр-залишку? (як-є залишок))", true),
    ];
    for (source, expected) in cases {
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("SENS-виконання {source}: {error}"));
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(expected),
            "meta-eval повинен повернути саме D1: {source}",
        );
    }


    // Д11: реальне SENS виконання двох бібліотечних композицій.
    // Власний примітив створює пару (primitive ім'я); предикат
    // читає структурний тег, не видаючи замикання за примітив.
    for (case, source, expected) in [
        (
            "існуючий-тег",
            "(це-примітив? (як-є (primitive атом?)))",
            true,
        ),
        (
            "конструктор-тег",
            "(це-примітив? (власний-примітив (як-є атом?)))",
            true,
        ),
        (
            "конструктор-інше-ім'я",
            "(це-примітив? (власний-примітив (як-є перше)))",
            true,
        ),
        (
            "сам-тег-у-списку",
            "(це-примітив? (як-є (primitive)))",
            true,
        ),
        (
            "замикання-не-примітив",
            "(це-примітив? (як-є (closure атом?)))",
            false,
        ),
        (
            "рекурсивне-замикання-не-примітив",
            "(це-примітив? (як-є (recursive-closure атом?)))",
            false,
        ),
        (
            "подібний-тег-не-примітив",
            "(це-примітив? (як-є (primitive-other атом?)))",
            false,
        ),
        (
            "порожній-список-не-примітив",
            "(це-примітив? (як-є ()))",
            false,
        ),
        (
            "атом-не-примітив",
            "(це-примітив? (як-є primitive))",
            false,
        ),
    ] {
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=d11-primitive-tag-{case} layer=SENS input={source} actual=error:{error}"
            )).value;
        assert_eq!(
            result.as_predicate_bit(), Some(expected),
            "test_id=d11-primitive-tag-{case} layer=SENS input={source} expected=D1:{expected} actual={result}"
        );
    }

    // Незалежний свідок власне побудови даних — не тільки предиката.
    // Обидві частини порівняння отримані через SENS.
    for (case, source, expected_source, same) in [
        (
            "ім'я-атом",
            "(власний-примітив (як-є атом?))",
            "(як-є (primitive атом?))",
            true,
        ),
        (
            "ім'я-перше",
            "(власний-примітив (як-є перше))",
            "(як-є (primitive перше))",
            true,
        ),
        (
            "ім'я-невідоме",
            "(власний-примітив (як-є довільне))",
            "(як-є (primitive довільне))",
            true,
        ),
        (
            "не-заміняти-ім'я",
            "(власний-примітив (як-є атом?))",
            "(як-є (primitive перше))",
            false,
        ),
        (
            "не-підміняти-тег",
            "(власний-примітив (як-є атом?))",
            "(як-є (closure атом?))",
            false,
        ),
    ] {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=d11-primitive-constructor-{case} layer=SENS input={source} actual=error:{error}"
            )).value;
        let expected = eval_program(expected_source, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=d11-primitive-constructor-{case} layer=SENS expected_source={expected_source} actual=error:{error}"
            )).value;
        assert_eq!(
            actual == expected, same,
            "test_id=d11-primitive-constructor-{case} layer=SENS input={source} expected_source={expected_source} expected_equal={same} actual={actual}"
        );
    }


    // Конструкція реальної позначки через SENS CONS (сполучити 0 ...).
    // Цитований текстовий 0 не прирівнюємо до виконуваного коду 0:
    // його область та тотожність не гарантовано збігаються.
    // Значення та D1 результати обчислюються лише SENS.
    for (case, source, expected) in [
        ("позначка-кадру", "(зв'язування-спільного-кадру? (сполучити 0 (як-є (а б))))", true),
        ("звичайне-зв'язування", "(зв'язування-спільного-кадру? (як-є (ім'я а б)))", false),
        ("атом-не-кадр", "(зв'язування-спільного-кадру? (як-є ім'я))", false),
        ("порожнє-не-кадр", "(зв'язування-спільного-кадру? (як-є ()))", false),
        ("порожнє-оточення", "(оточення-має-спільний-кадр? (як-є ()))", false),
        ("лише-звичайні", "(оточення-має-спільний-кадр? (як-є ((а б) (в г))))", false),
        ("кадр-на-початку", "(оточення-має-спільний-кадр? (сполучити (сполучити 0 (як-є (б))) (сполучити (як-є (а б)) (як-є ()))))", true),
        ("кадр-в-середині", "(оточення-має-спільний-кадр? (сполучити (як-є (а б)) (сполучити (сполучити 0 (як-є (в))) (сполучити (як-є (г д)) (як-є ())))))", true),
        ("кадр-наприкінці", "(оточення-має-спільний-кадр? (сполучити (як-є (а б)) (сполучити (як-є (в г)) (сполучити (сполучити 0 (як-є (д))) (як-є ())))))", true),
    ] {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("test_id=d11-shared-frame-{case} layer=SENS input={source} actual=error:{error}")).value;
        assert_eq!(actual.as_predicate_bit(), Some(expected),
            "test_id=d11-shared-frame-{case} layer=SENS input={source} expected=D1:{expected} actual={actual}");
    }

    for (case, source, expected_source, equal) in [
        ("значення-порожнього", "(значення-спільного-кадру (як-є ()))", "(як-є ())", true),
        ("значення-без-кадру", "(значення-спільного-кадру (як-є ((а б) (в г))))", "(як-є ())", true),
        ("значення-першого", "(значення-спільного-кадру (сполучити (сполучити 0 (як-є (а б))) (сполучити (як-є (в г)) (як-є ()))))", "(як-є (а б))", true),
        ("значення-внутрішнього", "(значення-спільного-кадру (сполучити (як-є (а б)) (сполучити (сполучити 0 (як-є (в г))) (сполучити (як-є (г д)) (як-є ())))))", "(як-є (в г))", true),
        ("значення-першого-з-двох", "(значення-спільного-кадру (сполучити (сполучити 0 (як-є (а))) (сполучити (сполучити 0 (як-є (б))) (як-є ()))))", "(як-є (а))", true),
        ("другий-не-витісняє-першого", "(значення-спільного-кадру (сполучити (сполучити 0 (як-є (а))) (сполучити (сполучити 0 (як-є (б))) (як-є ()))))", "(як-є (б))", false),
        ("створити-кадр-на-порожньому", "(забезпечити-спільний-кадр (як-є ()))", "(сполучити (сполучити 0 (як-є ())) (як-є ()))", true),
        ("створити-перед-звичайним", "(забезпечити-спільний-кадр (як-є ((а б))))", "(сполучити (сполучити 0 (як-є ())) (сполучити (як-є (а б)) (як-є ())))", true),
        ("наявний-кадр-не-змінити", "(забезпечити-спільний-кадр (сполучити (як-є (а б)) (сполучити (сполучити 0 (як-є (в г))) (як-є ()))))", "(сполучити (як-є (а б)) (сполучити (сполучити 0 (як-є (в г))) (як-є ())))", true),
        ("наявний-кадр-не-дублювати", "(забезпечити-спільний-кадр (сполучити (як-є (а б)) (сполучити (сполучити 0 (як-є (в г))) (як-є ()))))", "(сполучити (сполучити 0 (як-є ())) (сполучити (як-є (а б)) (сполучити (сполучити 0 (як-є (в г))) (як-є ()))))", false),
        ("замінити-порожнє", "(замінити-спільний-кадр (як-є ()) (як-є (новий)))", "(як-є ())", true),
        ("не-чіпати-чужі-зв'язки", "(замінити-спільний-кадр (як-є ((а б) (в г))) (як-є (новий)))", "(як-є ((а б) (в г)))", true),
        ("замінити-перший", "(замінити-спільний-кадр (сполучити (сполучити 0 (як-є (старий))) (сполучити (як-є (а б)) (як-є ()))) (як-є (новий)))", "(сполучити (сполучити 0 (як-є (новий))) (сполучити (як-є (а б)) (як-є ())))", true),
        ("замінити-в-середині", "(замінити-спільний-кадр (сполучити (як-є (а б)) (сполучити (сполучити 0 (як-є (старий))) (сполучити (як-є (в г)) (як-є ())))) (як-є (новий)))", "(сполучити (як-є (а б)) (сполучити (сполучити 0 (як-є (новий))) (сполучити (як-є (в г)) (як-є ()))))", true),
        ("замінити-лише-перший", "(замінити-спільний-кадр (сполучити (сполучити 0 (як-є (а))) (сполучити (сполучити 0 (як-є (б))) (як-є ()))) (як-є (новий)))", "(сполучити (сполучити 0 (як-є (новий))) (сполучити (сполучити 0 (як-є (б))) (як-є ())))", true),
        ("не-чіпати-наступний-кадр", "(замінити-спільний-кадр (сполучити (сполучити 0 (як-є (а))) (сполучити (сполучити 0 (як-є (б))) (як-є ()))) (як-є (новий)))", "(сполучити (сполучити 0 (як-є (новий))) (сполучити (сполучити 0 (як-є (новий))) (як-є ())))", false),
    ] {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("test_id=d11-shared-frame-{case} layer=SENS input={source} actual=error:{error}")).value;
        let expected = eval_program(expected_source, &mut session)
            .unwrap_or_else(|error| panic!("test_id=d11-shared-frame-{case} layer=SENS expected_source={expected_source} actual=error:{error}")).value;
        assert_eq!(actual == expected, equal,
            "test_id=d11-shared-frame-{case} layer=SENS input={source} expected_source={expected_source} equal={equal} actual={actual}");
    }

    // Д11: збереження виду, причини та payload структурованої помилки
    // в живому метаобчислювачі. Обидва значення порівнює host лише
    // після обчислення кожного через SENS (жодної host-семантики).
    for (case, source, reference_source, equal) in [
        (
            "незмінний-канонічний-лямбда",
            "(помилка-незмінності-канонічного-імені (як-є функція))",
            "(як-є (error invalid-form (canonical-name-immutable функція)))",
            true,
        ),
        (
            "незмінний-канонічний-define",
            "(помилка-незмінності-канонічного-імені (як-є визначити))",
            "(як-є (error invalid-form (canonical-name-immutable визначити)))",
            true,
        ),
        (
            "незмінний-канонічний-довільний-символ",
            "(помилка-незмінності-канонічного-імені (як-є невідоме))",
            "(як-є (error invalid-form (canonical-name-immutable невідоме)))",
            true,
        ),
        (
            "незмінний-канонічний-не-змінювати-ім'я",
            "(помилка-незмінності-канонічного-імені (як-є функція))",
            "(як-є (error invalid-form (canonical-name-immutable визначити)))",
            false,
        ),
        (
            "незмінний-канонічний-не-змінювати-вид",
            "(помилка-незмінності-канонічного-імені (як-є функція))",
            "(як-є (error arity (canonical-name-immutable функція)))",
            false,
        ),
        (
            "лямбда-неприпустимий-параметр",
            "(помилка-форми-лямбди (як-є (поганий)))",
            "(як-є (error invalid-form (lambda-parameters поганий)))",
            true,
        ),
        (
            "лямбда-кілька-параметрів",
            "(помилка-форми-лямбди (як-є (поганий другий)))",
            "(як-є (error invalid-form (lambda-parameters поганий другий)))",
            true,
        ),
        (
            "лямбда-порожній-payload",
            "(помилка-форми-лямбди (як-є ()))",
            "(як-є (error invalid-form (lambda-parameters)))",
            true,
        ),
        (
            "лямбда-не-губити-причину",
            "(помилка-форми-лямбди (як-є (поганий)))",
            "(як-є (error invalid-form (lambda-parameters інший)))",
            false,
        ),
        (
            "лямбда-не-підміняти-причину",
            "(помилка-форми-лямбди (як-є (поганий)))",
            "(як-є (error invalid-form (canonical-name-immutable поганий)))",
            false,
        ),
    ] {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=d11-meta-structured-error-{case} layer=SENS input={source} actual=error:{error}"
            )).value;
        let expected = eval_program(reference_source, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=d11-meta-structured-error-{case} layer=SENS expected_source={reference_source} actual=error:{error}"
            )).value;
        assert_eq!(
            actual == expected, equal,
            "test_id=d11-meta-structured-error-{case} layer=SENS input={source} reference={reference_source} expected_equal={equal} actual={actual}"
        );
    }
}

// Виконуємо оригінальні українські Lisp-свідки графа, не Python таблицю
// й не лише перевірку текстових токенів. Мутант мусить дати D1:0.
#[test]
fn meta_eval_graph_exact_d1_law_and_negative_mutant_execute_in_sens() {
    for (name, source, expected) in [
        (
            "закон",
            include_str!("../../../tests/semantic/meta-eval-graph-d1-law.lisp"),
            true,
        ),
        (
            "мутант",
            include_str!("../../../tests/semantic/meta-eval-graph-d1-mutant.lisp"),
            false,
        ),
    ] {
        let mut session = core_session();
        common::load_meta_evaluator_library(&mut session)
            .expect("MetaEval має завантажитися у справжній SENS");
        let result = eval_program(source, &mut session).unwrap_or_else(|err| {
            panic!("test_id=meta-eval-graph-d1 case={name} actual=execution-error: {err}")
        });
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(expected),
            "test_id=meta-eval-graph-d1 case={name} expected={expected} actual={}",
            result.value,
        );
    }

    // D11: реальні закони двох композицій зі старого MetaEval:
    // залежності-графа та досяжність-залежностей-графа?.
    // Rust лише порівнює дві відповіді справжнього SENS і читає D1.
    let mut session = core_session();
    common::load_meta_evaluator_library(&mut session).expect("дійсний метаобчислювач SENS");
    for (case, actual_source, expected_source) in [
        (
            "перший-запис",
            "(залежності-графа (як-є а) (як-є ((а (б в)) (б (г)))))",
            "(як-є (б в))",
        ),
        (
            "другий-запис",
            "(залежності-графа (як-є б) (як-є ((а (б в)) (б (г)))))",
            "(як-є (г))",
        ),
        (
            "немає-імені",
            "(залежності-графа (як-є г) (як-є ((а (б в)) (б (г)))))",
            "(як-є ())",
        ),
        (
            "порожній-граф",
            "(залежності-графа (як-є а) (як-є ()))",
            "(як-є ())",
        ),
        (
            "перший-дублікат",
            "(залежності-графа (як-є а) (як-є ((а (перший)) (а (другий)))))",
            "(як-є (перший))",
        ),
    ] {
        let actual = eval_program(actual_source, &mut session)
            .unwrap_or_else(|error| panic!("test_id=d11-meta-graph-{case} layer=SENS input={actual_source} actual=error:{error}")).value;
        let expected = eval_program(expected_source, &mut session)
            .unwrap_or_else(|error| panic!("test_id=d11-meta-graph-{case} layer=SENS expected_source={expected_source} actual=error:{error}")).value;
        assert_eq!(
            actual, expected,
            "test_id=d11-meta-graph-{case} layer=SENS input={actual_source} expected_source={expected_source} actual={actual}"
        );
    }

    for (case, source, expected) in [
        (
            "прямий-шлях",
            "(досяжність-залежностей-графа? (як-є (б)) (як-є б) (як-є ()) (як-є ()))",
            true,
        ),
        (
            "один-перехід",
            "(досяжність-залежностей-графа? (як-є (б)) (як-є в) (як-є ((б (в)))) (як-є ()))",
            true,
        ),
        (
            "два-переходи",
            "(досяжність-залежностей-графа? (як-є (б)) (як-є г) (як-є ((б (в)) (в (г)))) (як-є ()))",
            true,
        ),
        (
            "немає-шляху",
            "(досяжність-залежностей-графа? (як-є (б)) (як-є г) (як-є ((б (в)) (в ()))) (як-є ()))",
            false,
        ),
        (
            "порожні-залежності",
            "(досяжність-залежностей-графа? (як-є ()) (як-є г) (як-є ((б (г)))) (як-є ()))",
            false,
        ),
        (
            "цикл-без-цілі",
            "(досяжність-залежностей-графа? (як-є (а)) (як-є г) (як-є ((а (б)) (б (а)))) (як-є ()))",
            false,
        ),
        (
            "відвідану-обійти-інший-шлях-знайти",
            "(досяжність-залежностей-графа? (як-є (а в)) (як-є г) (як-є ((в (г)))) (як-є (а)))",
            true,
        ),
        (
            "ціль-не-підмінено",
            "(досяжність-залежностей-графа? (як-є (б)) (як-є інша) (як-є ((б (в)) (в (г)))) (як-є ()))",
            false,
        ),
    ] {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("test_id=d11-meta-graph-{case} layer=SENS input={source} actual=error:{error}")).value;
        assert_eq!(
            actual.as_predicate_bit(),
            Some(expected),
            "test_id=d11-meta-graph-{case} layer=SENS input={source} expected=D1:{expected} actual={actual}"
        );
    }

    // D11: конструкція графа із дійсних верхніх Lisp DEFINE, а не host
    // графовий алгоритм. Лексичне затінення і цитата не створюють ребер.
    for (case, source, expected_source) in [
        (
            "імена-порожні",
            "(імена-визначень-лямбди (як-є ()))",
            "(як-є ())",
        ),
        (
            "імена-зберігають-порядок",
            "(імена-визначень-лямбди (як-є ((визначити а (функція (x) x)) (визначити б (функція (x) x)))))",
            "(як-є (а б))",
        ),
        (
            "імена-не-гублять-повтор",
            "(імена-визначень-лямбди (як-є ((визначити а (функція (x) x)) (визначити а (функція (y) y)))))",
            "(як-є (а а))",
        ),
        (
            "граф-порожній",
            "(побудувати-граф-залежностей-за-іменами (як-є ()) (як-є (а б)))",
            "(як-є ())",
        ),
        (
            "граф-одне-ім'я-без-кандидатів",
            "(побудувати-граф-залежностей-за-іменами (як-є ((визначити а (функція (x) (б x))))) (як-є ()))",
            "(як-є ((а ())))",
        ),
        (
            "граф-вільна-залежність",
            "(побудувати-граф-залежностей-за-іменами (як-є ((визначити а (функція (x) (б x))))) (як-є (а б)))",
            "(як-є ((а (б))))",
        ),
        (
            "граф-цитата-не-залежність",
            "(побудувати-граф-залежностей-за-іменами (як-є ((визначити а (функція (x) (як-є (б)))))) (як-є (а б)))",
            "(як-є ((а ())))",
        ),
        (
            "граф-формальний-параметр-не-залежність",
            "(побудувати-граф-залежностей-за-іменами (як-є ((визначити а (функція (б) б)))) (як-є (а б)))",
            "(як-є ((а ())))",
        ),
        (
            "граф-взаємна-рекурсія",
            "(побудувати-граф-залежностей-за-іменами (як-є ((визначити а (функція (x) (б x))) (визначити б (функція (x) (а x))))) (як-є (а б)))",
            "(як-є ((а (б)) (б (а))))",
        ),
        (
            "граф-перший-запис-не-загублено",
            "(побудувати-граф-залежностей-за-іменами (як-є ((визначити а (функція (x) (б x))) (визначити б (функція (x) x)))) (як-є (а б)))",
            "(як-є ((а (б)) (б ())))",
        ),
    ] {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|err| panic!("test_id=d11-define-graph-{case} layer=SENS input={source} error={err}")).value;
        let expected = eval_program(expected_source, &mut session)
            .unwrap_or_else(|err| panic!("test_id=d11-define-graph-{case} layer=SENS expected_source={expected_source} error={err}")).value;
        assert_eq!(actual, expected,
            "test_id=d11-define-graph-{case} layer=SENS input={source} expected_source={expected_source} actual={actual}");
    }

    // D11: сильна компонента означає *взаємну* досяжність, не
    // односторонню. Ці D1 / структурні результати обчислює сам SENS.
    for (case, source, expected_source) in [
        (
            "немає-кандидатів",
            "(імена-сильно-зв'язаної-компоненти (як-є а) (як-є ()) (як-є ()))",
            "(як-є ())",
        ),
        (
            "сам-у-власній-компоненті",
            "(імена-сильно-зв'язаної-компоненти (як-є а) (як-є (а)) (як-є ((а ()))))",
            "(як-є (а))",
        ),
        (
            "двостороння-компонента",
            "(імена-сильно-зв'язаної-компоненти (як-є а) (як-є (а б)) (як-є ((а (б)) (б (а)))))",
            "(як-є (а б))",
        ),
        (
            "односторонній-зв'язок-недостатній",
            "(імена-сильно-зв'язаної-компоненти (як-є а) (як-є (а б)) (як-є ((а (б)) (б ()))))",
            "(як-є (а))",
        ),
        (
            "транзитивна-взаємність",
            "(імена-сильно-зв'язаної-компоненти (як-є а) (як-є (а б в)) (як-є ((а (б)) (б (в)) (в (а)))))",
            "(як-є (а б в))",
        ),
        (
            "незалежний-вузол-не-учасник",
            "(імена-сильно-зв'язаної-компоненти (як-є а) (як-є (а б в)) (як-є ((а (б)) (б (а)) (в ()))))",
            "(як-є (а б))",
        ),
        (
            "обхід-не-переставляє-кандидатів",
            "(імена-сильно-зв'язаної-компоненти (як-є а) (як-є (в б а)) (як-є ((а (б)) (б (а)) (в ()))))",
            "(як-є (б а))",
        ),
    ] {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|err| panic!("test_id=d11-strong-component-{case} layer=SENS input={source} error={err}")).value;
        let expected = eval_program(expected_source, &mut session)
            .unwrap_or_else(|err| panic!("test_id=d11-strong-component-{case} layer=SENS expected_source={expected_source} error={err}")).value;
        assert_eq!(actual, expected,
            "test_id=d11-strong-component-{case} layer=SENS input={source} expected_source={expected_source} actual={actual}");
    }
}

// Шістнадцять окремих семантичних результатів від живого SENS.
// Неперевірений статичний Python-збіг не може задовольнити цей тест.
#[test]
fn meta_eval_lexical_eight_laws_and_eight_mutants_execute_in_sens() {
    fn forms(source: &str) -> Vec<&str> {
        source
            .lines()
            .map(str::trim)
            .filter(|line| !line.is_empty() && !line.starts_with(';'))
            .collect()
    }
    let laws = forms(include_str!(
        "../../../tests/semantic/meta-eval-lexical-shadow-d1-law.lisp"
    ));
    let mutants = forms(include_str!(
        "../../../tests/semantic/meta-eval-lexical-shadow-d1-mutants.lisp"
    ));
    let first = forms(include_str!(
        "../../../tests/semantic/meta-eval-lexical-shadow-d1-mutant.lisp"
    ));
    assert_eq!((laws.len(), mutants.len(), first.len()), (8, 8, 8));
    assert_eq!(first[0], mutants[0]);
    assert_eq!(&first[1..], &laws[1..]);
    let mut session = core_session();
    common::load_meta_evaluator_library(&mut session).expect("живе українське визначення MetaEval");
    for (index, (law, mutant)) in laws.iter().zip(mutants.iter()).enumerate() {
        for (case, source, expected) in [("закон", *law, true), ("мутант", *mutant, false)]
        {
            let result = eval_program(source, &mut session).unwrap_or_else(|error| {
                panic!(
                    "test_id=meta-eval-lexical-shadow-d1 case={} role={case} SENS: {error}",
                    index + 1
                )
            });
            assert_eq!(
                result.value.as_predicate_bit(),
                Some(expected),
                "test_id=meta-eval-lexical-shadow-d1 case={} role={case} input={source}",
                index + 1
            );
        }
    }
}

// D10:0101100100: запускається справжній метаобчислювач SENS,
// а не Python/Rust реалізація семантики тіл LAMBDA.
#[test]
fn meta_eval_body_result_observes_last_form_and_early_failure() {
    let mut session = core_session();
    common::load_meta_evaluator_library(&mut session).expect("дійсний SENS MetaEval");

    // До виправлення перша форма помилково ставала остаточним результатом.
    assert_eq!(
        execute(
            &mut session,
            "(решта (обчислити-послідовне-тіло-з-раннім-збоєм (як-є (1 2)) (як-є ())))"
        ),
        "2"
    );

    // Перша помилка припиняє обчислення, не повертаючи успіх наступної форми.
    assert_eq!(
        execute(
            &mut session,
            "(це-результат-невдалого-обчислення? (обчислити-послідовне-тіло-з-раннім-збоєм (як-є (невідоме-імя 2)) (як-є ())))"
        ),
        execute(&mut session, "(атом? (як-є а))")
    );
}
