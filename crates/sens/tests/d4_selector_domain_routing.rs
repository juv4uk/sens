//! Rust відповідає лише за запуск виконуваного Lisp-свідка в своєму runtime.
//! Очікувані результати CAR/CDR-подібних селекторів задає сама програма SENS.
use sens::{eval_program, load_core_library, Session};

#[test]
fn rust_runtime_executes_lisp_owned_d4_selector_witness() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("SENS core must load");

    let source = include_str!("../../../tests/semantic/d4-selector-domain-law.lisp");
    let result = eval_program(source, &mut session)
        .expect("Lisp-owned selector law must execute")
        .value
        .to_string();

    assert!(
        result.starts_with("(d4-selector-domain-law (status pass)"),
        "SENS Lisp witness rejected selector semantics: {result}"
    );
}
