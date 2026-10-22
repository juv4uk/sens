//! #1001 Datalog: old C-ABI byte witness, not SENS domain-law proof.
//! Current D5/D6 laws are admitted only through the distinct exact-domain path.

use wsm_datalog_kernel::{
    Atom, Database, DatalogAbiAdapter, Evaluator, Program, Rule, Term, Value,
    arithmetic::{
        DatalogMathError, NumericExpr, ArithmeticMechanism, parse_arithmetic_mechanism,
        LEGACY_ABI_ABS, LEGACY_ABI_ADD, LEGACY_ABI_DIV, LEGACY_ABI_MAX, LEGACY_ABI_MIN, LEGACY_ABI_MOD,
        LEGACY_ABI_MUL, LEGACY_ABI_QUOTIENT, LEGACY_ABI_SUB,
    },
};
use wsm_kernel_c_abi::{WsmByteSpan, WsmKernelRequest, WsmMutableByteSpan, WsmStatus};

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

/// These laws are owned by the current D5/D6 tables. The host can only
/// execute a typed mechanism received from SENS; it must not convert SID8,
/// domain bits or D7 spelling into a callable operation.
#[test]
fn present_day_ukr_tables_and_typed_arithmetic_mechanisms() {
    for (mechanism, width, bits, ukr, input, expected) in [
        (ArithmeticMechanism::Add, 5, "01010", "додати", "2 3", 5),
        (ArithmeticMechanism::Sub, 5, "01011", "відняти", "7 3", 4),
        (ArithmeticMechanism::Mul, 5, "10110", "помножити", "6 7", 42),
        (ArithmeticMechanism::Abs, 6, "010011", "модуль", "-5", 5),
        (ArithmeticMechanism::Min, 6, "110101", "найменше", "4 9", 4),
        (ArithmeticMechanism::Max, 6, "110111", "найбільше", "4 9", 9),
    ] {
        let table = match width {
            5 => include_str!("../../../lib/domains/d5.lisp"),
            6 => include_str!("../../../lib/domains/d6.lisp"),
            _ => unreachable!("only current D5/D6 evidence"),
        };
        let prefix = format!("  ({bits} ");
        let resident = table.lines().find(|line| line.starts_with(&prefix))
            .unwrap_or_else(|| panic!("Missing D{width}:{bits} resident"));
        assert!(resident.contains(&format!("(укр {ukr})")),
            "D{width}:{bits} changed its ratified Ukrainian projection");
        let operation = parse_arithmetic_mechanism(mechanism, input)
            .unwrap_or_else(|error| panic!("host mechanism {mechanism:?}: {error}"));
        assert_eq!(operation.evaluate(&std::collections::HashMap::new()),
            Ok(Value::int(expected)));
    }
    // Unsupported/untrusted text cannot become a mechanism selector.
    assert!(parse_arithmetic_mechanism(ArithmeticMechanism::Add, "+ 2 3").is_err());
    // Historical W8 ADD lives exclusively in the explicit legacy C-ABI test;
    // no runtime Rust function takes (domain width, bits) and invents identity.
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
        (LEGACY_ABI_ADD, b"2 3".as_slice(), b"5".as_slice()),
        (LEGACY_ABI_SUB, b"7 3".as_slice(), b"4".as_slice()),
        (LEGACY_ABI_MUL, b"6 7".as_slice(), b"42".as_slice()),
        (LEGACY_ABI_DIV, b"8 2".as_slice(), b"4".as_slice()),
        (LEGACY_ABI_MOD, b"7 3".as_slice(), b"1".as_slice()),
        (LEGACY_ABI_QUOTIENT, b"7 3".as_slice(), b"2".as_slice()),
        (LEGACY_ABI_ABS, b"-5".as_slice(), b"5".as_slice()),
        (LEGACY_ABI_MIN, b"4 9".as_slice(), b"4".as_slice()),
        (LEGACY_ABI_MAX, b"4 9".as_slice(), b"9".as_slice()),
    ] {
        let (status, output) = exchange_math(&adapter, semantic_id, arguments);
        assert_eq!(status, WsmStatus::Ok, "legacy-ABI byte {semantic_id:08b}");
        assert_eq!(output, expected, "legacy-ABI byte {semantic_id:08b}");
    }

    let (text_status, text_output) = exchange_math(&adapter, LEGACY_ABI_ADD, b"+ 2 3");
    assert_eq!(
        text_status,
        WsmStatus::KernelFailure,
        "operator text must not select semantic execution"
    );
    assert!(text_output.is_empty());

    let (sub_status, sub_output) = exchange_math(&adapter, LEGACY_ABI_SUB, b"7 3");
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
