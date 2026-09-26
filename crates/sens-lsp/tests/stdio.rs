//! Acceptance 1: the server initializes successfully OVER REAL STDIO —
//! this test spawns the `sens-lsp` binary and speaks framed LSP to it
//! through pipes, exactly like an editor would.

use std::io::{BufRead, BufReader, Write};
use std::process::{Command, Stdio};

fn frame(msg: &str) -> Vec<u8> {
    format!("Content-Length: {}\r\n\r\n{}", msg.len(), msg).into_bytes()
}

fn read_frame(reader: &mut impl BufRead) -> String {
    let mut content_length: Option<usize> = None;
    loop {
        let mut line = String::new();
        reader.read_line(&mut line).expect("read header");
        let line = line.trim_end();
        if line.is_empty() {
            break;
        }
        if let Some(v) = line.strip_prefix("Content-Length:") {
            content_length = v.trim().parse().ok();
        }
    }
    let len = content_length.expect("Content-Length header");
    let mut buf = vec![0u8; len];
    reader.read_exact(&mut buf).expect("read body");
    String::from_utf8(buf).expect("utf8")
}

#[test]
fn initializes_over_real_stdio() {
    let mut child = Command::new(env!("CARGO_BIN_EXE_sens-lsp"))
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .expect("spawn sens-lsp");

    let mut stdin = child.stdin.take().unwrap();
    let mut stdout = BufReader::new(child.stdout.take().unwrap());

    // initialize
    stdin
        .write_all(&frame(
            r#"{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}"#,
        ))
        .unwrap();
    let response = read_frame(&mut stdout);
    assert!(response.contains("\"capabilities\""), "{response}");
    assert!(response.contains("\"hoverProvider\":true"), "{response}");

    // initialized notification → no response expected, then shutdown
    stdin
        .write_all(&frame(
            r#"{"jsonrpc":"2.0","method":"initialized","params":{}}"#,
        ))
        .unwrap();
    stdin
        .write_all(&frame(r#"{"jsonrpc":"2.0","id":2,"method":"shutdown"}"#))
        .unwrap();
    let response = read_frame(&mut stdout);
    assert!(
        response.contains("\"id\":2") && response.contains("\"result\":null"),
        "{response}"
    );

    // clean exit
    stdin
        .write_all(&frame(r#"{"jsonrpc":"2.0","method":"exit"}"#))
        .unwrap();
    drop(stdin);
    let status = child.wait().expect("wait");
    assert!(status.success(), "server must exit cleanly");
}
