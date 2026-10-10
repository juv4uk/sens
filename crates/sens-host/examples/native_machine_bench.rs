//! Native Machine #1: no native fallback, and no cross-workload speed ratios.
#![cfg(all(target_os = "linux", target_arch = "x86_64"))]

use sens::{eval_program, eval_t5_program, load_core_library, Session};
use std::fs;
use std::hint::black_box;
use std::time::Instant;

const PAIR: &[u8] = include_bytes!("../../../tests/fixtures/migration-pair-cohort-main/pair-car-cdr.sens");
const SELECT: &[u8] = include_bytes!("../../../tests/fixtures/migration-eq-cond-cohort-main/eq-cond-select.sens");
const SKIP: &[u8] = include_bytes!("../../../tests/fixtures/migration-eq-cond-cohort-main/eq-cond-skip.sens");

fn clean(s: &str) -> String { s.replace(['\t', '\r', '\n'], " ") }
fn emit(name: &str, lane: &str, iteration: i32, ns: u128, value: &str, status: &str) {
    println!("{}\t{}\t{}\t{}\t{}\t{}", name, lane, iteration, ns, clean(value), clean(status));
}
fn measured_source(s: &mut Session, source: &str) -> Result<(u128, String), String> {
    let start = Instant::now();
    let result = eval_program(source, s).map_err(|e| e.to_string())?;
    black_box(&result.value);
    let duration = start.elapsed().as_nanos();
    Ok((duration, result.value.to_string()))
}
fn measured_t5(s: &mut Session, bytes: &[u8]) -> Result<(u128, String), String> {
    let start = Instant::now();
    let result = eval_t5_program(bytes, s).map_err(|e| format!("{e:?}"))?;
    black_box(&result.value);
    let duration = start.elapsed().as_nanos();
    Ok((duration, result.value.to_string()))
}
fn machine_session() -> Result<Session, String> {
    let mut state = Session::default();
    load_core_library(&mut state).map_err(|e| format!("core: {e:?}"))?;
    for path in [
        "lib/machine/layout/pair-x86-64.lisp",
        "lib/machine/encoding/x86-64.lisp",
        "lib/machine/admission/x86-64.lisp",
        "lib/machine/lowering/semantic-x86-64.lisp",
    ] {
        let source = fs::read_to_string(path).map_err(|e| format!("{path}: {e}"))?;
        eval_program(&source, &mut state).map_err(|e| format!("{path}: {e:?}"))?;
    }
    Ok(state)
}
fn benchmark_pair(reps: usize, warmups: usize) -> Result<(), String> {
    let mut interpreter = Session::default();
    load_core_library(&mut interpreter).map_err(|e| format!("interpreter bootstrap: {e:?}"))?;
    let (mut native, setup_problem) = match machine_session() {
        Ok(s) => (Some(s), String::new()),
        Err(e) => (None, e),
    };
    let cases = [
        ("car-cons-2-3", "(перше (сполучити 2 3))",
         "(x86-call-admitted-u64 (x86-lower-cons-car-u64-forms 2 3) x86-pair-cell-bytes)", "2"),
        ("cdr-cons-2-3", "(решта (сполучити 2 3))",
         "(x86-call-admitted-u64 (x86-lower-cons-cdr-u64-forms 2 3) x86-pair-cell-bytes)", "3"),
    ];
    for (name, lisp, machine, expected) in cases {
        let baseline = measured_source(&mut interpreter, lisp);
        match baseline {
            Ok((_, ref value)) if value == expected => {},
            Ok((_, ref value)) => {
                emit(name, "interpreter-source", -1, 0, value, "BLOCKED:reference-mismatch");
                emit(name, "native-admitted-cpu", -1, 0, "", "BLOCKED:independent-reference");
                continue;
            },
            Err(ref error) => {
                emit(name, "interpreter-source", -1, 0, "", &format!("BLOCKED:{error}"));
                emit(name, "native-admitted-cpu", -1, 0, "", "BLOCKED:independent-reference");
                continue;
            },
        };
        let admitted = if let Some(ref mut engine) = native {
            match measured_source(engine, machine) {
                Ok((_, observed)) if observed == expected => true,
                Ok((_, observed)) => {
                    emit(name, "native-admitted-cpu", -1, 0, &observed, "BLOCKED:parity-mismatch");
                    false
                },
                Err(e) => {
                    emit(name, "native-admitted-cpu", -1, 0, "", &format!("BLOCKED:{e}"));
                    false
                },
            }
        } else {
            emit(name, "native-admitted-cpu", -1, 0, "",
                 &format!("BLOCKED:machine-bootstrap:{setup_problem}"));
            false
        };
        for _ in 0..warmups {
            if measured_source(&mut interpreter, lisp)?.1 != expected {
                return Err(format!("interpreter drift in {name}"));
            }
            if admitted && measured_source(native.as_mut().expect("native admitted"), machine)?.1 != expected {
                return Err(format!("native drift in {name}"));
            }
        }
        for i in 0..reps {
            if admitted && i % 2 == 1 {
                let (ns, value) = measured_source(native.as_mut().expect("admitted"), machine)?;
                if value != expected { return Err(format!("native drift in {name}")); }
                emit(name, "native-admitted-cpu", i as i32, ns, &value, "PASS");
            }
            let (ns, value) = measured_source(&mut interpreter, lisp)?;
            if value != expected { return Err(format!("interpreter drift in {name}")); }
            emit(name, "interpreter-source", i as i32, ns, &value, "PASS");
            if admitted && i % 2 == 0 {
                let (ns, value) = measured_source(native.as_mut().expect("admitted"), machine)?;
                if value != expected { return Err(format!("native drift in {name}")); }
                emit(name, "native-admitted-cpu", i as i32, ns, &value, "PASS");
            }
        }
    }
    Ok(())
}
fn benchmark_t5(reps: usize, warmups: usize) -> Result<(), String> {
    let cases = [
        ("t5-car-cdr-quote", PAIR, "()"),
        ("t5-eq-cond-select", SELECT, "(())"),
        ("t5-eq-cond-skip", SKIP, "()"),
    ];
    for (name, bytes, expected) in cases {
        let mut s = Session::default();
        match measured_t5(&mut s, bytes) {
            Err(e) => { emit(name, "physical-t5-inprocess", -1, 0, "", &format!("BLOCKED:{e}")); continue; },
            Ok((_, value)) if value != expected => {
                emit(name, "physical-t5-inprocess", -1, 0, &value,
                     "BLOCKED:expected-value-mismatch");
                continue;
            },
            Ok(_) => {}
        }
        for _ in 0..warmups {
            if measured_t5(&mut s, bytes)?.1 != expected { return Err(format!("T5 drift: {name}")); }
        }
        for i in 0..reps {
            let (ns, value) = measured_t5(&mut s, bytes)?;
            if value != expected { return Err(format!("T5 drift: {name}")); }
            emit(name, "physical-t5-inprocess", i as i32, ns, &value, "PASS");
        }
        eprintln!("PHYSICAL_T5_BYTES {name} {}", bytes.len());
    }
    Ok(())
}
fn main() {
    let mut reps = 15;
    let mut warmups = 4;
    let mut args = std::env::args().skip(1);
    while let Some(key) = args.next() {
        let value = args.next().unwrap_or_default();
        let number = value.parse::<usize>().unwrap_or(usize::MAX);
        match key.as_str() {
            "--reps" if (3..=1000).contains(&number) => reps = number,
            "--warmups" if number <= 1000 => warmups = number,
            _ => { eprintln!("unsupported argument {key}={value}"); std::process::exit(2); }
        }
    }
    sens_host::install();
    println!("case\tlane\titeration\telapsed_ns\tvalue\tstatus");
    if let Err(e) = benchmark_pair(reps, warmups).and_then(|_| benchmark_t5(reps, warmups)) {
        eprintln!("BENCH_ABORTED {e}");
        std::process::exit(1);
    }
}
