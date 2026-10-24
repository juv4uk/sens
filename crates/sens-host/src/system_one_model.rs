//! Local, mechanism-only adapter from a SENS Choice query to model log-probabilities.
//!
//! The adapter deliberately returns a distribution plus provenance, never a decision.
//! SENS remains responsible for validating the domain, deriving confidence, and choosing,
//! deferring, or rejecting the observation. Only loopback HTTP is accepted: this boundary
//! is for a local vLLM-compatible model, not arbitrary network exfiltration.

use sens::{
    exact_domain_fraction_parts, BinaryNumber, Environment, ErrorKind, LanguageError, Span, Value,
};
use serde_json::{json, Value as Json};
use std::{
    collections::HashMap,
    env,
    io::{Read, Write},
    net::TcpStream,
    rc::Rc,
    time::Duration,
};

const PROBABILITY_DENOMINATOR: u64 = 1_000_000_000;
const PROBABILITY_DOMAIN_WIDTH: usize = 48;
const MAX_OPTIONS: usize = 19;
const MAX_RESPONSE_BYTES: usize = 8 * 1024 * 1024;
const CONNECT_TIMEOUT: Duration = Duration::from_secs(5);
const IO_TIMEOUT: Duration = Duration::from_secs(90);

fn fail(kind: ErrorKind, message: impl Into<String>, span: Span) -> LanguageError {
    LanguageError::new(kind, message.into(), span)
}

fn symbol(name: &str) -> Value {
    Value::Symbol(Rc::from(name))
}

fn text(value: &Value, what: &str, span: Span) -> Result<String, LanguageError> {
    match value {
        Value::String(value) | Value::Symbol(value) => Ok(value.to_string()),
        _ => Err(fail(
            ErrorKind::Type,
            format!("{what} must be a SENS string or symbol"),
            span,
        )),
    }
}

fn proper_list(value: &Value, what: &str, span: Span) -> Result<Vec<Value>, LanguageError> {
    let mut result = Vec::new();
    let mut cursor = value;
    loop {
        match cursor {
            Value::Nil => return Ok(result),
            Value::Pair(node) => {
                result.push(node.head.clone());
                cursor = &node.tail;
            }
            _ => {
                return Err(fail(
                    ErrorKind::Type,
                    format!("{what} must be a proper SENS list"),
                    span,
                ));
            }
        }
    }
}

#[derive(Clone)]
struct Criterion {
    label: Value,
    label_text: String,
    description: String,
    letter: String,
}

fn parse_criteria(value: &Value, span: Span) -> Result<Vec<Criterion>, LanguageError> {
    let rows = proper_list(value, "criteria", span)?;
    if !(2..=MAX_OPTIONS).contains(&rows.len()) {
        return Err(fail(
            ErrorKind::InvalidForm,
            format!("local model Choice needs 2..={MAX_OPTIONS} criteria"),
            span,
        ));
    }

    let mut seen = HashMap::<String, ()>::new();
    let mut criteria = Vec::with_capacity(rows.len());
    for (index, row) in rows.iter().enumerate() {
        let fields = proper_list(row, "criterion row", span)?;
        if fields.len() != 2 {
            return Err(fail(
                ErrorKind::InvalidForm,
                "each criterion must contain exactly (label description)",
                span,
            ));
        }
        let label_text = text(&fields[0], "criterion label", span)?;
        let description = text(&fields[1], "criterion description", span)?;
        if label_text.trim().is_empty() || description.trim().is_empty() {
            return Err(fail(
                ErrorKind::InvalidForm,
                "criterion labels and descriptions must not be empty",
                span,
            ));
        }
        if seen.insert(label_text.clone(), ()).is_some() {
            return Err(fail(
                ErrorKind::InvalidForm,
                format!("duplicate Choice criterion: {label_text}"),
                span,
            ));
        }
        criteria.push(Criterion {
            label: fields[0].clone(),
            label_text,
            description,
            letter: ((b'A' + index as u8) as char).to_string(),
        });
    }
    Ok(criteria)
}

struct LocalEndpoint {
    port: u16,
    path: String,
}

