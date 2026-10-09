//! sens-host - the OS capability layer for sens.
//!
//! The core installs no OS capabilities. This crate owns filesystem, process,
//! and TCP mechanisms and registers them explicitly through [`install`].
//! Trusted native sessions remain unrestricted by default; embeddings may opt
//! into per-session filesystem/TCP scopes carried by `Environment`.

use sens::{
    eval_expr, exact_arity, register_capability, register_evaluated_capability, Environment,
    ErrorKind, Exactness, Expr, LanguageError, Span, Value,
};
use std::{path::{Path, PathBuf}, rc::Rc};

#[cfg(all(any(target_os = "linux", target_os = "windows"), target_arch = "x86_64"))]
mod native_exec;
#[cfg(all(any(target_os = "linux", target_os = "windows"), target_arch = "x86_64"))]
mod platform;
mod process_raw;

fn denied(operation: &str, detail: impl std::fmt::Display, span: Span) -> LanguageError {
    LanguageError::new(
        ErrorKind::InvalidForm,
        format!(
            "{operation}: {detail} is outside this session's capability scope · {operation}: {detail} poza mezhamy capability tsiiei sesii · {operation}: {detail} liegt außerhalb des Capability-Bereichs dieser Sitzung"
        ),
        span,
    )
}

#[cfg(not(target_arch = "wasm32"))]
fn canonical_write_target(path: &Path) -> Option<PathBuf> {
    if path.exists() {
        return std::fs::canonicalize(path).ok();
    }
    let parent = path
        .parent()
        .filter(|parent| !parent.as_os_str().is_empty())
        .unwrap_or_else(|| Path::new("."));
    let file_name = path.file_name()?;
    std::fs::canonicalize(parent).ok().map(|p| p.join(file_name))
}

#[cfg(not(target_arch = "wasm32"))]
fn path_under_any_root(path: &str, roots: &[PathBuf], write: bool) -> bool {
    let path = Path::new(path);
    let target = if write {
        canonical_write_target(path)
    } else {
        std::fs::canonicalize(path).ok()
    };
    let Some(target) = target else {
        return false;
    };
    roots.iter().any(|root| {
        std::fs::canonicalize(root)
            .map(|canonical_root| target.starts_with(canonical_root))
            .unwrap_or(false)
    })
}

#[cfg(target_arch = "wasm32")]
fn path_under_any_root(_path: &str, _roots: &[PathBuf], _write: bool) -> bool {
    false
}

fn ensure_fs_read_allowed(
    environment: &Environment,
    operation: &str,
    path: &str,
    span: Span,
) -> Result<(), LanguageError> {
    if let Some(roots) = environment.fs_read_roots() {
        if !path_under_any_root(path, &roots, false) {
            return Err(denied(operation, path, span));
        }
    }
    Ok(())
}

fn ensure_fs_write_allowed(
    environment: &Environment,
    operation: &str,
    path: &str,
    span: Span,
) -> Result<(), LanguageError> {
    if let Some(roots) = environment.fs_write_roots() {
        if !path_under_any_root(path, &roots, true) {
            return Err(denied(operation, path, span));
        }
    }
    Ok(())
}

fn evaluate_read_dir(
    arguments: &[(Value, Span)],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    let (evaluated, _argument_span) = &arguments[0];
    let Value::String(path) = evaluated else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "read-dir expects a string path · read-dir ochikuie riadok-shliakh · read-dir erwartet einen String-Pfad",
            span,
        ));
    };
    ensure_fs_read_allowed(environment, "read-dir", path, span)?;
    let entries = read_dir(path, span)?;
    Ok(Value::list(
        entries
            .into_iter()
            .map(|name| Value::String(Rc::from(name))),
    ))
}

