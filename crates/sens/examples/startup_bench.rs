//! Вартість старту: MODE = session | bytes | decode | decode-lower | decoded-eval | parse | macro | core.
//! Діагностичні режими розкладають активний FASL bootstrap без зміни runtime.
use sens::{
    eval_lowered_expressions, fasl_decode_program, load_core_library, load_macro_library,
    lower_program, parse, CoreProfile, Session, CORE_LIBRARY_SOURCE,
};
use std::{env, fs, process::ExitCode};

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    let (mode, fasl_path) = (args[1].as_str(), args.get(2));
    let mut session = Session::default();
    match mode {
        "session" => {}
        "bytes" => { std::hint::black_box(fs::read(fasl_path.unwrap()).unwrap()); }
        "decode" => {
            let bytes = fs::read(fasl_path.unwrap()).unwrap();
            std::hint::black_box(fasl_decode_program(&bytes).expect("fasl decodes"));
        }
        "decode-lower" => {
            let bytes = fs::read(fasl_path.unwrap()).unwrap();
            let (expressions, _) = fasl_decode_program(&bytes).expect("fasl decodes");
            std::hint::black_box(lower_program(&expressions));
        }
        "decoded-eval" => {
            let bytes = fs::read(fasl_path.unwrap()).unwrap();
            let (expressions, _) = fasl_decode_program(&bytes).expect("fasl decodes");
            let lowered = lower_program(&expressions);
            session.environment.select_core_profile(CoreProfile::Core4);
            std::hint::black_box(
                eval_lowered_expressions(&lowered, &mut session).expect("decoded Core evaluates")
            );
        }
        "parse" => { std::hint::black_box(parse(CORE_LIBRARY_SOURCE).expect("core parses")); }
        "macro" => { load_macro_library(&mut session).expect("macros load"); }
        "core" => { load_core_library(&mut session).expect("core loads"); }
        _ => return ExitCode::from(2),
    }
    std::hint::black_box(&session);
    ExitCode::SUCCESS
}
