//! Isolated transport proof-of-concept for
//! docs/FOREIGN-RUNTIME-PROTOCOL-DESIGN-2026-09-11.md — proves ONLY the
//! riskiest unknown first: can a persistent Python subprocess be spawned
//! once, sent multiple requests over stdin, and produce parsed responses
//! over stdout, without embedding CPython (no PyO3 dependency).
//!
//! Deliberately touches NOTHING in `crates/sens` itself: no `Value`
//! variant, no evaluator change, no capability registration. This is
//! infrastructure feasibility research, not the feature. See the design
//! document's own "Next steps, not started here" for what still needs
//! real design work before this becomes a real sens capability
//! (Value::Foreign, ErrorKind mapping, allowlist-gated registration).
//!
//! Run: `cargo run -p sens-host --example foreign_python_probe`
//! Requires: `python` on PATH (confirmed present in this environment,
//! `python3` was not — checked directly, not assumed).

use std::io::{BufRead, BufReader, Write};
use std::process::{Command, Stdio};

fn main() {
    let script_path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/examples/foreign_python_bridge.py"
    );

    let mut child = Command::new("python")
        .arg(script_path)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("failed to spawn python -- is it on PATH?");

    let mut stdin = child.stdin.take().expect("child stdin should be piped");
    let stdout = child.stdout.take().expect("child stdout should be piped");
    let mut reader = BufReader::new(stdout);

    // Three requests over the SAME persistent subprocess -- the actual
    // thing being proven: one spawn, many calls, not one-shot
    // process-run-raw-style invocation per call.
    let requests = [
        "call math sqrt 9",
        "call math sqrt 2",
        "call math floor 3.9",
    ];

    for request in requests {
        writeln!(stdin, "{request}").expect("write request to python stdin");
        let mut response = String::new();
        reader
            .read_line(&mut response)
            .expect("read response from python stdout");
        let response = response.trim_end();
        println!("{request} -> {response}");
        assert!(
            response.starts_with("ok ") || response.starts_with("err "),
            "malformed response from bridge: {response:?}"
        );
    }

    // Explicit lifetime: close stdin so the Python side's read loop ends
    // naturally, then wait for real exit -- proving the persistent
    // subprocess can be released cleanly, not just abandoned.
    drop(stdin);
    let status = child.wait().expect("wait for python subprocess to exit");
    println!("python subprocess exited: {status}");
    assert!(status.success(), "python bridge should exit cleanly");

    println!("\nTransport proof-of-concept PASSED: persistent subprocess, multiple requests, clean shutdown.");
}