fn parse_loopback_endpoint(endpoint: &str, span: Span) -> Result<LocalEndpoint, LanguageError> {
    let rest = endpoint.strip_prefix("http://").ok_or_else(|| {
        fail(
            ErrorKind::InvalidForm,
            "local model endpoint must use plain HTTP to 127.0.0.1",
            span,
        )
    })?;
    let (authority, path_suffix) = rest.split_once('/').ok_or_else(|| {
        fail(
            ErrorKind::InvalidForm,
            "local model endpoint must include a request path",
            span,
        )
    })?;
    let Some(port_text) = authority.strip_prefix("127.0.0.1:") else {
        return Err(fail(
            ErrorKind::InvalidForm,
            "local model endpoint is restricted to 127.0.0.1",
            span,
        ));
    };
    let port = port_text.parse::<u16>().map_err(|_| {
        fail(
            ErrorKind::InvalidForm,
            "local model endpoint must contain a valid TCP port",
            span,
        )
    })?;
    if port == 0
        || path_suffix.is_empty()
        || path_suffix
            .chars()
            .any(|ch| matches!(ch, '\r' | '\n' | '#' | '?'))
    {
        return Err(fail(
            ErrorKind::InvalidForm,
            "local model endpoint path or port is not canonical",
            span,
        ));
    }
    Ok(LocalEndpoint {
        port,
        path: format!("/{path_suffix}"),
    })
}

fn chunked_body(mut body: &[u8]) -> Result<Vec<u8>, String> {
    let mut output = Vec::new();
    loop {
        let line_end = body
            .windows(2)
            .position(|window| window == b"\r\n")
            .ok_or_else(|| "invalid chunked HTTP response: missing size line".to_string())?;
        let size_line = std::str::from_utf8(&body[..line_end])
            .map_err(|_| "invalid chunked HTTP response: non-UTF-8 size".to_string())?;
        let size_text = size_line.split(';').next().unwrap_or_default().trim();
        let size = usize::from_str_radix(size_text, 16)
            .map_err(|_| "invalid chunked HTTP response: bad chunk size".to_string())?;
        body = &body[line_end + 2..];
        if size == 0 {
            return Ok(output);
        }
        if body.len() < size + 2 || &body[size..size + 2] != b"\r\n" {
            return Err("invalid chunked HTTP response: truncated chunk".to_string());
        }
        output.extend_from_slice(&body[..size]);
        if output.len() > MAX_RESPONSE_BYTES {
            return Err("local model response exceeded the size limit".to_string());
        }
        body = &body[size + 2..];
    }
}

