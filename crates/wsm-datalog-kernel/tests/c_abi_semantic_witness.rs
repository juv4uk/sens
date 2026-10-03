use wsm_datalog_kernel::{
    Atom, Database, DatalogAbiAdapter, Program, Rule, LegacyAbiSemanticId, Term, Value,
};
use wsm_kernel_c_abi::{
    WsmByteSpan, WsmKernelKind, WsmKernelRequest, WsmMutableByteSpan, WsmStatus,
};

const PROBE_ID: u8 = 0b0000_0100;

fn fixture() -> (Database, Program) {
    let mut db = Database::new();
    db.add_fact("edge", vec![Value::int(1), Value::int(2)]);
    db.add_fact("edge", vec![Value::int(2), Value::int(3)]);
    db.add_fact("edge", vec![Value::int(3), Value::int(4)]);
    db.add_fact("singleton", vec![Value::sym("only")]);

    let mut program = Program::new();
    program.add_rule(Rule::with_id(
        "path-base",
        Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
        vec![Atom::new("edge", vec![Term::v("X"), Term::v("Y")])],
    ));
    program.add_rule(Rule::with_id(
        "path-rec",
        Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
        vec![
            Atom::new("edge", vec![Term::v("X"), Term::v("Z")]),
            Atom::new("path", vec![Term::v("Z"), Term::v("Y")]),
        ],
    ));
    (db, program)
}

#[test]
fn opaque_legacy_abi_id_crosses_same_c_abi_into_datalog_fixpoint() {
    let (db, program) = fixture();
    let adapter = DatalogAbiAdapter::new(db, program);
    let vtable = adapter.vtable();

    assert_eq!(vtable.kernel, WsmKernelKind::Datalog);
    assert_eq!(
        unsafe { vtable.start.expect("start")(vtable.context) },
        WsmStatus::Ok
    );

    let query = b"path";
    let mut output = [0u8; 256];
    let mut written = 0usize;
    let status = unsafe {
        vtable.exchange.expect("exchange")(
            vtable.context,
            WsmKernelRequest {
                semantic_id: PROBE_ID,
                payload: WsmByteSpan {
                    ptr: query.as_ptr(),
                    len: query.len(),
                },
            },
            WsmMutableByteSpan {
                ptr: output.as_mut_ptr(),
                len: output.len(),
            },
            &mut written,
        )
    };

    assert_eq!(status, WsmStatus::Ok);
    assert_eq!(
        String::from_utf8_lossy(&output[..written]),
        "path(1,2)\npath(1,3)\npath(1,4)\npath(2,3)\npath(2,4)\npath(3,4)\n"
    );
    assert_eq!(adapter.last_legacy_abi_id(), Some(LegacyAbiSemanticId(PROBE_ID)));

    assert_eq!(
        unsafe { vtable.stop.expect("stop")(vtable.context) },
        WsmStatus::Ok
    );
}

fn exchange_relation(adapter: &DatalogAbiAdapter, relation: &[u8]) -> (WsmStatus, Vec<u8>) {
    let vtable = adapter.vtable();
    let mut output = vec![0u8; 256];
    let mut written = 0usize;
    let status = unsafe {
        vtable.exchange.expect("exchange")(
            vtable.context,
            WsmKernelRequest {
                semantic_id: PROBE_ID,
                payload: WsmByteSpan {
                    ptr: relation.as_ptr(),
                    len: relation.len(),
                },
            },
            WsmMutableByteSpan {
                ptr: output.as_mut_ptr(),
                len: output.len(),
            },
            &mut written,
        )
    };
    output.truncate(written.min(output.len()));
    (status, output)
}

#[test]
fn datalog_native_relations_preserve_zero_one_many_without_truth_projection() {
    let (db, program) = fixture();
    let adapter = DatalogAbiAdapter::new(db, program);
    let vtable = adapter.vtable();
    assert_eq!(
        unsafe { vtable.start.expect("start")(vtable.context) },
        WsmStatus::Ok
    );

    let (zero_status, zero) = exchange_relation(&adapter, b"missing");
    assert_eq!(zero_status, WsmStatus::Ok);
    assert!(zero.is_empty(), "empty relation stays an empty Datalog observation");

    let (one_status, one) = exchange_relation(&adapter, b"singleton");
    assert_eq!(one_status, WsmStatus::Ok);
    assert_eq!(String::from_utf8_lossy(&one), "singleton(only)\n");

    let (many_status, many) = exchange_relation(&adapter, b"path");
    assert_eq!(many_status, WsmStatus::Ok);
    assert_eq!(many.iter().filter(|byte| **byte == b'\n').count(), 6);

    assert_eq!(adapter.last_legacy_abi_id(), Some(LegacyAbiSemanticId(PROBE_ID)));
    assert_eq!(
        unsafe { vtable.stop.expect("stop")(vtable.context) },
        WsmStatus::Ok
    );
}
