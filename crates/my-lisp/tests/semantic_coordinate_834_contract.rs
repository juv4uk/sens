//! #834 observer for the Lisp-owned mathematical-law coordinate view.
//! This test checks structure/provenance only; mathematical meaning remains in Lisp.

use std::collections::HashSet;
use std::fs;
use std::path::PathBuf;

use my_lisp::{eval_program, load_core_library, parse, Expr, ExprKind, Session};

fn repo_file(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(relative)
}

fn pair_string<'a>(entries: &'a [Expr], key: &str) -> Option<&'a str> {
    entries.iter().find_map(|entry| {
        let ExprKind::Pair(k, v) = &entry.kind else { return None; };
        let ExprKind::Symbol(name) = &k.kind else { return None; };
        if &**name != key { return None; }
        match &v.kind {
            ExprKind::String(s) | ExprKind::Symbol(s) => Some(s.as_ref()),
            _ => None,
        }
    })
}

#[test]
fn lisp_owned_coordinate_contract_is_well_formed_and_registry_backed() {
    let source = fs::read_to_string(repo_file("contracts/semantic-mathematical-coordinate-834.lisp"))
        .expect("#834 coordinate contract");
    let forms = parse(&source).expect("#834 coordinate contract must parse");
    assert_eq!(forms.len(), 1);
    let ExprKind::List(top) = &forms[0].kind else { panic!("#834 top form must be a list"); };
    assert!(matches!(&top[0].kind, ExprKind::Symbol(s) if &**s == "semantic-mathematical-coordinate/1"));

    let rows = top
        .iter()
        .find_map(|entry| {
            let ExprKind::List(items) = &entry.kind else { return None; };
            if !matches!(&items.first()?.kind, ExprKind::Symbol(s) if &**s == "rows") {
                return None;
            }
            Some(&items[1..])
        })
        .expect("#834 rows field");

    let registry = fs::read_to_string(repo_file("lib/surface/semantic-registry.lisp"))
        .expect("canonical semantic registry");
    let mut seen = HashSet::new();

    for row in rows.iter() {
        let ExprKind::List(items) = row else { panic!("#834 row must be a list"); };
        let sid = pair_string(items, "sid").expect("#834 row SID");
        assert_eq!(sid.len(), 8);
        assert!(sid.chars().all(|ch| ch == '0' || ch == '1'));
        assert!(seen.insert(sid.to_string()), "duplicate #834 SID {sid}");
        assert!(
            registry.contains(&format!("(\"{}\" ", sid)),
            "#834 SID {sid} must come from canonical sr/2 registry"
        );
        let witness = pair_string(items, "witness").expect("#834 witness path");
        assert!(repo_file(witness).is_file(), "missing #834 witness {witness}");
    }

    assert_eq!(seen.len(), 5, "#834 bounded slice must contain exactly five SIDs");
}

#[test]
fn lisp_owned_mathematical_coordinate_witness_passes() {
    let source = fs::read_to_string(repo_file(
        "tests/fixtures/semantic-coordinate-math-834.lisp",
    ))
    .expect("#834 witness");
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    let result = eval_program(&source, &mut session)
        .expect("#834 Lisp witness must execute")
        .value
        .to_string();
    assert!(
        result.starts_with("(semantic-coordinate-math-834 (status pass)"),
        "#834 Lisp-owned witness failed: {result}"
    );
}
