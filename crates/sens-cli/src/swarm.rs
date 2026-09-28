//! swarm.rs — the CLI-owned semantic TCP/oracle transport.
//! :9999 is intentionally semantic-only: request framing, eval/parse/diagnose,
//! contract-version and related oracle operations. Agent coordination lives in
//! swarm-node (:910x, swarm/1) and has no state or dispatch path in this module.

use sens::{
    eval_parsed_expressions, eval_parsed_expressions_incremental, parse, Environment, ErrorKind,
    Exactness, Session, Value,
};
use std::io::{self, BufRead, BufReader, Write};
use std::net::{Ipv4Addr, TcpListener, TcpStream};
use std::process;
use std::sync::Arc;
use std::thread;

/// Walks a `Value` list (the `Pair`-chain shape `Value::list` builds) into
/// a `Vec`, stopping at the first non-`Pair` tail. Used only for reading
/// the machine-protocol's own request/response envelopes — the language
/// itself has `car`/`cdr` for this, but the CLI here is reading a `Value`
/// that was never `def`d into a running `Session`.
fn list_items(mut value: &Value) -> Vec<Value> {
    let mut items = Vec::new();
    while let Value::Pair(head, tail) = value {
        items.push((**head).clone());
        value = tail;
    }
    items
}

enum RequestFrame {
    Eof,
    Line(Vec<u8>),
    TooLarge,
}

/// Read one newline-delimited frame without ever allocating more than `limit`
/// bytes for it. Oversized frames are drained through the newline and then
/// reported, so the connection cannot be desynchronised by the rejected data.
fn read_request_frame(reader: &mut BufReader<TcpStream>, limit: usize) -> io::Result<RequestFrame> {
    let mut bytes = Vec::with_capacity(limit.min(4096));
    let mut too_large = false;
    loop {
        let chunk = reader.fill_buf()?;
        if chunk.is_empty() {
            return Ok(if too_large {
                RequestFrame::TooLarge
            } else if bytes.is_empty() {
                RequestFrame::Eof
            } else {
                RequestFrame::Line(bytes)
            });
        }
        if let Some(newline) = chunk.iter().position(|byte| *byte == b'\n') {
            let frame_len = newline + 1;
            if too_large || bytes.len() + frame_len > limit {
                reader.consume(frame_len);
                return Ok(RequestFrame::TooLarge);
            }
            bytes.extend_from_slice(&chunk[..frame_len]);
            reader.consume(frame_len);
            return Ok(RequestFrame::Line(bytes));
        }
        if too_large || bytes.len() + chunk.len() > limit {
            too_large = true;
            let consume_len = chunk.len();
            reader.consume(consume_len);
        } else {
            let copied = chunk.to_vec();
            let consume_len = copied.len();
            bytes.extend_from_slice(&copied);
            reader.consume(consume_len);
        }
    }
}

/// Looks up `(key . value)` in a dotted-pair alist like
/// `language-contract.lisp`'s `((major . 1) (minor . 0) ...)` — distinct
/// from `list_items`' 2-element-list reading of the request/response
/// envelope, since a dotted pair's cdr is the value directly, not a
/// nested one-element list.
pub(crate) fn dotted_alist_lookup(alist: &Value, key: &str) -> Option<Value> {
    list_items(alist).into_iter().find_map(|item| match &item {
        Value::Pair(k, v) => match &**k {
            Value::Symbol(name) if &**name == key => Some((**v).clone()),
            _ => None,
        },
        _ => None,
    })
}

/// Process generation carried on every semantic-oracle response so a stateless
/// client can detect that the reference process restarted between calls. It is
/// transport metadata only: no coordination state is attached to it.
static SERVER_GENERATION: std::sync::OnceLock<u64> = std::sync::OnceLock::new();

fn server_generation() -> u64 {
    *SERVER_GENERATION.get_or_init(|| {
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0)
    })
}

