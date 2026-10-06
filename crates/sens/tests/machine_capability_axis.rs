use std::fs;
use std::path::PathBuf;

use sens::semantic_registry_export::semantic_id_for_admitted_surface;
use sens::{eval_program, load_core_library, lower_program, parse, ExprKind, Session};

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
fn current_exact_domain_identities_project_to_target_neutral_capabilities() {
    let lowered = lower_program(&parse("(додати 2 3)").expect("PLUS source"));
    let ExprKind::DomainCall(add_identity, _) = lowered[0].kind else {
        panic!("current PLUS surface must lower to DomainCall");
    };
    assert_eq!((add_identity.width(), add_identity.packed_bits()), (5, 0b01010));

    let lowered = lower_program(&parse("(перше '(a b))").expect("CAR source"));
    let ExprKind::DomainCall(car_identity, _) = lowered[0].kind else {
        panic!("current CAR surface must lower to DomainCall");
    };
    assert_eq!((car_identity.width(), car_identity.packed_bits()), (3, 0b100));

    let mut s = session();
    let add = eval_program(
        "(machine-capabilities-for-domain 01010)",
        &mut s,
    )
    .expect("D5 PLUS capability lookup")
    .value
    .to_string();
    assert_eq!(add, "((integer-add bounded-u32-inputs u64-result))");

    let car = eval_program(
        "(machine-capabilities-for-domain 100)",
        &mut s,
    )
    .expect("D3 CAR capability lookup")
    .value
    .to_string();
    assert_eq!(car, "((pair-field-load head bounded-u64))");

    let quoted_shadow = eval_program(
        r#"(machine-capabilities-for-domain "01010")"#,
        &mut s,
    )
    .expect("quoted domain shadow must remain ordinary String data")
    .value
    .to_string();
    assert_eq!(
        quoted_shadow, "()",
        "String data must not act as exact-domain machine-capability identity"
    );
}

#[test]
fn historical_sid_capability_lookup_is_compatibility_only() {
    let mut s = session();
    let legacy = eval_program(
        "(machine-capabilities-for-sid 00001100)",
        &mut s,
    )
    .expect("legacy ADD compatibility lookup")
    .value
    .to_string();
    assert_eq!(legacy, "((integer-add bounded-u64))");

    let source = fs::read_to_string(repo_root().join("lib/machine/capability-axis.lisp"))
        .expect("capability axis source");
    assert!(source.contains("machine-capability-legacy-sid-axis-v1"));
    assert!(source.contains("New machine work must use"));
}

#[test]
fn capability_names_do_not_mint_semantic_identities() {
    for capability in [
        "integer-add",
        "integer-subtract",
        "integer-multiply",
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
        "x86-lower-difference-u64-forms",
        "x86-lower-times-u64-forms",
        "x86-lower-eq-cond-u64-forms",
        "x86-lower-bounded-pair-store-u64-forms",
        "x86-lower-cons-car-u64-forms",
        "x86-lower-cons-cdr-u64-forms",
    ] {
        assert!(source.contains(name), "axis references {name}");
        assert!(
            lowering.contains(&format!("(00001001 {name}")),
            "referenced x86 witness {name} must exist"
        );
    }
}
