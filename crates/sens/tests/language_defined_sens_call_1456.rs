//! #1456 — language-defined function mechanisms are reachable by exact SENS.
//!
//! The semantic registry owns identity. Rust stores only the closure mechanism
//! attached by a language `define`; exact SENS invocation never round-trips
//! through a human surface name.

use sens::{eval_program, load_core_library, ErrorKind, Session};

fn core_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library must bootstrap");
    session
}

#[test]
fn exact_sens_calls_language_defined_core_functions() {
    let cases = [
        ("(00100111 1 2)", "(list 1 2)"),
        ("(00010100 17 5)", "(quotient 17 5)"),
        (
            "(00101100 2 (00000001 (1 2 3)))",
            "(member? 2 (quote (1 2 3)))",
        ),
    ];

    for (exact, surface) in cases {
        let mut session = core_session();
        let exact_value = eval_program(exact, &mut session)
            .unwrap_or_else(|error| panic!("{exact}: {error}"))
            .value;
        let surface_value = eval_program(surface, &mut session)
            .unwrap_or_else(|error| panic!("{surface}: {error}"))
            .value;
        assert_eq!(exact_value, surface_value, "{exact} != {surface}");
    }
}

#[test]
fn surface_shadowing_does_not_retarget_exact_sens_slot() {
    let mut session = core_session();

    let result = eval_program(
        "((lambda (member?) (00101100 2 (00000001 (1 2 3))))
           (lambda (item lst) (00000001 shadowed)))",
        &mut session,
    )
    .expect("exact SENS must bypass the shadowed surface");

    assert_eq!(result.value.to_string(), "t");
}

#[test]
fn exact_sens_without_primitive_or_language_definition_fails_closed() {
    let mut session = core_session();
    let error = eval_program("(11111111)", &mut session)
        .expect_err("unbound exact SENS must remain non-callable");

    assert_eq!(error.kind, ErrorKind::Type);
    assert!(
        error.message.contains("no admitted callable mechanism"),
        "unexpected error: {error}"
    );
}
