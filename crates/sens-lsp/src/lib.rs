//! Library face of sens-lsp so integration tests (and future
//! embedders) can drive the exact same server loop the stdio binary runs.
pub mod analysis;
pub mod guard_knowledge;
pub mod jsonout;
pub mod protocol;
pub mod server;
pub mod transport;
pub mod workspace;

/// Convenience used by end-to-end tests: process raw JSON-RPC texts in
/// order, collecting every outgoing message.
pub struct Harness {
    inner: server::Server,
}

impl Default for Harness {
    fn default() -> Self {
        Self::new()
    }
}

impl Harness {
    pub fn new() -> Self {
        Self {
            inner: server::Server::new(),
        }
    }
    pub fn feed(&mut self, messages: &[String]) -> Vec<String> {
        let mut out = Vec::new();
        for m in messages {
            if server::Server::wants_exit(m) {
                continue;
            }
            out.extend(self.inner.handle_message(m));
        }
        out
    }
}

/// Run the LSP server over stdin/stdout until EOF or `exit`.
///
/// This is the same loop the standalone `sens-lsp` binary runs; the
/// CLI exposes it as `sens lsp` so editors need only one binary.
/// stdout carries ONLY framed LSP protocol traffic — there is nothing
/// here that prints diagnostics or banners to stdout by design.
pub fn run_stdio() {
    use std::io::{BufReader, BufWriter, Write};
    use std::process::exit;

    let stdin = std::io::stdin();
    let stdout = std::io::stdout();
    let mut input = BufReader::new(stdin.lock());
    let mut output = BufWriter::new(stdout.lock());
    let mut lsp = server::Server::new();

    loop {
        match transport::read_message(&mut input) {
            Ok(Some(message)) => {
                if server::Server::wants_exit(&message) {
                    exit(0);
                }
                for outgoing in lsp.handle_message(&message) {
                    if transport::write_message(&mut output, &outgoing).is_err() {
                        return; // client went away; nothing sensible left to do
                    }
                }
                let _ = output.flush();
            }
            Ok(None) => return,
            Err(_) => {
                // Malformed framing: answer once and stop rather than spin.
                let _ = transport::write_message(
                    &mut output,
                    &protocol::response(&None, None, Some((-32700, "invalid framing".into()))),
                );
                let _ = Write::flush(&mut output);
                return;
            }
        }
    }
}
