//! M4 · тонкий Rust-ланцюгер для бібліотеки тверджень.
//!
//! Судження живе в SENS (семантика). Rust лише:
//! - завантажує core + lib
//! - запускає law
//! - перевіряє механічний успіх (позитив) або відмову (мутант)
//!
//! Не дублює таблиці істинності й не читає D1-значення як оракул.

use sens::{eval_program, load_core_library, Session};

fn load(session: &mut Session, path: &str, source: &str) {
    eval_program(source, session).unwrap_or_else(|e| {
        panic!("механічне завантаження {path}: {e:?}");
    });
}

#[test]
fn m1_твердження_самотест_виконується() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("ініціалізація SENS");
    load(
        &mut session,
        "lib/твердження.lisp",
        include_str!("../../../lib/твердження.lisp"),
    );
    eval_program(
        include_str!("../../../tests/semantic/твердження-самотест-law.lisp"),
        &mut session,
    )
    .expect("M1 самотест: Rust backend мусить виконати Lisp-owned law");
}

#[test]
fn m2_негативні_law_виконується() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("ініціалізація SENS");
    load(
        &mut session,
        "lib/твердження.lisp",
        include_str!("../../../lib/твердження.lisp"),
    );
    eval_program(
        include_str!("../../../tests/semantic/твердження-негативні-law.lisp"),
        &mut session,
    )
    .expect("M2 негативні: Rust backend мусить виконати Lisp-owned law");
}

#[test]
fn m2_car_mutant_відхиляється() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("ініціалізація SENS");
    let result = eval_program(
        include_str!("../../../tests/semantic/твердження-car-mutant.lisp"),
        &mut session,
    );
    assert!(
        result.is_err(),
        "M2 mutant CAR: очікувана відмова SENS, не зелений прогін"
    );
}

#[test]
fn m3_медіана_law_виконується() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("ініціалізація SENS");
    eval_program(
        include_str!("../../../tests/semantic/бенчмарк-медіана-law.lisp"),
        &mut session,
    )
    .expect("M3 медіана: Rust backend мусить виконати Lisp-owned law");
}

#[test]
fn m1_lib_твердження_завантажується() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("ініціалізація SENS");
    load(
        &mut session,
        "lib/твердження.lisp",
        include_str!("../../../lib/твердження.lisp"),
    );
    load(
        &mut session,
        "lib/бенчмарк.lisp",
        include_str!("../../../lib/бенчмарк.lisp"),
    );
}
