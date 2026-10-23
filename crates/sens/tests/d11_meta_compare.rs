//! Rust перевіряє лише механізм завантаження MetaEval і Lisp-свідків.
//! Закони порівняння й негативний мутант визначає Lisp; D1 перевіряє фізичний SENS/T5M.

use sens::{eval_program, load_core_library, load_meta_evaluator_library, Session};
use std::path::PathBuf;

#[test]
fn rust_mechanism_loads_d11_meta_compare_lisp_witnesses() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("чинне ядро SENS");
    load_meta_evaluator_library(&mut session).expect("визначення MetaEval у SENS");
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    for witness in [
        "tests/semantic/d11-meta-compare-laws.lisp",
        "tests/semantic/d11-meta-compare-mutant.lisp",
    ] {
        let path = root.join(witness);
        let source = std::fs::read_to_string(&path).unwrap_or_else(|error| {
            panic!("test_id=D11-META-COMPARE-IO layer=Rust path={} actual={error}", path.display())
        });
        eval_program(&source, &mut session).unwrap_or_else(|error| {
            panic!("test_id=D11-META-COMPARE-EXEC layer=SENS source={witness} actual={error}")
        });
    }
}
