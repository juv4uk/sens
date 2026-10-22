use sens::{eval_program, Session};

fn loaded_session() -> Session {
    let mut session = Session::default();
    for library in [
        include_str!("../../../lib/core.lisp"),
        include_str!("../../../lib/unify.lisp"),
        include_str!("../../../lib/reason.lisp"),
        include_str!("../../../lib/forward.lisp"),
        include_str!("../../../lib/knowledge.lisp"),
    ] {
        eval_program(library, &mut session).expect("knowledge stack fixture should load");
    }
    session
}

fn eval(session: &mut Session, source: &str) -> String {
    eval_program(source, session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn large_module_projection_and_existence_scan_are_stack_safe_on_default_thread() {
    const N: usize = 2_000;
    let mut session = loaded_session();

    let mut source = String::from("(визначити-модуль bench (як-є (");
    for i in 0..N {
        source.push_str(&format!("((item f{i}))"));
    }
    source.push_str(")))");
    eval(&mut session, &source);

    assert_eq!(eval(&mut session, "(модуль-відомий? (як-є bench))"), "t");
    assert_eq!(
        eval(
            &mut session,
            "(length (отримати-події-журналу-окремого-модуля (як-є bench) журнал-знань))",
        ),
        N.to_string()
    );
    assert_eq!(
        eval(&mut session, "(length (модуль-клаузи-зараз (як-є bench)))"),
        N.to_string()
    );

    // The tail-safe rewrite must preserve the historical projection order.
    assert_eq!(
        eval(
            &mut session,
            "(second (car (car (модуль-клаузи-зараз (як-є bench)))))",
        ),
        "f0"
    );
    assert_eq!(
        eval(
            &mut session,
            &format!(
                "(second (car (nth {} (модуль-клаузи-зараз (як-є bench)))))",
                N - 1
            ),
        ),
        format!("f{}", N - 1)
    );
}
