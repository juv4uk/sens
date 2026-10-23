//! Rust відповідає тільки за механіку завантаження UTF-8 і запуск SENS.
//! Вісім законів останнього DEFINE, D7/D8 і негативний мутант — у Lisp.

mod common;

use sens::{eval_program, load_core_library, Session};
use std::path::PathBuf;

#[test]
fn rust_mechanism_executes_last_define_lisp_witnesses() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("завантажити чинне ядро SENS");
    common::load_meta_evaluator_library(&mut session).expect("завантажити MetaEval SENS");

    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    for witness in [
        "tests/semantic/d11-meta-last-define-laws.lisp",
        "tests/semantic/d11-meta-last-define-mutant.lisp",
    ] {
        let path = root.join(witness);
        let source = std::fs::read_to_string(&path).unwrap_or_else(|error| {
            panic!("test_id=D11-LAST-DEFINE-IO layer=Rust path={} actual={error}", path.display())
        });
        eval_program(&source, &mut session)
            .unwrap_or_else(|error| panic!("test_id=D11-LAST-DEFINE-EXEC layer=SENS source={witness} actual={error}"));
    }
}
