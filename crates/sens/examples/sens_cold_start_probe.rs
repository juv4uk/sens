//! One invocation per process: process start and Core bootstrap are measured
//! by a separate host runner. Rust owns only timing; Lisp owns core semantics.
use sens::{eval_parsed_expressions, load_core_library, parse_canonical_binary, Session, Value};
use std::{env, hint::black_box, process, time::Instant};

fn probe(mode: &str) -> Result<(&'static str, u128), String> {
    let started = Instant::now();
    let outcome = match mode {
        "noop" => {
            black_box(1u8);
            "NONE"
        }
        "session" => {
            black_box(Session::default());
            "SESSION"
        }
        "d3" => {
            let mut session = Session::default();
            let forms = parse_canonical_binary("10 001 00 000 01")
                .map_err(|e| format!("D2 parse: {e:?}"))?;
            let result = eval_parsed_expressions(&forms, &mut session)
                .map_err(|e| format!("D3 execute: {e:?}"))?;
            if !matches!(result.value, Value::Nil) || !result.output.is_empty() {
                return Err("D3 QUOTE must evaluate to structural EMPTY with no output".into());
            }
            black_box(result);
            "D3_EMPTY"
        }
        "core" => {
            let mut session = Session::default();
            let result = load_core_library(&mut session)
                .map_err(|e| format!("Lisp-owned Core4 bootstrap: {e:?}"))?;
            black_box(result);
            "CORE_LOADED"
        }
        "core-d3" => {
            let mut session = Session::default();
            let result = load_core_library(&mut session)
                .map_err(|e| format!("Lisp-owned Core4 bootstrap: {e:?}"))?;
            black_box(result);
            let forms = parse_canonical_binary("10 001 00 000 01")
                .map_err(|e| format!("D2 parse: {e:?}"))?;
            let result = eval_parsed_expressions(&forms, &mut session)
                .map_err(|e| format!("Core4 D3 execute: {e:?}"))?;
            if !matches!(result.value, Value::Nil) || !result.output.is_empty() {
                return Err("Core4 D3 QUOTE result differs from structural EMPTY".into());
            }
            black_box(result);
            "CORE_AND_D3_EMPTY"
        }
        _ => return Err(format!("unknown mode: {mode}")),
    };
    Ok((outcome, started.elapsed().as_nanos()))
}

fn main() {
    let mut args = env::args().skip(1);
    let mode = args.next().unwrap_or_default();
    if args.next().is_some() {
        eprintln!("usage: sens_cold_start_probe <noop|session|d3|core|core-d3>");
        process::exit(2);
    }
    match probe(&mode) {
        Ok((value, elapsed_ns)) => {
            println!("INNER_NS={elapsed_ns}");
            println!("VALUE={value}");
        }
        Err(error) => {
            eprintln!("BLOCKED: {error}");
            process::exit(2);
        }
    }
}
