//! JSON wire-format decoder exposed to host adapters as a plain parser.
//! This module does not register a language resident or grant callability.
//!
//! Representation handed back to the language:
//! - object  → alist of dotted pairs `("key" . value)`
//! - array   → proper list
//! - string  → `Value::String`
//! - integer-token number → exact scalar (`Value::Number` or `Value::Rational`)
//! - decimal/exponent number → `Value::Number(..., Exactness::Inexact)`
//! - true/false → `Value::Bool`
//! - null    → `Value::Nil`
//!
//! Hand-rolled, no external dependency — this crate's zero-dependency policy
//! (see Cargo.toml) predates and outlives this mechanism.

use crate::{PairNode, Value};
use std::rc::Rc;

/// Plain-function form of the canonical JSON decoder, for host adapters
/// (LSP, CLI tooling) that must consume JSON without going through `eval`.
/// The matching serializer is deliberately not provided: JSON output is a
/// transport concern of each adapter, not sens semantics.
///
/// Maximum container nesting. Recursive descent needs a bound so deeply
/// nested input fails named instead of overflowing the Rust stack - the
/// same S3-shaped discipline the reader applies to numeric literals.
const MAX_NESTING_DEPTH: u32 = 256;

pub fn parse_json(text: &str) -> Result<Value, String> {
    let mut parser = JsonParser {
        bytes: text.as_bytes(),
        pos: 0,
        depth: 0,
    };
    parser.skip_ws();
    let value = parser.parse_value()?;
    parser.skip_ws();
    if parser.pos != parser.bytes.len() {
        return Err(parser.error("trailing characters after JSON value"));
    }
    Ok(value)
}

struct JsonParser<'a> {
    bytes: &'a [u8],
    pos: usize,
    depth: u32,
}

impl<'a> JsonParser<'a> {
    fn error(&self, message: &str) -> String {
        format!("json-parse: {message} at byte {}", self.pos)
    }

    fn peek(&self) -> Option<u8> {
        self.bytes.get(self.pos).copied()
    }

    fn bump(&mut self) -> Option<u8> {
        let byte = self.peek();
        if byte.is_some() {
            self.pos += 1;
        }
        byte
    }

    fn skip_ws(&mut self) {
        while matches!(self.peek(), Some(b' ' | b'\t' | b'\n' | b'\r')) {
            self.pos += 1;
        }
    }

    fn expect(&mut self, byte: u8) -> Result<(), String> {
        if self.bump() == Some(byte) {
            Ok(())
        } else {
            Err(self.error(&format!("expected '{}'", byte as char)))
        }
    }

    fn enter(&mut self) -> Result<(), String> {
        if self.depth >= MAX_NESTING_DEPTH {
            return Err(self.error("nesting too deep"));
        }
        self.depth += 1;
        Ok(())
    }

    fn parse_value(&mut self) -> Result<Value, String> {
        match self.peek() {
            Some(b'{') => self.parse_object(),
            Some(b'[') => self.parse_array(),
            Some(b'"') => self
                .parse_string()
                .map(|s| Value::String(Rc::from(s.as_str()))),
            Some(b't') => self.parse_literal("true", Value::Bool(true)),
            Some(b'f') => self.parse_literal("false", Value::Bool(false)),
            Some(b'n') => self.parse_literal("null", Value::Nil),
            Some(c) if c == b'-' || c.is_ascii_digit() => self.parse_number(),
            _ => Err(self.error("unexpected character")),
        }
    }

    fn parse_literal(&mut self, word: &str, value: Value) -> Result<Value, String> {
        if self.bytes[self.pos..].starts_with(word.as_bytes()) {
            self.pos += word.len();
            Ok(value)
        } else {
            Err(self.error(&format!("invalid literal, expected {word}")))
        }
    }

    fn parse_object(&mut self) -> Result<Value, String> {
        self.enter()?;
        let result = self.parse_object_inner();
        self.depth -= 1;
        result
    }

    fn parse_object_inner(&mut self) -> Result<Value, String> {
        self.expect(b'{')?;
        let mut pairs: Vec<(Value, Value)> = Vec::new();
        self.skip_ws();
        if self.peek() == Some(b'}') {
            self.pos += 1;
            return Ok(Value::Nil);
        }
        loop {
            self.skip_ws();
            let key = self.parse_string()?;
            self.skip_ws();
            self.expect(b':')?;
            self.skip_ws();
            let value = self.parse_value()?;
            pairs.push((Value::String(Rc::from(key.as_str())), value));
            self.skip_ws();
            match self.bump() {
                Some(b',') => continue,
                Some(b'}') => break,
                _ => return Err(self.error("expected ',' or '}' in object")),
            }
        }
        let mut alist = Value::Nil;
        for (key, value) in pairs.into_iter().rev() {
            alist = Value::Pair(Rc::new(PairNode {
                head: Value::Pair(Rc::new(PairNode {
                    head: key,
                    tail: value,
                })),
                tail: alist,
            }));
        }
        Ok(alist)
    }

