use sens::{eval_program, load_core_library, Session};

fn load_surface_prerequisites(session: &mut Session) {
    for source in [
        include_str!("../../../lib/unify.lisp"),
        include_str!("../../../lib/reason.lisp"),
        include_str!("../../../lib/forward.lisp"),
        include_str!("../../../lib/knowledge.lisp"),
        include_str!("../../../lib/persistent-map.lisp"),
        include_str!("../../../lib/persistent-vector.lisp"),
        include_str!("../../../lib/time.lisp"),
        include_str!("../../../lib/epistemic.lisp"),
    ] {
        eval_program(source, session).expect("surface prerequisite should load");
    }
}

#[test]
fn ukrainian_surface_defines_functions_without_rust_knowing_ukrainian_form_names() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("canonical macro + core bootstrap should preload");
    load_surface_prerequisites(&mut session);
    eval_program(include_str!("../../../lib/surface/uk.lisp"), &mut session)
        .expect("Ukrainian surface should preload");

    let result = eval_program(
        r#"
            (визначити квадрат
              (функція (х)
                (* х х)))
            (квадрат 7)
        "#,
        &mut session,
    )
    .expect("Ukrainian DEFINE/LAMBDA surface should execute");

    assert_eq!(result.value.to_string(), "49");
}

#[test]
fn canonical_ukrainian_syntax_and_batch_one_aliases_preserve_results() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("canonical macro + core bootstrap should preload");
    load_surface_prerequisites(&mut session);
    eval_program(include_str!("../../../lib/surface/uk.lisp"), &mut session)
        .expect("Ukrainian surface should preload");

    let quoted = eval_program("(як-є (додати 2 3))", &mut session)
        .expect("canonical як-є should preserve the source form instead of evaluating it");
    assert_eq!(quoted.value.to_string(), "(додати 2 3)");

    let aliases = eval_program(
        r#"
            (список
              (додати 2 3)
              (менше? 2 3)
              (хибне? ())
              (текст-порожній? "")
              (без-змін 7))
        "#,
        &mut session,
    )
    .expect("word-first aliases should execute through existing operations");
    // Surface aliases must preserve each operation's CURRENT result domain;
    // they do not coerce unrelated predicate-like answers back into a
    // historical universal T/NIL model. In this mixed-domain witness:
    //   менше?         -> exact-Q binary decision 1
    //   хибне?         -> current compatibility/helper result t
    //   текст-порожній? -> explicit identity-relation observation
    assert_eq!(
        aliases.value.to_string(),
        "(5 1 t (identity-relation same) 7)"
    );
}

#[test]
fn historical_def_remains_compatible_but_is_not_the_canonical_form_identity() {
    let mut session = Session::default();
    let result = eval_program("(def x 5) (define y 7) (+ x y)", &mut session)
        .expect("def compatibility and canonical define should coexist");
    assert_eq!(result.value.to_string(), "12");
}
