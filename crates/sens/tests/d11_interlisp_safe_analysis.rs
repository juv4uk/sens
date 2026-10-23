//! Rust доводить лише механізм завантаження українських Lisp-свідків.
//! Семантика DWIM і Masterscope належить Lisp → Zig/T5M → SENS.

use sens::{eval_program, load_core_library, Session};
use std::path::PathBuf;

#[test]
fn interlisp_lisp_witnesses_execute_in_sens() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("чинний Core4 SENS");
    eval_program(
        include_str!("../../../lib/d11-interlisp-safe-analysis.lisp"),
        &mut session,
    )
    .expect("чинні українські визначення Interlisp у SENS");

    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    for witness in [
        "tests/semantic/d11-interlisp-dwim-laws.lisp",
        "tests/semantic/d11-interlisp-dwim-mutant.lisp",
        "tests/semantic/d11-interlisp-masterscope-laws.lisp",
        "tests/semantic/d11-interlisp-masterscope-mutant.lisp",
    ] {
        let path = root.join(witness);
        let source = std::fs::read_to_string(&path).unwrap_or_else(|error| {
            panic!("test_id=D11-INTERLISP-IO layer=Rust path={} actual={error}", path.display())
        });
        // У Rust немає істиннісної таблиці, лише реальне SENS виконання.
        eval_program(&source, &mut session).unwrap_or_else(|error| {
            panic!("test_id=D11-INTERLISP-EXEC layer=SENS source={witness} actual={error}")
        });
    }
}
