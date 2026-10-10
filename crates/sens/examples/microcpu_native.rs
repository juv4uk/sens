//! Experimental native CPU slot tape for exact D1/D3 packed T5.
//!
//! Only the existing SENS T5 decoder and D2 reader establish source framing;
//! the compiled tape is a disposable, restricted mechanism and cannot mint
//! language semantics. A unsupported domain/syntax fails closed, never falling
//! back to historic Lisp or legacy eight-bit routing.
//!
//! Reproduction:
//!   cargo test --locked -p sens --example microcpu_native -- --nocapture
//!   cargo run --release --locked -p sens --example microcpu_native -- --samples 11 --loops 500

use sens::{
    decode_ternary_words, encode_binary_projection_ternary, eval_t5_program,
    parse_canonical_word_sequence, BinarySourceWord, DomainIdentity, Expr, ExprKind,
    Session, Value,
};
use std::hint::black_box;
use std::rc::Rc;
use std::time::Instant;

const MAX_DEPTH: usize = 128;
const MAX_SLOTS: usize = 100_000;
const MAX_STACK: usize = 100_000;

/// Internal CPU instruction tags; never new domain words or source syntax.
#[derive(Clone, Debug)]
enum Slot {
    Push(Value),
    Atom,
    Car,
    Cdr,
    Eq,
    Cons,
    SkipZero(usize),
    Jump(usize),
}

#[derive(Debug)]
struct Tape {
    forms: Vec<Vec<Slot>>,
    bytes: usize,
    words: usize,
}

impl Tape {
    fn slots(&self) -> usize {
        self.forms.iter().map(Vec::len).sum()
    }
}

fn blocked(message: &str) -> String {
    format!("MICROCPU BLOCKED: {message}")
}

/// Ratified D2 reader is the sole grammar authority; check the experiment's
/// stricter subset *before* discarding source-word provenance into an AST.
fn subset_framing(words: &[BinarySourceWord]) -> Result<(), String> {
    if words.is_empty() {
        return Err(blocked("empty T5 stream"));
    }
    for (index, word) in words.iter().enumerate() {
        match (word.width(), word.packed_bits()) {
            (2, 3) => return Err(blocked("dotted D2 outside the bounded subset")),
            (2, 2) => {
                let mut next = index + 1;
                while next < words.len()
                    && words[next].width() == 2
                    && words[next].packed_bits() == 0
                {
                    next += 1;
                }
                if next < words.len()
                    && words[next].width() == 2
                    && words[next].packed_bits() == 1
                {
                    return Err(blocked("D2 empty list is not canonical D3:000"));
                }
            }
            _ => {}
        }
    }
    Ok(())
}

fn quote_datum(expression: &Expr, depth: usize) -> Result<Value, String> {
    if depth >= MAX_DEPTH {
        return Err(blocked("quoted structure depth exceeded"));
    }
    match &expression.kind {
        ExprKind::List(items) => {
            if items.is_empty() {
                Ok(Value::Nil)
            } else {
                Ok(Value::list(
                    items
                        .iter()
                        .map(|item| quote_datum(item, depth + 1))
                        .collect::<Result<Vec<_>, _>>()?,
                ))
            }
        }
        ExprKind::DomainIdentity(domain)
            if matches!(domain, DomainIdentity::D1(_) | DomainIdentity::D3(_)) =>
        {
            Ok(Value::DomainIdentity(*domain))
        }
        _ => Err(blocked("unsupported quoted data domain")),
    }
}

struct Builder {
    ops: Vec<Slot>,
}

impl Builder {
    fn new() -> Self {
        Self { ops: Vec::new() }
    }

    fn push(&mut self, slot: Slot) -> Result<usize, String> {
        if self.ops.len() >= MAX_SLOTS {
            return Err(blocked("slot count exhausted"));
        }
        let at = self.ops.len();
        self.ops.push(slot);
        Ok(at)
    }

    fn patch(&mut self, at: usize, target: usize) -> Result<(), String> {
        if at >= target || target > self.ops.len() {
            return Err(blocked("invalid forward-only branch"));
        }
        let slot = self
            .ops
            .get_mut(at)
            .ok_or_else(|| blocked("missing branch slot"))?;
        match slot {
            Slot::SkipZero(to) | Slot::Jump(to) => *to = target,
            _ => return Err(blocked("branch target is not a jump")),
        }
        Ok(())
    }

