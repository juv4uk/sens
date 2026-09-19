use std::collections::HashSet;
use std::fs;
use std::path::PathBuf;

use my_lisp::semantic_registry_export::semantic_id_for_admitted_surface;
use my_lisp::{eval_program, load_core_library, parse, Expr, ExprKind, Session};

const CAR_SID_BITS: &str = "00000101";

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

fn kernel_names_for_sid(source: &str, wanted_sid: &str) -> HashSet<String> {
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

        let mut sid: Option<String> = None;
        let mut witnesses: Vec<Expr> = Vec::new();

        for field in &fields[1..] {
            match &field.kind {
                ExprKind::Pair(key, value)
                    if matches!(&key.kind, ExprKind::Symbol(s) if &**s == "sid") =>
                {
                    sid = Some(match &value.kind {
                        ExprKind::String(s) | ExprKind::Symbol(s) => s.to_string(),
                        _ => panic!("sid must be a string/bitstring"),
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

        if sid.as_deref() != Some(wanted_sid) {
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

fn kernel_car_block(source: &str) -> &str {
    let marker = "(sid      . \"00000101\")";
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
    assert_eq!(semantic_id_for_admitted_surface("car"), Some(0b0000_0101));

    let mut session = load_coordinate_session();

    let math = eval_program(
        r#"(semantic-coordinate-law-for-sid "00000101")"#,
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
        r#"(machine-capabilities-for-sid "00000101")"#,
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
    let kernels = kernel_names_for_sid(&kernel_source, CAR_SID_BITS);
    assert!(kernels.contains("my-lisp"));
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
