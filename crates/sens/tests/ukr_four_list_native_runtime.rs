//! Живі українські D3/D4 програми: виконання, а не підрахунок назв чи Python-oracle.
//! Обидва вихідні Lisp є власними композиціями ратифікованих CAR/CDR/CONS.
//! Позитив і адресна помилка мутації перевіряються в справжній SENS-сесії.
use sens::{eval_program, Session};

fn execute_with_negative(source_name: &str, source: &str, original: &str, changed: &str) {
    assert_eq!(
        source.matches(original).count(),
        1,
        "test_id=ukr-four-list layer=fixture source={source_name} expected=unique-mutation-site"
    );
    // D3/D4 та DEFINE/FUNCTION вже є в чинному SENS; повний історичний
    // Core4 не потрібен для цих самостійних виконуваних програм.
    let mut session = Session::default();
    let expected = eval_program("(атом? (як-є ()))", &mut session)
        .expect("native D1:так")
        .value;
    let actual = eval_program(source, &mut session)
        .unwrap_or_else(|error| {
            panic!(
                "test_id=ukr-four-list layer=SENS source={source_name} case=positive error={error}"
            )
        })
        .value;
    assert_eq!(
        actual, expected,
        "test_id=ukr-four-list layer=SENS source={source_name} case=positive expected=D1:так"
    );

    // Псуємо саме закон перестановки, не синтаксис, не доменні таблиці.
    // Негатив запускається іншою реальною SENS-сесією, не Rust-інтерпретатором.
    let mutant = source.replacen(original, changed, 1);
    let mut negative_session = Session::default();
    match eval_program(&mutant, &mut negative_session) {
        Ok(value) => assert_ne!(
            value.value, expected,
            "test_id=ukr-four-list layer=SENS source={source_name} case=mutant expected=non-true actual=D1:так"
        ),
        Err(_) => {} // Дозволене семантичне відхилення хибної гілки, а не PASS мутації.
    }
}

#[test]
fn replace_third_preserves_first_second_fourth_and_rejects_old_third() {
    execute_with_negative(
        "lib/замінити-третій-в-четвірці.lisp",
        include_str!("../../../lib/замінити-третій-в-четвірці.lisp"),
        "(сполучити новий (решта (решта (решта елементи))))",
        "(сполучити (як-є решта) (решта (решта (решта елементи))))",
    );
}

#[test]
fn swap_second_third_preserves_outer_positions_and_rejects_identity_swap() {
    execute_with_negative(
        "lib/поміняти-другий-і-третій.lisp",
        include_str!("../../../lib/поміняти-другий-і-третій.lisp"),
        "(перше (решта (решта четвірка)))",
        "(перше (решта четвірка))",
    );
}

#[test]
fn pair_swap_executes_car_cdr_involution_and_rejects_identity() {
    execute_with_negative(
        "lib/pair-swap.lisp",
        include_str!("../../../lib/pair-swap.lisp"),
        "(сполучити (решта пара) (перше пара))",
        "(сполучити (перше пара) (решта пара))",
    );
}

#[test]
fn pair_replace_first_executes_tail_preservation_and_rejects_old_head() {
    execute_with_negative(
        "lib/pair-replace-first.lisp",
        include_str!("../../../lib/pair-replace-first.lisp"),
        "(сполучити нове (решта пара))",
        "(сполучити (перше пара) (решта пара))",
    );
}

#[test]
fn pair_replace_rest_executes_head_preservation_and_rejects_old_tail() {
    execute_with_negative(
        "lib/pair-replace-rest.lisp",
        include_str!("../../../lib/pair-replace-rest.lisp"),
        "(сполучити (перше пара) новий-хвіст)",
        "(сполучити (перше пара) (решта пара))",
    );
}

#[test]
fn interleave_pairs_executes_four_positions_and_rejects_duplicate_second() {
    execute_with_negative(
        "lib/interleave-pairs.lisp",
        include_str!("../../../lib/interleave-pairs.lisp"),
        "(перше друга-пара)",
        "(перше перша-пара)",
    );
}

#[test]
fn zip_unzip_two_executes_inverse_and_rejects_swapped_pair() {
    execute_with_negative(
        "lib/pair-zip-unzip-two.lisp",
        include_str!("../../../lib/pair-zip-unzip-two.lisp"),
        "(сполучити (перше ліві) (перше праві))",
        "(сполучити (перше праві) (перше ліві))",
    );
}

