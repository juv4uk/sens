//! transport.rs — stdio framing only. Reads `Content-Length`-framed
//! JSON-RPC messages from stdin and writes framed messages to stdout.
//! Knows nothing about the language and nothing about LSP methods.

use std::io::{BufRead, Write};

/// One incoming message's raw JSON text, or None on clean EOF.
pub fn read_message(input: &mut impl BufRead) -> std::io::Result<Option<String>> {
    let mut content_length: Option<usize> = None;
    loop {
        let mut line = String::new();
        if input.read_line(&mut line)? == 0 {
            return Ok(None); // EOF
        }
        let line = line.trim_end();
        if line.is_empty() {
            break; // end of headers
        }
        if let Some(value) = line.strip_prefix("Content-Length:") {
            content_length = value.trim().parse::<usize>().ok();
        }
        // Other headers (Content-Type) are ignored per spec.
    }
    let Some(length) = content_length else {
        // A body without a length cannot be trusted; drop it by refusing
        // to proceed — a robust server must not spin or crash here.
        return Ok(None);
    };
    let mut buffer = vec![0u8; length];
    input.read_exact(&mut buffer)?;
    String::from_utf8(buffer)
        .map(Some)
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))
}

pub fn write_message(output: &mut impl Write, json: &str) -> std::io::Result<()> {
    write!(output, "Content-Length: {}\r\n\r\n", json.len())?;
    output.write_all(json.as_bytes())?;
    output.flush()
}