/// `output` carries every `print`/`println`-style side-effect line the
/// evaluated expression produced, in order — dropping it (the first cut
/// of this protocol did) silently discards real program output, which is
/// exactly the "optimistic" half-truth this protocol exists to prevent.
fn ok_response(id: &Value, value: Value, output: &[String], contract_version: &Value) -> Value {
    Value::list([
        Value::Symbol("response".into()),
        Value::list([Value::Symbol("id".into()), id.clone()]),
        Value::list([Value::Symbol("status".into()), Value::Symbol("ok".into())]),
        Value::list([Value::Symbol("value".into()), value]),
        Value::list([
            Value::Symbol("output".into()),
            Value::list(
                output
                    .iter()
                    .map(|line| Value::String(line.as_str().into())),
            ),
        ]),
        Value::list([
            Value::Symbol("contract-version".into()),
            contract_version.clone(),
        ]),
        Value::list([
            Value::Symbol("server-generation".into()),
            Value::Number(server_generation() as f64, Exactness::Exact),
        ]),
    ])
}

fn error_response(id: &Value, kind: &str, message: &str, contract_version: &Value) -> Value {
    Value::list([
        Value::Symbol("response".into()),
        Value::list([Value::Symbol("id".into()), id.clone()]),
        Value::list([
            Value::Symbol("status".into()),
            Value::Symbol("error".into()),
        ]),
        Value::list([Value::Symbol("kind".into()), Value::Symbol(kind.into())]),
        Value::list([
            Value::Symbol("message".into()),
            Value::String(message.into()),
        ]),
        Value::list([
            Value::Symbol("contract-version".into()),
            contract_version.clone(),
        ]),
        Value::list([
            Value::Symbol("server-generation".into()),
            Value::Number(server_generation() as f64, Exactness::Exact),
        ]),
    ])
}

/// Same wire shape as `error_response`, plus one additive `(classification
/// ...)` field for a genuine `ErrorKind`-derived failure (evaluator/parser
/// errors only — request-shape validation like "missing field" has no
/// `ErrorKind` to classify and keeps using `error_response`). `status`
/// stays `error` and `kind` stays exactly as before, so an existing
/// consumer that only reads those two fields (e.g. `conformance-check.py`,
/// `mccarthy.rs`) is unaffected — this is Stage 1 of a two-stage design
/// (`ecosystem/decisions/`), not a protocol-version change.
fn error_response_classified(
    id: &Value,
    kind: &str,
    classification: sens::Classification,
    message: &str,
    contract_version: &Value,
) -> Value {
    Value::list([
        Value::Symbol("response".into()),
        Value::list([Value::Symbol("id".into()), id.clone()]),
        Value::list([
            Value::Symbol("status".into()),
            Value::Symbol("error".into()),
        ]),
        Value::list([Value::Symbol("kind".into()), Value::Symbol(kind.into())]),
        Value::list([
            Value::Symbol("classification".into()),
            Value::Symbol(classification.as_str().into()),
        ]),
        Value::list([
            Value::Symbol("message".into()),
            Value::String(message.into()),
        ]),
        Value::list([
            Value::Symbol("contract-version".into()),
            contract_version.clone(),
        ]),
        Value::list([
            Value::Symbol("server-generation".into()),
            Value::Number(server_generation() as f64, Exactness::Exact),
        ]),
    ])
}

fn protocol_error(kind: &str, message: &str, contract_version: &Value) -> Value {
    Value::list([
        Value::Symbol("protocol-error".into()),
        Value::list([Value::Symbol("kind".into()), Value::Symbol(kind.into())]),
        Value::list([
            Value::Symbol("message".into()),
            Value::String(message.into()),
        ]),
        Value::list([
            Value::Symbol("contract-version".into()),
            contract_version.clone(),
        ]),
        Value::list([
            Value::Symbol("server-generation".into()),
            Value::Number(server_generation() as f64, Exactness::Exact),
        ]),
    ])
}

fn source_digest(source: &str) -> String {
    let digest = sens::sha256_source(source.as_bytes());
    let mut hex = String::with_capacity(7 + digest.len() * 2);
    hex.push_str("sha256:");
    for byte in digest {
        use std::fmt::Write as _;
        let _ = write!(hex, "{byte:02x}");
    }
    hex
}

fn exact_usize(value: usize) -> Value {
    Value::Number(value as f64, Exactness::Exact)
}

