//! #1433: швидкий бенчмарк для CI — один процес на одне навантаження.
//!
//! Міряється під valgrind (кількість інструкцій — відтворювана, на відміну
//! від часу на спільній машині). Бібліотека core НЕ завантажується:
//! навантаження користуються лише примітивами мови.
//!
//! SENS — це 8-бітна функція, а не текст. Тому програма у формі `sens`
//! виконується з двійкового вигляду (fasl), де функція займає рівно 1 байт;
//! текст `run.py` — лише людська поверхня, з якої двійковий вигляд кодується
//! заздалегідь (режим `encode`, не міряється). Англійська форма (`en`)
//! читається з тексту — це її людська поверхня.
//!
//!   ci_bench DIR NAME FORM [MODE]
//!     MODE = full (за замовчуванням) — завантажити й виконати, звірити відповідь;
//!            load — лише завантажити програму (розбір тексту або декодування fasl);
//!            encode — `sens`: закодувати текст у DIR/NAME-sens.{setup,call}.fasl.
//!   ci_bench DIR empty -     — лише створення сесії.
//!
//! Лише стабільний публічний API (`parse`, `fasl_encode_program`,
//! `fasl_decode_program`, `Session`, `eval_parsed_expressions`), щоб той самий
//! файл збирався й на попередньому коміті.

use sens::{
    eval_parsed_expressions, fasl_decode_program, fasl_encode_program, parse, Expr, Session,
};
use std::{env, fs, path::Path, process::ExitCode};

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    let (dir, name, form) = (Path::new(&args[1]), &args[2], &args[3]);
    let mode = args.get(4).map(String::as_str).unwrap_or("full");
    let mut session = Session::default();
    if name == "empty" {
        return ExitCode::SUCCESS;
    }
    let file = |part: &str, ext: &str| dir.join(format!("{name}-{form}.{part}.{ext}"));
    let text = |part: &str| {
        fs::read_to_string(file(part, "lisp")).unwrap_or_else(|e| panic!("{name}-{form}.{part}: {e}"))
    };

    if mode == "encode" {
        for part in ["setup", "call"] {
            let program = parse(&text(part)).expect("surface text parses");
            fs::write(file(part, "fasl"), fasl_encode_program(&program, &[0u8; 32]))
                .expect("fasl written");
        }
        return ExitCode::SUCCESS;
    }

    let load = |part: &str| -> Vec<Expr> {
        if form == "sens" {
            let bytes = fs::read(file(part, "fasl"))
                .unwrap_or_else(|e| panic!("{name}-sens.{part}.fasl (run encode first): {e}"));
            fasl_decode_program(&bytes).expect("fasl decodes").0
        } else {
            parse(&text(part)).expect("text parses")
        }
    };
    let setup = load("setup");
    let call = load("call");
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
