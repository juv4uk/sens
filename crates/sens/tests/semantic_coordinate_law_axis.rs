use std::fs;
use std::path::PathBuf;

use sens::semantic_registry_export::semantic_id_for_admitted_surface;
use sens::{eval_program, load_core_library, Session};

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
    let source = fs::read_to_string(
        repo_root().join("tests/fixtures/semantic-coordinate-law-axis-v1.lisp"),
    )
    .expect("semantic coordinate law witness");
    eval_program(&source, &mut session).expect("law witness must load");
    session
}

#[test]
fn coordinate_rows_use_current_semantic_ids_without_minting_new_identity() {
    assert_eq!(semantic_id_for_admitted_surface("+"), Some(sens::sid!(00001100)));
    assert_eq!(semantic_id_for_admitted_surface("eq"), Some(sens::sid!(00000011)));
    assert_eq!(semantic_id_for_admitted_surface("cons"), Some(sens::sid!(00000100)));
    assert_eq!(semantic_id_for_admitted_surface("car"), Some(sens::sid!(00000101)));
    assert_eq!(semantic_id_for_admitted_surface("cond"), Some(sens::sid!(00000111)));

    for label in [
        "exact-rational-arithmetic",
        "identity-relation",
        "pair-construction",
        "pair-elimination",
        "no-mathematical-law-claimed",
    ] {
        assert_eq!(
            semantic_id_for_admitted_surface(label),
            None,
            "{label} is coordinate evidence/data, not a semantic identity"
        );
    }
}

#[test]
fn exact_rational_addition_reuses_existing_mathematical_result_contract() {
    let fixture = fs::read_to_string(repo_root().join("tests/fixtures/mathematical-result-v1.lisp"))
        .expect("mathematical result fixture");
    assert!(
        fixture.contains(r#"(expr . "(+ 1/3 1/6)")"#)
            && fixture.contains(r#"(expected . "1/2")"#),
        "the coordinate witness must reuse the existing exact-rational result anchor"
    );

    let mut s = session();
    let value = eval_program("(+ 1/3 1/6)", &mut s)
        .expect("exact rational addition")
        .value
        .to_string();
    assert_eq!(value, "1/2");
}

#[test]
fn pair_equation_is_executable_and_independent_of_machine_representation() {
    let mut s = session();
    let value = eval_program("(car (cons (quote left) (quote right)))", &mut s)
        .expect("car(cons(a,b)) law")
        .value
        .to_string();
    assert_eq!(value, "left");

    let row = eval_program(
        r#"(semantic-coordinate-law-for-sid 00000101)"#,
        &mut s,
    )
    .expect("CAR law row")
    .value
    .to_string();
    assert!(row.contains("car-cons-left-inverse"));
    assert!(!row.contains("x86"));
    assert!(!row.contains("mov-"));
}

#[test]
fn eq_relation_law_stays_separate_from_exact_q_binary_policy() {
    let mut s = session();
    let value = eval_program("(eq? (quote radio) (quote radio))", &mut s)
        .expect("identity relation witness")
        .value
        .to_string();
    assert_eq!(value, "(identity-relation same)");

    let row = eval_program(
        r#"(semantic-coordinate-law-for-sid 00000011)"#,
        &mut s,
    )
    .expect("EQ law row")
    .value
    .to_string();
    assert!(row.contains("identity-relation"));
    assert!(!row.contains("0/1"));
    assert!(!row.contains("1/1"));
}

#[test]
fn cond_proves_that_not_every_semantic_identity_is_a_mathematical_law() {
    let mut s = session();
    let row = eval_program(
        r#"(semantic-coordinate-law-for-sid 00000111)"#,
        &mut s,
    )
    .expect("COND coordinate row")
    .value
    .to_string();
    assert!(row.contains("non-mathematical-in-this-slice"));
    assert!(row.contains("no-mathematical-law-claimed"));

    let quoted_shadow = eval_program(
        r#"(semantic-coordinate-law-for-sid "00000111")"#,
        &mut s,
    )
    .expect("quoted SID shadow stays ordinary String data")
    .value
    .to_string();
    assert_eq!(quoted_shadow, "()");
}
