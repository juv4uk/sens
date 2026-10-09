//! Disposable exact D1 bootstrap identity probe; DO NOT merge into main.
use sens::{eval_program, Session};
#[test]
fn isolate_letstar_after_exact_d1_cond_migration() {
    let mut session=Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    for (label,expr) in [
        ("quote", "(00000001 datum)"),
        ("let surface", "(let ((x (00000001 datum))) x)"),
        ("let* surface", "(let* ((x (00000001 datum))) x)"),
        ("let sid", "(10011100 ((x (00000001 datum))) x)"),
        ("let* sid", "(10011101 ((x (00000001 datum))) x)"),
        ("let* two bindings", "(10011101 ((x (00000001 datum)) (y x)) y)"),
        ("ATOM empty", "(00000010 (00000001 ()))"),
        ("ATOM pair", "(00000010 (00000001 (a b)))"),
        ("NO comparator", "(00100010 (00000010 (00000001 (a b))) (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))"),
    ] {
        match eval_program(expr,&mut session) {
            Ok(v)=>eprintln!("LETSTAR-DEBUG {label}: {}",v.value),
            Err(e)=>eprintln!("LETSTAR-DEBUG {label}: ERROR {e}"),
        }
    }
}