    fn parse_array(&mut self) -> Result<Value, String> {
        self.enter()?;
        let result = self.parse_array_inner();
        self.depth -= 1;
        result
    }

    fn parse_array_inner(&mut self) -> Result<Value, String> {
        self.expect(b'[')?;
        let mut items = Vec::new();
        self.skip_ws();
        if self.peek() == Some(b']') {
            self.pos += 1;
            return Ok(Value::Nil);
        }
        loop {
            self.skip_ws();
            items.push(self.parse_value()?);
            self.skip_ws();
            match self.bump() {
                Some(b',') => continue,
                Some(b']') => break,
                _ => return Err(self.error("expected ',' or ']' in array")),
            }
        }
        Ok(Value::list(items))
    }

    fn parse_string(&mut self) -> Result<String, String> {
        self.expect(b'"')?;
        let mut out = String::new();
        loop {
            match self.bump() {
                None => return Err(self.error("unterminated string")),
                Some(b'"') => return Ok(out),
                Some(b'\\') => match self.bump() {
                    Some(b'"') => out.push('"'),
                    Some(b'\\') => out.push('\\'),
                    Some(b'/') => out.push('/'),
                    Some(b'b') => out.push('\u{0008}'),
                    Some(b'f') => out.push('\u{000C}'),
                    Some(b'n') => out.push('\n'),
                    Some(b'r') => out.push('\r'),
                    Some(b't') => out.push('\t'),
                    Some(b'u') => {
                        let code = self.parse_hex4()?;
                        let codepoint = if (0xD800..0xDC00).contains(&code) {
                            if self.bytes[self.pos..].starts_with(b"\\u") {
                                self.pos += 2;
                                let low = self.parse_hex4()?;
                                if (0xDC00..0xE000).contains(&low) {
                                    0x10000 + ((code - 0xD800) << 10) + (low - 0xDC00)
                                } else {
                                    0xFFFD
                                }
                            } else {
                                0xFFFD
                            }
                        } else if (0xDC00..0xE000).contains(&code) {
                            0xFFFD
                        } else {
                            code
                        };
                        match char::from_u32(codepoint) {
                            Some(ch) => out.push(ch),
                            None => out.push('\u{FFFD}'),
                        }
                    }
                    _ => return Err(self.error("invalid escape sequence")),
                },
                Some(_byte) => {
                    let start = self.pos - 1;
                    let mut end = self.pos;
                    while end < self.bytes.len() && self.bytes[end] & 0xC0 == 0x80 {
                        end += 1;
                    }
                    self.pos = end;
                    match std::str::from_utf8(&self.bytes[start..end]) {
                        Ok(text) => out.push_str(text),
                        Err(_) => return Err(self.error("invalid UTF-8 in string")),
                    }
                }
            }
        }
    }

    fn parse_hex4(&mut self) -> Result<u32, String> {
        let mut code: u32 = 0;
        for _ in 0..4 {
            let digit = match self.bump() {
                Some(b) if b.is_ascii_hexdigit() => (b as char).to_digit(16).unwrap(),
                _ => return Err(self.error("invalid \\u escape: expected 4 hex digits")),
            };
            code = code * 16 + digit;
        }
        Ok(code)
    }

    fn parse_number(&mut self) -> Result<Value, String> {
        let start = self.pos;
        if self.peek() == Some(b'-') {
            self.pos += 1;
        }
        while matches!(self.peek(), Some(c) if c.is_ascii_digit()) {
            self.pos += 1;
        }
        let mut integral = true;
        if self.peek() == Some(b'.') {
            integral = false;
            self.pos += 1;
            while matches!(self.peek(), Some(c) if c.is_ascii_digit()) {
                self.pos += 1;
            }
        }
        if matches!(self.peek(), Some(b'e' | b'E')) {
            integral = false;
            self.pos += 1;
            if matches!(self.peek(), Some(b'+' | b'-')) {
                self.pos += 1;
            }
            while matches!(self.peek(), Some(c) if c.is_ascii_digit()) {
                self.pos += 1;
            }
        }
        let text = std::str::from_utf8(&self.bytes[start..self.pos])
            .map_err(|_| self.error("invalid number"))?;
        if integral {
            let integer = crate::Rational::from_literal(text, "1")
                .ok_or_else(|| self.error("invalid number"))?;
            return Ok(super::super::arithmetic::exact_value(integer));
        }
        text.parse::<f64>()
            .map(|n| Value::Number(n, crate::Exactness::Inexact))
            .map_err(|_| self.error("invalid number"))
    }
}