/// Turn the canonical `LanguageError` into an agent-oriented, machine-readable
/// diagnostic.  The parser remains the only syntax authority; this merely
/// preserves its span and adds a conservative suggested edit for the two most
/// common parenthesis failures.  The edit is advice, never applied silently.
fn oracle_error_payload(source: &str, error: &sens::LanguageError) -> Value {
    let (line, column) = error.line_col(source);
    let (code, guidance, repair) = if error.message.starts_with("unclosed list") {
        (
            "unclosed-list",
            "Додайте одну ')' в кінці незакритої форми · Add one ')' at the end of the unclosed form",
            Value::list([
                Value::list([Value::Symbol("action".into()), Value::Symbol("insert".into())]),
                Value::list([Value::Symbol("text".into()), Value::String(")".into())]),
                Value::list([Value::Symbol("offset".into()), exact_usize(source.len())]),
            ]),
        )
    } else if error.message.starts_with("unexpected closing parenthesis") {
        (
            "unexpected-closing-parenthesis",
            "Приберіть зайву ')' у вказаному діапазоні · Remove the extra ')' at the reported span",
            Value::list([
                Value::list([
                    Value::Symbol("action".into()),
                    Value::Symbol("delete".into()),
                ]),
                Value::list([Value::Symbol("start".into()), exact_usize(error.span.start)]),
                Value::list([Value::Symbol("end".into()), exact_usize(error.span.end)]),
            ]),
        )
    } else {
        (
            error_kind_symbol(&error.kind),
            "Перевірте вказаний діапазон і повторіть oracle-check · Inspect the reported span and run oracle-check again",
            Value::list([Value::list([
                Value::Symbol("action".into()),
                Value::Symbol("inspect".into()),
            ])]),
        )
    };

    Value::list([
        Value::Symbol("error".into()),
        Value::list([
            Value::list([
                Value::Symbol("kind".into()),
                Value::Symbol(error_kind_symbol(&error.kind).into()),
            ]),
            Value::list([Value::Symbol("code".into()), Value::Symbol(code.into())]),
            Value::list([
                Value::Symbol("message".into()),
                Value::String(error.message.clone().into()),
            ]),
            Value::list([
                Value::Symbol("span".into()),
                Value::list([
                    Value::list([Value::Symbol("start".into()), exact_usize(error.span.start)]),
                    Value::list([Value::Symbol("end".into()), exact_usize(error.span.end)]),
                ]),
            ]),
            Value::list([
                Value::Symbol("location".into()),
                Value::list([
                    Value::list([Value::Symbol("line".into()), exact_usize(line)]),
                    Value::list([Value::Symbol("column".into()), exact_usize(column)]),
                ]),
            ]),
            Value::list([
                Value::Symbol("rendered".into()),
                Value::String(error.render(source).into()),
            ]),
            Value::list([
                Value::Symbol("guidance".into()),
                Value::String(guidance.into()),
            ]),
            Value::list([Value::Symbol("suggested-edit".into()), repair]),
        ]),
    ])
}

/// Versioned semantic result carried as the value of `oracle-eval`'s normal
/// transport response.  Transport success and language outcome are separate:
/// an evaluator error is a successfully delivered `(outcome error)` record,
/// not a TCP/protocol failure. Existing `eval` clients remain byte-compatible.
fn oracle_result_value(
    source: &str,
    contract_version: &Value,
    outcome: Value,
    payload: Value,
    output: &[String],
    evidence_class: &str,
) -> Value {
    Value::list([
        Value::Symbol("oracle-result".into()),
        Value::list([
            Value::Symbol("protocol".into()),
            Value::Symbol("oracle-result/1".into()),
        ]),
        Value::list([
            Value::Symbol("contract-revision".into()),
            contract_version.clone(),
        ]),
        Value::list([
            Value::Symbol("source-digest".into()),
            Value::String(source_digest(source).into()),
        ]),
        Value::list([
            Value::Symbol("implementation-revision".into()),
            Value::String(format!("sens-cli/{}", env!("CARGO_PKG_VERSION")).into()),
        ]),
        Value::list([Value::Symbol("outcome".into()), outcome]),
        payload,
        Value::list([
            Value::Symbol("output".into()),
            Value::list(
                output
                    .iter()
                    .map(|line| Value::String(line.as_str().into())),
            ),
        ]),
        Value::list([
            Value::Symbol("evidence-class".into()),
            Value::Symbol(evidence_class.into()),
        ]),
        Value::list([
            Value::Symbol("relation".into()),
            Value::Symbol("reference-implementation".into()),
        ]),
        Value::list([
            Value::Symbol("provenance".into()),
            Value::list([
                Value::list([
                    Value::Symbol("repository".into()),
                    Value::String("sens".into()),
                ]),
                Value::list([
                    Value::Symbol("runner".into()),
                    Value::String("sens-cli".into()),
                ]),
            ]),
        ]),
    ])
}

