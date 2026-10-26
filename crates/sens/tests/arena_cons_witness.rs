//! Свідок: арена як BACKING-STORE для `cons` на єдиному шві `cons_values`
//! (`crates/sens/src/eval/special_forms/core.rs`).
//!
//! Тест виконує РЕАЛЬНУ SENS-програму — побудову списку вкладеними `cons` і
//! обхід його `car`/`cdr` — і доводить:
//!   1) за увімкненого перемикача арени результат біт-у-біт той самий, що й без
//!      арени (та сама програма, той самий список);
//!   2) шов `cons` справді обслуговує арена: кожен `cons` народжує комірку в
//!      арені, а значення читається назад крізь арену;
//!   3) колектор збирає саме недосяжне з коренів, а досяжне лишається живим.

use sens::{eval_program, load_core_library, Session, Value};

/// Побудова списку `(1 2 3)` вкладеними `cons` і обхід його `car`/`cdr`.
const BUILD_AND_WALK: &str = "
    (define lst (cons 1 (cons 2 (cons 3 ()))))
    (car (cdr (cdr lst)))
";

/// Список, що стане недосяжним: його результат ніде не втримується.
const UNREACHABLE: &str = "(cons 8 (cons 9 ()))";

fn session(arena: bool) -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("Core4 loads");
    if arena {
        session.environment = session.environment.clone().with_arena_cons();
    }
    session
}

#[test]
fn arena_backs_cons_on_the_real_eval_path_and_collects_the_unreachable() {
    // ── Еталон: та сама SENS-програма БЕЗ арени ──
    let mut off = session(false);
    let base_walk = eval_program(BUILD_AND_WALK, &mut off).expect("baseline builds and walks");
    let base_lst = off.environment.get("lst").expect("lst is bound");
    assert!(matches!(base_lst, Value::Pair(_)));
    assert_eq!(base_walk.value.to_string(), "3");
    assert_eq!(base_lst.to_string(), "(1 2 3)");

    // ── Та сама програма З ареною ──
    let mut on = session(true);
    let walk = eval_program(BUILD_AND_WALK, &mut on).expect("arena session builds and walks");
    let lst = on.environment.get("lst").expect("lst is bound");

    // (1) Біт-у-біт: той самий результат обходу й той самий список.
    assert_eq!(walk.value, base_walk.value, "обхід мусить бути біт-у-біт однаковий");
    assert_eq!(walk.value.to_string(), base_walk.value.to_string());
    assert_eq!(lst, base_lst, "список мусить бути біт-у-біт однаковий");
    assert_eq!(lst.to_string(), "(1 2 3)");

    // (2) Шов cons обслуговує арена: три cons — три комірки.
    assert_eq!(
        on.environment.arena_len(),
        3,
        "три cons мусять дати рівно три комірки арени"
    );
    assert!(on.environment.arena_backs(&lst), "список мусить опиратися на арену");
    assert_eq!(on.environment.arena_reachable_count(std::slice::from_ref(&lst)), 3);

    // ── Друга SENS-програма будує список, що стає недосяжним ──
    let dropped = eval_program(UNREACHABLE, &mut on)
        .expect("garbage list builds")
        .value;
    assert!(matches!(dropped, Value::Pair(_)));
    assert!(on.environment.arena_backs(&dropped));
    assert_eq!(on.environment.arena_len(), 5, "плюс два cons другої програми");
    assert_eq!(on.environment.arena_reachable_count(std::slice::from_ref(&lst)), 3);
    assert_eq!(on.environment.arena_garbage_count(std::slice::from_ref(&lst)), 2);

    // (3) Колектор збирає саме недосяжне з коренів.
    let swept = on.environment.arena_collect(std::slice::from_ref(&lst));
    assert_eq!(swept, 2, "недосяжний список мусить бути вигрібений");
    assert!(on.environment.arena_backs(&lst), "досяжний список лишається живим");
    assert!(!on.environment.arena_backs(&dropped), "недосяжний список вигрібено");
    assert_eq!(on.environment.arena_reachable_count(std::slice::from_ref(&lst)), 3);
    assert_eq!(on.environment.arena_garbage_count(std::slice::from_ref(&lst)), 0);
}
