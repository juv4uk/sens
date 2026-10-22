use sens::{
    eval_core_library_source, eval_parsed_expressions, eval_program,
    parse_mixed_exact_domain_reasoning_source, Session,
};

fn loaded_session() -> Session {
    let mut session = Session::default();
    eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("точне ядро СЕНС");
    for (path, library) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
        ("lib/forward.lisp", include_str!("../../../lib/forward.lisp")),
        ("lib/knowledge.lisp", include_str!("../../../lib/knowledge.lisp")),
    ] {
        let forms = parse_mixed_exact_domain_reasoning_source(path, library)
            .unwrap_or_else(|error| panic!("читач СЕНС {path}: {error}"));
        eval_parsed_expressions(&forms, &mut session)
            .unwrap_or_else(|error| panic!("виконання СЕНС {path}: {error}"));
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
            "(довжина (отримати-події-журналу-окремого-модуля (як-є bench) журнал-знань))",
        ),
        N.to_string()
    );
    assert_eq!(
        eval(&mut session, "(довжина (модуль-клаузи-зараз (як-є bench)))"),
        N.to_string()
    );

    // The tail-safe rewrite must preserve the historical projection order.
    assert_eq!(
        eval(
            &mut session,
            "(друге (перше (перше (модуль-клаузи-зараз (як-є bench)))))",
        ),
        "f0"
    );
    assert_eq!(
        eval(
            &mut session,
            &format!(
                "(друге (перше (елемент-списку-за-індексом {} (модуль-клаузи-зараз (як-є bench)))))",
                N - 1
            ),
        ),
        format!("f{}", N - 1)
    );
}
