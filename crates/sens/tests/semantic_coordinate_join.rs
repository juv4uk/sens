use std::collections::HashSet;
use std::fs;
use std::path::PathBuf;

use sens::semantic_registry_export::semantic_id_for_admitted_surface;
use sens::{eval_program, load_core_library, parse, Expr, ExprKind, Session, Sens8};

const CAR_SID: Sens8 = sens::sens!(00000101);

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

fn kernel_names_for_sid(source: &str, wanted_sid: Sens8) -> HashSet<String> {
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

        let mut sid: Option<Sens8> = None;
        let mut witnesses: Vec<Expr> = Vec::new();

        for field in &fields[1..] {
            match &field.kind {
                ExprKind::Pair(key, value)
                    if matches!(&key.kind, ExprKind::Symbol(s) if &**s == "sid") =>
                {
                    sid = Some(match &value.kind {
                        ExprKind::Sid(sid) => *sid,
                        other => panic!("kernel witness SID must be exact bare Sens8, got {other:?}"),
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


fn kernel_statuses_for_sid(source: &str, wanted_sid: Sens8) -> Vec<(String, String)> {
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
                        ExprKind::Sid(sid) => *sid,
                        other => panic!("kernel witness SID must be exact bare Sens8, got {other:?}"),
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

fn math_coordinate_value(session: &mut Session, sid: Sens8) -> String {
    eval_program(
        &format!("(semantic-coordinate-law-for-sid {sid})"),
        session,
    )
    .unwrap_or_else(|error| panic!("semantic coordinate lookup failed for {sid}: {error:?}"))
    .value
    .to_string()
}

fn machine_coordinate_value(session: &mut Session, exact_domain_bits: &str) -> String {
    eval_program(
        &format!("(machine-capabilities-for-domain {exact_domain_bits})"),
        session,
    )
    .unwrap_or_else(|error| {
        panic!(
            "exact-domain machine capability lookup failed for {exact_domain_bits}: {error:?}"
        )
    })
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
fn car_provenance_sid_keeps_math_kernel_history_while_machine_uses_exact_d3() {
    assert_eq!(semantic_id_for_admitted_surface("car"), Some(sens::sens!(00000101)));

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
        r#"(machine-capabilities-for-domain 100)"#,
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
    let kernels = kernel_names_for_sid(&kernel_source, CAR_SID);
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
fn add_provenance_sid_preserves_math_history_while_machine_uses_exact_d5() {
    assert_eq!(semantic_id_for_admitted_surface("+"), Some(sens::sens!(00001100)));

    let mut session = load_coordinate_session();
    let math = math_coordinate_value(&mut session, sens::sens!(00001100));
    let machine = machine_coordinate_value(&mut session, "01010");
    let kernel_source =
        fs::read_to_string(repo_root().join("contracts/sid-kernel-witness-735.lisp"))
            .expect("kernel witness contract");
    let kernels = kernel_statuses_for_sid(&kernel_source, sens::sens!(00001100));

    assert!(math.contains("exact-rational-sum"));
    assert_eq!(machine, "((integer-add bounded-u64))");
    assert!(kernels.is_empty(), "absence must remain explicit, not guessed");
    assert!(!math.contains("add-r64-r64"));
    assert!(!machine.contains("exact-rational-sum"));
}

#[test]
fn eq_provenance_sid_keeps_kernel_history_while_machine_uses_exact_d3() {
    assert_eq!(semantic_id_for_admitted_surface("eq?"), Some(sens::sens!(00000011)));

    let mut session = load_coordinate_session();
    let machine = machine_coordinate_value(&mut session, "101");
    let kernel_source =
        fs::read_to_string(repo_root().join("contracts/sid-kernel-witness-735.lisp"))
            .expect("kernel witness contract");
    let kernels = kernel_statuses_for_sid(&kernel_source, sens::sens!(00000011));

    assert_eq!(machine, "((identity-compare bounded-u64))");
    assert_eq!(kernels, vec![("sens".into(), "live".into())]);
}

#[test]
fn cons_provenance_sid_keeps_law_and_kernels_while_machine_uses_exact_d3() {
    assert_eq!(semantic_id_for_admitted_surface("cons"), Some(sens::sens!(00000100)));

    let mut session = load_coordinate_session();
    let math = math_coordinate_value(&mut session, sens::sens!(00000100));
    let machine = machine_coordinate_value(&mut session, "111");
    let kernel_source =
        fs::read_to_string(repo_root().join("contracts/sid-kernel-witness-735.lisp"))
            .expect("kernel witness contract");
    let kernels = kernel_statuses_for_sid(&kernel_source, sens::sens!(00000100));

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
fn cond_provenance_sid_keeps_history_while_machine_uses_exact_d3() {
    assert_eq!(semantic_id_for_admitted_surface("cond"), Some(sens::sens!(00000111)));

    let mut session = load_coordinate_session();
    let math = math_coordinate_value(&mut session, sens::sens!(00000111));
    let machine = machine_coordinate_value(&mut session, "110");
    let kernel_source =
        fs::read_to_string(repo_root().join("contracts/sid-kernel-witness-735.lisp"))
            .expect("kernel witness contract");
    let kernels = kernel_statuses_for_sid(&kernel_source, sens::sens!(00000111));

    assert!(math.contains("non-mathematical-in-this-slice"));
    assert!(math.contains("no-mathematical-law-claimed"));
    assert_eq!(machine, "((conditional-branch bounded-u64))");
    assert!(kernels.contains(&("sens".into(), "live".into())));
    assert!(kernels.contains(&("prolog".into(), "absent".into())));
    assert!(kernels.contains(&("clips".into(), "absent".into())));
    assert_eq!(kernels.len(), 3);
}
