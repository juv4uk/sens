use std::collections::HashSet;
use std::fs;
use std::path::PathBuf;

use sens::semantic_registry_export::semantic_id_for_admitted_surface;
use sens::{eval_program, load_core_library, parse, Expr, ExprKind, Session};

const CAR_BITS: u8 = 0b0000_0101;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(|p| p.parent())
        .expect("repo root")
        .to_path_buf()
}

fn load_coordinate_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must load");

    for path in [
        "tests/fixtures/semantic-coordinate-law-axis-v1.lisp",
        "lib/machine/capability-axis.lisp",
    ] {
        let source = fs::read_to_string(repo_root().join(path))
            .unwrap_or_else(|error| panic!("{path} must be readable: {error}"));
        eval_program(&source, &mut session)
            .unwrap_or_else(|error| panic!("{path} must load: {error:?}"));
    }
    session
}

fn kernel_names_for_sid(source: &str, wanted_sid: u8) -> HashSet<String> {
    let exprs = parse(source).expect("kernel witness contract must parse");
    let map_items = match &exprs[0].kind {
        ExprKind::List(items) => items,
        _ => panic!("kernel witness map must be a list"),
    };

    for entry in &map_items[1..] {
        let fields = match &entry.kind {
            ExprKind::List(items) => items,
            _ => continue,
        };
        if fields.is_empty()
            || !matches!(&fields[0].kind, ExprKind::Symbol(s) if &**s == "sid-witness")
        {
            continue;
        }

        let mut sid: Option<u8> = None;
        let mut witnesses: Vec<Expr> = Vec::new();

        for field in &fields[1..] {
            match &field.kind {
                ExprKind::Pair(key, value)
                    if matches!(&key.kind, ExprKind::Symbol(s) if &**s == "sid") =>
                {
                    sid = Some(match &value.kind {
                        ExprKind::Sid(identity) => identity
                            .legacy8_bits()
                            .expect("kernel witness must carry historical exact-8 identity"),
                        other => panic!("kernel witness must be exact bare legacy-8, got {other:?}"),
                    });
                }
                ExprKind::List(items)
                    if !items.is_empty()
                        && matches!(&items[0].kind, ExprKind::Symbol(s) if &**s == "witnesses") =>
                {
                    witnesses = items[1..].to_vec();
                }
                _ => {}
            }
        }

        if sid != Some(wanted_sid) {
            continue;
        }

        let mut kernels = HashSet::new();
        for witness in witnesses {
            let items = match witness.kind {
                ExprKind::List(items) => items,
                _ => continue,
            };
            if items.is_empty()
                || !matches!(&items[0].kind, ExprKind::Symbol(s) if &**s == "witness")
            {
                continue;
            }
            for field in &items[1..] {
                if let ExprKind::Pair(key, value) = &field.kind {
                    if matches!(&key.kind, ExprKind::Symbol(s) if &**s == "kernel") {
                        if let ExprKind::Symbol(s) = &value.kind {
                            kernels.insert(s.to_string());
                        }
                    }
                }
            }
        }
        return kernels;
    }

    panic!("SID {wanted_sid} missing from kernel witness map");
}


