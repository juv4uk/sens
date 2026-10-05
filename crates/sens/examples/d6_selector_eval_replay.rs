//! #3583 — real-evaluator replay for the current D6 selector family.
//!
//! Benchmark-only. No production dispatch is changed.
//! D6 exact words are compared with an equivalent nested chain of exact D3
//! CAR/CDR DomainCall nodes and with the shared exact D3 QUOTE argument alone.

use sens::{
    eval_parsed_expressions, Bija3, Bit3, Bit6, CoreD6, CoreDomainIdentity, Exactness, Expr,
    ExprKind, Session, Span,
};
use std::{env, hint::black_box, process::ExitCode, rc::Rc};

const SELECTORS: [u8; 16] = [
    0b011000, 0b011001, 0b011010, 0b011011,
    0b011100, 0b011101, 0b011110, 0b011111,
    0b100000, 0b100001, 0b100010, 0b100011,
    0b100100, 0b100101, 0b100110, 0b100111,
];

fn span() -> Span {
    Span { start: 0, end: 0 }
}

fn expr(kind: ExprKind) -> Expr {
    Expr { kind, span: span() }
}

fn d3(raw: u8) -> CoreDomainIdentity {
    CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(raw).unwrap()))
}

fn d6(raw: u8) -> CoreDomainIdentity {
    CoreDomainIdentity::D6(CoreD6::from_word(Bit6::new(raw).unwrap()))
}

fn call(identity: CoreDomainIdentity, argument: Expr) -> Expr {
    expr(ExprKind::DomainCall(identity, vec![argument].into()))
}

fn pair(left: Expr, right: Expr) -> Expr {
    expr(ExprKind::Pair(Rc::new(left), Rc::new(right)))
}

fn data_tree() -> Expr {
    let mut level: Vec<Expr> = (1..=16)
        .map(|n| expr(ExprKind::Number(n as f64, Exactness::Exact)))
        .collect();
    while level.len() > 1 {
        let mut next = Vec::with_capacity(level.len() / 2);
        for chunk in level.as_chunks::<2>().0 {
            next.push(pair(chunk[0].clone(), chunk[1].clone()));
        }
        level = next;
    }
    level.pop().unwrap()
}

fn quoted_tree() -> Expr {
    call(d3(0b001), data_tree())
}

fn d6_form(raw: u8) -> Expr {
    call(d6(raw), quoted_tree())
}

fn d3_chain_form(raw: u8) -> Expr {
    let root = raw >> 3;
    assert!(root == 0b100 || root == 0b011);

    let mut operations = [0u8; 4];
    operations[0] = root;
    for i in 0..3 {
        let shift = 2 - i;
        operations[i + 1] = if ((raw >> shift) & 1) == 0 {
            0b100 // CAR
        } else {
            0b011 // CDR
        };
    }

    let mut current = quoted_tree();
    for operation in operations.into_iter().rev() {
        current = call(d3(operation), current);
    }
    current
}

fn quote_form() -> Expr {
    quoted_tree()
}

fn expected_leaf(raw: u8) -> u32 {
    let root = raw >> 3;
    let root_bit = match root {
        0b100 => 0u8,
        0b011 => 1u8,
        _ => panic!("not a selector root: {raw:06b}"),
    };
    let path = (raw & 0b111) | (root_bit << 3);

    let mut index = 0u32;
    for shift in 0..4 {
        index = index * 2 + 1 + u32::from((path >> shift) & 1);
    }
    index - 14
}

fn eval_one(form: &Expr, session: &mut Session) -> String {
    eval_parsed_expressions(std::slice::from_ref(form), session)
        .expect("prepared exact-domain form must evaluate")
        .value
        .to_string()
}

fn verify() -> u64 {
    let mut checksum = 0u64;
    for raw in SELECTORS {
        let mut a = Session::default();
        let mut b = Session::default();
        let d6_result = eval_one(&d6_form(raw), &mut a);
        let chain_result = eval_one(&d3_chain_form(raw), &mut b);
        assert_eq!(d6_result, chain_result, "D6/D3-chain parity for {raw:06b}");
        let expected = expected_leaf(raw).to_string();
        assert_eq!(d6_result, expected, "independent tree oracle for {raw:06b}");
        checksum = checksum.wrapping_add(expected.parse::<u64>().unwrap());
    }
    checksum
}

fn forms(mode: &str) -> Vec<Expr> {
    match mode {
        "d6" => SELECTORS.into_iter().map(d6_form).collect(),
        "d3-chain" => SELECTORS.into_iter().map(d3_chain_form).collect(),
        "quote-only" => (0..16).map(|_| quote_form()).collect(),
        _ => panic!("unknown mode: {mode}"),
    }
}

fn choose(pattern: &str, i: usize, state: &mut u64) -> usize {
    match pattern {
        "repeated" => 0,
        "alternating" => if i & 1 == 0 { 0 } else { 15 },
        "random" => {
            *state = state
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            ((*state >> 32) as usize) & 15
        }
        _ => panic!("unknown pattern: {pattern}"),
    }
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    if args.len() != 5 {
        eprintln!("usage: d6_selector_eval_replay MODE PHASE PATTERN CALLS");
        return ExitCode::from(2);
    }
    let mode = args[1].as_str();
    let phase = args[2].as_str();
    let pattern = args[3].as_str();
    let calls = args[4].parse::<usize>().expect("CALLS");
    assert!(calls > 0);

    let oracle = verify();
    if mode == "verify" {
        println!("VERIFY\tPASS\tchecksum={oracle}");
        return ExitCode::SUCCESS;
    }

    let prepared = forms(mode);
    black_box(&prepared);
    println!("ORACLE_CHECKSUM\t{oracle}");
    println!("FORMS\t{}", prepared.len());

    if phase == "prepare" {
        println!("CHECKSUM\t{}", prepared.len());
        return ExitCode::SUCCESS;
    }
    assert_eq!(phase, "full", "phase must be prepare or full");

    let mut session = Session::default();
    let mut state = 0x9E37_79B9_7F4A_7C15u64;
    let mut last = None;
    for i in 0..calls {
        let index = choose(pattern, i, &mut state);
        let outcome = eval_parsed_expressions(std::slice::from_ref(&prepared[index]), &mut session)
            .expect("prepared evaluator replay");
        last = Some(black_box(outcome.value));
    }
    black_box(last);

    println!("CHECKSUM\t{}", oracle.wrapping_add(calls as u64));
    ExitCode::SUCCESS
}