fn evaluate_write_file_bytes(
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_arity("write-file-bytes", arguments, 2, span)?;
    let path_value = eval_expr(&arguments[0], environment)?;
    let Value::String(ref path) = path_value else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "write-file-bytes expects a string path · write-file-bytes ochikuie riadok-shliakh · write-file-bytes erwartet einen String-Pfad",
            span,
        ));
    };
    let bytes_value = eval_expr(&arguments[1], environment)?;
    let bytes = expect_byte_list(&bytes_value, arguments[1].span)?;
    ensure_fs_write_allowed(environment, "write-file-bytes", path, span)?;
    write_file_bytes(path, &bytes, span)?;
    Ok(bytes_value)
}

fn evaluate_read_file_bytes(
    arguments: &[(Value, Span)],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    let (evaluated, _argument_span) = &arguments[0];
    let Value::String(path) = evaluated else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "read-file-bytes expects a string path · read-file-bytes ochikuie riadok-shliakh · read-file-bytes erwartet einen String-Pfad",
            span,
        ));
    };
    ensure_fs_read_allowed(environment, "read-file-bytes", path, span)?;
    let bytes = read_file_bytes(path, span)?;
    Ok(Value::list(
        bytes
            .into_iter()
            .map(|byte| Value::Number(byte as f64, Exactness::Exact)),
    ))
}

/// Raw host mechanism only: reads a file and validates it as UTF-8 in one
/// native pass, using Rust's own `str::from_utf8` (the same complete
/// validation `lib/utf8.lisp` hand-implements byte-by-byte in Lisp). This
/// mechanism decides nothing about language meaning — it returns exactly the
/// two-tag domain `lib/utf8.lisp::utf8-decode-string` already defines
/// (`(decoded text)` / `(rejected invalid-utf8)`), so Lisp keeps owning that
/// rejection domain and every caller of `read-file` sees an unchanged
/// contract. Introduced under sens#1228: high-load byte/text processing
/// belongs in a Rust mechanism, not in a per-byte recursive Lisp walk.
fn evaluate_read_file_utf8_raw(
    arguments: &[(Value, Span)],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    let (evaluated, _argument_span) = &arguments[0];
    let Value::String(path) = evaluated else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "read-file-utf8-raw expects a string path · read-file-utf8-raw ochikuie riadok-shliakh · read-file-utf8-raw erwartet einen String-Pfad",
            span,
        ));
    };
    ensure_fs_read_allowed(environment, "read-file-utf8-raw", path, span)?;
    let bytes = read_file_bytes(path, span)?;
    match std::str::from_utf8(&bytes) {
        Ok(text) => Ok(Value::list([
            Value::Symbol(Rc::from("decoded")),
            Value::String(Rc::from(text)),
        ])),
        Err(_) => Ok(Value::list([
            Value::Symbol(Rc::from("rejected")),
            Value::Symbol(Rc::from("invalid-utf8")),
        ])),
    }
}

fn expect_byte_list(value: &Value, span: Span) -> Result<Vec<u8>, LanguageError> {
    let mut bytes = Vec::new();
    let mut current = value;
    loop {
        match current {
            Value::Nil => return Ok(bytes),
            Value::Pair(head, tail) => {
                let Value::Number(number, _) = **head else {
                    return Err(LanguageError::new(
                        ErrorKind::Type,
                        "write-file-bytes expects a list of integers 0-255 · write-file-bytes ochikuie spysok tsilykh chysel 0-255 · write-file-bytes erwartet eine Liste von Ganzzahlen 0-255",
                        span,
                    ));
                };
                if number.fract() != 0.0 || !(0.0..=255.0).contains(&number) {
                    return Err(LanguageError::new(
                        ErrorKind::Type,
                        "write-file-bytes expects each element to be an integer between 0 and 255 · write-file-bytes ochikuie, shchob kozhen element buv tsilym chyslom vid 0 do 255 · write-file-bytes erwartet, dass jedes Element eine Ganzzahl zwischen 0 und 255 ist",
                        span,
                    ));
                }
                bytes.push(number as u8);
                current = tail;
            }
            _ => {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "write-file-bytes expects a proper list of integers 0-255 · write-file-bytes ochikuie pravylnyi spysok tsilykh chysel 0-255 · write-file-bytes erwartet eine echte Liste von Ganzzahlen 0-255",
                    span,
                ))
            }
        }
    }
}