/// Side-effect-free agent preflight shared by the local CLI and TCP Oracle.
/// `true` means the complete source parsed; no evaluation has taken place.
pub(crate) fn oracle_check(source: &str, contract_version: &Value) -> (Value, bool) {
    match parse(source) {
        Ok(ast) => (
            oracle_result_value(
                source,
                contract_version,
                Value::Symbol("valid".into()),
                Value::list([
                    Value::Symbol("syntax".into()),
                    Value::list([
                        Value::list([
                            Value::Symbol("status".into()),
                            Value::Symbol("valid".into()),
                        ]),
                        Value::list([Value::Symbol("forms".into()), exact_usize(ast.len())]),
                    ]),
                ]),
                &[],
                "oracle-syntax-check",
            ),
            true,
        ),
        Err(error) => (
            oracle_result_value(
                source,
                contract_version,
                Value::Symbol("error".into()),
                oracle_error_payload(source, &error),
                &[],
                "oracle-syntax-check",
            ),
            false,
        ),
    }
}

/// Query the WSM-owned reference directory without duplicating its entries in
/// Rust. The session already contains core.lisp; Guard is the one shared
/// embed in `wsm-guard-core` (same library every Guard consumer uses), but
/// its reference directory is read fresh from disk on every call, exactly
/// like the LSP's `guard_knowledge.rs` already does — adding or editing a
/// topic in `knowledge/guard-reference.lisp` takes effect immediately, no
/// rebuild. `None` lists the curated frequently-used tool names. A named
/// query goes through `guard-ask`, which searches the tool directory and
/// the reference-topic directory together and tags the result `type
/// tool` / `type reference-topic` / `ambiguous` (found in both) / a
/// generic unknown-routed `not-found` — a cold agent asks one thing and
/// never needs to know which of the two directories actually held the
/// answer.
pub(crate) fn oracle_help(session: &mut Session, topic: Option<&str>) -> Result<Value, String> {
    let reference = std::fs::read_to_string("knowledge/guard-reference.lisp").map_err(|error| {
        format!(
            "cannot read knowledge/guard-reference.lisp (run from the sens repo root): {error}"
        )
    })?;
    for (name, source) in [
        ("lib/guard.lisp", wsm_guard_core::GUARD),
        ("knowledge/guard-reference.lisp", reference.as_str()),
    ] {
        let ast = parse(source)
            .map_err(|error| format!("cannot parse {name}: {}", error.render(source)))?;
        eval_parsed_expressions_incremental(&ast, session)
            .map_err(|error| format!("cannot load {name}: {}", error.render(source)))?;
    }

    let query = match topic {
        None => "(guard-scripts *guard-script-directory*)".to_string(),
        Some(topic)
            if !topic.is_empty()
                && topic
                    .chars()
                    .all(|character| character.is_ascii_alphanumeric() || character == '-') =>
        {
            format!("(guard-ask (quote {topic}))")
        }
        Some(_) => {
            return Err("oracle-help topic must contain only ASCII letters, digits, or '-'".into())
        }
    };
    let ast = parse(&query).map_err(|error| error.render(&query))?;
    eval_parsed_expressions_incremental(&ast, session)
        .map(|result| result.value)
        .map_err(|error| error.render(&query))
}

