//! #3490/#3513 — phase-decomposed exact-domain SENS benchmark runner.
//!
//! Benchmark-only modes separate cold bootstrap, exact source processing,
//! steady execution, and warm program setup on top of one resident Core.
//! Semantic authority remains in the language contracts and exact domains.

use sens::{
    eval_lowered_expressions, eval_parsed_expressions, load_core_library, lower_program,
    parse_mixed_exact_domain, Session,
};
use std::{env, fs, hint::black_box, process::ExitCode};

fn read(path: &str) -> Result<String, String> {
    fs::read_to_string(path).map_err(|error| format!("read {path}: {error}"))
}

fn parse_source(source: &str, label: &str) -> Result<Vec<sens::Expr>, String> {
    parse_mixed_exact_domain(source)
        .map_err(|error| format!("exact-domain parse {label}: {error:?}"))
}

fn parse(path: &str) -> Result<Vec<sens::Expr>, String> {
    let source = read(path)?;
    parse_source(&source, path)
}

fn load_session() -> Result<Session, String> {
    let mut session = Session::default();
    load_core_library(&mut session)
        .map_err(|error| format!("load current Core: {error:?}"))?;
    Ok(session)
}

fn repeat_arg(args: &[String], index: usize) -> Result<usize, String> {
    let raw = args
        .get(index)
        .ok_or_else(|| "missing repeat argument".to_string())?;
    let repeat: usize = raw
        .parse()
        .map_err(|error| format!("invalid repeat {raw}: {error}"))?;
    if repeat == 0 {
        return Err("repeat must be >= 1".to_string());
    }
    Ok(repeat)
}

fn child_session(core: &Session) -> Session {
    Session {
        environment: core.environment.child(),
    }
}

fn run() -> Result<(), String> {
    let args: Vec<String> = env::args().collect();
    let Some(mode) = args.get(1).map(String::as_str) else {
        return Err(
            "usage: current_exact_domain_phase_bench <startup|load|parse|lower|setup|ready|steady|warm-child|warm-parsed|warm-source> ..."
                .to_string(),
        );
    };

    match mode {
        "startup" => {
            black_box(0usize);
            println!("0");
        }
        "load" => {
            let session = load_session()?;
            black_box(&session);
            println!("0");
        }
        "parse" => {
            if args.len() != 4 {
                return Err(
                    "usage: current_exact_domain_phase_bench parse <setup.lisp> <call.lisp>"
                        .to_string(),
                );
            }
            let setup = parse(&args[2])?;
            let call = parse(&args[3])?;
            black_box(setup.len());
            black_box(call.len());
            println!("{}", setup.len() + call.len());
        }
        "lower" => {
            if args.len() != 4 {
                return Err(
                    "usage: current_exact_domain_phase_bench lower <setup.lisp> <call.lisp>"
                        .to_string(),
                );
            }
            let setup = parse(&args[2])?;
            let call = parse(&args[3])?;
            let setup_lowered = lower_program(&setup);
            let call_lowered = lower_program(&call);
            black_box(setup_lowered.len());
            black_box(call_lowered.len());
            println!("{}", setup_lowered.len() + call_lowered.len());
        }
        "setup" => {
            if args.len() != 3 {
                return Err(
                    "usage: current_exact_domain_phase_bench setup <setup.lisp>".to_string(),
                );
            }
            let setup = parse(&args[2])?;
            let mut session = load_session()?;
            let outcome = eval_parsed_expressions(&setup, &mut session)
                .map_err(|error| format!("evaluate setup: {error:?}"))?;
            black_box(&outcome.value);
            println!("0");
        }
        "ready" => {
            if args.len() != 4 {
                return Err(
                    "usage: current_exact_domain_phase_bench ready <setup.lisp> <call.lisp>"
                        .to_string(),
                );
            }
            let setup = parse(&args[2])?;
            let call = parse(&args[3])?;
            let setup_lowered = lower_program(&setup);
            let call_lowered = lower_program(&call);
            let mut session = load_session()?;
            let outcome = eval_lowered_expressions(&setup_lowered, &mut session)
                .map_err(|error| format!("evaluate ready setup: {error:?}"))?;
            black_box(&outcome.value);
            black_box(&call_lowered);
            println!("0");
        }
        "steady" => {
            if args.len() != 5 {
                return Err(
                    "usage: current_exact_domain_phase_bench steady <setup.lisp> <call.lisp> <repeat>"
                        .to_string(),
                );
            }
            let repeat = repeat_arg(&args, 4)?;
            let setup = parse(&args[2])?;
            let call = parse(&args[3])?;
            let mut session = load_session()?;
            eval_parsed_expressions(&setup, &mut session)
                .map_err(|error| format!("evaluate setup: {error:?}"))?;

            let mut final_value = None;
            for _ in 0..repeat {
                let outcome = eval_parsed_expressions(&call, &mut session)
                    .map_err(|error| format!("evaluate steady call: {error:?}"))?;
                final_value = Some(outcome.value.to_string());
            }
            println!("{}", final_value.expect("repeat >= 1"));
        }
        "warm-child" => {
            if args.len() != 3 {
                return Err(
                    "usage: current_exact_domain_phase_bench warm-child <repeat>".to_string(),
                );
            }
            let repeat = repeat_arg(&args, 2)?;
            let core = load_session()?;
            for _ in 0..repeat {
                let child = child_session(&core);
                black_box(&child);
            }
            println!("0");
        }
        "warm-parsed" => {
            if args.len() != 4 {
                return Err(
                    "usage: current_exact_domain_phase_bench warm-parsed <setup.lisp> <repeat>"
                        .to_string(),
                );
            }
            let repeat = repeat_arg(&args, 3)?;
            let setup = parse(&args[2])?;
            let core = load_session()?;
            for _ in 0..repeat {
                let mut child = child_session(&core);
                let outcome = eval_parsed_expressions(&setup, &mut child)
                    .map_err(|error| format!("evaluate warm parsed setup: {error:?}"))?;
                black_box(&outcome.value);
            }
            println!("0");
        }
        "warm-source" => {
            if args.len() != 4 {
                return Err(
                    "usage: current_exact_domain_phase_bench warm-source <setup.lisp> <repeat>"
                        .to_string(),
                );
            }
            let repeat = repeat_arg(&args, 3)?;
            let setup_source = read(&args[2])?;
            let core = load_session()?;
            for _ in 0..repeat {
                let setup = parse_source(&setup_source, &args[2])?;
                let mut child = child_session(&core);
                let outcome = eval_parsed_expressions(&setup, &mut child)
                    .map_err(|error| format!("evaluate warm source setup: {error:?}"))?;
                black_box(&outcome.value);
            }
            println!("0");
        }
        other => return Err(format!("unknown phase mode: {other}")),
    }

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