fn expect_tcp_byte_list(value: &Value, span: Span) -> Result<Vec<u8>, LanguageError> {
    let mut bytes = Vec::new();
    let mut current = value;
    loop {
        match current {
            Value::Nil => return Ok(bytes),
            Value::Pair(head, tail) => {
                let Value::Number(number, _) = **head else {
                    return Err(LanguageError::new(
                        ErrorKind::Type,
                        "tcp-write-raw expects a list of integers 0-255 · tcp-write-raw ochikuie spysok tsilykh chysel 0-255 · tcp-write-raw erwartet eine Liste von Ganzzahlen 0-255",
                        span,
                    ));
                };
                if number.fract() != 0.0 || !(0.0..=255.0).contains(&number) {
                    return Err(LanguageError::new(
                        ErrorKind::Type,
                        "tcp-write-raw expects each element to be an integer between 0 and 255 · tcp-write-raw ochikuie, shchob kozhen element buv tsilym chyslom vid 0 do 255 · tcp-write-raw erwartet, dass jedes Element eine Ganzzahl zwischen 0 und 255 ist",
                        span,
                    ));
                }
                bytes.push(number as u8);
                current = tail;
            }
            _ => {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "tcp-write-raw expects a proper list of integers 0-255 · tcp-write-raw ochikuie pravylnyi spysok tsilykh chysel 0-255 · tcp-write-raw erwartet eine echte Liste von Ganzzahlen 0-255",
                    span,
                ))
            }
        }
    }
}

#[cfg(not(target_arch = "wasm32"))]
fn read_dir(path: &str, span: Span) -> Result<Vec<String>, LanguageError> {
    let reader = std::fs::read_dir(path).map_err(|error| {
        LanguageError::new(
            ErrorKind::InvalidForm,
            format!("read-dir: failed to read directory {path}: {error}"),
            span,
        )
    })?;
    let mut entries = Vec::new();
    for entry in reader {
        match entry {
            Ok(entry) => entries.push(entry.file_name().to_string_lossy().into_owned()),
            Err(error) => {
                return Err(LanguageError::new(
                    ErrorKind::InvalidForm,
                    format!("read-dir: failed to read an entry in {path}: {error}"),
                    span,
                ))
            }
        }
    }
    Ok(entries)
}

#[cfg(target_arch = "wasm32")]
fn read_dir(_path: &str, span: Span) -> Result<Vec<String>, LanguageError> {
    Err(LanguageError::new(
        ErrorKind::InvalidForm,
        "read-dir: file system access is not available in this build",
        span,
    ))
}

#[cfg(not(target_arch = "wasm32"))]
fn read_file_bytes(path: &str, span: Span) -> Result<Vec<u8>, LanguageError> {
    std::fs::read(path).map_err(|error| {
        LanguageError::new(
            ErrorKind::InvalidForm,
            format!("read-file-bytes: failed to read file {path}: {error}"),
            span,
        )
    })
}

#[cfg(target_arch = "wasm32")]
fn read_file_bytes(_path: &str, span: Span) -> Result<Vec<u8>, LanguageError> {
    Err(LanguageError::new(
        ErrorKind::InvalidForm,
        "read-file-bytes: file system access is not available in this build",
        span,
    ))
}

#[cfg(not(target_arch = "wasm32"))]
fn write_file_bytes(path: &str, bytes: &[u8], span: Span) -> Result<(), LanguageError> {
    std::fs::write(path, bytes).map_err(|error| {
        LanguageError::new(
            ErrorKind::InvalidForm,
            format!("write-file-bytes: failed to write file {path}: {error}"),
            span,
        )
    })
}

