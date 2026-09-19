use my_lisp::{eval_program, semantic_registry_export, Session, Value};
use std::rc::Rc;

const ADD_SEMANTIC_ID: u8 = 12;
const UK_SURFACE: &str = include_str!("../../../lib/surface/uk.lisp");
const SA_SURFACE: &str = include_str!("../../../lib/surface/sa.lisp");

fn add_surfaces() -> Vec<(&'static str, &'static str)> {
    semantic_registry_export::admitted_surfaces_for_semantic_id(ADD_SEMANTIC_ID)
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
fn shadowing_one_admitted_add_surface_does_not_retarget_its_peers() {
    let surfaces = add_surfaces();

    for (_, shadowed) in &surfaces {
        let mut session = Session::default();
        eval_program(
            &format!("(define {shadowed} (lambda (a b) (quote shadowed)))"),
            &mut session,
        )
        .expect("ordinary peer spelling remains lexically shadowable");

        assert_eq!(
            eval_program(&format!("({shadowed} 1 2)"), &mut session)
                .unwrap()
                .value
                .to_string(),
            "shadowed"
        );

        for (_, peer) in &surfaces {
            if peer == shadowed {
                continue;
            }
            assert_eq!(
                eval_program(&format!("({peer} 1 2)"), &mut session)
                    .unwrap()
                    .value
                    .to_string(),
                "3",
                "shadowing {shadowed} retargeted peer {peer}"
            );
        }
    }
}

#[test]
fn human_surface_files_do_not_redefine_admitted_add_peers() {
    let surfaces = add_surfaces();

    for (namespace, name) in surfaces {
        let source = match namespace {
            "uk" => Some(UK_SURFACE),
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