fn kernel_statuses_for_sid(source: &str, wanted_sid: u8) -> Vec<(String, String)> {
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
        let mut witnesses = Vec::new();
        for field in &fields[1..] {
            match &field.kind {
                ExprKind::Pair(key, value)
                    if matches!(&key.kind, ExprKind::Symbol(symbol) if &**symbol == "sid") =>
                {
                    sid = Some(match &value.kind {
                        ExprKind::Sid(identity) => identity
                            .legacy8_bits()
                            .expect("kernel witness must carry historical exact-8 identity"),
                        other => panic!("kernel witness must be exact bare legacy-8, got {other:?}"),
                    });
                }
                ExprKind::List(w)
                    if matches!(
                        w.first().map(|expr| &expr.kind),
                        Some(ExprKind::Symbol(symbol)) if &**symbol == "witnesses"
                    ) =>
                {
                    witnesses = w[1..].to_vec();
                }
                _ => {}
            }
        }

        if sid != Some(wanted_sid) {
            continue;
        }

        let mut out = Vec::new();
        for witness in witnesses {
            let ExprKind::List(fields) = witness.kind else {
                continue;
            };
            let mut kernel = None;
            let mut status = None;
            for field in &fields[1..] {
                let ExprKind::Pair(key, value) = &field.kind else {
                    continue;
                };
                let ExprKind::Symbol(key) = &key.kind else {
                    continue;
                };
                match &**key {
                    "kernel" => {
                        if let ExprKind::Symbol(value) = &value.kind {
                            kernel = Some(value.to_string());
                        }
                    }
                    "status" => {
                        if let ExprKind::Symbol(value) = &value.kind {
                            status = Some(value.to_string());
                        }
                    }
                    _ => {}
                }
            }
            if let (Some(kernel), Some(status)) = (kernel, status) {
                out.push((kernel, status));
            }
        }
        return out;
    }

    Vec::new()
}

fn math_coordinate_value(session: &mut Session, sid: u8) -> String {
    eval_program(
        &format!("(semantic-coordinate-law-for-sid {sid:08b})"),
        session,
    )
    .unwrap_or_else(|error| panic!("semantic coordinate lookup failed for {sid}: {error:?}"))
    .value
    .to_string()
}

fn machine_coordinate_value(session: &mut Session, sid: u8) -> String {
    eval_program(
        &format!("(machine-capabilities-for-sid {sid:08b})"),
        session,
    )
    .unwrap_or_else(|error| panic!("machine capability lookup failed for {sid}: {error:?}"))
    .value
    .to_string()
}

fn kernel_car_block(source: &str) -> &str {
    let marker = "(sid      . 00000101)";
    let sid_pos = source.find(marker).expect("CAR SID row");
    let start = source[..sid_pos]
        .rfind("(sid-witness")
        .expect("CAR sid-witness start");
    let rest = &source[sid_pos + marker.len()..];
    let end = rest
        .find("\n\n  (sid-witness")
        .map(|offset| sid_pos + marker.len() + offset)
        .unwrap_or(source.len());
    &source[start..end]
}

#[test]
fn car_sid_joins_math_kernel_and_machine_axes_without_collapsing_them() {
    assert_eq!(semantic_id_for_admitted_surface("car").map(|sid| sid.packed_byte()), Some(0b0000_0101));

    let mut session = load_coordinate_session();

    let math = eval_program(
        r#"(semantic-coordinate-law-for-sid 00000101)"#,
        &mut session,
    )
    .expect("CAR mathematical coordinate")
    .value
    .to_string();
    assert!(math.contains("car-cons-left-inverse"));
    assert!(!math.contains("x86"));
    assert!(!math.contains("pair-field-load"));
    assert!(!math.contains("common-lisp"));

    let machine = eval_program(
        r#"(machine-capabilities-for-sid 00000101)"#,
        &mut session,
    )
    .expect("CAR machine capability coordinate")
    .value
    .to_string();
    assert_eq!(machine, "((pair-field-load head bounded-u64))");
    assert!(!machine.contains("car-cons-left-inverse"));
    assert!(!machine.contains("common-lisp"));

    let kernel_source = fs::read_to_string(repo_root().join("contracts/sid-kernel-witness-735.lisp"))
        .expect("kernel witness contract");
    let kernels = kernel_names_for_sid(&kernel_source, CAR_BITS);
    assert!(kernels.contains("sens"));
    assert!(kernels.contains("common-lisp"));
    assert!(!kernels.contains("prolog"));
    assert!(!kernels.contains("datalog"));
    assert!(!kernels.contains("clips"));

    let car_block = kernel_car_block(&kernel_source);
    assert!(!car_block.contains("x86"));
    assert!(!car_block.contains("mov-"));
    assert!(!car_block.contains("pair-field-load"));
    assert!(!car_block.contains("car-cons-left-inverse"));
}


