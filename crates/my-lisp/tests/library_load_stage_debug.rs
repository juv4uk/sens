use my_lisp::{
    eval_program, load_core_library, load_macro_library, load_process_library, load_time_library,
    Environment, Session, PROCESS_LIBRARY_SOURCE, TCP_LIBRARY_SOURCE, UTF8_LIBRARY_SOURCE,
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