#[cfg(target_arch = "wasm32")]
fn write_file_bytes(_path: &str, _bytes: &[u8], span: Span) -> Result<(), LanguageError> {
    Err(LanguageError::new(
        ErrorKind::InvalidForm,
        "write-file-bytes: file system access is not available in this build",
        span,
    ))
}

fn evaluate_tcp_connect(
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_arity("tcp-connect", arguments, 2, span)?;
    let host_value = eval_expr(&arguments[0], environment)?;
    let Value::String(ref host) = host_value else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "tcp-connect expects a string host · tcp-connect ochikuie riadok-khost · tcp-connect erwartet einen String-Host",
            arguments[0].span,
        ));
    };
    let port = expect_port(&arguments[1], environment)?;
    if !environment.is_tcp_connect_allowed(host, port) {
        return Err(denied("tcp-connect", format!("{host}:{port}"), span));
    }
    let stream = tcp_connect(host, port, span)?;
    Ok(Value::TcpConnection(Rc::new(std::cell::RefCell::new(stream))))
}

fn evaluate_tcp_listen_raw(
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_arity("tcp-listen-raw", arguments, 2, span)?;
    let address_value = eval_expr(&arguments[0], environment)?;
    let Value::String(ref address) = address_value else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "tcp-listen-raw expects a string bind address · tcp-listen-raw ochikuie riadok-adresu pryviazky · tcp-listen-raw erwartet eine String-Bind-Adresse",
            arguments[0].span,
        ));
    };
    let port = expect_port(&arguments[1], environment)?;
    if !environment.is_tcp_listen_allowed(address, port) {
        return Err(denied("tcp-listen-raw", format!("{address}:{port}"), span));
    }
    let listener = tcp_listen_raw(address, port, span)?;
    Ok(Value::TcpListener(Rc::new(listener)))
}

fn evaluate_tcp_accept(
    arguments: &[(Value, Span)],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    let (listener_value, listener_span) = &arguments[0];
    let Value::TcpListener(listener) = listener_value else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "tcp-accept expects a TCP listener · tcp-accept ochikuie TCP-listener · tcp-accept erwartet einen TCP-Listener",
            *listener_span,
        ));
    };
    let stream = tcp_accept(listener, span)?;
    Ok(Value::TcpConnection(Rc::new(std::cell::RefCell::new(stream))))
}

fn evaluate_tcp_read_raw(
    arguments: &[(Value, Span)],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    let (connection_value, connection_span) = &arguments[0];
    let Value::TcpConnection(connection) = connection_value else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "tcp-read-raw expects a TCP connection · tcp-read-raw ochikuie TCP-ziednannia · tcp-read-raw erwartet eine TCP-Verbindung",
            *connection_span,
        ));
    };
    let bytes = tcp_read_raw(connection, span)?;
    Ok(Value::list(
        bytes
            .into_iter()
            .map(|byte| Value::Number(byte as f64, Exactness::Exact)),
    ))
}

fn evaluate_tcp_write_raw(
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_arity("tcp-write-raw", arguments, 2, span)?;
    let connection_value = eval_expr(&arguments[0], environment)?;
    let Value::TcpConnection(ref connection) = connection_value else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "tcp-write-raw expects a TCP connection · tcp-write-raw ochikuie TCP-ziednannia · tcp-write-raw erwartet eine TCP-Verbindung",
            arguments[0].span,
        ));
    };
    let bytes_value = eval_expr(&arguments[1], environment)?;
    let bytes = expect_tcp_byte_list(&bytes_value, arguments[1].span)?;
    tcp_write_raw(connection, &bytes, span)?;
    Ok(bytes_value)
}

fn evaluate_tcp_close(
    arguments: &[(Value, Span)],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if arguments.len() != 1 {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            format!(
                "tcp-close: expected / ochikuvalosia / erwartet 1; received / otrymano / erhalten {}",
                arguments.len()
            ),
            span,
        ));
    }
    let (value, argument_span) = &arguments[0];
    let Value::TcpConnection(connection) = value else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "tcp-close expects a TCP connection · tcp-close ochikuie TCP-ziednannia · tcp-close erwartet eine TCP-Verbindung",
            *argument_span,
        ));
    };
    tcp_close(connection, span)?;
    Ok(Value::Bool(true))
}

