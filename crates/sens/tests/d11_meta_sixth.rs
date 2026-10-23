//! Rust: механізм завантаження MetaEval і запуску українських Lisp-свідків.
//! Усі дев’ять законів селектора шостого елемента належать Lisp/SENS.
//! Точний D1 позитиву й негативного мутанта доводить фізичний Zig/T5M → SENS.

mod common;

use sens::{eval_program, load_core_library, Session};
use std::path::PathBuf;

#[test]
fn rust_mechanism_loads_meta_sixth_lisp_witnesses() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("завантажити чинне ядро SENS");
    common::load_meta_evaluator_library(&mut session)
        .expect("завантажити живі визначення MetaEval SENS");

    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    for witness in [
        "tests/semantic/d11-meta-sixth-laws.lisp",
        "tests/semantic/d11-meta-sixth-mutant.lisp",
    ] {
        let path = root.join(witness);
        let source = std::fs::read_to_string(&path)
            .unwrap_or_else(|error| panic!("Rust I/O path={} error={error}", path.display()));
        // Rust тестує транспорт джерела до реального SENS, а не формулу закону.
        eval_program(&source, &mut session)
            .unwrap_or_else(|error| panic!("SENS eval path={witness} error={error}"));
    }
}
