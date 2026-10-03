use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use sens::semantic_registry_export::semantic_id_for_admitted_surface;
use sens::{eval_program, load_core_library, parse, Expr, ExprKind, Session};

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

fn matrix_source_path(key: &str) -> String {
    let source = read("contracts/semantic-coordinate-matrix-845.lisp");
    let forms = parse(&source).expect("matrix contract must parse");
    let ExprKind::List(top) = &forms[0].kind else {
        panic!("matrix contract top form must be a list");
    };

    top.iter()
        .find_map(|entry| {
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
                ExprKind::String(value) | ExprKind::Symbol(value) => {
                    Some(value.to_string())
                }
                _ => None,
            }
        })
        .unwrap_or_else(|| panic!("matrix contract missing {key}"))
}

fn load_axis_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must load");

    for key in ["math-axis-source", "machine-axis-source"] {
        let path = matrix_source_path(key);
        let source = read(&path);
        eval_program(&source, &mut session)
            .unwrap_or_else(|error| panic!("{path} must load: {error:?}"));
    }

    session
}

fn kernel_statuses_for_sid(
    source: &str,
    wanted_sid: u8,
) -> Option<BTreeMap<String, String>> {
    let exprs = parse(source).expect("kernel witness contract must parse");
    let ExprKind::List(items) = &exprs[0].kind else {
        panic!("kernel witness map must be a list");
    };

    for entry in &items[1..] {
        let ExprKind::List(fields) = &entry.kind else {
            continue;
        };
        if !matches!(
            fields.first().map(|expr| &expr.kind),
            Some(ExprKind::Symbol(symbol)) if &**symbol == "sid-witness"
        ) {
            continue;
        }

        let mut sid = None;
        let mut witness_items: Vec<Expr> = Vec::new();

        for field in &fields[1..] {
            match &field.kind {
                ExprKind::Pair(key, value)
                    if matches!(
                        &key.kind,
                        ExprKind::Symbol(symbol) if &**symbol == "sid"
                    ) =>
                {
                    sid = match &value.kind {
                        ExprKind::Sid(identity) => identity.legacy8_bits(),
                        other => panic!("kernel witness must be exact bare legacy-8, got {other:?}"),
                    };
                }
                ExprKind::List(items)
                    if !items.is_empty()
                        && matches!(
                            &items[0].kind,
                            ExprKind::Symbol(symbol) if &**symbol == "witnesses"
                        ) =>
                {
                    witness_items = items[1..].to_vec();
                }
                _ => {}
            }
        }

        if sid != Some(wanted_sid) {
            continue;
        }

        let mut statuses = BTreeMap::new();
        for witness in witness_items {
            let ExprKind::List(items) = witness.kind else {
                continue;
            };
            if !matches!(
                items.first().map(|expr| &expr.kind),
                Some(ExprKind::Symbol(symbol)) if &**symbol == "witness"
            ) {
                continue;
            }

            let mut kernel = None;
            let mut status = None;
            for field in &items[1..] {
                let ExprKind::Pair(key, value) = &field.kind else {
                    continue;
                };
                let ExprKind::Symbol(key_name) = &key.kind else {
                    continue;
                };
                match (&**key_name, &value.kind) {
                    ("kernel", ExprKind::Symbol(value)) => {
                        kernel = Some(value.to_string());
                    }
                    ("status", ExprKind::Symbol(value)) => {
                        status = Some(value.to_string());
                    }
                    _ => {}
                }
            }

            if let (Some(kernel), Some(status)) = (kernel, status) {
                statuses.insert(kernel, status);
            }
        }

        return Some(statuses);
    }

    None
}

fn math_coordinate(session: &mut Session, sid: u8) -> String {
    eval_program(
        &format!("(semantic-coordinate-law-for-sid {sid:08b})"),
        session,
    )
    .expect("math coordinate query")
    .value
    .to_string()
}

fn machine_coordinate(session: &mut Session, sid: u8) -> String {
    eval_program(
        &format!("(machine-capabilities-for-sid {sid:08b})"),
        session,
    )
    .expect("machine coordinate query")
    .value
    .to_string()
}

