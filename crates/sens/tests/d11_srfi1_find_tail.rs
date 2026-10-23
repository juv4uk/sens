//! Rust перевіряє механізм завантаження файлів і виклику SENS, не закони FIND-TAIL.
//! Твердження про списки, хвости та D1 належать тільки виконуваним Lisp-свідкам.
//! Джерела читаються з файлів під час тесту, а не вшиваються у Rust-бінарник.

use sens::{eval_program, load_core_library, Session};
use std::path::PathBuf;

fn джерело_лісп(відносний_шлях: &str) -> String {
    let корінь = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let шлях = корінь.join(відносний_шлях);
    std::fs::read_to_string(&шлях)
        .unwrap_or_else(|помилка| panic!("Rust I/O не відкрив {}: {помилка}", шлях.display()))
}

#[test]
fn rust_mechanism_runs_lisp_owned_find_tail_laws() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("завантажити ядро SENS");

    let бібліотека = джерело_лісп("lib/d11-srfi1-find-tail.lisp");
    eval_program(&бібліотека, &mut session)
        .expect("SENS має прийняти бібліотечні визначення FIND-TAIL");

    // Rust перевіряє лише доступність файлу, запуск і статус виконання.
    // Справжній позитив/мутант і фізичний паритет перевіряє Lisp → Zig/T5M → SENS.
    let свідок = джерело_лісп("tests/semantic/d11-srfi1-find-tail-laws.lisp");
    eval_program(&свідок, &mut session)
        .expect("SENS має виконати власний Lisp-свідок без механічної помилки");
}
