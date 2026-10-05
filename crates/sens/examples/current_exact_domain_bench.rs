//! Contract 11-5 exact-domain benchmark runner.
//!
//! Reads one mixed exact-domain SENS program from a file, preserves D3-D6
//! call-head identity through parse_mixed_exact_domain, loads the ordinary Core
//! environment, evaluates all forms, and prints only the final value.
//!
//! This is benchmark tooling. It never accepts historical Sens8/Sid8 bytes as
//! semantic authority for the benchmark program.

use sens::{
    eval_parsed_expressions, load_core_library, parse_mixed_exact_domain, Session,
};
use std::{env, fs, process::ExitCode};

fn run() -> Result<(), String> {
    let mut args = env::args_os();
    let _program = args.next();
    let path = args
        .next()
        .ok_or_else(|| "usage: current_exact_domain_bench <program.lisp>".to_string())?;
    if args.next().is_some() {
        return Err("usage: current_exact_domain_bench <program.lisp>".to_string());
    }

    let source = fs::read_to_string(&path)
        .map_err(|error| format!("read {}: {error}", path.to_string_lossy()))?;
    let parsed = parse_mixed_exact_domain(&source)
        .map_err(|error| format!("exact-domain parse: {error:?}"))?;

    let mut session = Session::default();
    load_core_library(&mut session)
        .map_err(|error| format!("load current Core: {error:?}"))?;

    let outcome = eval_parsed_expressions(&parsed, &mut session)
        .map_err(|error| format!("evaluate exact-domain program: {error:?}"))?;
    println!("{}", outcome.value);
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("{error}");
            ExitCode::FAILURE
        }
    }
}
