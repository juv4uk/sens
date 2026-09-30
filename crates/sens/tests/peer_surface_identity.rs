use sens::{eval_program, semantic_registry_export, Session, Value};
use std::rc::Rc;

const UK_SURFACE: &str = include_str!("../../../lib/surface/uk.lisp");
const SA_SURFACE: &str = include_str!("../../../lib/surface/sa.lisp");

fn add_semantic_id() -> sens::Sens8 {
    semantic_registry_export::semantic_id_for_admitted_surface("додати")
        .expect("canonical add surface must be admitted by the registry projection")
}

fn add_surfaces() -> Vec<(&'static str, &'static str)> {
    semantic_registry_export::admitted_surfaces_for_semantic_id(add_semantic_id())
        .into_iter()
        .map(|row| (row.namespace, row.name))
        .collect()
}

fn assert_same_builtin_handle(left: &Value, right: &Value) {
    match (left, right) {
        // This is a Rust binding-mechanism invariant only: every admitted
        // surface for one semantic ID is installed with one shared handle.
        // Language-level identity is specified by the registry/Lisp contract,
        // not by Rc allocation identity.
        (Value::Builtin(left), Value::Builtin(right)) => assert!(Rc::ptr_eq(left, right)),
        // Після кроку «Rust лише примітиви» всі написання ведуть до одного
        // SENS-коду — спільна ідентичність тепер сам 1-байтовий код.
        (Value::Sid(left), Value::Sid(right)) => assert_eq!(left, right),
        other => panic!("expected two builtin values, got {other:?}"),
    }
}

#[test]
fn admitted_add_surfaces_share_one_runtime_handle_before_surface_library_loads() {
    let surfaces = add_surfaces();
    assert!(
        surfaces.len() >= 2,
        "SID 00001100 must expose multiple admitted peer surfaces for this mechanism test"
    );

    let mut session = Session::default();
    let mut values = Vec::new();

    for (_, name) in &surfaces {
        let value = eval_program(name, &mut session)
            .unwrap_or_else(|error| panic!("admitted SID 00001100 surface is missing: {name}: {error}"))
            .value;
        values.push((*name, value));
    }

    let first = &values[0].1;
    for (name, value) in values.iter().skip(1) {
        assert_same_builtin_handle(first, value);
        assert_eq!(
            eval_program(&format!("({name} 20 22)"), &mut session)
                .unwrap()
                .value
                .to_string(),
            "42"
        );
    }

    let first_name = values[0].0;
    assert_eq!(
        eval_program(&format!("({first_name} 20 22)"), &mut session)
            .unwrap()
            .value
            .to_string(),
        "42"
    );
}

#[test]
fn admitted_add_surfaces_are_immutable_function_routes() {
    let surfaces = add_surfaces();

    for (_, admitted) in &surfaces {
        let mut session = Session::default();
        let error = eval_program(
            &format!("(define {admitted} (lambda (a b) (quote shadowed)))"),
            &mut session,
        )
        .expect_err("an admitted surface must not shadow its immutable Function8 route");

        assert_eq!(error.kind, sens::ErrorKind::InvalidForm);
        assert!(
            error
                .message
                .contains("surface routes to immutable function SID"),
            "unexpected immutability error for {admitted}: {error}"
        );

        for (_, peer) in &surfaces {
            assert_eq!(
                eval_program(&format!("({peer} 1 2)"), &mut session)
                    .unwrap()
                    .value
                    .to_string(),
                "3",
                "failed redefinition of {admitted} changed peer route {peer}"
            );
        }
    }
}

#[test]
fn human_surface_files_do_not_redefine_admitted_add_peers() {
    let surfaces = add_surfaces();

    for (namespace, name) in surfaces {
        let source = match namespace {
            "ук" => Some(UK_SURFACE),
            "sa" => Some(SA_SURFACE),
            _ => None,
        };

        if let Some(source) = source {
            assert!(
                !source.contains(&format!("(define {name} ")),
                "admitted SID 00001100 {namespace} surface {name} must be a direct runtime peer, not a surface-file alias"
            );
        }
    }
}