fn post_json(
    endpoint: &str,
    payload: &Json,
    environment: &Environment,
    span: Span,
) -> Result<Json, LanguageError> {
    let endpoint = parse_loopback_endpoint(endpoint, span)?;
    // Мережева capability сесії поширюється також на модельний адаптер.
    if !environment.is_tcp_connect_allowed("127.0.0.1", endpoint.port) {
        return Err(super::denied(
            "модельний-розподіл-вибору-сире",
            format!("127.0.0.1:{}", endpoint.port),
            span,
        ));
    }
    let body = serde_json::to_vec(payload).map_err(|error| {
        fail(
            ErrorKind::InvalidForm,
            format!("could not encode local model request: {error}"),
            span,
        )
    })?;

    let address = std::net::SocketAddr::new(
        std::net::IpAddr::V4(std::net::Ipv4Addr::LOCALHOST),
        endpoint.port,
    );
    let mut stream = TcpStream::connect_timeout(&address, CONNECT_TIMEOUT).map_err(|error| {
        fail(
            ErrorKind::InvalidForm,
            format!("could not connect to the local model: {error}"),
            span,
        )
    })?;
    stream.set_read_timeout(Some(IO_TIMEOUT)).map_err(|error| {
        fail(
            ErrorKind::InvalidForm,
            format!("could not set local model read timeout: {error}"),
            span,
        )
    })?;
    stream
        .set_write_timeout(Some(IO_TIMEOUT))
        .map_err(|error| {
            fail(
                ErrorKind::InvalidForm,
                format!("could not set local model write timeout: {error}"),
                span,
            )
        })?;

    let mut request = format!(
        "POST {} HTTP/1.1\r\nHost: 127.0.0.1:{}\r\nContent-Type: application/json\r\nAccept: application/json\r\nConnection: close\r\nContent-Length: {}\r\n",
        endpoint.path,
        endpoint.port,
        body.len()
    );
    if let Ok(key) = env::var("SENS_SYSTEM_ONE_API_KEY") {
        if !key.is_empty() && !key.contains('\r') && !key.contains('\n') {
            request.push_str(&format!("Authorization: Bearer {key}\r\n"));
        }
    }
    request.push_str("\r\n");

    stream
        .write_all(request.as_bytes())
        .and_then(|_| stream.write_all(&body))
        .map_err(|error| {
            fail(
                ErrorKind::InvalidForm,
                format!("could not send request to the local model: {error}"),
                span,
            )
        })?;

    let mut response = Vec::new();
    let mut buffer = [0u8; 8192];
    loop {
        let read = stream.read(&mut buffer).map_err(|error| {
            fail(
                ErrorKind::InvalidForm,
                format!("could not read local model response: {error}"),
                span,
            )
        })?;
        if read == 0 {
            break;
        }
        if response.len() + read > MAX_RESPONSE_BYTES {
            return Err(fail(
                ErrorKind::InvalidForm,
                "local model HTTP response exceeded the size limit",
                span,
            ));
        }
        response.extend_from_slice(&buffer[..read]);
    }

    let header_end = response
        .windows(4)
        .position(|window| window == b"\r\n\r\n")
        .ok_or_else(|| {
            fail(
                ErrorKind::InvalidForm,
                "malformed local model HTTP response",
                span,
            )
        })?;
    let header = std::str::from_utf8(&response[..header_end]).map_err(|_| {
        fail(
            ErrorKind::InvalidForm,
            "local model returned non-UTF-8 HTTP headers",
            span,
        )
    })?;
    let status = header
        .lines()
        .next()
        .and_then(|line| line.split_whitespace().nth(1))
        .and_then(|code| code.parse::<u16>().ok())
        .ok_or_else(|| {
            fail(
                ErrorKind::InvalidForm,
                "local model returned an invalid HTTP status",
                span,
            )
        })?;
    if !(200..300).contains(&status) {
        return Err(fail(
            ErrorKind::InvalidForm,
            format!("local model returned HTTP status {status}"),
            span,
        ));
    }

    let raw_body = &response[header_end + 4..];
    let lower_header = header.to_ascii_lowercase();
    let response_body = if lower_header.contains("transfer-encoding: chunked") {
        chunked_body(raw_body).map_err(|message| fail(ErrorKind::InvalidForm, message, span))?
    } else if let Some(length) = header.lines().find_map(|line| {
        let (name, value) = line.split_once(':')?;
        if name.eq_ignore_ascii_case("content-length") {
            value.trim().parse::<usize>().ok()
        } else {
            None
        }
    }) {
        if raw_body.len() != length {
            return Err(fail(
                ErrorKind::InvalidForm,
                "local model HTTP body does not match Content-Length",
                span,
            ));
        }
        raw_body.to_vec()
    } else {
        raw_body.to_vec()
    };

    serde_json::from_slice(&response_body).map_err(|error| {
        fail(
            ErrorKind::InvalidForm,
            format!("local model returned invalid JSON: {error}"),
            span,
        )
    })
}

fn log_add(left: f64, right: f64) -> f64 {
    let maximum = left.max(right);
    maximum + ((left - maximum).exp() + (right - maximum).exp()).ln()
}