    fn expression(&mut self, expression: &Expr, depth: usize) -> Result<(), String> {
        if depth >= MAX_DEPTH {
            return Err(blocked("expression depth exceeded"));
        }
        match &expression.kind {
            ExprKind::DomainIdentity(DomainIdentity::D1(_)) => {
                self.push(Slot::Push(quote_datum(expression, depth + 1)?))?;
            }
            ExprKind::List(items) if items.is_empty() => {
                self.push(Slot::Push(Value::Nil))?;
            }
            ExprKind::List(items) => {
                let Some(head) = items.first() else {
                    return Err(blocked("empty call"));
                };
                let ExprKind::DomainIdentity(domain) = &head.kind else {
                    return Err(blocked("only exact D3 heads are callable"));
                };
                if domain.width() != 3 || domain.packed_bits() == 0 {
                    return Err(blocked("unratified call head"));
                }
                let args = &items[1..];
                match domain.packed_bits() {
                    1 => {
                        if args.len() != 1 {
                            return Err(blocked("D3 QUOTE needs one datum"));
                        }
                        self.push(Slot::Push(quote_datum(&args[0], depth + 1)?))?;
                    }
                    op @ (2 | 3 | 4) => {
                        if args.len() != 1 {
                            return Err(blocked("D3 unary arity"));
                        }
                        self.expression(&args[0], depth + 1)?;
                        let instruction = match op {
                            2 => Slot::Atom,
                            3 => Slot::Cdr,
                            _ => Slot::Car,
                        };
                        self.push(instruction)?;
                    }
                    op @ (5 | 7) => {
                        if args.len() != 2 {
                            return Err(blocked("D3 binary arity"));
                        }
                        self.expression(&args[0], depth + 1)?;
                        self.expression(&args[1], depth + 1)?;
                        self.push(if op == 5 { Slot::Eq } else { Slot::Cons })?;
                    }
                    6 => {
                        // Validate *all* clause shapes before executing any test.
                        for clause in args {
                            match &clause.kind {
                                ExprKind::List(parts) if parts.len() == 2 => {}
                                _ => {
                                    return Err(blocked(
                                        "D3 COND requires exact (test expression) clauses",
                                    ))
                                }
                            }
                        }
                        let mut ends = Vec::new();
                        for clause in args {
                            let ExprKind::List(parts) = &clause.kind else {
                                unreachable!("clauses validated above")
                            };
                            self.expression(&parts[0], depth + 1)?;
                            let skip = self.push(Slot::SkipZero(0))?;
                            self.expression(&parts[1], depth + 1)?;
                            ends.push(self.push(Slot::Jump(0))?);
                            self.patch(skip, self.ops.len())?;
                        }
                        self.push(Slot::Push(Value::Nil))?;
                        for end in ends {
                            self.patch(end, self.ops.len())?;
                        }
                    }
                    _ => return Err(blocked("unratified D3 call")),
                }
            }
            _ => return Err(blocked("executable domain outside D1/D3 subset")),
        }
        Ok(())
    }
}

fn compile_physical(physical: &[u8]) -> Result<Tape, String> {
    let words = decode_ternary_words(physical)
        .map_err(|error| format!("MICROCPU T5 REJECTED: {error:?}"))?;
    subset_framing(&words)?;
    let forms = parse_canonical_word_sequence(&words)
        .map_err(|error| format!("MICROCPU D2 REJECTED: {error}"))?;
    if forms.is_empty() {
        return Err(blocked("no expressions"));
    }
    let mut tapes = Vec::with_capacity(forms.len());
    let mut total = 0usize;
    for form in &forms {
        let mut builder = Builder::new();
        builder.expression(form, 0)?;
        total = total
            .checked_add(builder.ops.len())
            .ok_or_else(|| blocked("slot count overflow"))?;
        if total > MAX_SLOTS {
            return Err(blocked("total slot budget exceeded"));
        }
        tapes.push(builder.ops);
    }
    Ok(Tape {
        forms: tapes,
        bytes: physical.len(),
        words: words.len(),
    })
}

