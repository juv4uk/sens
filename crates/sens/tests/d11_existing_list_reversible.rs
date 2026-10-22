//! D11: наявні оборотні закони списків, без додавання машинних примітивів.
//! Джерело семантики — справжній eval_program SENS, а не Rust/Python-імітація.
//! Кожен приклад повертає тільки канонічний предикат D1 (так/ні).
//! Це адресні бібліотечні свідки; не ратифікація D11 і не T5M-атестація.

use sens::{eval_program, load_core_library, Session};

fn session_with_library(source: &str) -> Session {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("завантажити чинне ядро SENS");
    eval_program(source, &mut session).expect("виконати українську SENS-бібліотеку");
    session
}

fn assert_sens_cases(session: &mut Session, family: &str, cases: &[(&str, &str, bool)]) {
    for (id, program, expected) in cases {
        let actual = eval_program(program, session).unwrap_or_else(|error| {
            panic!(
                "test_id=D11-LIST-{family}-{id} layer=SENS input={program} expected=D1:{expected} actual_error={error}"
            )
        }).value;
        assert_eq!(
            actual.as_predicate_bit(),
            Some(*expected),
            "test_id=D11-LIST-{family}-{id} layer=SENS input={program} expected=D1:{expected} actual={actual}"
        );
    }
}

