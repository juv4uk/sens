//! protocol.rs — decoding of incoming JSON-RPC/LSP messages into the
//! sens `Value` representation (via the canonical `sens::parse_json`)
//! plus small typed accessors, and builders for outgoing messages using
//! this crate's transport-local encoder.

use crate::analysis::offset_to_position;
use crate::jsonout::str_lit;
use sens::Value;

/// Navigate an alist produced by `parse_json`: objects decode to lists of
/// dotted pairs whose keys are strings.
pub fn get<'a>(value: &'a Value, key: &str) -> Option<&'a Value> {
    let mut current = value;
    loop {
        match current {
            Value::Nil => return None,
            Value::Pair(entry, rest) => {
                if let Value::Pair(k, v) = &**entry {
                    if let Value::String(name) = &**k {
                        if name.as_ref() == key {
                            return Some(v);
                        }
                    }
                }
                current = rest;
            }
            _ => return None,
        }
    }
}

pub fn as_str(value: Option<&Value>) -> Option<&str> {
    match value? {
        Value::String(s) => Some(s),
        _ => None,
    }
}

pub fn as_i64(value: Option<&Value>) -> Option<i64> {
    match value? {
        // Integral JSON numbers decode as exact numbers.
        Value::Number(n, _)
            if n.fract() == 0.0 && *n >= i64::MIN as f64 && *n <= i64::MAX as f64 =>
        {
            Some(*n as i64)
        }
        _ => None,
    }
}

pub fn as_array(value: Option<&Value>) -> Vec<&Value> {
    let mut items = Vec::new();
    let Some(mut current) = value else {
        return items;
    };
    loop {
        match current {
            Value::Nil => return items,
            Value::Pair(head, tail) => {
                items.push(&**head);
                current = tail;
            }
            _ => return items,
        }
    }
}

/// The decoded shape of one incoming message.
#[derive(Debug)]
pub struct Incoming {
    pub id: Option<Value>,
    pub method: Option<String>,
    pub params: Option<Value>,
}

/// Decode a raw JSON-RPC text into its parts; malformed messages yield
/// an error so the server can answer ParseError instead of crashing.
pub fn decode(text: &str) -> Result<Incoming, String> {
    let value = sens::parse_json(text)?;
    Ok(Incoming {
        id: get(&value, "id").cloned(),
        method: as_str(get(&value, "method")).map(str::to_string),
        params: get(&value, "params").cloned(),
    })
}

// ---------------------------------------------------------------------------
// Outgoing message builders (transport-local encoding).
// ---------------------------------------------------------------------------

pub fn span_to_range(source: &str, start: usize, end: usize) -> String {
    let (sl, sc) = offset_to_position(source, start);
    let (el, ec) = offset_to_position(source, end);
    format!(
        "{{\"start\":{{\"line\":{sl},\"character\":{sc}}},\"end\":{{\"line\":{el},\"character\":{ec}}}}}"
    )
}

fn id_text(id: &Option<Value>) -> String {
    match id {
        Some(Value::String(s)) => str_lit(s),
        Some(Value::Number(n, _)) if n.fract() == 0.0 => format!("{}", *n as i64),
        Some(Value::Number(n, _)) => format!("{n}"),
        Some(Value::Nil) | None => "null".to_string(),
        Some(other) => str_lit(&other.to_string()),
    }
}

pub fn response(
    id: &Option<Value>,
    result: Option<String>,
    error: Option<(i64, String)>,
) -> String {
    let body = if let Some((code, message)) = error {
        format!(
            "\"error\":{{\"code\":{code},\"message\":{}}}",
            str_lit(&message)
        )
    } else {
        format!(
            "\"result\":{}",
            result.unwrap_or_else(|| "null".to_string())
        )
    };
    let mut out = String::with_capacity(body.len() + 32);
    out.push_str("{\"jsonrpc\":\"2.0\",\"id\":");
    out.push_str(&id_text(id));
    out.push(',');
    out.push_str(&body);
    out.push('}');
    out
}

pub fn notification(method: &str, params: String) -> String {
    let mut out = String::with_capacity(params.len() + method.len() + 40);
    out.push_str("{\"jsonrpc\":\"2.0\",\"method\":");
    out.push_str(&str_lit(method));
    out.push_str(",\"params\":");
    out.push_str(&params);
    out.push('}');
    out
}

pub fn publish_diagnostics(uri: &str, diagnostics: &[String]) -> String {
    notification(
        "textDocument/publishDiagnostics",
        format!(
            "{{\"uri\":{},\"diagnostics\":[{}]}}",
            str_lit(uri),
            diagnostics.join(",")
        ),
    )
}

pub fn diagnostic(source_text: &str, message: &str, start: usize, end: usize) -> String {
    format!(
        "{{\"range\":{},\"severity\":1,\"source\":\"sens\",\"message\":{}}}",
        span_to_range(source_text, start, end),
        str_lit(message)
    )
}