fn expect_port(expr: &Expr, environment: &Environment) -> Result<u16, LanguageError> {
    let value = eval_expr(expr, environment)?;
    let Value::Number(port, _) = value else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "expected a port number · ochikuvavsia nomer portu · erwartete eine Portnummer",
            expr.span,
        ));
    };
    if port.fract() != 0.0 || port < 0.0 || port > u16::MAX as f64 {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "port must be an integer between 0 and 65535 · port maie buty tsilym chyslom vid 0 do 65535 · Port muss eine Ganzzahl zwischen 0 und 65535 sein",
            expr.span,
        ));
    }
    Ok(port as u16)
}

#[cfg(not(target_arch = "wasm32"))]
fn tcp_connect(host: &str, port: u16, span: Span) -> Result<std::net::TcpStream, LanguageError> {
    std::net::TcpStream::connect((host, port)).map_err(|error| {
        LanguageError::new(
            ErrorKind::InvalidForm,
            format!("tcp-connect: failed to connect to {host}:{port}: {error}"),
            span,
        )
    })
}

#[cfg(target_arch = "wasm32")]
fn tcp_connect(_host: &str, _port: u16, span: Span) -> Result<std::net::TcpStream, LanguageError> {
    Err(LanguageError::new(
        ErrorKind::InvalidForm,
        "tcp-connect: networking is not available in this build",
        span,
    ))
}

#[cfg(not(target_arch = "wasm32"))]
fn tcp_listen_raw(
    address: &str,
    port: u16,
    span: Span,
) -> Result<std::net::TcpListener, LanguageError> {
    std::net::TcpListener::bind((address, port)).map_err(|error| {
        LanguageError::new(
            ErrorKind::InvalidForm,
            format!("tcp-listen-raw: failed to bind {address}:{port}: {error}"),
            span,
        )
    })
}

#[cfg(target_arch = "wasm32")]
fn tcp_listen_raw(
    _address: &str,
    _port: u16,
    span: Span,
) -> Result<std::net::TcpListener, LanguageError> {
    Err(LanguageError::new(
        ErrorKind::InvalidForm,
        "tcp-listen-raw: networking is not available in this build",
        span,
    ))
}

fn tcp_accept(
    listener: &std::net::TcpListener,
    span: Span,
) -> Result<std::net::TcpStream, LanguageError> {
    listener.accept().map(|(stream, _)| stream).map_err(|error| {
        LanguageError::new(
            ErrorKind::InvalidForm,
            format!("tcp-accept: failed to accept a connection: {error}"),
            span,
        )
    })
}

fn tcp_read_raw(
    connection: &std::cell::RefCell<std::net::TcpStream>,
    span: Span,
) -> Result<Vec<u8>, LanguageError> {
    use std::io::Read;
    let mut buffer = [0u8; 65536];
    let read = connection.borrow_mut().read(&mut buffer).map_err(|error| {
        LanguageError::new(
            ErrorKind::InvalidForm,
            format!("tcp-read-raw: failed to read from the connection: {error}"),
            span,
        )
    })?;
    Ok(buffer[..read].to_vec())
}

fn tcp_write_raw(
    connection: &std::cell::RefCell<std::net::TcpStream>,
    bytes: &[u8],
    span: Span,
) -> Result<(), LanguageError> {
    use std::io::Write;
    connection.borrow_mut().write_all(bytes).map_err(|error| {
        LanguageError::new(
            ErrorKind::InvalidForm,
            format!("tcp-write-raw: failed to write to the connection: {error}"),
            span,
        )
    })
}

