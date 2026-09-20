//! #1001 native Datalog arithmetic witnesses.

use wsm_datalog_kernel::{
    arithmetic::{DatalogMathError, NumericExpr},
    Atom, Database, DatalogAbiAdapter, Evaluator, Program, Rule, Term, Value,
};
use wsm_kernel_c_abi::{
    WsmByteSpan, WsmKernelRequest, WsmMutableByteSpan, WsmStatus,
};

fn exchange_math(adapter: &DatalogAbiAdapter, request: &[u8]) -> (WsmStatus, Vec<u8>) {
    let vtable = adapter.vtable();
    let mut output = vec![0u8; 64];
    let mut written = 0usize;
    let status = unsafe {
        vtable.exchange.expect("exchange")(
            vtable.context,
            WsmKernelRequest {
                semantic_id: 0b0000_1100,
                payload: WsmByteSpan {
                    ptr: request.as_ptr(),
                    len: request.len(),
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

    for (request, expected) in [
        (b"math + 2 3".as_slice(), b"5".as_slice()),
        (b"math - 7 3".as_slice(), b"4".as_slice()),
        (b"math * 6 7".as_slice(), b"42".as_slice()),
        (b"math / 8 2".as_slice(), b"4".as_slice()),
        (b"math mod 7 3".as_slice(), b"1".as_slice()),
        (b"math quotient 7 3".as_slice(), b"2".as_slice()),
        (b"math abs -5".as_slice(), b"5".as_slice()),
        (b"math min 4 9".as_slice(), b"4".as_slice()),
        (b"math max 4 9".as_slice(), b"9".as_slice()),
    ] {
        let (status, output) = exchange_math(&adapter, request);
        assert_eq!(status, WsmStatus::Ok, "request {:?}", request);
        assert_eq!(output, expected, "request {:?}", request);
    }

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
