use my_lisp::{eval_program, load_macro_library, Environment, Session, Value};
use std::rc::Rc;

fn eval_with_derived_macros(source: &str) -> String {
    let mut session = Session::default();
    eval_program(source, &mut session)
        .expect("program using derived macros should evaluate")
        .value
        .to_string()
}

fn assert_same_macro_value(values: [Value; 2]) {
    match (&values[0], &values[1]) {
        (Value::Macro(defmacro), Value::Macro(uk)) => {
            assert!(
                Rc::ptr_eq(defmacro, uk),
                "defmacro and визначити-макрос must share one Macro value"
            );
        }
        other => panic!("expected two Macro bindings, got {other:?}"),
    }
}

#[test]
fn default_session_binds_all_defmacro_peers_to_one_value() {
    let session = Session::default();
    assert_same_macro_value([
        session
            .environment
            .get("defmacro")
            .expect("default session must bind defmacro"),
        session
            .environment
            .get("визначити-макрос")
            .expect("default session must bind визначити-макрос"),
    ]);
}

#[test]
fn macro_peer_admission_is_recorded_under_identity_00001010_without_binding_the_machine_id() {
    let id = my_lisp::semantic_registry_export::semantic_id_for_admitted_surface("defmacro")
        .expect("defmacro must be registry-admitted");
    assert_eq!(
        my_lisp::semantic_registry_export::semantic_id_bits(id),
        "00001010"
    );

    let surfaces = my_lisp::semantic_registry_export::admitted_surfaces_for_semantic_id(id);
    assert!(surfaces.iter().any(|row| row.namespace == "en" && row.name == "defmacro"));
    assert!(surfaces.iter().any(|row| row.namespace == "uk" && row.name == "визначити-макрос"));
    assert!(surfaces.iter().any(|row| row.namespace == "ukr" && row.name == "визначити-макрос"));
    assert!(surfaces.iter().all(|row| row.namespace != "sa" && row.namespace != "sym"));

    let session = Session::default();
    assert!(
        session.environment.get("00001010").is_none(),
        "opaque semantic IDs must never become ordinary lexical bindings"
    );
}
#[test]
fn bare_root_gains_peer_bindings_only_through_macro_loader() {
    let environment = Environment::root();
    assert!(environment.get("defmacro").is_none());
    assert!(environment.get("визначити-макрос").is_none());

    let mut session = Session { environment };
    let loaded = load_macro_library(&mut session).expect("macro library should bootstrap");
    let loaded_macro = match &loaded.value {
        Value::Macro(value) => value,
        other => panic!("macro library must return one Macro value, got {other:?}"),
    };

    let defmacro = session
        .environment
        .get("defmacro")
        .expect("loader must bind defmacro");
    let uk = session
        .environment
        .get("визначити-макрос")
        .expect("loader must bind визначити-макрос");

    assert_same_macro_value([defmacro.clone(), uk]);
    match &defmacro {
        Value::Macro(bound) => assert!(
            Rc::ptr_eq(loaded_macro, bound),
            "loader must bind the exact Macro value returned by lib/macro.lisp"
        ),
        other => panic!("defmacro binding must be a Macro value, got {other:?}"),
    }
}

#[test]
fn language_owned_defmacro_introduces_a_working_macro() {
    let value = eval_with_derived_macros(
        r#"
        (defmacro identity (x) x)
        (identity 42)
        "#,
    );
    assert_eq!(value, "42");
}

#[test]
fn ukrainian_defmacro_peer_works_without_loading_uk_surface_bridge() {
    let value = eval_with_derived_macros(
        r#"
        (визначити-макрос identity-uk (x) x)
        (identity-uk 11)
        "#,
    );
    assert_eq!(value, "11");
}

#[test]
fn language_owned_defmacro_preserves_unevaluated_arguments() {
    let value = eval_with_derived_macros(
        r#"
        (defmacro first-form (a b) a)
        (first-form (quote ok) never-defined)
        "#,
    );
    assert_eq!(value, "ok");
}

#[test]
fn language_owned_defmacro_can_build_control_flow() {
    let value = eval_with_derived_macros(
        r#"
        (defmacro unless (condition body)
          (cons (quote cond)
            (cons
              (cons condition
                (cons (quote ()) (quote ())))
              (cons
                (cons (quote t)
                  (cons body (quote ())))
                (quote ())))))
        (unless () (quote success))
        "#,
    );
    assert_eq!(value, "success");
}