fn error_kind_symbol(kind: &ErrorKind) -> &'static str {
    match kind {
        ErrorKind::Parse => "parse-error",
        ErrorKind::UnknownSymbol => "unknown-symbol",
        ErrorKind::Arity => "arity-error",
        ErrorKind::Type => "type-error",
        ErrorKind::InvalidForm => "invalid-form",
        ErrorKind::UnsatisfiedConditional => "unsatisfied-conditional",
        ErrorKind::MechanismUnavailable => "mechanism-unavailable",
        ErrorKind::OutOfMemory => "out-of-memory",
        ErrorKind::NumericOverflow => "numeric-overflow",
        ErrorKind::DivisionByZero => "division-by-zero",
    }
}

/// `--tcp=PORT --protocol=sexpr` — the same live oracle as `run_tcp_repl`,
/// but for machines instead of humans: no banner, no prompt, one strict
/// `(request (id ..) (op ..) (source ..))` in, one `(response (id ..)
/// (status ..) ..)` out, every time, so `cml`/`fpga-lisp`/`my-idea` can
/// parse a response without guessing whether a given line is a value, an
/// error, or REPL chrome. Op set: `eval`, `parse`, `diagnose`,
/// `contract-version` for semantic-oracle use. `oracle-eval` returns the
/// same semantics in a versioned, provenance-bearing result value while
/// leaving the legacy `eval` response unchanged. `notify`/`poll` are for
/// short-lived, poll-based agent mailbox; `subscribe`/`publish` for
/// genuine push (owner decision, 2026-08-12) — a `subscribe`d connection
/// blocks and receives `(event ...)` lines the instant a matching
/// `publish` happens on any other connection, not on the next poll.
///
/// One OS thread per accepted connection (changed from strictly
/// sequential handling to make `subscribe` possible — a subscriber has
/// to block waiting for events while other connections keep working).
/// Each thread builds its own `Session`/`Environment` locally and never
/// shares it — `Value`'s `Rc`-based sharing (non-atomic refcounts) would
/// be unsound across threads, so nothing `Rc`-based ever crosses a
/// thread boundary here: `contract_version` is rebuilt fresh per
/// connection from two plain `f64`s, and the mailbox/broker only ever
/// pass already-`to_string()`-rendered `String`s between threads, never
/// a live `Value`. The isolation guarantee (`eval`/`parse`/`diagnose`
/// state invisible across connections) is now also physical (separate
/// threads), not just logical (separate `Environment`s in one thread).
pub(crate) fn run_tcp_repl_sexpr(
    port: u16,
    core_lib: &'static str,
    allowed: Vec<String>,
    contract_major: f64,
    contract_minor: f64,
) {
    let listener = match TcpListener::bind((Ipv4Addr::LOCALHOST, port)) {
        Ok(listener) => listener,
        Err(err) => {
            eprintln!("Error: could not bind TCP REPL to 127.0.0.1:{port}: {err}");
            process::exit(1);
        }
    };
    let actual_port = listener.local_addr().map(|a| a.port()).unwrap_or(port);
    eprintln!(
        "sens TCP REPL v{} (sexpr protocol) listening on 127.0.0.1:{actual_port}",
        env!("CARGO_PKG_VERSION")
    );

    let allowed = Arc::new(allowed);

    for stream in listener.incoming() {
        let stream = match stream {
            Ok(stream) => stream,
            Err(_) => continue,
        };
        let allowed = Arc::clone(&allowed);
        // Deep sens recursion (e.g. (fact 1000)) consumes native stack
        // through the tree-walking evaluator; the default 2 MiB thread
        // stack overflowed and ABORTED the whole shared oracle process
        // (found 2026-08-25 by wsl-nidana-1/wsl-ganaka-1). Give every
        // connection its own generous stack instead.
        thread::Builder::new()
            .stack_size(256 * 1024 * 1024)
            .spawn(move || {
                handle_sexpr_connection(stream, core_lib, &allowed, contract_major, contract_minor);
            })
            .expect("failed to spawn TCP connection thread");
    }
}

