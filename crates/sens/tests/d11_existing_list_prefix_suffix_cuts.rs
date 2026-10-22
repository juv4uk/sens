//! Наявні українські бібліотечні програми: повні префікси, суфікси й усі розрізи.
//! Тут перевіряються дійсні SENS-визначення і конкретні закони на D1.
//! Rust лише запускає eval_program і звіряє D1; не реалізує семантику.
//! НЕ ратифікація 11-бітних опкодів і НЕ твердження про фізичну T5M-пару.

use sens::{eval_program, load_core_library, Session};

#[test]
fn d11_prefixes_preserve_order_and_empty_boundary() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("завантажити чинне ядро SENS");
    eval_program(include_str!("../../../lib/list-all-prefixes-general.lisp"), &mut session)
        .expect("визначення та власні свідки спискової бібліотеки SENS");
    for (id, program, expected) in [
        ("порожній", r#"(однакові? (усі-префікси (як-є ())) (як-є (())))"#, true),
        ("один", r#"(однакові? (усі-префікси (як-є (а))) (як-є (() (а))))"#, true),
        ("два", r#"(однакові? (усі-префікси (як-є (а б))) (як-є (() (а) (а б))))"#, true),
        ("три", r#"(однакові? (усі-префікси (як-є (а б в))) (як-є (() (а) (а б) (а б в))))"#, true),
        ("повтори", r#"(однакові? (усі-префікси (як-є (а а))) (як-є (() (а) (а а))))"#, true),
        ("зворотний-порядок", r#"(однакові? (усі-префікси (як-є (а б))) (як-є ((а б) (а) ())))"#, false),
        ("без-порожнього", r#"(однакові? (усі-префікси (як-є (а б))) (як-є ((а) (а б))))"#, false),
        ("не-суфікси", r#"(однакові? (усі-префікси (як-є (а б))) (як-є (() (б) (а б))))"#, false),
    ] {
        let actual = eval_program(program, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=D11-LIST-d11_prefixes_preserve_order_and_empty_boundary-{id} layer=SENS input={program} expected=D1:{expected} actual_error={error}"
            )).value;
        assert_eq!(actual.as_predicate_bit(), Some(expected),
            "test_id=D11-LIST-d11_prefixes_preserve_order_and_empty_boundary-{id} layer=SENS input={program} expected=D1:{expected} actual={actual}");
    }
}

#[test]
fn d11_suffixes_preserve_order_and_empty_boundary() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("завантажити чинне ядро SENS");
    eval_program(include_str!("../../../lib/list-all-suffixes-general.lisp"), &mut session)
        .expect("визначення та власні свідки спискової бібліотеки SENS");
    for (id, program, expected) in [
        ("порожній", r#"(однакові? (усі-суфікси (як-є ())) (як-є (())))"#, true),
        ("один", r#"(однакові? (усі-суфікси (як-є (а))) (як-є ((а) ())))"#, true),
        ("два", r#"(однакові? (усі-суфікси (як-є (а б))) (як-є ((а б) (б) ())))"#, true),
        ("три", r#"(однакові? (усі-суфікси (як-є (а б в))) (як-є ((а б в) (б в) (в) ())))"#, true),
        ("повтори", r#"(однакові? (усі-суфікси (як-є (а а))) (як-є ((а а) (а) ())))"#, true),
        ("зворотний-порядок", r#"(однакові? (усі-суфікси (як-є (а б))) (як-є (() (б) (а б))))"#, false),
        ("без-порожнього", r#"(однакові? (усі-суфікси (як-є (а б))) (як-є ((а б) (б))))"#, false),
        ("не-префікси", r#"(однакові? (усі-суфікси (як-є (а б))) (як-є ((а б) (а) ())))"#, false),
    ] {
        let actual = eval_program(program, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=D11-LIST-d11_suffixes_preserve_order_and_empty_boundary-{id} layer=SENS input={program} expected=D1:{expected} actual_error={error}"
            )).value;
        assert_eq!(actual.as_predicate_bit(), Some(expected),
            "test_id=D11-LIST-d11_suffixes_preserve_order_and_empty_boundary-{id} layer=SENS input={program} expected=D1:{expected} actual={actual}");
    }
}

#[test]
fn d11_all_cuts_are_reconstructible_and_reject_mutants() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("завантажити чинне ядро SENS");
    eval_program(include_str!("../../../lib/list-all-cuts-general.lisp"), &mut session)
        .expect("визначення та власні свідки спискової бібліотеки SENS");
    for (id, program, expected) in [
        ("порожній", r#"(однакові? (всі-розрізи (як-є ())) (як-є ((() ()))))"#, true),
        ("один", r#"(однакові? (всі-розрізи (як-є (а))) (як-є ((() (а)) ((а) ()))))"#, true),
        ("два", r#"(однакові? (всі-розрізи (як-є (а б))) (як-є ((() (а б)) ((а) (б)) ((а б) ()))))"#, true),
        ("три", r#"(однакові? (всі-розрізи (як-є (а б в))) (як-є ((() (а б в)) ((а) (б в)) ((а б) (в)) ((а б в) ()))))"#, true),
        ("повтор", r#"(однакові? (всі-розрізи (як-є (а а))) (як-є ((() (а а)) ((а) (а)) ((а а) ()))))"#, true),
        ("зворотний-порядок", r#"(однакові? (всі-розрізи (як-є (а б))) (як-є (((а б) ()) ((а) (б)) (() (а б)))))"#, false),
        ("зайвий-розріз", r#"(однакові? (всі-розрізи (як-є (а))) (як-є ((() (а)) ((а) ()) ((а) ()))))"#, false),
        ("загублений-елемент", r#"(однакові? (всі-розрізи (як-є (а б))) (як-є ((() (а б)) ((а) ()) ((а б) ()))))"#, false),
        ("відновити-два", r#"(усі-розрізи-відновлюють? (всі-розрізи (як-є (а б))) (як-є (а б)))"#, true),
        ("відновити-порожній", r#"(усі-розрізи-відновлюють? (всі-розрізи (як-є ())) (як-є ()))"#, true),
        ("відновити-інші-дані", r#"(усі-розрізи-відновлюють? (всі-розрізи (як-є (а б))) (як-є (а в)))"#, false),
        ("відхилити-пошкоджений", r#"(усі-розрізи-відновлюють? (як-є (((а) (в)))) (як-є (а б)))"#, false),
    ] {
        let actual = eval_program(program, &mut session)
            .unwrap_or_else(|error| panic!(
                "test_id=D11-LIST-d11_all_cuts_are_reconstructible_and_reject_mutants-{id} layer=SENS input={program} expected=D1:{expected} actual_error={error}"
            )).value;
        assert_eq!(actual.as_predicate_bit(), Some(expected),
            "test_id=D11-LIST-d11_all_cuts_are_reconstructible_and_reject_mutants-{id} layer=SENS input={program} expected=D1:{expected} actual={actual}");
    }
}