fn tcp_close(
    connection: &std::cell::RefCell<std::net::TcpStream>,
    span: Span,
) -> Result<(), LanguageError> {
    connection
        .borrow()
        .shutdown(std::net::Shutdown::Both)
        .map_err(|error| {
            LanguageError::new(
                ErrorKind::InvalidForm,
                format!("tcp-close: failed to close the connection: {error}"),
                span,
            )
        })
}

fn evaluate_load(
    arguments: &[(Value, Span)],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    let (evaluated, argument_span) = &arguments[0];
    let Value::String(path) = evaluated else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "load expects a string path / load ochikuie riadok-shliakh / load erwartet einen String-Pfad",
            *argument_span,
        ));
    };
    ensure_fs_read_allowed(environment, "load", path, span)?;
    let source = std::fs::read_to_string(path.as_ref()).map_err(|error| {
        LanguageError::new(
            ErrorKind::InvalidForm,
            format!("load: failed to read file {path}: {error}"),
            span,
        )
    })?;
    let expressions = sens::parse_mixed_exact_domain(&source).map_err(|mut error| {
        error.span = span;
        error
    })?;

    let mut session = sens::Session {
        environment: environment.clone(),
    };
    sens::eval_parsed_expressions(&expressions, &mut session).map(|result| result.value)
}

pub fn install() {
    register_evaluated_capability("read-dir", 1, evaluate_read_dir);
    register_evaluated_capability("read-file-bytes", 1, evaluate_read_file_bytes);
    register_evaluated_capability("read-file-utf8-raw", 1, evaluate_read_file_utf8_raw);
    register_capability("write-file-bytes", evaluate_write_file_bytes);
    register_capability("process-run-raw", process_raw::evaluate_process_run_raw);
    register_evaluated_capability("load", 1, evaluate_load);
    register_capability("tcp-connect", evaluate_tcp_connect);
    register_capability("tcp-listen-raw", evaluate_tcp_listen_raw);
    register_evaluated_capability("tcp-accept", 1, evaluate_tcp_accept);
    register_evaluated_capability("tcp-read-raw", 1, evaluate_tcp_read_raw);
    register_capability("tcp-write-raw", evaluate_tcp_write_raw);
    register_evaluated_capability("tcp-close", 1, evaluate_tcp_close);
    #[cfg(all(any(target_os = "linux", target_os = "windows"), target_arch = "x86_64"))]
    register_capability(
        "native-call-u64-raw",
        native_exec::evaluate_native_call_u64_raw,
    );
}

#[cfg(test)]
mod install_tests {
    use sens::{Environment, ErrorKind, Exactness, Span, Value};

    #[test]
    fn tcp_close_value_handler_keeps_argument_local_span() {
        let argument_span = Span { start: 13, end: 15 };
        let call_span = Span { start: 0, end: 19 };
        let error = super::evaluate_tcp_close(
            &[(Value::Number(42.0, Exactness::Exact), argument_span)],
            &Environment::root(),
            call_span,
        )
        .expect_err("non-connection must fail before touching host TCP");

        assert_eq!(error.kind, ErrorKind::Type);
        assert_eq!(error.span, argument_span);
    }

    #[test]
    fn install_registers_every_host_form() {
        super::install();
        let installed = sens::installed_capabilities();
        for name in [
            "read-dir",
            "read-file-bytes",
            "read-file-utf8-raw",
            "write-file-bytes",
            "process-run-raw",
            "load",
            "tcp-connect",
            "tcp-listen-raw",
            "tcp-accept",
            "tcp-read-raw",
            "tcp-write-raw",
            "tcp-close",
        ] {
            assert!(installed.iter().any(|n| n == name), "{name} not registered");
        }
    }

    #[test]
    fn write_file_bytes_rejects_bad_path_before_evaluating_bytes() {
        super::install();
        let mut session = sens::Session::default();
        let error = sens::eval_program(
            "(write-file-bytes 42 definitely-missing-order-probe)",
            &mut session,
        )
        .expect_err("argument 0 type failure must short-circuit argument 1 evaluation");

        assert_eq!(error.kind, ErrorKind::Type);
    }
}