fn evaluate_slots(tape: &Tape) -> Result<Value, String> {
    let mut result = Value::Nil;
    for program in &tape.forms {
        let mut pc = 0usize;
        let mut stack = Vec::<Value>::new();
        while pc < program.len() {
            match &program[pc] {
                Slot::Push(value) => stack.push(value.clone()),
                Slot::Atom => {
                    let value = stack.pop().ok_or_else(|| blocked("ATOM stack underflow"))?;
                    stack.push(Value::predicate_bit(value.is_atom()));
                }
                Slot::Car | Slot::Cdr => {
                    let value = stack.pop().ok_or_else(|| blocked("pair stack underflow"))?;
                    let Value::Pair(head, tail) = value else {
                        return Err(blocked("D3 CAR/CDR expects pair"));
                    };
                    stack.push(if matches!(program[pc], Slot::Car) {
                        (*head).clone()
                    } else {
                        (*tail).clone()
                    });
                }
                Slot::Eq => {
                    let right = stack.pop().ok_or_else(|| blocked("EQ missing right"))?;
                    let left = stack.pop().ok_or_else(|| blocked("EQ missing left"))?;
                    if !left.is_atom() || !right.is_atom() {
                        return Err(blocked("D3 EQ is atom-only"));
                    }
                    stack.push(Value::predicate_bit(left == right));
                }
                Slot::Cons => {
                    let right = stack.pop().ok_or_else(|| blocked("CONS missing tail"))?;
                    let left = stack.pop().ok_or_else(|| blocked("CONS missing head"))?;
                    stack.push(Value::Pair(Rc::new(left), Rc::new(right)));
                }
                Slot::SkipZero(to) => {
                    let value = stack.pop().ok_or_else(|| blocked("COND test underflow"))?;
                    match value.as_predicate_bit() {
                        Some(true) => {}
                        Some(false) => {
                            pc = *to;
                            continue;
                        }
                        None => return Err(blocked("D3 COND accepts exact D1 only")),
                    }
                }
                Slot::Jump(to) => {
                    pc = *to;
                    continue;
                }
            }
            if stack.len() > MAX_STACK {
                return Err(blocked("slot stack budget exceeded"));
            }
            pc += 1;
        }
        if stack.len() != 1 {
            return Err(blocked("one result per D2 top-level expression required"));
        }
        result = stack.pop().ok_or_else(|| blocked("missing result"))?;
    }
    Ok(result)
}

fn physical(source: &str) -> Vec<u8> {
    encode_binary_projection_ternary(source).expect("fixture must have canonical D2/T5")
}

const Q: &str = "10 001 00 000 01";
const PAIR: &str = "10 111 00 10 001 00 000 01 00 10 001 00 000 01 01";
const ATOM_TRUE: &str = "10 010 00 000 01";
const ATOM_FALSE: &str =
    "10 010 00 10 111 00 10 001 00 000 01 00 10 001 00 000 01 01 01";
const EQ_TRUE: &str = "10 101 00 10 001 00 000 01 00 10 001 00 000 01 01";
const EQ_FALSE: &str = "10 101 00 0 00 1 01";
const COND: &str =
    "10 110 00 10 0 00 0 01 00 10 1 00 1 01 01";

fn corpus() -> [(&'static str, &'static str); 7] {
    [
        ("quote", Q),
        ("pair", PAIR),
        ("atom-true", ATOM_TRUE),
        ("atom-false", ATOM_FALSE),
        ("eq-true", EQ_TRUE),
        ("eq-false", EQ_FALSE),
        ("cond", COND),
    ]
}

fn median_p95(samples: &[u128]) -> (u128, u128) {
    let mut sorted = samples.to_vec();
    sorted.sort_unstable();
    let median = sorted[sorted.len() / 2];
    let p95 = sorted[(95 * sorted.len()).div_ceil(100).saturating_sub(1)];
    (median, p95)
}

fn measure<F: FnMut()>(mut f: F, loops: usize, samples: usize) -> (u128, u128) {
    for _ in 0..100 {
        f();
    }
    let mut observed = Vec::with_capacity(samples);
    for _ in 0..samples {
        let started = Instant::now();
        for _ in 0..loops {
            f();
        }
        observed.push(started.elapsed().as_nanos() / loops as u128);
    }
    median_p95(&observed)
}