#[test]
fn delete_second_executes_removal_and_rejects_unchanged_list() {
    execute_with_negative(
        "lib/list-delete-second.lisp",
        include_str!("../../../lib/list-delete-second.lisp"),
        "(сполучити (перше елементи) (решта-решти елементи))",
        "(сполучити (перше елементи) (решта елементи))",
    );
}

#[test]
fn insert_second_executes_insertion_and_rejects_duplicate_first() {
    execute_with_negative(
        "lib/list-insert-second.lisp",
        include_str!("../../../lib/list-insert-second.lisp"),
        "(сполучити вставлене (решта елементи))",
        "(сполучити (перше елементи) (решта елементи))",
    );
}

#[test]
fn swap_neighbors_four_executes_involution_and_rejects_duplicate_first() {
    execute_with_negative(
        "lib/list-swap-neighbors-four.lisp",
        include_str!("../../../lib/list-swap-neighbors-four.lisp"),
        "(друге четвірка)",
        "(перше четвірка)",
    );
}

#[test]
fn swap_middle_four_executes_involution_and_rejects_duplicate_second() {
    execute_with_negative(
        "lib/list-swap-middle-four.lisp",
        include_str!("../../../lib/list-swap-middle-four.lisp"),
        "(перше (решта-решти четвірка))",
        "(друге четвірка)",
    );
}

#[test]
fn reverse_four_executes_double_inverse_and_rejects_wrong_first() {
    execute_with_negative(
        "lib/list-reverse-four.lisp",
        include_str!("../../../lib/list-reverse-four.lisp"),
        "(перше (решта (решта (решта елементи))))",
        "(перше елементи)",
    );
}

#[test]
fn halfturn_four_executes_double_inverse_and_rejects_wrong_first() {
    execute_with_negative(
        "lib/list-halfturn-four.lisp",
        include_str!("../../../lib/list-halfturn-four.lisp"),
        "(перше (решта (решта елементи)))",
        "(перше елементи)",
    );
}

#[test]
fn rotate_five_by_two_executes_inverse_and_rejects_identity() {
    execute_with_negative(
        "lib/list-rotate-five-by-two.lisp",
        include_str!("../../../lib/list-rotate-five-by-two.lisp"),
        "(список (перше (решта (решта елементи)))",
        "(список (перше елементи)",
    );
}

#[test]
fn rotate_four_left_executes_fourfold_inverse_and_rejects_identity() {
    execute_with_negative(
        "lib/rotate-four-left.lisp",
        include_str!("../../../lib/rotate-four-left.lisp"),
        "(друге елементи)",
        "(перше елементи)",
    );
}

#[test]
fn rotate_four_right_executes_fourfold_inverse_and_rejects_identity() {
    execute_with_negative(
        "lib/rotate-four-right.lisp",
        include_str!("../../../lib/rotate-four-right.lisp"),
        "(друге (решта-решти елементи))",
        "(перше елементи)",
    );
}

#[test]
fn replace_fourth_executes_preservation_and_rejects_corrupted_third() {
    execute_with_negative(
        "lib/list-replace-fourth.lisp",
        include_str!("../../../lib/list-replace-fourth.lisp"),
        "(третє четвірка)",
        "(друге четвірка)",
    );
}

#[test]
fn rotate_three_right_executes_exact_d3_without_append_dependency() {
    execute_with_negative(
        "lib/rotate-three-right.lisp",
        include_str!("../../../lib/rotate-three-right.lisp"),
        "(перше (решта-решти елементи))",
        "(перше елементи)",
    );
}

// Історичні спискові закони: тільки власні SENS-композиції з lib/list-*.
// Це не доказ руйнівних MACLISP NCONC/NREVERSE і не нові D11 opcodes.
// Негативи змінюють сам алгоритм, а не текст очікуваної відповіді.
#[test]
fn historical_subset_by_position_preserves_order_and_duplicate_choices() {
    execute_with_negative(
        "lib/list-all-subsets-by-position-general.lisp",
        include_str!("../../../lib/list-all-subsets-by-position-general.lisp"),
        "(зєднати-списки-підмножин\n      підмножини-хвоста\n      (додати-голову-до-всіх-підмножин голова підмножини-хвоста))",
        "(зєднати-списки-підмножин\n      (додати-голову-до-всіх-підмножин голова підмножини-хвоста)\n      підмножини-хвоста)",
    );
}

#[test]
fn historical_stable_union_preserves_first_occurrences_not_destructive_nconc() {
    execute_with_negative(
        "lib/list-stable-union-general.lisp",
        include_str!("../../../lib/list-stable-union-general.lisp"),
        "(зберегти-унікальні-атоми праві\n      (зберегти-унікальні-атоми ліві (як-є ())))",
        "(зберегти-унікальні-атоми ліві\n      (зберегти-унікальні-атоми праві (як-є ())))",
    );
}