fn handle_sexpr_connection(
    mut stream: TcpStream,
    core_lib: &str,
    allowed: &[String],
    contract_major: f64,
    contract_minor: f64,
) {
    const MAX_REQUEST_LINE_BYTES: usize = 256 * 1024;
    let contract_version = Value::list([
        Value::Number(contract_major, Exactness::Exact),
        Value::Number(contract_minor, Exactness::Exact),
    ]);

    let peer = stream
        .peer_addr()
        .map(|a| a.to_string())
        .unwrap_or_else(|_| "?".into());
    eprintln!("TCP REPL: connection from {peer}");

    // The oracle protocol is an unauthenticated network boundary. Keep its
    // process policy explicit even though trusted native root sessions are
    // unrestricted by default.
    let environment = Environment::root().with_process_allowlist(allowed.to_vec());
    let mut session = Session { environment };
    if let Ok(core_ast) = parse(core_lib) {
        let _ = eval_parsed_expressions(&core_ast, &mut session);
    }

    let mut reader = BufReader::new(stream.try_clone().expect("clone TCP stream"));
    loop {
        let frame = match read_request_frame(&mut reader, MAX_REQUEST_LINE_BYTES) {
            Ok(frame) => frame,
            Err(error) => {
                let resp = error_response(
                    &Value::Nil,
                    "invalid-encoding",
                    &format!("request is not valid UTF-8: {error}"),
                    &contract_version,
                );
                let _ = writeln!(stream, "{resp}");
                break;
            }
        };
        let line = match frame {
            RequestFrame::Eof => break,
            RequestFrame::TooLarge => {
                let resp = error_response(
                    &Value::Nil,
                    "request-too-large",
                    &format!("request line exceeds {MAX_REQUEST_LINE_BYTES} bytes"),
                    &contract_version,
                );
                let _ = writeln!(stream, "{resp}");
                break;
            }
            RequestFrame::Line(bytes) => match String::from_utf8(bytes) {
                Ok(line) => line,
                Err(error) => {
                    let resp = error_response(
                        &Value::Nil,
                        "invalid-encoding",
                        &format!("request is not valid UTF-8: {error}"),
                        &contract_version,
                    );
                    let _ = writeln!(stream, "{resp}");
                    break;
                }
            },
        };
        let trimmed = line.trim();
        {
            if trimmed.is_empty() {
                continue;
            }
            eprintln!("TCP REPL: {peer} > request-bytes={}", line.len());

            // The request envelope itself is read as literal data
            // (`quote`), never evaluated — `(op eval)` deciding to
            // evaluate `source` is the only place code ever runs.
            let quoted = format!("(quote {trimmed})");
            let request = match parse(&quoted).ok().and_then(|ast| {
                eval_parsed_expressions_incremental(&ast, &mut session)
                    .ok()
                    .map(|r| r.value)
            }) {
                Some(value) => value,
                None => {
                    let resp = error_response(
                        &Value::Nil,
                        "parse-error",
                        "request envelope is not a valid s-expression",
                        &contract_version,
                    );
                    let _ = writeln!(stream, "{resp}");
                    continue;
                }
            };

            let fields = list_items(&request);
            // fields[0] is the `request` tag symbol itself.
            let mut id = Value::Nil;
            let mut id_seen = false;
            let mut op: Option<String> = None;
            let mut source: Option<String> = None;
            let mut topic: Option<String> = None;
            for field in fields.iter().skip(1) {
                let kv = list_items(field);
                let (Some(key), Some(val)) = (kv.first(), kv.get(1)) else {
                    continue;
                };
                if let Value::Symbol(name) = key {
                    match &**name {
                        "id" => {
                            id_seen = true;
                            id = val.clone();
                        }
                        "op" => {
                            if let Value::Symbol(value) = val {
                                op = Some(value.to_string());
                            }
                        }
                        "source" => {
                            if let Value::String(value) = val {
                                source = Some(value.to_string());
                            }
                        }
                        "topic" => {
                            if let Value::String(value) = val {
                                topic = Some(value.to_string());
                            }
                        }
                        _ => {}
                    }
                }
            }

            if !id_seen || matches!(id, Value::Nil) {
                let response = protocol_error(
                    "missing-id",
                    "request requires a non-nil id",
                    &contract_version,
                );
                let _ = writeln!(stream, "{response}");
                continue;
            }

            let response = match op.as_deref() {
                Some("contract-version") => {
                    ok_response(&id, contract_version.clone(), &[], &contract_version)
                }
                // `parse` renders the canonical structure via the same
                // `quote`-and-print path the request envelope itself
                // uses, not Rust's `{:?}` — the caller gets sens
                // syntax back, not this CLI's internal AST debug
                // format. Limited to a single top-level form, the
                // same arity `quote` itself has.
                Some("parse") => match &source {
                    None => error_response(
                        &id,
                        "invalid-form",
                        "op `parse` requires a `source` field",
                        &contract_version,
                    ),
                    Some(src) => match parse(src) {
                        Ok(ast) if ast.len() == 1 => {
                            let quoted_src = format!("(quote {src})");
                            match parse(&quoted_src).ok().and_then(|q| {
                                eval_parsed_expressions_incremental(&q, &mut session)
                                    .ok()
                                    .map(|r| r.value)
                            }) {
                                Some(structure) => {
                                    ok_response(&id, structure, &[], &contract_version)
                                }
                                None => error_response(
                                    &id,
                                    "parse-error",
                                    "source parsed but could not be rendered as data",
                                    &contract_version,
                                ),
                            }
                        }
                        Ok(_) => error_response(
                            &id,
                            "invalid-form",
                            "op `parse` accepts exactly one top-level form",
                            &contract_version,
                        ),
                        Err(e) => error_response_classified(
                            &id,
                            error_kind_symbol(&e.kind),
                            e.kind.classification(),
                            &e.message,
                            &contract_version,
                        ),
                    },
                },
                // Agent-facing syntax preflight. Unlike `oracle-eval`,
                // this never evaluates the submitted program or invokes
                // capabilities. It preserves canonical parser spans and
                // gives a conservative suggested edit for mismatched
                // parentheses.
                Some("oracle-check") => match &source {
                    None => error_response(
                        &id,
                        "invalid-form",
                        "op `oracle-check` requires a `source` field",
                        &contract_version,
                    ),
                    Some(src) => ok_response(
                        &id,
                        oracle_check(src, &contract_version).0,
                        &[],
                        &contract_version,
                    ),
                },
                Some("oracle-help") => match oracle_help(&mut session, topic.as_deref()) {
                    Ok(reference) => ok_response(&id, reference, &[], &contract_version),
                    Err(message) => {
                        error_response(&id, "invalid-form", &message, &contract_version)
                    }
                },
                Some("oracle-eval") => match &source {
                    None => error_response(
                        &id,
                        "invalid-form",
                        "op `oracle-eval` requires a `source` field",
                        &contract_version,
                    ),
                    Some(src) => {
                        let result = match parse(src) {
                            Ok(ast) => match eval_parsed_expressions(&ast, &mut session) {
                                Ok(result) => oracle_result_value(
                                    src,
                                    &contract_version,
                                    Value::Symbol("value".into()),
                                    Value::list([Value::Symbol("value".into()), result.value]),
                                    &result.output,
                                    "oracle-evaluation",
                                ),
                                Err(error) => oracle_result_value(
                                    src,
                                    &contract_version,
                                    Value::Symbol("error".into()),
                                    oracle_error_payload(src, &error),
                                    &[],
                                    "oracle-evaluation",
                                ),
                            },
                            Err(error) => oracle_result_value(
                                src,
                                &contract_version,
                                Value::Symbol("error".into()),
                                oracle_error_payload(src, &error),
                                &[],
                                "oracle-evaluation",
                            ),
                        };
                        ok_response(&id, result, &[], &contract_version)
                    }
                },
                Some(op_name @ ("eval" | "diagnose")) => match &source {
                    None => error_response(
                        &id,
                        "invalid-form",
                        &format!("op `{op_name}` requires a `source` field"),
                        &contract_version,
                    ),
                    Some(src) => match parse(src) {
                        Ok(ast) => match eval_parsed_expressions(&ast, &mut session) {
                            Ok(result) => {
                                ok_response(&id, result.value, &result.output, &contract_version)
                            }
                            Err(e) => error_response_classified(
                                &id,
                                error_kind_symbol(&e.kind),
                                e.kind.classification(),
                                &e.message,
                                &contract_version,
                            ),
                        },
                        Err(e) => error_response_classified(
                            &id,
                            error_kind_symbol(&e.kind),
                            e.kind.classification(),
                            &e.message,
                            &contract_version,
                        ),
                    },
                },
                Some(other) => error_response(
                    &id,
                    "invalid-form",
                    &format!("unknown op `{other}`"),
                    &contract_version,
                ),
                None => error_response(
                    &id,
                    "invalid-form",
                    "request is missing an `op` field",
                    &contract_version,
                ),
            };

            if writeln!(stream, "{response}").is_err() {
                break;
            }
        }
    }
    eprintln!("TCP REPL: {peer} disconnected");
}

