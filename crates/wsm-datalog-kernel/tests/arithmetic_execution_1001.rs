//! #1001 Datalog: old C-ABI byte witness, not SENS domain-law proof.
//! Current D5/D6 laws are admitted only through the distinct exact-domain path.

use wsm_datalog_kernel::{
    Atom, Database, DatalogAbiAdapter, Evaluator, Program, Rule, Term, Value,
    arithmetic::{
        DatalogMathError, NumericExpr, parse_exact_domain_request,
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

/// Current SENS ownership is D5/D6 exact-domain words and their full укр
/// projection, not the flat historical one-byte C-ABI mechanism slot.
#[test]
fn present_day_domain_ladder_executes_exact_ukr_math_without_sid8() {
    for (width, bits, ukr, input, expected) in [
        (5, "01010", "додати", "2 3", 5),
        (5, "01011", "відняти", "7 3", 4),
        (5, "10110", "помножити", "6 7", 42),
        (6, "010011", "модуль", "-5", 5),
        (6, "110101", "найменше", "4 9", 4),
        (6, "110111", "найбільше", "4 9", 9),
    ] {
        let operation = parse_exact_domain_request(width, bits, input)
            .unwrap_or_else(|error| panic!("D{width}:{bits} {ukr}: {error}"));
        // Ratified domain tables are authority, not the flat 8-bit ABI.
        // Verify the Ukrainian callable spelling against the current row.
        let table = match width {
            5 => include_str!("../../../lib/domains/d5.lisp"),
            6 => include_str!("../../../lib/domains/d6.lisp"),
            _ => unreachable!("only current D5/D6 admitted"),
        };
        let prefix = format!("  ({bits} ");
        let resident = table.lines().find(|line| line.starts_with(&prefix))
            .unwrap_or_else(|| panic!("Missing resident D{width}:{bits}"));
        assert!(resident.contains(&format!("(укр {ukr})")),
            "D{width}:{bits} changed its ratified Ukrainian projection");
        assert_eq!(operation.evaluate(&std::collections::HashMap::new()),
            Ok(Value::int(expected)), "D{width}:{bits} {ukr}");
    }
    for (width, bits, input) in [
        (8, "00001100", "2 3"), // old W8 ADD != D8 resident
        (5, "00001100", "2 3"), // incorrect width
        (5, "10111", "7 3"),    // D5 quotient needs SENS rational-law parity
        (6, "010100", "7 3"),   // D6 remainder needs signed-law parity
        (8, "11110110", "7 3"), // D8 division needs separate callability proof
    ] {
        assert!(matches!(
            parse_exact_domain_request(width, bits, input),
            Err(DatalogMathError::UnsupportedDomainOperation { .. })
        ), "cannot infer current identity from historical SID8: D{width}:{bits}");
    }
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