#[test]
fn historical_stable_symmetric_difference_keeps_multiplicity_and_order() {
    execute_with_negative(
        "lib/list-stable-symmetric-difference-general.lisp",
        include_str!("../../../lib/list-stable-symmetric-difference-general.lisp"),
        // Міняємо єдиний справжній виклик, а не його відступи.
        // Два праві фільтри порушують симетричну різницю у живому SENS.
        "(лише-один-бік ліві праві)",
        "(лише-один-бік праві ліві)",
    );
}

#[test]
fn sixth_atomic_tail_skips_compounds_and_preserves_original_suffix() {
    // D3/D5 algorithm and all positive laws execute in a real SENS session.
    // The mutant skips one atomic position; it cannot satisfy the same laws.
    execute_with_negative(
        "lib/list-tail-after-sixth-atom-zero-copy-general.lisp",
        include_str!("../../../lib/list-tail-after-sixth-atom-zero-copy-general.lisp"),
        "((атом? (перше елементи)) (хвіст-після-пяти-для-шостого (решта елементи)))",
        "((атом? (перше елементи)) (хвіст-після-чотирьох-для-шостого (решта елементи)))",
    );
}

#[test]
fn bija3_1968_atom_null_partial_law_executes_and_rejects_false_generator() {
    // Українська проєкція виконується реальною SENS-сесією.
    // Мутант прибирає уточнення EQ(x, NIL): непорожній атом починає
    // помилково проходити як порожній, і СЕНС виконує CAR NIL.
    execute_with_negative(
        "tests/semantic/біджа3-уточнення-атома-1968.lisp",
        include_str!("../../../tests/semantic/біджа3-уточнення-атома-1968.lisp"),
        "(тотожне? значення (як-є ()))",
        "(атом? значення)",
    );

    // Два позитивні керувальні випадки: саме Д1:так/ні придатні COND.
    for (case, program, expected) in [
        (
            "Д1-так",
            "(за-умовою ((атом? (як-є ())) (як-є підтверджено)))",
            "підтверджено",
        ),
        (
            "Д1-ні-та-так",
            "(за-умовою ((тотожне? (як-є атом?) (як-є решта)) (як-є помилка)) ((атом? (як-є ())) (як-є підтверджено)))",
            "підтверджено",
        ),
    ] {
        let mut session = Session::default();
        let observed = eval_program(program, &mut session).unwrap_or_else(|error| {
            panic!("test_id=1968-D1-COND-{case} layer=SENS input={program} expected={expected} actual_error={error}")
        });
        assert_eq!(
            observed.value.to_string(),
            expected,
            "test_id=1968-D1-COND-{case} layer=SENS input={program} expected={expected}"
        );
    }

    // Контракт #3161: D3:000 — не D1:0, проте COND пропускає
    // обидва як різні причини невибору. Виконання хибної гілки
    // має залишатися неможливим (у ній CAR від порожнього).
    for (case, condition) in [
        ("структурне-без-свідка", "(як-є ())"),
        ("д1-ні", "ні"),
    ] {
        let source = format!(
            "(за-умовою ({condition} (перше (як-є ()))) (так (як-є підтверджено)))"
        );
        let mut session = Session::default();
        let value = eval_program(&source, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=1968-D1-COND-{case} layer=SENS input={source} actual_error={error}"
            ))
            .value;
        assert_eq!(
            value.to_string(),
            "підтверджено",
            "test_id=1968-D1-COND-{case} layer=SENS expected=підтверджено actual={value}"
        );
    }

    // Математичний нуль або сторонній символ не є D1 чи D3:000.
    // Відхилення повинне бути саме доменною помилкою SENS COND,
    // а не побічною помилкою синтаксису або невизначеної функції.
    for (case, source) in [
        ("математичний-нуль", "(за-умовою (0 (як-є неправильно)))"),
        ("сторонній-атом", "(за-умовою ((як-є сторонній) (як-є неправильно)))"),
    ] {
        let mut session = Session::default();
        let error = eval_program(source, &mut session)
            .expect_err("SENS COND не має приймати чужий домен");
        let diagnostic = error.to_string();
        assert!(
            diagnostic.contains("D3:110 COND expects exact D1"),
            "test_id=1968-D1-COND-{case} layer=SENS input={source} expected=typed_domain_rejection actual_error={diagnostic}"
        );
    }
}
