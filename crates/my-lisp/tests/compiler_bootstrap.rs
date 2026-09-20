//! Determinism witness for the Lisp-owned compiler-shaped emitter.

use my_lisp::{eval_program, Session};

fn emit(source: &str) -> String {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).expect("core");
    eval_program(include_str!("../../../../../lib/compiler.lisp"), &mut session).expect("compiler");
    eval_program(source, &mut session).expect("compiler program").value.to_string()
}

#[test]
fn compiler_emitter_is_byte_identical_for_repeated_source() {
    let source = "(compiler-program (quote ((define square (lambda (n) (* n n))) (square 6))))";
    let first = emit(source);
    let second = emit(source);
    assert_eq!(first, second);
    assert!(!first.is_empty());
}
