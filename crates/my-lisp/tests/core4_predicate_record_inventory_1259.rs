//! #1259 observer for the Lisp-owned Core4 predicate/record migration inventory.
//!
//! This test validates only the inventory's classification shape. It does not
//! define predicate semantics, result values, or migration behavior.

use my_lisp::{parse, Expr, ExprKind};
use std::collections::{HashMap, HashSet};

const SOURCE: &str = include_str!("../../../knowledge/core4-predicate-record-inventory.lisp");

fn pair_symbol<'a>(entry: &'a Expr, key: &str) -> Option<&'a str> {
    let ExprKind::Pair(k, v) = &entry.kind else {
        return None;
    };
    let ExprKind::Symbol(k) = &k.kind else {
        return None;
    };
    if &**k != key {
        return None;
    }
    match &v.kind {
        ExprKind::Symbol(value) => Some(value.as_ref()),
        _ => None,
    }
}

fn row_fields(expr: &Expr) -> Option<HashMap<String, String>> {
    let ExprKind::List(entries) = &expr.kind else {
        return None;
    };
    let mut fields = HashMap::new();
    for entry in entries {
        for key in [
            "surface",
            "current-role",
            "target-role",
            "migration",
            "profile",
            "status",
            "semantic-change",
            "core1-core2-core3",
        ] {
            if let Some(value) = pair_symbol(entry, key) {
                fields.insert(key.to_string(), value.to_string());
            }
        }
    }
    Some(fields)
}

fn inventory_rows() -> Vec<HashMap<String, String>> {
    let forms = parse(SOURCE).expect("Core4 predicate/record inventory must parse");
    assert_eq!(forms.len(), 1, "inventory must remain one Lisp data document");
    let ExprKind::List(entries) = &forms[0].kind else {
        panic!("inventory root must be a list");
    };
    entries
        .iter()
        .skip(1)
        .filter_map(row_fields)
        .collect()
}

fn row<'a>(
    rows: &'a [HashMap<String, String>],
    surface: &str,
) -> &'a HashMap<String, String> {
    rows.iter()
        .find(|row| row.get("surface").map(String::as_str) == Some(surface))
        .unwrap_or_else(|| panic!("missing inventory row for {surface}"))
}

#[test]
fn inventory_is_explicitly_core4_only_and_non_semantic() {
    let rows = inventory_rows();
    let header = rows
        .iter()
        .find(|row| row.get("profile").map(String::as_str) == Some("core4"))
        .expect("inventory header must declare Core4");

    assert_eq!(header.get("status").map(String::as_str), Some("inventory-only"));
    assert_eq!(header.get("semantic-change").map(String::as_str), Some("forbidden"));
    assert_eq!(
        header.get("core1-core2-core3").map(String::as_str),
        Some("out-of-scope")
    );
}

#[test]
fn semantic_roots_have_distinct_roles_instead_of_one_bulk_rewrite_class() {
    let rows = inventory_rows();

    let atom = row(&rows, "atom");
    assert_eq!(
        atom.get("current-role").map(String::as_str),
        Some("classifier-observer")
    );
    assert_eq!(
        atom.get("target-role").map(String::as_str),
        Some("classifier-observer")
    );
    assert_eq!(
        atom.get("migration").map(String::as_str),
        Some("retain-richer-classifier-data")
    );

    let eq = row(&rows, "eq");
    assert_eq!(
        eq.get("current-role").map(String::as_str),
        Some("classifier-observer")
    );
    assert_eq!(eq.get("target-role").map(String::as_str), Some("predicate-question"));
    assert_eq!(
        eq.get("migration").map(String::as_str),
        Some("bounded-after-selected-core-signal")
    );

    for surface in ["equal?", "symbol?", "string?", "numeric-buffer?"] {
        let predicate = row(&rows, surface);
        assert_eq!(
            predicate.get("current-role").map(String::as_str),
            Some("predicate-question"),
            "{surface} must be inventoried as a question, not a classifier-only API"
        );
        assert_eq!(
            predicate.get("target-role").map(String::as_str),
            Some("predicate-question")
        );
    }

    let cond = row(&rows, "cond");
    assert_eq!(cond.get("current-role").map(String::as_str), Some("control-consumer"));
    assert_eq!(cond.get("target-role").map(String::as_str), Some("control-consumer"));

    let compatibility = row(&rows, "historical-two-part-cond");
    assert_eq!(
        compatibility.get("current-role").map(String::as_str),
        Some("compatibility")
    );

    let experiment = row(&rows, "core4-eq-answer-1258");
    assert_eq!(experiment.get("current-role").map(String::as_str), Some("test-only"));
    assert_eq!(experiment.get("target-role").map(String::as_str), Some("test-only"));
}

#[test]
fn inventory_uses_only_the_ratified_role_vocabulary() {
    let rows = inventory_rows();
    let allowed: HashSet<&str> = [
        "predicate-question",
        "classifier-observer",
        "control-consumer",
        "compatibility",
        "test-only",
    ]
    .into_iter()
    .collect();

    for row in &rows {
        for field in ["current-role", "target-role"] {
            if let Some(value) = row.get(field).map(String::as_str) {
                assert!(
                    allowed.contains(value),
                    "unratified migration role {value} in {field}"
                );
            }
        }
    }
}
