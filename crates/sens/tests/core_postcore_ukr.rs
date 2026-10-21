//! Живе виконання виправлених post-core функцій через справжній SENS evaluator.
//! Не підмінює семантику Rust або Python; Rust лише викликає SENS та звіряє результат.
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
    sens::eval_core_library_source(
        include_str!("../../../lib/core.lisp"),
        &mut session,
    )
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

// Реальний D1-свідок Core4: порівняння проходить УСІ елементи списку.
// До ремонту перша гілка повертала істину вже для непорожнього хвоста.
#[test]
fn core_order_predicates_recurse_until_empty_tail_in_sens() {
    let mut session = core_session();
    for (source, expected) in [
        ("(перевірити-неспадання-значень? 1 (як-є ()))", true),
        ("(перевірити-неспадання-значень? 1 (як-є (1 2)))", true),
        ("(перевірити-неспадання-значень? 1 (як-є (2 1)))", false),
        ("(перевірити-неспадання-значень? 2 (як-є (1)))", false),
        ("(перевірити-незростання-значень? 2 (як-є ()))", true),
        ("(перевірити-незростання-значень? 2 (як-є (2 1)))", true),
        ("(перевірити-незростання-значень? 2 (як-є (1 2)))", false),
        ("(перевірити-незростання-значень? 1 (як-є (2)))", false),
    ] {
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("SENS-виконання {source}: {error}"));
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(expected),
            "test_id=core4-order-d1 input={source} expected={expected} actual={}",
            result.value
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
        execute(&mut session,
            &format!("(стан-привязки-відповідника (як-є другий) {bindings})")),
        "present"
    );
    assert_eq!(
        execute(&mut session,
            &format!("(стан-привязки-відповідника (як-є третій) {bindings})")),
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
        execute(&mut session,
            "(побудувати-визначення-відповідників (як-є джерело) (як-є (перший другий)))"),
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
        execute(&mut session,
            "(підставити-пари (список (сполучити (як-є а) (як-є б))) (як-є (а в а)))"),
        execute(&mut session, "(як-є (б в б))")
    );
    assert_eq!(
        execute(&mut session,
            "(підставити-пари (список (сполучити (як-є (а в)) (як-є ціле))) (як-є (а в)))"),
        execute(&mut session, "(як-є ціле)")
    );
    assert_eq!(
        execute(&mut session,
            "(відобразити-залишки (як-є (а б)) (функція (хвіст) (перше хвіст)))"),
        execute(&mut session, "(як-є (а б))")
    );
}


// Живий SENS-метаобчислювач: атомарні мітки даних і справжні
// складені замикання мають повертати біт D1, не Lisp-символ "так"/"ні".
#[test]
fn meta_eval_predicates_are_actual_d1_bits() {
    let mut session = core_session();
    sens::load_meta_evaluator_library(&mut session)
        .expect("чинний український MetaEval має виконуватися в SENS");
    let cases = [
        ("(це-макрос? (як-є приклад))", false),
        ("(це-макрос? (як-є (macro приклад)))", true),
        ("(це-замикання? (як-є приклад))", false),
        ("(це-замикання? (як-є (closure приклад)))", true),
        ("(це-рекурсивне-замикання? (як-є приклад))", false),
        ("(це-рекурсивне-замикання? (як-є (recursive-closure приклад)))", true),
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
}

// Виконуємо оригінальні українські Lisp-свідки графа, не Python таблицю
// й не лише перевірку текстових токенів. Мутант мусить дати D1:0.
#[test]
fn meta_eval_graph_exact_d1_law_and_negative_mutant_execute_in_sens() {
    for (name, source, expected) in [
        ("закон", include_str!("../../../tests/semantic/meta-eval-graph-d1-law.lisp"), true),
        ("мутант", include_str!("../../../tests/semantic/meta-eval-graph-d1-mutant.lisp"), false),
    ] {
        let mut session = core_session();
        sens::load_meta_evaluator_library(&mut session)
            .expect("MetaEval має завантажитися у справжній SENS");
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|err| panic!("test_id=meta-eval-graph-d1 case={name} actual=execution-error: {err}"));
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(expected),
            "test_id=meta-eval-graph-d1 case={name} expected={expected} actual={}",
            result.value,
        );
    }
}

// Шістнадцять окремих семантичних результатів від живого SENS.
// Неперевірений статичний Python-збіг не може задовольнити цей тест.
#[test]
fn meta_eval_lexical_eight_laws_and_eight_mutants_execute_in_sens() {
    fn forms(source: &str) -> Vec<&str> {
        source.lines()
            .map(str::trim)
            .filter(|line| !line.is_empty() && !line.starts_with(';'))
            .collect()
    }
    let laws = forms(include_str!("../../../tests/semantic/meta-eval-lexical-shadow-d1-law.lisp"));
    let mutants = forms(include_str!("../../../tests/semantic/meta-eval-lexical-shadow-d1-mutants.lisp"));
    let first = forms(include_str!("../../../tests/semantic/meta-eval-lexical-shadow-d1-mutant.lisp"));
    assert_eq!((laws.len(), mutants.len(), first.len()), (8, 8, 8));
    assert_eq!(first[0], mutants[0]);
    assert_eq!(&first[1..], &laws[1..]);
    let mut session = core_session();
    sens::load_meta_evaluator_library(&mut session)
        .expect("живе українське визначення MetaEval");
    for (index, (law, mutant)) in laws.iter().zip(mutants.iter()).enumerate() {
        for (case, source, expected) in [("закон", *law, true), ("мутант", *mutant, false)] {
            let result = eval_program(source, &mut session)
                .unwrap_or_else(|error| panic!(
                    "test_id=meta-eval-lexical-shadow-d1 case={} role={case} SENS: {error}",
                    index + 1
                ));
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
    sens::load_meta_evaluator_library(&mut session).expect("дійсний SENS MetaEval");

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