/// One-shot machine client for the semantic TCP oracle. It forwards one
/// newline-delimited sexpr request from stdin and prints one response line.
/// This transport helper carries no coordination semantics of its own.
pub(crate) fn run_client(address: &str) {
    let mut stream = match TcpStream::connect(address) {
        Ok(stream) => stream,
        Err(e) => {
            eprintln!("sens: cannot connect to {address}: {e}");
            process::exit(1);
        }
    };
    let mut line = String::new();
    match std::io::stdin().lock().read_line(&mut line) {
        Ok(0) => {
            eprintln!("sens: --connect expects a request on stdin, none was found");
            process::exit(1);
        }
        Ok(_) => {
            let request = line.trim();
            if request.is_empty() {
                eprintln!("sens: --connect expects a non-empty request on stdin");
                process::exit(1);
            }
            if writeln!(stream, "{request}").is_err() {
                eprintln!("sens: write to {address} failed");
                process::exit(1);
            }
            let mut response = String::new();
            if BufReader::new(&stream).read_line(&mut response).is_ok() {
                print!("{response}");
            } else {
                eprintln!("sens: read from {address} failed");
                process::exit(1);
            }
        }
        Err(e) => {
            eprintln!("sens: cannot read request from stdin: {e}");
            process::exit(1);
        }
    }
}