fn log_probabilities(
    response: &Json,
    criteria: &[Criterion],
    span: Span,
) -> Result<Vec<f64>, LanguageError> {
    let rows = response
        .get("choices")
        .and_then(Json::as_array)
        .and_then(|choices| choices.first())
        .and_then(|choice| choice.get("logprobs"))
        .and_then(|logprobs| logprobs.get("content"))
        .and_then(Json::as_array)
        .and_then(|content| content.first())
        .and_then(|position| position.get("top_logprobs"))
        .and_then(Json::as_array)
        .ok_or_else(|| {
            fail(
                ErrorKind::InvalidForm,
                "local model response has no top_logprobs; refusing to invent a distribution",
                span,
            )
        })?;

    let mut by_letter = HashMap::<String, f64>::new();
    for row in rows {
        let Some(token) = row.get("token").and_then(Json::as_str) else {
            continue;
        };
        let Some(log_probability) = row.get("logprob").and_then(Json::as_f64) else {
            continue;
        };
        if !log_probability.is_finite() {
            continue;
        }
        let token = token.trim();
        if criteria.iter().any(|criterion| criterion.letter == token) {
            by_letter
                .entry(token.to_string())
                .and_modify(|previous| *previous = log_add(*previous, log_probability))
                .or_insert(log_probability);
        }
    }

    criteria
        .iter()
        .map(|criterion| {
            by_letter.get(&criterion.letter).copied().ok_or_else(|| {
                fail(
                    ErrorKind::InvalidForm,
                    format!(
                        "local model omitted probability for allowed label {}",
                        criterion.letter
                    ),
                    span,
                )
            })
        })
        .collect()
}

fn domain_word(value: u64, span: Span) -> Result<BinaryNumber, LanguageError> {
    // D48 keeps the fixed-point denominator 1e9 positive in a signed exact domain.
    if value >= (1_u64 << (PROBABILITY_DOMAIN_WIDTH - 1)) {
        return Err(fail(
            ErrorKind::NumericOverflow,
            "model probability count does not fit a positive signed D48 word",
            span,
        ));
    }
    let bits: Vec<u8> = (0..PROBABILITY_DOMAIN_WIDTH)
        .rev()
        .map(|shift| ((value >> shift) & 1) as u8)
        .collect();
    BinaryNumber::from_numeric_domain_bits(PROBABILITY_DOMAIN_WIDTH, &bits).ok_or_else(|| {
        fail(
            ErrorKind::InvalidForm,
            "could not construct a domain-qualified D48 probability component",
            span,
        )
    })
}

fn exact_distribution(
    log_probabilities: &[f64],
    criteria: &[Criterion],
    span: Span,
) -> Result<Value, LanguageError> {
    if log_probabilities.len() != criteria.len() || log_probabilities.is_empty() {
        return Err(fail(
            ErrorKind::InvalidForm,
            "local model produced a mismatched label/probability count",
            span,
        ));
    }
    if log_probabilities.iter().any(|value| !value.is_finite()) {
        return Err(fail(
            ErrorKind::InvalidForm,
            "local model produced a non-finite log-probability",
            span,
        ));
    }
    let maximum = log_probabilities
        .iter()
        .copied()
        .fold(f64::NEG_INFINITY, f64::max);
    let exponentials: Vec<f64> = log_probabilities
        .iter()
        .map(|value| (value - maximum).exp())
        .collect();
    let total: f64 = exponentials.iter().sum();
    if !total.is_finite() || total <= 0.0 {
        return Err(fail(
            ErrorKind::InvalidForm,
            "local model log-probabilities do not yield a finite distribution",
            span,
        ));
    }

    // The model's floating-point scores are quantized once at this adapter edge.
    // Largest-remainder allocation preserves a total of exactly 1e9 integer units.
    // Each count becomes an exact D48 fraction through the core's canonical factory:
    // no bare Rational/float is promoted into arithmetic and no new Value variant exists.
    let scaled: Vec<f64> = exponentials
        .iter()
        .map(|value| value / total * PROBABILITY_DENOMINATOR as f64)
        .collect();
    let mut counts: Vec<u64> = scaled.iter().map(|value| value.floor() as u64).collect();
    let assigned: u64 = counts.iter().sum();
    let remaining = PROBABILITY_DENOMINATOR
        .checked_sub(assigned)
        .ok_or_else(|| {
            fail(
                ErrorKind::InvalidForm,
                "local model probability quantization overflowed",
                span,
            )
        })?;
    if remaining as usize > counts.len() {
        return Err(fail(
            ErrorKind::InvalidForm,
            "local model probability quantization was numerically unstable",
            span,
        ));
    }
    let mut order: Vec<usize> = (0..scaled.len()).collect();
    order.sort_by(|left, right| {
        let l = scaled[*left] - scaled[*left].floor();
        let r = scaled[*right] - scaled[*right].floor();
        r.total_cmp(&l).then_with(|| left.cmp(right))
    });
    for index in order.into_iter().take(remaining as usize) {
        counts[index] += 1;
    }

    let denominator = domain_word(PROBABILITY_DENOMINATOR, span)?;
    let mut entries = Vec::with_capacity(criteria.len());
    for (criterion, count) in criteria.iter().zip(counts.iter()) {
        let numerator = domain_word(*count, span)?;
        let exact =
            exact_domain_fraction_parts(false, &numerator, &denominator).ok_or_else(|| {
                fail(
                    ErrorKind::NumericOverflow,
                    "could not encode normalized model probability as an exact D48 fraction",
                    span,
                )
            })?;
        entries.push(Value::list([criterion.label.clone(), exact]));
    }
    Ok(Value::list(entries))
}

