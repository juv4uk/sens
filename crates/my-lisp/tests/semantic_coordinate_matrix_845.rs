//! #845 observer for the read-only SID coordinate matrix.
//! The observer composes existing source artifacts; it does not define semantics.

use std::collections::HashSet;
use std::fs;
use std::path::PathBuf;

use my_lisp::{eval_program, load_core_library, parse, Expr, ExprKind, Session};

fn repo_file(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..").join(relative)
}

fn read(relative: &str) -> String {
    fs::read_to_string(repo_file(relative)).unwrap_or_else(|e| panic!("{relative}: {e}"))
}

fn field_string<'a>(fields: &'a [Expr], key: &str) -> Option<&'a str> {
    fields.iter().find_map(|entry| {
        let ExprKind::Pair(k, v) = &entry.kind else { return None; };
        let ExprKind::Symbol(name) = &k.kind else { return None; };
        if &**name != key { return None; }
        match &v.kind {
            ExprKind::String(value) | ExprKind::Symbol(value) => Some(value.as_ref()),
            _ => None,
        }
    })
}

#[test]
fn matrix_is_a_view_over_existing_source_axes() {
    let source = read("contracts/semantic-coordinate-matrix-845.lisp");
    let forms = parse(&source).expect("#845 matrix must parse");
    assert_eq!(forms.len(), 1);
    let ExprKind::List(top) = &forms[0].kind else { panic!("#845 top form must be a list"); };
    assert!(matches!(&top[0].kind, ExprKind::Symbol(s) if &**s == "semantic-coordinate-matrix/1"));

    let identity = field_string(top, "identity-source").expect("identity source");
    let math = field_string(top, "math-axis-source").expect("math source");
    let kernel = field_string(top, "kernel-axis-source").expect("kernel source");
    let machine = field_string(top, "machine-axis-source").expect("machine source");
    assert_eq!(identity, "lib/surface/semantic-registry.lisp");
    assert_eq!(math, "tests/fixtures/semantic-coordinate-law-axis-v1.lisp");
    assert_eq!(kernel, "contracts/sid-kernel-witness-735.lisp");
    assert_eq!(machine, "lib/machine/capability-axis.lisp");

    let registry = read(identity);
    let math_source = read(math);
    let kernel_source = read(kernel);
    let machine_source = read(machine);

    let rows = top.iter().find_map(|entry| {
        let ExprKind::List(items) = &entry.kind else { return None; };
        if !matches!(&items.first()?.kind, ExprKind::Symbol(s) if &**s == "rows") { return None; }
        let row_container = items.get(1)?;
        let ExprKind::List(rows) = &row_container.kind else { return None; };
        Some(rows)
    }).expect("#845 rows");

    let mut seen = HashSet::new();
    for row in rows {
        let ExprKind::List(fields) = &row.kind else { panic!("#845 row must be a list"); };
        let sid = field_string(fields, "sid").expect("row SID");
        let math_sid = field_string(fields, "math-entry-sid").expect("math SID");
        let kernel_sid = field_string(fields, "kernel-entry-sid").expect("kernel SID");
        let machine_sid = field_string(fields, "machine-entry-sid").expect("machine SID");
        assert!(seen.insert(sid.to_string()), "duplicate matrix SID {sid}");
        assert_eq!(sid, math_sid);
        assert_eq!(sid, kernel_sid);
        assert_eq!(sid, machine_sid);
        assert_eq!(sid.len(), 8);
        assert!(sid.chars().all(|c| c == '0' || c == '1'));
        assert!(registry.contains(&format!("(\"{sid}\" ")), "SID {sid} absent from sr/2");
        assert!(math_source.contains(sid));
        assert!(kernel_source.contains(sid));
        assert!(machine_source.contains(sid));
    }
    assert_eq!(seen.len(), 5);

    // Boundary-specific evidence required by the issue.
    assert!(math_source.contains("non-mathematical-in-this-slice"));
    assert!(kernel_source.contains("(kernel . common-lisp)"));
    assert!(machine_source.contains("pair-field-load head"));
    assert!(machine_source.contains("conditional-branch bounded-u64"));
}

#[test]
fn coordinate_view_fixture_is_lisp_owned() {
    let source = read("tests/fixtures/semantic-coordinate-matrix-845.lisp");
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    let value = eval_program(&source, &mut session)
        .expect("#845 fixture must execute")
        .value
        .to_string();
    assert_eq!(value, "(semantic-coordinate-matrix-845 (status pass) (axes independent) (authority canonical-sid-registry) (rows 5))");
}