//! Вартість старту: MODE = session | read | decode | parse | macro | core.
//! read — прочитати двійкове ядро з диска; decode — прочитати й декодувати;
//! parse — розібрати текстове ядро; macro — сесія + бібліотека макросів;
//! core — повний старт load_core_library.
use sens::{fasl_decode_program, load_core_library, load_macro_library, parse, Session, CORE_LIBRARY_SOURCE};
use std::{env, fs, process::ExitCode};

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    let (mode, fasl_path) = (args[1].as_str(), args.get(2));
    let mut session = Session::default();
    match mode {
        "session" => {}
        "read" => { std::hint::black_box(fs::read(fasl_path.unwrap()).unwrap()); }
        "decode" => {
            let bytes = fs::read(fasl_path.unwrap()).unwrap();
            std::hint::black_box(fasl_decode_program(&bytes).expect("fasl decodes"));
        }
        "parse" => { std::hint::black_box(parse(CORE_LIBRARY_SOURCE).expect("core parses")); }
        "macro" => { load_macro_library(&mut session).expect("macros load"); }
        "core" => { load_core_library(&mut session).expect("core loads"); }
        _ => return ExitCode::from(2),
    }
    std::hint::black_box(&session);
    ExitCode::SUCCESS
}
