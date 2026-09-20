//! #988 observer for the four-island mathematical capability projection.
//!
//! This is a read-only capability witness. It does not define mathematical
//! meaning and it does not allocate semantic identities.

use std::fs;
use std::path::PathBuf;

use my_lisp::{parse, Expr, ExprKind};

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(|path| path.parent())
        .expect("repo root")
        .to_path_buf()
}

fn read_contract() -> String {
    fs::read_to_string(repo_root().join("contracts/island-math-intersection-988.lisp"))
        .expect("#988 capability contract must exist")
}

fn field_string<'a>(fields: &'a [Expr], key: &str) -> Option<&'a str> {
    fields.iter().find_map(|entry| {
        let ExprKind::Pair(k, v) = &entry.kind else {
            return None;
        };
        let ExprKind::Symbol(name) = &k.kind else {
            return None;
        };
        if &**name != key {
            return None;
        }
        match &v.kind {
            ExprKind::String(value) | ExprKind::Symbol(value) => Some(value.as_ref()),
            _ => None,
        }
    })
}

fn row_lists<'a>(top: &'a [Expr]) -> Vec<&'a [Expr]> {
    top.iter()
        .filter_map(|entry| match &entry.kind {
            ExprKind::List(items)
                if matches!(
                    items.first().map(|expr| &expr.kind),
                    Some(ExprKind::List(_))
                ) =>
            {
                None
            }
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
fn contract_has_explicit_empty_four_way_native_intersection() {
    let source = read_contract();
    let forms = parse(&source).expect("#988 contract must parse");
    assert_eq!(forms.len(), 1);

    let ExprKind::List(top) = &forms[0].kind else {
        panic!("#988 top form must be a list");
    };
    assert!(matches!(
        &top[0].kind,
        ExprKind::Symbol(name) if &**name == "island-math-intersection/1"
    ));

    assert!(
        source.contains("(four-way-native-intersection . ())"),
        "the current native four-way arithmetic intersection must remain explicit"
    );
}

#[test]
fn every_candidate_preserves_the_current_datalog_gap() {
    let source = read_contract();
    let forms = parse(&source).expect("#988 contract must parse");
    let ExprKind::List(top) = &forms[0].kind else {
        panic!("#988 top form must be a list");
    };

    let rows = row_lists(top);
    assert!(
        rows.len() >= 20,
        "#988 should keep the candidate inventory broad; got {} rows",
        rows.len()
    );

    for row in &rows {
        let operation = field_string(row, "operation").expect("candidate operation");
        assert_eq!(
            field_string(row, "datalog"),
            Some("absent"),
            "Datalog capability gap must stay explicit for {operation}"
        );
        assert_eq!(
            field_string(row, "four-way-native?"),
            Some("no"),
            "no candidate may be promoted into the four-way native intersection before Datalog exists: {operation}"
        );
    }
}

#[test]
fn existing_semantic_ids_are_reused_and_not_minted_by_the_matrix() {
    let source = read_contract();

    for expected in [
        "(operation . "+")",
        "(semantic-id . "00001100")",
        "(operation . "-")",
        "(semantic-id . "00001101")",
        "(operation . "*")",
        "(semantic-id . "00001110")",
        "(operation . "/")",
        "(semantic-id . "00001111")",
        "(operation . "abs")",
        "(semantic-id . "00010000")",
        "(operation . "min")",
        "(semantic-id . "00010001")",
        "(operation . "max")",
        "(semantic-id . "00010010")",
        "(operation . "mod")",
        "(semantic-id . "00010011")",
        "(operation . "integer-quotient")",
        "(semantic-id . "00010100")",
        "(operation . "sqrt")",
        "(semantic-id . "00010101")",
    ] {
        assert!(
            source.contains(expected),
            "#988 must reference existing registry identity without deriving IDs from capability data: {expected}"
        );
    }
}
