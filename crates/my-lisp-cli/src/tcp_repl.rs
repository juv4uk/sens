//! tcp_repl.rs - the line-based TCP REPL (plain `expr\n` in, value out),
//! served on 127.0.0.1 only. The semantic sexpr/oracle protocol lives in
//! swarm.rs. Moved verbatim from main.rs (2026-08-22 mechanical split).

use my_lisp::{
    eval_parsed_expressions, eval_parsed_expressions_incremental, eval_program,
    load_macro_library, load_process_library, parse, Environment, Session, TIME_LIBRARY_SOURCE,
};
use std::io::{BufRead, BufReader, Write};
use std::net::{Ipv4Addr, TcpListener};
use std::process;

/// `--tcp` / `--tcp=PORT` — a REPL reachable over TCP instead of stdio, for
/// other local processes (e.g. a cross-session tool) to eval expressions
/// against without shelling out to the CLI per call. Bound to
/// `127.0.0.1` only — never `0.0.0.0` — since there is no authentication:
/// anything that can reach this port can eval arbitrary my-lisp, including
/// `process-run` if `--allow-process` was also passed. Loopback-only keeps
/// that blast radius to "processes already running as this user on this
/// machine", matching what the stdio REPL already allows.
/// Each connection gets its own fresh `Session` (core.lisp reloaded from
/// scratch) rather than sharing one across every caller — tried the shared
/// version first, and it let one connection's `def` (accidental or not)
/// corrupt every other caller's environment with no way to trace it back.
/// `Environment` clones cheaply (`Rc<RefCell<Frame>>`) but that's exactly
/// the problem: a clone shares the underlying frame, it doesn't fork it,
/// so cloning an existing `Session` would not have fixed this — a genuinely
/// new `Environment::root()` per connection is what isolates state.
/// State does NOT persist across reconnects within the same connection is
/// fine (a single connection's lines share state, same as one REPL
/// session), but two different connections never see each other's `def`s.
/// Every expression is still logged to stderr with its peer address, for
/// the same accountability reason the isolation itself was added for.
pub(crate) fn run_tcp_repl(port: u16, core_lib: &str, allowed: &[String]) {
    let listener = match TcpListener::bind((Ipv4Addr::LOCALHOST, port)) {
        Ok(listener) => listener,
        Err(err) => {
            eprintln!("Error: could not bind TCP REPL to 127.0.0.1:{port}: {err}");
            process::exit(1);
        }
    };
    let actual_port = listener.local_addr().map(|a| a.port()).unwrap_or(port);
    println!(
        "my-lisp TCP REPL v{} listening on 127.0.0.1:{actual_port}",
        env!("CARGO_PKG_VERSION")
    );

    for stream in listener.incoming() {
        let mut stream = match stream {
            Ok(stream) => stream,
            Err(_) => continue,
        };
        let peer = stream
            .peer_addr()
            .map(|a| a.to_string())
            .unwrap_or_else(|_| "?".into());
        eprintln!("TCP REPL: connection from {peer}");

        // TCP is an unauthenticated entry point, not the trusted local
        // Lisp-machine profile. Empty means deny all; a supplied list is exact.
        let environment = Environment::root().with_process_allowlist(allowed.to_vec());
        let mut session = Session { environment };

        // Keep the same language bootstrap invariant as the local CLI:
        // explicitly install the narrow make-macro mechanism, then let Lisp
        // own defmacro before core.lisp defines its derived forms. No evaluator
        // head-name fallback is allowed to rescue a bare custom Environment.
        if load_macro_library(&mut session).is_ok() {
            if let Ok(core_ast) = parse(core_lib) {
                if eval_parsed_expressions(&core_ast, &mut session).is_ok()
                    && eval_program(TIME_LIBRARY_SOURCE, &mut session).is_ok()
                {
                    let _ = load_process_library(&mut session);
                }
            }
        }

        let mut reader = BufReader::new(stream.try_clone().expect("clone TCP stream"));
        let mut line = String::new();
        loop {
            line.clear();
            match reader.read_line(&mut line) {
                Ok(0) => break, // connection closed
                Ok(_) => {
                    let trimmed = line.trim();
                    if trimmed.is_empty() {
                        continue;
                    }
                    eprintln!("TCP REPL: {peer} > {trimmed}");
                    let response = match parse(trimmed) {
                        Ok(ast) => match eval_parsed_expressions_incremental(&ast, &mut session) {
                            Ok(result) => {
                                let mut out = String::new();
                                for line in result.output {
                                    out.push_str(&line);
                                    out.push('\n');
                                }
                                out.push_str(&result.value.to_string());
                                out
                            }
                            Err(e) => format!("Error: {}", e.render(trimmed)),
                        },
                        Err(e) => format!("Parse error: {}", e.render(trimmed)),
                    };
                    if writeln!(stream, "{response}").is_err() {
                        break;
                    }
                }
                Err(_) => break,
            }
        }
        eprintln!("TCP REPL: {peer} disconnected");
    }
}
