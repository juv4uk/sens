//! #990 executable check for the ratified four-island math contract.
//!
//! This test is an observer over the Lisp-owned contract. It checks that the
//! contract references existing semantic identities and that excluded partial
//! overlap stays explicit. It does not create semantic IDs or machine mappings.

use std::fs;
use std::path::PathBuf;

use my_lisp::{eval_program, load_core_library, parse, Expr, ExprKind, Session};

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(|path| path.parent())
        .expect("repository root")
        .to_path_buf()
}

fn source() -> String {
    fs::read_to_string(repo_root().join("contracts/island-math-contract-990.lisp"))
        .expect("#990 contract must exist")
}

fn field<'a>(row: &'a [Expr], key: &str) -> Option<&'a Expr> {
    row.iter().find_map(|entry| {
        let ExprKind::Pair(k, v) = &entry.kind else { return None };
        let ExprKind::Symbol(name) = &k.kind else { return None };
        (&**name == key).then_some(v.as_ref())
    })
}

fn text_field<'a>(row: &'a [Expr], key: &str) -> &'a str {
    let value = field(row, key).expect("contract field");
    match &value.kind {
        ExprKind::String(value) | ExprKind::Symbol(value) => value.as_ref(),
        _ => panic!("contract field {key} must be text"),
    }
}

fn rows<'a>(top: &'a [Expr]) -> Vec<&'a [Expr]> {
    top.iter()
        .filter_map(|expr| match &expr.kind {
            ExprKind::List(items)
                if items.iter().any(|item| {
                    matches!(
                        &item.kind,
                        ExprKind::Pair(k, _)
                            if matches!(&k.kind, ExprKind::Symbol(name) if &**name == "operation")
                    )
                }) =>
            {
                Some(items.as_ref())
            }
            _ => None,
        })
        .collect()
}

#[test]
fn contract_is_lisp_data_and_is_not_a_second_registry() {
    let forms = parse(&source()).expect("#990 contract must parse");
    assert_eq!(forms.len(), 1);
    let ExprKind::List(top) = &forms[0].kind else {
        panic!("#990 top form must be a list");
    };
    assert!(matches!(
        &top[0].kind,
        ExprKind::Symbol(name) if &**name == "island-math-contract/1"
    ));
    assert_eq!(
        text_field(rows(top).first().copied().expect("metadata row"), "operation"),
        "+"
    );
}

#[test]
fn shared_set_reuses_only_existing_registry_ids() {
    let text = source();
    for (operation, sid) in [
        ("+", "00001100"),
        ("-", "00001101"),
        ("*", "00001110"),
        ("abs", "00010000"),
        ("min", "00010001"),
        ("max", "00010010"),
    ] {
        assert!(
            text.contains(&format!("(operation . \"{operation}\")")),
            "shared operation missing: {operation}"
        );
        assert!(
            text.contains(&format!("(semantic-id . \"{sid}\")")),
            "shared semantic id missing: {sid}"
        );
    }
}

#[test]
fn shared_ids_resolve_through_lisp_owned_registry_api() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    eval_program(
        include_str!("../../../lib/surface/semantic-registry-api.lisp"),
        &mut session,
    )
    .expect("Lisp-owned semantic registry API should load");

    for (surface, expected_id) in [
        ("(quote +)", "00001100"),
        ("(quote -)", "00001101"),
        ("(quote *)", "00001110"),
        ("(quote abs)", "00010000"),
        ("(quote min)", "00010001"),
        ("(quote max)", "00010010"),
    ] {
        let program = format!("(binary 8) (semantic-registry-id {surface})");
        let rendered = eval_program(&program, &mut session)
            .expect("semantic registry surface lookup should evaluate")
            .value
            .to_string();
        assert_eq!(
            rendered, expected_id,
            "contract identity for {surface} must resolve through Lisp-owned registry"
        );
    }
}

#[test]
fn partial_overlap_is_visible_and_excluded_from_shared_set() {
    let forms = parse(&source()).expect("#990 contract must parse");
    let ExprKind::List(top) = &forms[0].kind else {
        panic!("#990 top form must be a list");
    };

    for (operation, reason_fragment) in [
        ("/", "integer"),
        ("mod", "floored"),
        ("quotient", "matching primitive"),
        ("sqrt", "Datalog"),
        ("comparisons", "decision/relation"),
    ] {
        let row = rows(top)
            .into_iter()
            .find(|row| text_field(row, "operation") == operation)
            .unwrap_or_else(|| panic!("excluded operation missing: {operation}"));
        assert!(
            text_field(row, "exclusion-reason").contains(reason_fragment),
            "exclusion rationale for {operation} is not explicit"
        );
        if operation != "comparisons" {
            assert_eq!(text_field(row, "common-lisp"), "partial");
        } else {
            assert_eq!(text_field(row, "common-lisp"), "present");
        }
    }
}

#[test]
fn shared_domain_and_arity_are_explicit() {
    let forms = parse(&source()).expect("#990 contract must parse");
    let ExprKind::List(top) = &forms[0].kind else {
        panic!("#990 top form must be a list");
    };

    for operation in ["+", "-", "*", "abs", "min", "max"] {
        let row = rows(top)
            .into_iter()
            .find(|row| text_field(row, "operation") == operation)
            .unwrap_or_else(|| panic!("shared operation missing: {operation}"));
        assert!(
            field(row, "operand-domain").is_some(),
            "operand domain missing for {operation}"
        );
        assert!(
            field(row, "result-domain").is_some(),
            "result domain missing for {operation}"
        );
        assert!(field(row, "arity").is_some(), "arity missing for {operation}");
        for island in ["common-lisp", "prolog", "clips", "datalog"] {
            assert_eq!(
                text_field(row, island),
                "present",
                "{operation} must be present on {island}"
            );
        }
    }
}