#[test]
fn d11_zip_with_tails_is_lossless() {
    let mut session = session_with_library(include_str!(
        "../../../lib/list-zip-with-tails-general.lisp"
    ));
    assert_sens_cases(&mut session, "ZIP-TAILS", &[
        ("empty", r#"(однакові? (спарити-зі-збереженням-хвостів (як-є ()) (як-є ())) (як-є (() () ())))"#, true),
        ("equal", r#"(однакові? (спарити-зі-збереженням-хвостів (як-є (а б)) (як-є (х у))) (як-є (((а х) (б у)) () ())))"#, true),
        ("left-tail", r#"(однакові? (спарити-зі-збереженням-хвостів (як-є (а б в)) (як-є (х у))) (як-є (((а х) (б у)) (в) ())))"#, true),
        ("right-tail", r#"(однакові? (спарити-зі-збереженням-хвостів (як-є (а)) (як-є (х у))) (як-є (((а х)) () (у))))"#, true),
        ("zero-left", r#"(однакові? (спарити-зі-збереженням-хвостів (як-є ()) (як-є (х))) (як-є (() () (х))))"#, true),
        ("restore-left", r#"(однакові? (відновити-два-списки-зі-хвостів (спарити-зі-збереженням-хвостів (як-є (а б в)) (як-є (х)))) (як-є ((а б в) (х))))"#, true),
        ("restore-right", r#"(однакові? (відновити-два-списки-зі-хвостів (спарити-зі-збереженням-хвостів (як-є (а)) (як-є (х у)))) (як-є ((а) (х у))))"#, true),
        ("restore-empty", r#"(однакові? (відновити-два-списки-зі-хвостів (спарити-зі-збереженням-хвостів (як-є ()) (як-є ()))) (як-є (() ())))"#, true),
        ("reject-lost-tail", r#"(однакові? (спарити-зі-збереженням-хвостів (як-є (а б)) (як-є (х))) (як-є (((а х)) () ())))"#, false),
        ("reject-reordered", r#"(однакові? (відновити-два-списки-зі-хвостів (спарити-зі-збереженням-хвостів (як-є (а б)) (як-є (х у)))) (як-є ((б а) (х у))))"#, false),
    ]);
}

#[test]
fn d11_interpose_roundtrip_only_on_its_image() {
    let mut session = session_with_library(include_str!(
        "../../../lib/list-interpose-general.lisp"
    ));
    assert_sens_cases(&mut session, "INTERPOSE", &[
        ("empty", r#"(однакові? (вставити-роздільник-між (як-є х) (як-є ())) (як-є ()))"#, true),
        ("singleton", r#"(однакові? (вставити-роздільник-між (як-є х) (як-є (а))) (як-є (а)))"#, true),
        ("three", r#"(однакові? (вставити-роздільник-між (як-є х) (як-є (а б в))) (як-є (а х б х в)))"#, true),
        ("nested", r#"(однакові? (вставити-роздільник-між (як-є х) (як-є ((а) (б)))) (як-є ((а) х (б))))"#, true),
        ("inverse-empty", r#"(однакові? (вилучити-роздільники-між (вставити-роздільник-між (як-є х) (як-є ()))) (як-є ()))"#, true),
        ("inverse-three", r#"(однакові? (вилучити-роздільники-між (вставити-роздільник-між (як-є х) (як-є (а б в)))) (як-є (а б в)))"#, true),
        ("inverse-repeat", r#"(однакові? (вилучити-роздільники-між (вставити-роздільник-між (як-є а) (як-є (а а а)))) (як-є (а а а)))"#, true),
        ("reject-duplicate-delimiter", r#"(однакові? (вставити-роздільник-між (як-є х) (як-є (а б))) (як-є (а х х б)))"#, false),
        ("reject-trailing-delimiter", r#"(однакові? (вставити-роздільник-між (як-є х) (як-є (а б))) (як-є (а х б х)))"#, false),
    ]);
}

#[test]
fn d11_unzip_and_zip_preserve_pair_order() {
    let mut session = session_with_library(include_str!(
        "../../../lib/list-unzip-pairs-general.lisp"
    ));
    assert_sens_cases(&mut session, "UNZIP", &[
        ("firsts", r#"(однакові? (розплести-перші-пари (як-є ((а х) (б у)))) (як-є (а б)))"#, true),
        ("seconds", r#"(однакові? (розплести-другі-пари (як-є ((а х) (б у)))) (як-є (х у)))"#, true),
        ("zip", r#"(однакові? (зшити-дві-послідовності (як-є (а б)) (як-є (х у))) (як-є ((а х) (б у))))"#, true),
        ("roundtrip", r#"(однакові? (зшити-дві-послідовності (розплести-перші-пари (як-є ((а х) (б у)))) (розплести-другі-пари (як-є ((а х) (б у))))) (як-є ((а х) (б у))))"#, true),
        ("empty", r#"(однакові? (зшити-дві-послідовності (як-є ()) (як-є ())) (як-є ()))"#, true),
        ("truncate", r#"(однакові? (зшити-дві-послідовності (як-є (а б)) (як-є (х))) (як-є ((а х))))"#, true),
        ("reject-swapped-columns", r#"(однакові? (зшити-дві-послідовності (як-є (а б)) (як-є (х у))) (як-є ((х а) (у б))))"#, false),
        ("reject-lost-second", r#"(однакові? (розплести-другі-пари (як-є ((а х) (б у)))) (як-є (х)))"#, false),
    ]);
}

#[test]
fn d11_common_prefix_stops_at_first_difference() {
    let mut session = session_with_library(include_str!(
        "../../../lib/list-common-prefix-general.lisp"
    ));
    assert_sens_cases(&mut session, "COMMON-PREFIX", &[
        ("empty-left", r#"(однакові? (спільний-префікс-атомів (як-є ()) (як-є (а))) (як-є ()))"#, true),
        ("empty-right", r#"(однакові? (спільний-префікс-атомів (як-є (а)) (як-є ())) (як-є ()))"#, true),
        ("equal", r#"(однакові? (спільний-префікс-атомів (як-є (а б)) (як-є (а б))) (як-є (а б)))"#, true),
        ("two", r#"(однакові? (спільний-префікс-атомів (як-є (а б в)) (як-є (а б х))) (як-є (а б)))"#, true),
        ("proper-prefix", r#"(однакові? (спільний-префікс-атомів (як-є (а б)) (як-є (а б в))) (як-є (а б)))"#, true),
        ("first-differs", r#"(однакові? (спільний-префікс-атомів (як-є (а б)) (як-є (х б))) (як-є ()))"#, true),
        ("reject-longer", r#"(однакові? (спільний-префікс-атомів (як-є (а б в)) (як-є (а б х))) (як-є (а б в)))"#, false),
        ("reject-suffix", r#"(однакові? (спільний-префікс-атомів (як-є (а б)) (як-є (х б))) (як-є (б)))"#, false),
    ]);
}
