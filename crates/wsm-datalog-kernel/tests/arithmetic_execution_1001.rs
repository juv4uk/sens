//! #1001 native Datalog arithmetic witnesses.

use wsm_datalog_kernel::{
    arithmetic::{
        DatalogMathError, NumericExpr, SID_ABS, SID_ADD, SID_DIV, SID_MAX, SID_MIN, SID_MOD,
        SID_MUL, SID_QUOTIENT, SID_SUB,
    },
    Atom, Database, DatalogAbiAdapter, Evaluator, Program, Rule, Term, Value,
};
use wsm_kernel_c_abi::{
    WsmByteSpan, WsmKernelRequest, WsmMutableByteSpan, WsmStatus,
};

fn exchange_math(
    adapter: &DatalogAbiAdapter,
    semantic_id: u8,
    arguments: &[u8],
) -> (WsmStatus, Vec<u8>) {
    let vtable = adapter.vtable();
    let mut output = vec![0u8; 64];
    let mut written = 0usize;
    let status = unsafe {
        vtable.exchange.expect("exchange")(
            vtable.context,
            WsmKernelRequest {
                semantic_id,
                payload: WsmByteSpan {
                    ptr: arguments.as_ptr(),
                    len: arguments.len(),
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
fn numeric_term_evaluates_after_relation_binding() {
    let mut db = Database::new();
    db.add_fact("value", vec![Value::int(7)]);

    let mut program = Program::new();
    program.add_rule(Rule::with_id(
        "sum-plus-three",
        Atom::new(
            "sum",
            vec![Term::Numeric(NumericExpr::Add(
                Box::new(NumericExpr::Variable("X".into())),
                Box::new(NumericExpr::Literal(3)),
            ))],
        ),
        vec![Atom::new("value", vec![Term::v("X")])],
    ));

    Evaluator::naive_fixpoint(&program, &mut db);

    assert_eq!(
        db.relation("sum"),
        &std::collections::HashSet::from([vec![Value::int(10)]])
    );
}

#[test]
fn numeric_term_can_match_a_relation_after_binding() {
    let mut db = Database::new();
    db.add_fact("value", vec![Value::int(7)]);
    db.add_fact("answer", vec![Value::int(10)]);

    let mut program = Program::new();
    program.add_rule(Rule::with_id(
        "select-sum",
        Atom::new("selected", vec![Term::v("X")]),
        vec![
            Atom::new("value", vec![Term::v("X")]),
            Atom::new(
                "answer",
                vec![Term::Numeric(NumericExpr::Add(
                    Box::new(NumericExpr::Variable("X".into())),
                    Box::new(NumericExpr::Literal(3)),
                ))],
            ),
        ],
    ));

    Evaluator::naive_fixpoint(&program, &mut db);

    assert!(db.relation("selected").contains(&vec![Value::int(7)]));
}

#[test]
fn c_abi_executes_the_admitted_integer_math_surface() {
    let adapter = DatalogAbiAdapter::new(Database::new(), Program::new());
    let vtable = adapter.vtable();
    assert_eq!(
        unsafe { vtable.start.expect("start")(vtable.context) },
        WsmStatus::Ok
    );

    for (semantic_id, arguments, expected) in [
        (SID_ADD, b"2 3".as_slice(), b"5".as_slice()),
        (SID_SUB, b"7 3".as_slice(), b"4".as_slice()),
        (SID_MUL, b"6 7".as_slice(), b"42".as_slice()),
        (SID_DIV, b"8 2".as_slice(), b"4".as_slice()),
        (SID_MOD, b"7 3".as_slice(), b"1".as_slice()),
        (SID_QUOTIENT, b"7 3".as_slice(), b"2".as_slice()),
        (SID_ABS, b"-5".as_slice(), b"5".as_slice()),
        (SID_MIN, b"4 9".as_slice(), b"4".as_slice()),
        (SID_MAX, b"4 9".as_slice(), b"9".as_slice()),
    ] {
        let (status, output) = exchange_math(&adapter, semantic_id, arguments);
        assert_eq!(status, WsmStatus::Ok, "SID {semantic_id:08b}");
        assert_eq!(output, expected, "SID {semantic_id:08b}");
    }

    let (text_status, text_output) = exchange_math(&adapter, SID_ADD, b"+ 2 3");
    assert_eq!(
        text_status,
        WsmStatus::KernelFailure,
        "operator text must not select semantic execution"
    );
    assert!(text_output.is_empty());

    let (sub_status, sub_output) = exchange_math(&adapter, SID_SUB, b"7 3");
    assert_eq!(sub_status, WsmStatus::Ok);
    assert_eq!(sub_output, b"4");

    assert_eq!(
        unsafe { vtable.stop.expect("stop")(vtable.context) },
        WsmStatus::Ok
    );
}

#[test]
fn arithmetic_failures_stay_typed_in_the_kernel() {
    assert_eq!(
        NumericExpr::Div(
            Box::new(NumericExpr::Literal(1)),
            Box::new(NumericExpr::Literal(0)),
        )
        .evaluate(&std::collections::HashMap::new()),
        Err(DatalogMathError::DivisionByZero)
    );

    assert_eq!(
        NumericExpr::Abs(Box::new(NumericExpr::Literal(i64::MIN)))
            .evaluate(&std::collections::HashMap::new()),
        Err(DatalogMathError::Overflow)
    );
}