#[cfg(test)]
mod oracle_result_tests {
    use super::*;

    fn contract() -> Value {
        Value::list([
            Value::Number(4.0, Exactness::Exact),
            Value::Number(0.0, Exactness::Exact),
        ])
    }

    #[test]
    fn oracle_result_is_versioned_and_provenance_bearing() {
        let result = oracle_result_value(
            "(+ 1 2)",
            &contract(),
            Value::Symbol("value".into()),
            Value::list([
                Value::Symbol("value".into()),
                Value::Number(3.0, Exactness::Exact),
            ]),
            &[],
            "oracle-evaluation",
        )
        .to_string();
        assert!(result.contains("(protocol oracle-result/1)"));
        assert!(result.contains("(contract-revision (4 0))"));
        assert!(result.contains("(source-digest \"sha256:"));
        assert!(result.contains("(outcome value)"));
        assert!(result.contains("(relation reference-implementation)"));
    }

    #[test]
    fn source_digest_is_stable_and_source_sensitive() {
        assert_eq!(source_digest("(+ 1 2)"), source_digest("(+ 1 2)"));
        assert_ne!(source_digest("(+ 1 2)"), source_digest("(+ 1 3)"));
    }

    #[test]
    fn unclosed_list_diagnostic_tells_agents_where_to_insert_one_paren() {
        let source = "(def answer\n  (+ 40 2)";
        let error = parse(source).unwrap_err();
        let diagnostic = oracle_error_payload(source, &error).to_string();
        assert!(diagnostic.contains("(code unclosed-list)"));
        assert!(diagnostic.contains("(location ((line 1) (column 1)))"));
        assert!(diagnostic.contains("(action insert)"));
        assert!(diagnostic.contains("(text \")\")"));
        assert!(diagnostic.contains(&format!("(offset {})", source.len())));
    }

    #[test]
    fn extra_closing_paren_diagnostic_tells_agents_exactly_what_to_delete() {
        let source = "(def answer 42)\n)";
        let error = parse(source).unwrap_err();
        let diagnostic = oracle_error_payload(source, &error).to_string();
        assert!(diagnostic.contains("(code unexpected-closing-parenthesis)"));
        assert!(diagnostic.contains("(location ((line 2) (column 1)))"));
        assert!(diagnostic.contains("(action delete)"));
        assert!(diagnostic.contains("(start 16)"));
        assert!(diagnostic.contains("(end 17)"));
    }
}