/// Evaluated capability: (модельний-розподіл-вибору-сире endpoint model context instruction criteria).
/// It returns (model-distribution/1 distribution provenance), not accept/defer/invalid.
pub(crate) fn evaluate_choice_distribution(
    arguments: &[(Value, Span)],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    let endpoint = text(&arguments[0].0, "model endpoint", arguments[0].1)?;
    let model = text(&arguments[1].0, "model name", arguments[1].1)?;
    let context = text(&arguments[2].0, "model context", arguments[2].1)?;
    let instruction = text(&arguments[3].0, "question instruction", arguments[3].1)?;
    if model.trim().is_empty() || instruction.trim().is_empty() {
        return Err(fail(
            ErrorKind::InvalidForm,
            "local model name and question instruction must not be empty",
            span,
        ));
    }
    let criteria = parse_criteria(&arguments[4].0, arguments[4].1)?;
    let letters: Vec<String> = criteria
        .iter()
        .map(|criterion| criterion.letter.clone())
        .collect();
    let prompt_criteria = criteria
        .iter()
        .map(|criterion| {
            format!(
                "{}: {} — {}",
                criterion.letter, criterion.label_text, criterion.description
            )
        })
        .collect::<Vec<_>>()
        .join("\n");
    let prompt = format!(
        "{}\n\nКритерії вибору:\n{}\n\nОціни зміст і поверни лише одну літеру з дозволеного набору. Не додавай пояснень.",
        instruction, prompt_criteria
    );

    let payload = json!({
        "model": model,
        "max_tokens": 1,
        "temperature": 0,
        "logprobs": true,
        "top_logprobs": 20,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": context}
        ],
        "structured_outputs": {"choice": letters},
        "chat_template_kwargs": {"enable_thinking": false}
    });
    let response = post_json(&endpoint, &payload, environment, span)?;
    let logs = log_probabilities(&response, &criteria, span)?;
    let distribution = exact_distribution(&logs, &criteria, span)?;

    let endpoint_record = endpoint
        .strip_prefix("http://")
        .and_then(|value| value.split('/').next())
        .unwrap_or("127.0.0.1");
    let provenance = Value::list([
        Value::list([symbol("source"), symbol("local-model")]),
        Value::list([symbol("provider"), symbol("vllm-openai-compatible")]),
        Value::list([symbol("model"), Value::String(Rc::from(model.as_str()))]),
        Value::list([
            symbol("method"),
            Value::String(Rc::from("softmax-top-logprobs-v1")),
        ]),
        Value::list([
            symbol("quantization"),
            Value::String(Rc::from("exact-rational-largest-remainder-1e9")),
        ]),
        Value::list([symbol("endpoint"), Value::String(Rc::from(endpoint_record))]),
    ]);
    Ok(Value::list([
        symbol("model-distribution/1"),
        distribution,
        provenance,
    ]))
}
