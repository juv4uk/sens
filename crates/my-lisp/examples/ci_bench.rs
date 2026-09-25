//! #1433: швидкий бенчмарк для CI — один процес на одне навантаження.
//!
//! Міряється під valgrind (кількість інструкцій — детермінована, на
//! відміну від часу на спільних CI-машинах). Бібліотека core НЕ
//! завантажується: навантаження користуються лише примітивами мови, а
//! старт із core (~4.8 млрд інструкцій) заглушив би їхню вартість.
//!
//! Використовує лише стабільний API (`parse`, `Session`,
//! `eval_parsed_expressions`), щоб той самий файл збирався й на базовому
//! коміті для порівняння «було / стало».
//!
//! `ci_bench DIR NAME FORM` — виконує `DIR/NAME-FORM.setup.lisp` і
//! `DIR/NAME-FORM.call.lisp` (див. `run.py --emit`), звіряє відповідь із
//! `DIR/NAME.expected`. `ci_bench DIR empty -` — лише створення сесії.

use my_lisp::{eval_parsed_expressions, parse, Session};
use std::{env, fs, path::Path, process::ExitCode};

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    let (dir, name, form) = (Path::new(&args[1]), &args[2], &args[3]);
    let mut session = Session::default();
    if name == "empty" {
        return ExitCode::SUCCESS;
    }
    let read = |file: String| fs::read_to_string(dir.join(&file)).unwrap_or_else(|e| panic!("{file}: {e}"));
    let setup = parse(&read(format!("{name}-{form}.setup.lisp"))).expect("setup parses");
    let call = parse(&read(format!("{name}-{form}.call.lisp"))).expect("call parses");
    let expected = read(format!("{name}.expected")).trim().to_owned();

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
