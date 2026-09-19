use wsm_datalog_kernel::{
    Atom, Database, DatalogAbiAdapter, Program, Rule, SemanticId, Term, Value,
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
fn opaque_semantic_id_crosses_same_c_abi_into_datalog_fixpoint() {
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
    assert_eq!(adapter.last_semantic_id(), Some(SemanticId(PROBE_ID)));

    assert_eq!(
        unsafe { vtable.stop.expect("stop")(vtable.context) },
        WsmStatus::Ok
    );
}