#[test]
fn remaining_bounded_scope_preserves_asymmetric_coordinates() {
    assert_eq!(semantic_id_for_admitted_surface("+").map(|sid| sid.packed_byte()), Some(0b0000_1100));
    assert_eq!(semantic_id_for_admitted_surface("eq?").map(|sid| sid.packed_byte()), Some(0b0000_0011));
    assert_eq!(semantic_id_for_admitted_surface("cons").map(|sid| sid.packed_byte()), Some(0b0000_0100));
    assert_eq!(semantic_id_for_admitted_surface("cond").map(|sid| sid.packed_byte()), Some(0b0000_0111));

    let kernel_path = matrix_source_path("kernel-axis-source");
    let kernel_source = read(&kernel_path);
    let mut session = load_axis_session();

    // + : mathematical law + physical capability exist, but #735 has no
    // semantic kernel witness row yet. Absence is evidence, not an error.
    let add_math = math_coordinate(&mut session, 0b0000_1100);
    assert!(add_math.contains("exact-rational-sum"));
    assert_eq!(
        machine_coordinate(&mut session, 0b0000_1100),
        "((integer-add bounded-u64))"
    );
    assert_eq!(kernel_statuses_for_sid(&kernel_source, 0b0000_1100), None);

    // EQ : Function8 execution witness + bounded machine compare.
    let eq_kernels =
        kernel_statuses_for_sid(&kernel_source, 0b0000_0011).expect("EQ kernel row");
    assert_eq!(eq_kernels.len(), 1);
    assert_eq!(eq_kernels.get("sens").map(String::as_str), Some("live"));
    assert_eq!(
        machine_coordinate(&mut session, 0b0000_0011),
        "((identity-compare bounded-u64))"
    );

    // CONS : equational pair law + two execution witnesses + two field stores.
    let cons_math = math_coordinate(&mut session, 0b0000_0100);
    assert!(cons_math.contains("car-cons-left-inverse"));
    let cons_kernels =
        kernel_statuses_for_sid(&kernel_source, 0b0000_0100).expect("CONS kernel row");
    assert_eq!(cons_kernels.get("sens").map(String::as_str), Some("live"));
    assert_eq!(
        cons_kernels.get("common-lisp").map(String::as_str),
        Some("integration-gated")
    );
    assert_eq!(
        machine_coordinate(&mut session, 0b0000_0100),
        "((pair-field-store head bounded-u64) (pair-field-store tail bounded-u64))"
    );

    // COND : the math axis explicitly refuses to invent a mathematical law;
    // kernel map records live sens and explicit absent foreign witnesses;
    // machine axis records only the bounded conditional branch capability.
    let cond_math = math_coordinate(&mut session, 0b0000_0111);
    assert!(cond_math.contains("non-mathematical-in-this-slice"));
    assert!(cond_math.contains("no-mathematical-law-claimed"));
    let cond_kernels =
        kernel_statuses_for_sid(&kernel_source, 0b0000_0111).expect("COND kernel row");
    assert_eq!(cond_kernels.get("sens").map(String::as_str), Some("live"));
    assert_eq!(cond_kernels.get("prolog").map(String::as_str), Some("absent"));
    assert_eq!(cond_kernels.get("clips").map(String::as_str), Some("absent"));
    assert_eq!(
        machine_coordinate(&mut session, 0b0000_0111),
        "((conditional-branch bounded-u64))"
    );
}

#[test]
fn coordinate_axes_do_not_leak_each_others_payloads() {
    let math = read(&matrix_source_path("math-axis-source"));
    let kernel = read(&matrix_source_path("kernel-axis-source"));
    let machine = read(&matrix_source_path("machine-axis-source"));

    for forbidden in ["x86-lower-", "admitted-form", "pair-field-load"] {
        assert!(!math.contains(forbidden), "math axis leaked {forbidden}");
        assert!(!kernel.contains(forbidden), "kernel axis leaked {forbidden}");
    }

    for forbidden in ["common-lisp", "prolog", "clips", "datalog"] {
        assert!(!math.contains(forbidden), "math axis leaked {forbidden}");
        assert!(!machine.contains(forbidden), "machine axis leaked {forbidden}");
    }

    for forbidden in ["exact-rational-sum", "car-cons-left-inverse"] {
        assert!(!kernel.contains(forbidden), "kernel axis leaked {forbidden}");
        assert!(!machine.contains(forbidden), "machine axis leaked {forbidden}");
    }
}
