//! `sens lsp` subcommand acceptance: the MAIN cli binary, spawned with
//! argument `lsp`, must serve the exact same framed LSP protocol over
//! stdio as the standalone sens-lsp binary. stdout must contain ONLY
//! valid LSP framing — no REPL banner, no prompts.

use std::io::{BufRead, BufReader, Read, Write};
use std::process::{Command, Stdio};

fn frame(msg: &str) -> Vec<u8> {
    format!("Content-Length: {}\r\n\r\n{}", msg.len(), msg).into_bytes()
}

/// Read one framed message and assert every byte of stdout so far was
/// well-formed framing (headers + declared length).
struct Reader {
    inner: BufReader<std::process::ChildStdout>,
}

impl Reader {
    fn read_message(&mut self) -> String {
        let mut content_length: Option<usize> = None;
        loop {
            let mut line = String::new();
            self.inner.read_line(&mut line).expect("read header");
            let trimmed = line.trim_end();
            if trimmed.is_empty() {
                break;
            }
            // Every stdout line before the blank separator MUST be a
            // header — a banner or prompt here would fail this parse.
            assert!(
                trimmed.contains(':'),
                "stdout leaked non-LSP output: {trimmed:?}"
            );
            if let Some(v) = trimmed.strip_prefix("Content-Length:") {
                content_length = v.trim().parse().ok();
            }
        }
        let len = content_length.expect("Content-Length header present");
        let mut buf = vec![0u8; len];
        self.inner.read_exact(&mut buf).expect("read body");
        String::from_utf8(buf).expect("utf8 body")
    }
}

#[test]
fn sens_lsp_subcommand_serves_lsp_over_stdio() {
    let mut child = Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg("lsp")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("spawn sens lsp");

    let mut stdin = child.stdin.take().unwrap();
    let mut reader = Reader {
        inner: BufReader::new(child.stdout.take().unwrap()),
    };

    // 1. initialize
    stdin
        .write_all(&frame(
            r#"{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}"#,
        ))
        .unwrap();
    let response = reader.read_message();
    assert!(response.contains("\"capabilities\""), "{response}");
    assert!(response.contains("\"hoverProvider\":true"), "{response}");

    // 2. didOpen a document with one def
    let doc = "(def yantra-root \"+ 1 1\")\n(def answer 42)\n";
    let escaped = doc.replace('"', "\\\"");
    stdin
        .write_all(&frame(&format!(
            r#"{{"jsonrpc":"2.0","method":"textDocument/didOpen","params":{{"textDocument":{{"uri":"file:///x.lisp","languageId":"sens","version":1,"text":"{escaped}"}}}}}}"#
        )))
        .unwrap();

    // publishDiagnostics (empty — valid doc)
    let diagnostics = reader.read_message();
    assert!(diagnostics.contains("publishDiagnostics"), "{diagnostics}");
    assert!(diagnostics.contains("\"diagnostics\":[]"), "{diagnostics}");

    // 3. documentSymbol finds both defs
    stdin
        .write_all(&frame(
            r#"{"jsonrpc":"2.0","id":2,"method":"textDocument/documentSymbol","params":{"textDocument":{"uri":"file:///x.lisp"}}}"#,
        ))
        .unwrap();
    let symbols = reader.read_message();
    assert!(symbols.contains("\"name\":\"yantra-root\""), "{symbols}");
    assert!(symbols.contains("\"name\":\"answer\""), "{symbols}");

    // clean shutdown + exit
    stdin
        .write_all(&frame(r#"{"jsonrpc":"2.0","id":3,"method":"shutdown"}"#))
        .unwrap();
    let shutdown = reader.read_message();
    assert!(
        shutdown.contains("\"id\":3") && shutdown.contains("\"result\":null"),
        "{shutdown}"
    );
    stdin
        .write_all(&frame(r#"{"jsonrpc":"2.0","method":"exit"}"#))
        .unwrap();
    drop(stdin);
    assert!(child.wait().expect("wait").success(), "clean exit");
}
