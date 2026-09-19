use my_lisp::{eval_program, load_core_library, Session};

#[test]
fn print_postcore_definition_data_shape() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core should load");
    let result = eval_program(
        "(write-to-string
            (list
              (my-postcore-peer-group 162 my-postcore-stable-peer-projection)
              (my-postcore-missing-peers
                (quote process-run)
                (cdr (my-postcore-peer-group 162 my-postcore-stable-peer-projection))
                (env))
              (my-postcore-build-definitions
                (quote process-run)
                (my-postcore-missing-peers
                  (quote process-run)
                  (cdr (my-postcore-peer-group 162 my-postcore-stable-peer-projection))
                  (env)))))",
        &mut session,
    )
    .expect("core helper should evaluate");
    println!("POSTCORE_BUILD_DEFINITIONS = {}", result.value);
}

#[test]
fn macro_generated_define_arity_probe() {
    let mut session = Session::default();
    let result = eval_program(
        "(defmacro make-binding (name value)
           (cons (quote define)
             (cons name
               (cons value (quote ())))))
         (make-binding probe 42)",
        &mut session,
    )
    .expect("a Lisp macro should be able to generate a two-argument define");
    println!("MACRO_GENERATED_DEFINE = {}", result.value);
}
