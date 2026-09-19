use std::fs;
use std::path::PathBuf;

use my_lisp::semantic_registry_export::semantic_id_for_admitted_surface;
use my_lisp::{eval_program, load_core_library, Session};

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(|p| p.parent())
        .expect("repo root")
        .to_path_buf()
}

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must load");
    let source = fs::read_to_string(repo_root().join("lib/machine/capability-axis.lisp"))
        .expect("capability axis source");
    eval_program(&source, &mut session).expect("capability axis must load");
    session
}

#[test]
fn current_semantic_ids_project_to_target_neutral_capabilities() {
    assert_eq!(semantic_id_for_admitted_surface("+"), Some(0b0000_1100));
    assert_eq!(semantic_id_for_admitted_surface("eq"), Some(0b0000_0011));
    assert_eq!(semantic_id_for_admitted_surface("cond"), Some(0b0000_0111));
    assert_eq!(semantic_id_for_admitted_surface("cons"), Some(0b0000_0100));
    assert_eq!(semantic_id_for_admitted_surface("car"), Some(0b0000_0101));
    assert_eq!(semantic_id_for_admitted_surface("cdr"), Some(0b0000_0110));

    let mut s = session();
    let add = eval_program(
        r#"(machine-capabilities-for-sid "00001100")"#,
        &mut s,
    )
    .expect("add capability lookup")
    .value
    .to_string();
    assert_eq!(add, "((integer-add bounded-u64))");

    let car = eval_program(
        r#"(machine-capabilities-for-sid "00000101")"#,
        &mut s,
    )
    .expect("car capability lookup")
    .value
    .to_string();
    assert_eq!(car, "((pair-field-load head bounded-u64))");
}

#[test]
fn capability_names_do_not_mint_semantic_identities() {
    for capability in [
        "integer-add",
        "identity-compare",
        "conditional-branch",
        "pair-field-store",
        "pair-field-load",
        "bounded-u64",
    ] {
        assert_eq!(
            semantic_id_for_admitted_surface(capability),
            None,
            "{capability} is machine-description data, not a language identity"
        );
    }
}

#[test]
fn unsupported_targets_are_explicitly_unwitnessed() {
    let mut s = session();

    for target in ["arm64", "risc-v", "fpga"] {
        let expression = format!("(machine-target-witness-status (quote {target}))");
        let value = eval_program(&expression, &mut s)
            .expect("target status lookup")
            .value
            .to_string();
        assert_eq!(value, "absent");
    }

    let x86 = eval_program(
        "(machine-target-witness-status (quote x86-64))",
        &mut s,
    )
    .expect("x86 witness status")
    .value
    .to_string();
    assert_eq!(x86, "witnessed");
}

#[test]
fn x86_target_witnesses_reference_existing_lowering_names_without_owning_meaning() {
    let source = fs::read_to_string(repo_root().join("lib/machine/capability-axis.lisp"))
        .expect("capability axis");
    let lowering = fs::read_to_string(repo_root().join("lib/machine/lowering/semantic-x86-64.lisp"))
        .expect("x86 semantic lowering");

    for name in [
        "x86-lower-add-u64-forms",
        "x86-lower-eq-cond-u64-forms",
        "x86-lower-bounded-pair-store-u64-forms",
        "x86-lower-cons-car-u64-forms",
        "x86-lower-cons-cdr-u64-forms",
    ] {
        assert!(source.contains(name), "axis references {name}");
        assert!(
            lowering.contains(&format!("(def {name}")),
            "referenced x86 witness {name} must exist"
        );
    }
}
