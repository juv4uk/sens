//! D11 00001010111: бібліотечний закон структурованої помилки арності.
//! Лише чинний MetaEval SENS визначає відповідь; Rust звіряє точний D1.
//! Дослідна координата не є ратифікованим машинним викликом.

mod common;

use sens::{eval_program, load_core_library, Session};

#[test]
fn d11_помилка_арності_мета_зберігає_очікувану_й_одержану_арність() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("ядро SENS");
    common::load_meta_evaluator_library(&mut session).expect("живий MetaEval SENS");

    // Очікуване дерево складається засобами SENS: математичні лічильники
    // лишаються D24+, а не цитованими текстовими мітками.
    for (id, source, expected) in [
        (
            "порожні",
            "(однакові? (помилка-арності-мета (як-є ()) (як-є ())) (список (як-є error) (як-є arity) (список (як-є expected) (список (як-є exact) 0) (як-є received) 0)))",
            true,
        ),
        (
            "один-без-аргументів",
            "(однакові? (помилка-арності-мета (як-є (х)) (як-є ())) (список (як-є error) (як-є arity) (список (як-є expected) (список (як-є exact) 1) (як-є received) 0)))",
            true,
        ),
        (
            "два-один",
            "(однакові? (помилка-арності-мета (як-є (х у)) (як-є (а))) (список (як-є error) (як-є arity) (список (як-є expected) (список (як-є exact) 2) (як-є received) 1)))",
            true,
        ),
        (
            "два-три",
            "(однакові? (помилка-арності-мета (як-є (х у)) (як-є (а б в))) (список (як-є error) (як-є arity) (список (як-є expected) (список (як-є exact) 2) (як-є received) 3)))",
            true,
        ),
        (
            "неправильна-очікувана",
            "(однакові? (помилка-арності-мета (як-є (х у)) (як-є (а))) (список (як-є error) (як-є arity) (список (як-є expected) (список (як-є exact) 1) (як-є received) 1)))",
            false,
        ),
        (
            "неправильна-одержана",
            "(однакові? (помилка-арності-мета (як-є (х у)) (як-є (а))) (список (як-є error) (як-є arity) (список (як-є expected) (список (як-є exact) 2) (як-є received) 2)))",
            false,
        ),
    ] {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|error| {
                panic!("test_id=D11-META-ARITY-{id} layer=SENS input={source} error={error}")
            })
            .value;
        assert_eq!(
            actual.as_predicate_bit(),
            Some(expected),
            "test_id=D11-META-ARITY-{id} layer=SENS input={source} expected=D1:{expected} actual={actual}"
        );
    }
}