fn main() -> Result<(), String> {
    let mut samples = 11usize;
    let mut loops = 500usize;
    let args: Vec<_> = std::env::args().collect();
    if args.len() > 1 {
        let mut i = 1;
        while i + 1 < args.len() {
            match args[i].as_str() {
                "--samples" => samples = args[i + 1].parse().map_err(|_| "samples")?,
                "--loops" => loops = args[i + 1].parse().map_err(|_| "loops")?,
                _ => return Err(format!("unknown parameter {}", args[i])),
            }
            i += 2;
        }
        if i != args.len() {
            return Err("unpaired CLI parameter".into());
        }
    }
    if samples < 7 || samples > 101 || samples % 2 == 0 || loops == 0 || loops > 1_000_000 {
        return Err("require odd samples 7..101 and loops 1..1000000".into());
    }

    println!("# SENS microCPU native Rust research only; same packed physical T5 per row");
    println!("# warmed slot replay excludes physical T5 decoding and compilation");
    println!("case\tT5_bytes\twords\tslots\tcold_p50_ns\tcold_p95_ns\twarm_p50_ns\twarm_p95_ns");
    for (name, source) in corpus() {
        let bytes = physical(source);
        let tape = compile_physical(&bytes)?;
        let mut oracle_session = Session::default();
        let oracle = eval_t5_program(&bytes, &mut oracle_session)
            .map_err(|e| format!("SENS oracle rejected admitted corpus {name}: {e:?}"))?;
        let warmed = evaluate_slots(&tape)?;
        if oracle.value != warmed || !oracle.output.is_empty() {
            return Err(format!("semantic mismatch for {name}"));
        }
        let (cold, cold95) = measure(
            || {
                let program = compile_physical(black_box(&bytes)).expect("valid T5");
                let value = evaluate_slots(&program).expect("native replay");
                black_box(value);
            },
            loops,
            samples,
        );
        let (hot, hot95) = measure(
            || {
                let value = evaluate_slots(black_box(&tape)).expect("prepared tape");
                black_box(value);
            },
            loops,
            samples,
        );
        println!(
            "{name}\t{}\t{}\t{}\t{cold}\t{cold95}\t{hot}\t{hot95}",
            tape.bytes,
            tape.words,
            tape.slots()
        );
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn same_packed_t5_yields_same_semantic_result_as_rust_sens() {
        for (name, source) in corpus() {
            let bytes = physical(source);
            let tape = compile_physical(&bytes).expect(name);
            let native = evaluate_slots(&tape).expect(name);
            let reference = eval_t5_program(&bytes, &mut Session::default()).expect(name);
            assert_eq!(native, reference.value, "{name}");
            assert!(reference.output.is_empty(), "{name}");
            assert_eq!(native, evaluate_slots(&tape).unwrap(), "repeat replay {name}");
        }
    }

    #[test]
    fn direct_current_d3_car_cdr_and_cond_remain_lazy() {
        let forms = [
            ("10 100 00 10 111 00 000 00 000 01 01", Value::Nil),
            ("10 011 00 10 111 00 000 00 000 01 01", Value::Nil),
            (
                "10 110 00 10 1 00 1 01 00 10 0 00 10 100 00 000 01 01",
                Value::predicate_bit(true),
            ),
        ];
        for (source, expected) in forms {
            let packed = physical(source);
            let observed = evaluate_slots(&compile_physical(&packed).unwrap()).unwrap();
            assert_eq!(observed, expected, "{source}");
            assert_eq!(
                observed,
                eval_t5_program(&packed, &mut Session::default()).unwrap().value,
                "independent Rust oracle {source}"
            );
        }
    }

    #[test]
    fn malformed_and_unadmitted_codes_never_enter_native_cpu() {
        for source in [
            "10 110 00 10 1 00 0 00 1 01 01",
            "10 110 00 10 1 01 01",
            "10 1000 00 000 01",
            "00000111",
            "10 01",
        ] {
            let words = sens::parse_binary_source_words(source)
                .unwrap()
                .into_iter()
                .map(|token| token.word)
                .collect::<Vec<_>>();
            let bytes = sens::encode_ternary_words(&words).unwrap();
            assert!(compile_physical(&bytes).is_err(), "unadmitted form {source}");
        }
        assert!(compile_physical(&[243]).is_err(), "bad physical trit byte");
    }

    #[test]
    fn wrong_domain_predicate_and_atom_only_eq_fail_closed() {
        let cases = [
            "10 110 00 10 10 001 00 000 01 00 1 01 01",
            "10 101 00 10 111 00 000 00 000 01 00 000 01",
            "10 100 00 000 01",
        ];
        for source in cases {
            let bytes = physical(source);
            assert!(evaluate_slots(&compile_physical(&bytes).unwrap()).is_err());
            assert!(eval_t5_program(&bytes, &mut Session::default()).is_err());
        }
    }

    #[test]
    fn unsupported_d2_dot_and_source_empty_never_compile() {
        for source in ["10 000 11 000 01", "10 01", "10 00 01"] {
            let words = sens::parse_binary_source_words(source)
                .unwrap()
                .into_iter()
                .map(|token| token.word)
                .collect::<Vec<_>>();
            let physical = sens::encode_ternary_words(&words).unwrap();
            assert!(compile_physical(&physical).is_err(), "{source}");
        }
    }
}
