//! #1433: вимірювач для закріпленого англійського Lisp до таблиці функцій
//! (b4f75d2f, 2026-09-08, крейт `my_lisp`). Той самий протокол, що
//! `crates/sens/examples/ci_bench.rs`, але лише текстова форма `legacy-en`:
//! у той час SENS ще не було.
//!
//!   ci_bench DIR NAME legacy-en [load|full]
//!   ci_bench DIR empty -

use my_lisp::{eval_parsed_expressions, parse, Session};
use std::{env, fs, path::Path, process::ExitCode};

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    let (dir, name, form) = (Path::new(&args[1]), &args[2], &args[3]);
    let mode = args.get(4).map(String::as_str).unwrap_or("full");
    let mut session = Session::default();
    if name == "empty" {
        return ExitCode::SUCCESS;
    }
    let text = |part: &str| {
        fs::read_to_string(dir.join(format!("{name}-{form}.{part}.lisp")))
            .unwrap_or_else(|e| panic!("{name}-{form}.{part}: {e}"))
    };
    let setup = parse(&text("setup")).expect("setup parses");
    let call = parse(&text("call")).expect("call parses");
    if mode == "load" {
        std::hint::black_box((&setup, &call));
        return ExitCode::SUCCESS;
    }
    let expected = fs::read_to_string(dir.join(format!("{name}.expected")))
        .expect("expected answer")
        .trim()
        .to_owned();
    if let Err(error) = eval_parsed_expressions(&setup, &mut session) {
        eprintln!("{name}/{form}: setup failed: {error}");
        return ExitCode::from(2);
    }
    match eval_parsed_expressions(&call, &mut session) {
        Ok(result) if result.value.to_string() == expected => ExitCode::SUCCESS,
        Ok(result) => {
            eprintln!("{name}/{form}: expected {expected}, got {}", result.value);
            ExitCode::from(3)
        }
        Err(error) => {
            eprintln!("{name}/{form}: {error}");
            ExitCode::from(4)
        }
    }
}
