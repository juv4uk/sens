//! #989 executable Datalog arithmetic capability/absence witnesses.

use wsm_datalog_kernel::{Atom, Database, DatalogAbiAdapter, Evaluator, Program, Rule, Term, Value};
use wsm_kernel_c_abi::{
    WsmByteSpan, WsmKernelRequest, WsmMutableByteSpan, WsmStatus,
};

fn exchange(adapter: &DatalogAbiAdapter, payload: &[u8]) -> (WsmStatus, Vec<u8>) {
    let vtable = adapter.vtable();
    let mut output = vec![0u8; 256];
    let mut written = 0usize;
    let status = unsafe {
        vtable.exchange.expect("exchange")(
            vtable.context,
            WsmKernelRequest {
                semantic_id: 0b0000_1100,
                payload: WsmByteSpan {
                    ptr: payload.as_ptr(),
                    len: payload.len(),
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
fn arithmetic_payload_is_not_evaluated() {
    let mut db = Database::new();
    db.add_fact("value", vec![Value::int(2)]);
    db.add_fact("value", vec![Value::int(3)]);

    let adapter = DatalogAbiAdapter::new(db, Program::new());
    let vtable = adapter.vtable();
    assert_eq!(
        unsafe { vtable.start.expect("start")(vtable.context) },
        WsmStatus::Ok
    );

    let (status, output) = exchange(&adapter, b"(+ 2 3)");
    assert_eq!(status, WsmStatus::Ok);
    assert!(
        output.is_empty(),
        "Datalog treats the ABI payload as a relation-name query; it must not evaluate (+ 2 3)"
    );
    assert_eq!(
        adapter.last_semantic_id(),
        Some(wsm_datalog_kernel::SemanticId(0b0000_1100))
    );
    assert_eq!(
        unsafe { vtable.stop.expect("stop")(vtable.context) },
        WsmStatus::Ok
    );
}

#[test]
fn relational_fixpoint_cannot_compute_sum_from_integer_inputs() {
    let mut db = Database::new();
    db.add_fact("value", vec![Value::int(2)]);
    db.add_fact("value", vec![Value::int(3)]);

    let mut program = Program::new();
    program.add_rule(Rule::with_id(
        "copy-value",
        Atom::new("seen", vec![Term::v("X")]),
        vec![Atom::new("value", vec![Term::v("X")])],
    ));

    Evaluator::naive_fixpoint(&program, &mut db);

    let seen = db.relation("seen");
    assert!(seen.contains(&vec![Value::int(2)]));
    assert!(seen.contains(&vec![Value::int(3)]));
    assert!(
        !seen.contains(&vec![Value::int(5)]),
        "current relational evaluator preserves integer constants but does not synthesize 2+3=5"
    );
}

#[test]
fn integer_payload_is_supported_without_arithmetic_semantics() {
    let mut db = Database::new();
    db.add_fact("value", vec![Value::int(2)]);
    db.add_fact("value", vec![Value::int(3)]);

    let mut program = Program::new();
    program.add_rule(Rule::with_id(
        "copy-value",
        Atom::new("seen", vec![Term::v("X")]),
        vec![Atom::new("value", vec![Term::v("X")])],
    ));

    Evaluator::semi_naive_fixpoint(&program, &mut db);

    assert_eq!(db.relation("seen").len(), 2);
    assert!(db.relation("seen").contains(&vec![Value::int(2)]));
    assert!(db.relation("seen").contains(&vec![Value::int(3)]));
}
