//! #845 v2 observer for the read-only SID coordinate matrix.
//!
//! Coordinates are derived from the existing axis sources. This observer does
//! not define SID meaning and does not maintain a copied semantic table.

use std::collections::HashSet;
use std::fs;
use std::path::PathBuf;

use sens::{parse, Expr, ExprKind};

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(|path| path.parent())
        .expect("repo root")
        .to_path_buf()
}

fn read(relative: &str) -> String {
    fs::read_to_string(repo_root().join(relative))
        .unwrap_or_else(|error| panic!("{relative}: {error}"))
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

fn matrix_sources_and_scope() -> (String, String, String, String, Vec<u8>) {
    let source = read("contracts/semantic-coordinate-matrix-845.lisp");
    let forms = parse(&source).expect("#845 matrix v2 must parse");
    assert_eq!(forms.len(), 1);

    let ExprKind::List(top) = &forms[0].kind else {
        panic!("matrix v2 top form must be a list");
    };
    assert!(matches!(
        &top[0].kind,
        ExprKind::Symbol(symbol) if &**symbol == "semantic-coordinate-matrix/2"
    ));

    let identity = field_string(top, "identity-source")
        .expect("identity-source")
        .to_string();
    let math = field_string(top, "math-axis-source")
        .expect("math-axis-source")
        .to_string();
    let kernel = field_string(top, "kernel-axis-source")
        .expect("kernel-axis-source")
        .to_string();
    let machine = field_string(top, "machine-axis-source")
        .expect("machine-axis-source")
        .to_string();

    assert_eq!(
        field_string(top, "missing-axis-policy"),
        Some("explicit"),
        "missing axis evidence must stay explicit"
    );

    let scope = top
        .iter()
        .find_map(|entry| {
            let ExprKind::List(items) = &entry.kind else {
                return None;
            };
            if !matches!(
                items.first().map(|expr| &expr.kind),
                Some(ExprKind::Symbol(symbol)) if &**symbol == "scope"
            ) {
                return None;
            }
            Some(
                items[1..]
                    .iter()
                    .map(|expr| match &expr.kind {
                        ExprKind::Sid(identity) => identity
                            .legacy8_bits()
                            .expect("scope entry must be historical exact-8 identity"),
                        other => panic!("scope SID must be exact bare legacy-8, got {other:?}"),
                    })
                    .collect::<Vec<_>>(),
            )
        })
        .expect("scope");

    (identity, math, kernel, machine, scope)
}

/// The law axis has a row keyed by `wanted_sid` inside the quoted data of
/// `semantic-coordinate-law-axis-v1`. A structural check: since the fixture
/// is written in SENS codes, its own `(00001000 ...)` lambdas must not count
/// as a lambda row.
fn law_axis_has_row(source: &str, wanted_sid: u8) -> bool {
    let exprs = parse(source).expect("law axis must parse");
    exprs.iter().any(|expr| {
        let ExprKind::List(definition) = &expr.kind else {
            return false;
        };
        let named = matches!(
            definition.get(1).map(|e| &e.kind),
            Some(ExprKind::Symbol(name)) if name.as_ref() == "semantic-coordinate-law-axis-v1"
        );
        if !named {
            return false;
        }
        let Some(ExprKind::List(quoted)) = definition.get(2).map(|e| &e.kind) else {
            return false;
        };
        let Some(ExprKind::List(rows)) = quoted.get(1).map(|e| &e.kind) else {
            return false;
        };
        rows.iter().any(|row| match &row.kind {
            ExprKind::List(items) => {
                matches!(items.first().map(|e| &e.kind), Some(ExprKind::Sid(identity)) if identity.legacy8_bits() == Some(wanted_sid))
            }
            _ => false,
        })
    })
}

fn source_has_bare_sid(source: &str, sid: u8) -> bool {
    source.contains(&format!("({sid:08b}"))
}

fn machine_axis_has_row(source: &str, wanted_sid: u8) -> bool {
    let exprs = parse(source).expect("machine capability axis must parse");

    exprs.iter().any(|expr| {
        let ExprKind::List(definition) = &expr.kind else {
            return false;
        };
        let Some(Expr {
            kind: ExprKind::Sid(define_sid),
            ..
        }) = definition.first()
        else {
            return false;
        };
        if define_sid.legacy8_bits() != Some(0b0000_1001) {
            return false;
        }
        if !matches!(
            definition.get(1).map(|expr| &expr.kind),
            Some(ExprKind::Symbol(name)) if &**name == "machine-capability-axis-v1"
        ) {
            return false;
        }

        let Some(quoted) = definition.get(2) else {
            return false;
        };
        let ExprKind::List(quote_form) = &quoted.kind else {
            return false;
        };
        if !matches!(
            quote_form.first().map(|expr| &expr.kind),
            Some(ExprKind::Sid(identity))
                if identity.legacy8_bits() == Some(0b0000_0001)
        ) {
            return false;
        }
        let Some(rows) = quote_form.get(1) else {
            return false;
        };
        let ExprKind::List(rows) = &rows.kind else {
            return false;
        };

        rows.iter().any(|row| {
            let ExprKind::List(fields) = &row.kind else {
                return false;
            };
            matches!(
                fields.first().map(|expr| &expr.kind),
                Some(ExprKind::Sid(identity)) if identity.legacy8_bits() == Some(wanted_sid)
            )
        })
    })
}

fn kernel_map_has_sid(source: &str, wanted_sid: u8) -> bool {
    let exprs = parse(source).expect("kernel witness contract must parse");
    let ExprKind::List(items) = &exprs[0].kind else {
        panic!("kernel witness map must be a list");
    };

    items[1..].iter().any(|entry| {
        let ExprKind::List(fields) = &entry.kind else {
            return false;
        };
        if !matches!(
            fields.first().map(|expr| &expr.kind),
            Some(ExprKind::Symbol(symbol)) if &**symbol == "sid-witness"
        ) {
            return false;
        }

        fields.iter().any(|field| {
            let ExprKind::Pair(key, value) = &field.kind else {
                return false;
            };
            matches!(&key.kind, ExprKind::Symbol(symbol) if &**symbol == "sid")
                && matches!(&value.kind, ExprKind::Sid(identity) if identity.legacy8_bits() == Some(wanted_sid))
        })
    })
}

#[test]
fn bounded_matrix_derives_coordinates_from_live_axes() {
    let (identity_path, math_path, kernel_path, machine_path, scope) =
        matrix_sources_and_scope();

    assert_eq!(scope.len(), 5);
    assert_eq!(scope.iter().collect::<HashSet<_>>().len(), 5);

    let identity = read(&identity_path);
    let math = read(&math_path);
    let kernel = read(&kernel_path);
    let machine = read(&machine_path);

    for sid in &scope {
        assert!(
            identity.contains(&format!("({sid:08b} ")),
            "SID {sid} must exist in canonical semantic registry"
        );

        // Presence is derived, never copied into the matrix contract.
        let _math_present = law_axis_has_row(&math, *sid);
        let _machine_present = source_has_bare_sid(&machine, *sid);
    }

    // Machine coordinates remain present for the whole bounded slice.
    for sid in &scope {
        assert!(
            source_has_bare_sid(&machine, *sid),
            "machine axis missing scoped SID {sid}"
        );
    }

    // EQ remains a scoped semantic identity, but its retired relation-law row
    // is intentionally absent. Missing axis evidence must stay explicit rather
    // than recreating identity-relation authority.
    assert!(!law_axis_has_row(&math, 0b0000_0011));
    for sid in [
        0b0000_1100,
        0b0000_0100,
        0b0000_0101,
        0b0000_0111,
    ] {
        assert!(law_axis_has_row(&math, sid), "math axis missing {sid}");
    }

    // Kernel evidence is intentionally asymmetric: + currently has no
    // sid-witness row, while eq/cons/car/cond do.
    assert!(!kernel_map_has_sid(&kernel, 0b0000_1100));
    for sid in [
        0b0000_0011,
        0b0000_0100,
        0b0000_0101,
        0b0000_0111,
    ] {
        assert!(kernel_map_has_sid(&kernel, sid), "kernel axis missing {sid}");
    }

    // COND's math coordinate is negative evidence, not a fabricated law.
    assert!(math.contains("non-mathematical-in-this-slice"));
    assert!(math.contains("no-mathematical-law-claimed"));
}

#[test]
fn missing_axis_evidence_does_not_erase_a_semantic_identity() {
    let (identity_path, math_path, kernel_path, machine_path, _) =
        matrix_sources_and_scope();

    const LAMBDA_SID: u8 = 0b0000_1000;

    let identity = read(&identity_path);
    let math = read(&math_path);
    let kernel = read(&kernel_path);
    let machine = read(&machine_path);

    assert!(identity.contains(&format!("({LAMBDA_SID:08b} ")));
    assert!(kernel_map_has_sid(&kernel, LAMBDA_SID));
    assert!(!law_axis_has_row(&math, LAMBDA_SID));
    assert!(!machine_axis_has_row(&machine, LAMBDA_SID));
}

#[test]
fn matrix_contract_does_not_copy_axis_payloads() {
    let source = read("contracts/semantic-coordinate-matrix-845.lisp");

    for forbidden in [
        "kernel-entry-status",
        "math-entry-sid",
        "machine-entry-sid",
        "pair-field-load",
        "integer-add",
        "common-lisp",
        "car-cons-left-inverse",
        "x86-lower-",
        "admitted-form",
    ] {
        assert!(
            !source.contains(forbidden),
            "matrix contract must not copy axis payload {forbidden}"
        );
    }
}
