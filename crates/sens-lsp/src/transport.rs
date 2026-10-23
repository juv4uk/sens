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

#[cfg(test)]
mod tests {
    use super::{read_message, write_message};
    use std::io::{Cursor, ErrorKind};

    #[test]
    fn рамка_зберігає_довжину_utf8_у_байтах() {
        // Тестуємо Rust stdio-фреймування, а не семантику JSON чи SENS.
        let повідомлення = r#"{"текст":"привіт"}"#;
        let mut вихід = Vec::new();
        write_message(&mut вихід, повідомлення).expect("запис фрейму");
        let заголовок = format!("Content-Length: {}\r\n\r\n", повідомлення.len());
        assert!(вихід.starts_with(заголовок.as_bytes()));
        let mut вхід = Cursor::new(вихід);
        assert_eq!(
            read_message(&mut вхід).expect("читання фрейму").as_deref(),
            Some(повідомлення)
        );
        assert_eq!(read_message(&mut вхід).expect("чистий EOF"), None);
    }

    #[test]
    fn рамка_відхиляє_передчасний_eof() {
        let mut вхід = Cursor::new(&b"Content-Length: 4\r\n\r\nab"[..]);
        let помилка = read_message(&mut вхід).expect_err("неповне тіло");
        assert_eq!(помилка.kind(), ErrorKind::UnexpectedEof);
    }

    #[test]
    fn рамка_відхиляє_некоректний_utf8() {
        let mut байти = b"Content-Length: 1\r\n\r\n".to_vec();
        байти.push(0xff);
        let mut вхід = Cursor::new(байти);
        let помилка = read_message(&mut вхід).expect_err("некоректний UTF-8");
        assert_eq!(помилка.kind(), ErrorKind::InvalidData);
    }
}