#[test]
fn add_sid_preserves_math_and_machine_evidence_with_explicit_kernel_gap() {
    assert_eq!(semantic_id_for_admitted_surface("+").map(|sid| sid.packed_byte()), Some(0b0000_1100));

    let mut session = load_coordinate_session();
    let math = math_coordinate_value(&mut session, 0b0000_1100);
    let machine = machine_coordinate_value(&mut session, 0b0000_1100);
    let kernel_source =
        fs::read_to_string(repo_root().join("contracts/sid-kernel-witness-735.lisp"))
            .expect("kernel witness contract");
    let kernels = kernel_statuses_for_sid(&kernel_source, 0b0000_1100);

    assert!(math.contains("exact-rational-sum"));
    assert_eq!(machine, "((integer-add bounded-u64))");
    assert!(kernels.is_empty(), "absence must remain explicit, not guessed");
    assert!(!math.contains("add-r64-r64"));
    assert!(!machine.contains("exact-rational-sum"));
}

#[test]
fn eq_sid_keeps_sens_and_compare_capability_without_old_relation_axis() {
    assert_eq!(semantic_id_for_admitted_surface("eq?").map(|sid| sid.packed_byte()), Some(0b0000_0011));

    let mut session = load_coordinate_session();
    let machine = machine_coordinate_value(&mut session, 0b0000_0011);
    let kernel_source =
        fs::read_to_string(repo_root().join("contracts/sid-kernel-witness-735.lisp"))
            .expect("kernel witness contract");
    let kernels = kernel_statuses_for_sid(&kernel_source, 0b0000_0011);

    assert_eq!(machine, "((identity-compare bounded-u64))");
    assert_eq!(kernels, vec![("sens".into(), "live".into())]);
}

#[test]
fn cons_sid_joins_pair_law_two_kernel_witnesses_and_pair_store_capability() {
    assert_eq!(semantic_id_for_admitted_surface("cons").map(|sid| sid.packed_byte()), Some(0b0000_0100));

    let mut session = load_coordinate_session();
    let math = math_coordinate_value(&mut session, 0b0000_0100);
    let machine = machine_coordinate_value(&mut session, 0b0000_0100);
    let kernel_source =
        fs::read_to_string(repo_root().join("contracts/sid-kernel-witness-735.lisp"))
            .expect("kernel witness contract");
    let kernels = kernel_statuses_for_sid(&kernel_source, 0b0000_0100);

    assert!(math.contains("car-cons-left-inverse"));
    assert_eq!(
        machine,
        "((pair-field-store head bounded-u64) (pair-field-store tail bounded-u64))"
    );
    assert!(kernels.contains(&("sens".into(), "live".into())));
    assert!(kernels.contains(&("common-lisp".into(), "integration-gated".into())));
    assert_eq!(kernels.len(), 2);
}

#[test]
fn cond_sid_keeps_negative_math_evidence_and_absent_external_kernels_visible() {
    assert_eq!(semantic_id_for_admitted_surface("cond").map(|sid| sid.packed_byte()), Some(0b0000_0111));

    let mut session = load_coordinate_session();
    let math = math_coordinate_value(&mut session, 0b0000_0111);
    let machine = machine_coordinate_value(&mut session, 0b0000_0111);
    let kernel_source =
        fs::read_to_string(repo_root().join("contracts/sid-kernel-witness-735.lisp"))
            .expect("kernel witness contract");
    let kernels = kernel_statuses_for_sid(&kernel_source, 0b0000_0111);

    assert!(math.contains("non-mathematical-in-this-slice"));
    assert!(math.contains("no-mathematical-law-claimed"));
    assert_eq!(machine, "((conditional-branch bounded-u64))");
    assert!(kernels.contains(&("sens".into(), "live".into())));
    assert!(kernels.contains(&("prolog".into(), "absent".into())));
    assert!(kernels.contains(&("clips".into(), "absent".into())));
    assert_eq!(kernels.len(), 3);
}
