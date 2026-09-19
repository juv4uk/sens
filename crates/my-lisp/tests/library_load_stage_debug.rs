use my_lisp::{
    eval_parsed_expressions, eval_program, fasl_decode_program, load_core_library,
    load_macro_library, load_process_library, load_time_library, Environment, Session,
    CORE_LIBRARY_SOURCE, PROCESS_LIBRARY_SOURCE, TCP_LIBRARY_SOURCE, UTF8_LIBRARY_SOURCE,
};

fn core_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must load");
    session
}

#[test]
fn diagnostic_utf8_library_loads_independently() {
    let mut session = core_session();
    eval_program(UTF8_LIBRARY_SOURCE, &mut session)
        .expect("UTF8_LIBRARY_SOURCE must load independently");
}

#[test]
fn diagnostic_process_library_loads_after_utf8() {
    let mut session = core_session();
    eval_program(UTF8_LIBRARY_SOURCE, &mut session)
        .expect("UTF8_LIBRARY_SOURCE must load first");
    eval_program(PROCESS_LIBRARY_SOURCE, &mut session)
        .expect("PROCESS_LIBRARY_SOURCE must load after UTF-8");
}

#[test]
fn diagnostic_tcp_library_loads_after_utf8_and_process() {
    let mut session = core_session();
    eval_program(UTF8_LIBRARY_SOURCE, &mut session)
        .expect("UTF8_LIBRARY_SOURCE must load first");
    eval_program(PROCESS_LIBRARY_SOURCE, &mut session)
        .expect("PROCESS_LIBRARY_SOURCE must load second");
    eval_program(TCP_LIBRARY_SOURCE, &mut session)
        .expect("TCP_LIBRARY_SOURCE must load third");
}


#[test]
fn diagnostic_cli_bootstrap_context_loads_process_stack() {
    let mut session = Session {
        environment: Environment::root(),
    };
    load_macro_library(&mut session).expect("macro layer must load");
    load_core_library(&mut session).expect("core layer must load");
    load_time_library(&mut session).expect("time layer must load before process");
    load_process_library(&mut session)
        .expect("CLI bootstrap context must load UTF-8/process/TCP stack");
}


#[test]
fn diagnostic_cli_fasl_core_path_loads_process_stack() {
    let mut session = Session {
        environment: Environment::root(),
    };
    load_macro_library(&mut session).expect("macro layer must load");

    let fasl = include_bytes!("../../../lib/core.lisp.fasl");
    let (core_ast, _hash) = fasl_decode_program(fasl).expect("core FASL must decode");
    eval_parsed_expressions(&core_ast, &mut session)
        .expect("CLI FASL core path must evaluate");

    load_time_library(&mut session).expect("time layer must load after FASL core");
    load_process_library(&mut session)
        .expect("FASL CLI bootstrap context must load UTF-8/process/TCP stack");

    // Keep source in scope so this diagnostic remains explicitly tied to the
    // same compiled-in core source used by the CLI.
    assert!(!CORE_LIBRARY_SOURCE.is_empty());
}
