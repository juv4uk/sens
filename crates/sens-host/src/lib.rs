//! sens-host — шар системних можливостей для SENS.
//!
//! Ядро SENS не встановлює можливостей доступу до операційної системи.
//! Цей крейт містить файлові, процесні та мережеві засоби й явно
//! реєструє їх через [`install`].
//! Довірені нативні сеанси за замовчуванням мають повний доступ; вбудовувач
//! може обмежити файлові й мережеві права окремого сеансу через `Environment`.

use sens::{
    eval_expr, exact_arity, register_capability, register_evaluated_capability, BinaryNumber,
    Environment, ErrorKind, Exactness, Expr, LanguageError, Span, Value,
};
use std::{
    cell::RefCell,
    path::{Path, PathBuf},
    rc::Rc,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT_TCP_HANDLE_TOKEN: AtomicU64 = AtomicU64::new(1);

fn allocate_tcp_handle_token(counter: &AtomicU64, span: Span) -> Result<u64, LanguageError> {
    let mut current = counter.load(Ordering::Relaxed);
    loop {
        let Some(next) = current.checked_add(1) else {
            return Err(LanguageError::new(
                ErrorKind::NumericOverflow,
                "TCP host-resource identity space exhausted",
                span,
            ));
        };
        match counter.compare_exchange_weak(current, next, Ordering::Relaxed, Ordering::Relaxed) {
            Ok(previous) => return Ok(previous),
            Err(observed) => current = observed,
        }
    }
}

fn next_tcp_handle_token(span: Span) -> Result<u64, LanguageError> {
    allocate_tcp_handle_token(&NEXT_TCP_HANDLE_TOKEN, span)
}

/// Represent one host I/O byte as its exact nonnegative D24+ mathematical value.
fn d24_byte_value(byte: u8) -> Value {
    let mut bits = vec![0; 16];
    bits.extend((0..8).rev().map(|shift| (byte >> shift) & 1));
    let number = BinaryNumber::from_numeric_domain_bits(24, &bits)
        .expect("an unsigned byte is representable as a nonnegative D24+ integer");
    Value::BinaryNumber(number)
}

fn tcp_connection_value(stream: std::net::TcpStream, span: Span) -> Result<Value, LanguageError> {
    Ok(Value::host_resource(
        "tcp-connection",
        next_tcp_handle_token(span)?,
        RefCell::new(stream),
    ))
}

fn tcp_listener_value(listener: std::net::TcpListener, span: Span) -> Result<Value, LanguageError> {
    Ok(Value::host_resource(
        "tcp-listener",
        next_tcp_handle_token(span)?,
        listener,
    ))
}

#[cfg(all(
    any(target_os = "linux", target_os = "windows"),
    target_arch = "x86_64"
))]
mod native_exec;
#[cfg(all(
    any(target_os = "linux", target_os = "windows"),
    target_arch = "x86_64"
))]
mod platform;
mod process_raw;
mod system_one_model;

/// Сире спостереження монотонного лічильника ОС, без часової семантики в Rust.
///
/// Зовнішня host-capability `clock-mono-raw` існує окремо від дослідницької
/// D10:0011110110: реєстрація механізму за назвою НЕ допускає прямий D10 виклик.
/// Арифметику різниці, одиниці і вимірювання визначають тільки функції SENS.
/// Дві послідовні відповіді мають один точний D96-носій, не f64/Rational.
fn observe_monotonic_nanoseconds(
    arguments: &[(Value, Span)],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if !arguments.is_empty() {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            "clock-mono-raw expects exactly zero arguments",
            span,
        ));
    }
    static START: std::sync::OnceLock<std::time::Instant> = std::sync::OnceLock::new();
    let nanoseconds = START
        .get_or_init(std::time::Instant::now)
        .elapsed()
        .as_nanos();
    const WIDTH: usize = 96;
    if nanoseconds >= (1u128 << WIDTH) {
        return Err(LanguageError::new(
            ErrorKind::NumericOverflow,
            "clock-mono-raw observed nanoseconds exceed D96",
            span,
        ));
    }
    let bits: Vec<u8> = (0..WIDTH)
        .rev()
        .map(|shift| ((nanoseconds >> shift) & 1) as u8)
        .collect();
    let exact = sens::BinaryNumber::from_numeric_domain_bits(WIDTH, &bits)
        .expect("the checked 96-bit monotonic observation is an exact D96 word");
    Ok(Value::BinaryNumber(exact))
}

/// `читати-енергію-у-мікроджоулях` — RAPL-лічильники через powercap sysfs.
///
/// Повертає ПАРУ точних D64-слів: (package, dram), у мікроджоулях.
/// Механізм німий: жодної семантики тут — перетворення й нормування
/// живуть у lib/бенчмарк.lisp (мікроджоулі-у-джоулі, джоулів-на-тисячу-форм).
///
/// Якщо лічильника немає (не Intel, контейнер без MSR, немає прав) —
/// ЧЕСНА ВІДМОВА з поясненням, а не нуль: нуль зіпсував би вимір тихо.
#[cfg(not(target_arch = "wasm32"))]
fn read_energy_microjoules(
    arguments: &[(Value, Span)],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if !arguments.is_empty() {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            "читати-енергію-у-мікроджоулях expects exactly zero arguments",
            span,
        ));
    }
    const WIDTH: usize = 96;
    fn read_one(path: &str, label: &str, span: Span) -> Result<Value, LanguageError> {
        let text = std::fs::read_to_string(path).map_err(|error| {
            LanguageError::new(
                ErrorKind::InvalidForm,
                format!(
                    "читати-енергію-у-мікроджоулях: {label} counter unavailable at {path}: {error} · лічильник недоступний · Zähler nicht verfügbar"
                ),
                span,
            )
        })?;
        let value: u64 = text.trim().parse().map_err(|error| {
            LanguageError::new(
                ErrorKind::InvalidForm,
                format!("читати-енергію-у-мікроджоулях: {label} counter is not an integer: {error}"),
                span,
            )
        })?;
        // Лічильник RAPL — u64, але числовий домен починається з D12 і
            // йде кроками 12: D24, D48, D96. D64 у драбині НЕМАЄ, тож
            // 64-бітне значення розширюємо до D96 (як clock-mono-raw).
        let bits: Vec<u8> = (0..WIDTH)
            .rev()
            .map(|shift| {
                if shift >= 64 { 0 } else { ((value >> shift) & 1) as u8 }
            })
            .collect();
        let exact = sens::BinaryNumber::from_numeric_domain_bits(WIDTH, &bits)
            .expect("the checked 64-bit RAPL counter is an exact D64 word");
        Ok(Value::BinaryNumber(exact))
    }
    let package = read_one("/sys/class/powercap/intel-rapl:0/energy_uj", "package", span)?;
    let dram = read_one("/sys/class/powercap/intel-rapl:0:0/energy_uj", "dram", span)?;
    Ok(Value::list(vec![package, dram]))
}

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
    std::fs::canonicalize(parent)
        .ok()
        .map(|p| p.join(file_name))
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
    exact_arity("записати-байти-файла", arguments, 2, span)?;
    let path_value = eval_expr(&arguments[0], environment)?;
    let Value::String(ref path) = path_value else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "записати-байти-файла expects a string path · записати-байти-файла ochikuie riadok-shliakh · записати-байти-файла erwartet einen String-Pfad",
            span,
        ));
    };
    let bytes_value = eval_expr(&arguments[1], environment)?;
    let bytes = expect_byte_list(&bytes_value, arguments[1].span)?;
    ensure_fs_write_allowed(environment, "записати-байти-файла", path, span)?;
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
            "читати-сирий-текст-файла expects a string path · читати-сирий-текст-файла ochikuie riadok-shliakh · читати-сирий-текст-файла erwartet einen String-Pfad",
            span,
        ));
    };
    ensure_fs_read_allowed(environment, "читати-сирий-текст-файла", path, span)?;
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
            Value::Pair(node) => {
                // SENS arithmetic now returns exactly qualified D24+ numbers.
                // The FS host transports raw bytes only: decode 0..255 at
                // this I/O boundary, never turn decimal host values into the
                // normative numeric identity and never accept negative bits.
                let byte = match &node.head {
                    Value::Number(number, _)
                        if number.is_finite()
                            && number.fract() == 0.0
                            && (0.0..=255.0).contains(number) =>
                    {
                        *number as u8
                    }
                    Value::BinaryNumber(number) if number.numeric_domain_width().is_some() => {
                        let bits = number.as_bits();
                        if bits.len() > 8 && bits[..bits.len() - 8].iter().any(|&bit| bit != 0) {
                            return Err(LanguageError::new(
                                ErrorKind::Type,
                                "записати-байти-файла expects each element to be an integer between 0 and 255 · записати-байти-файла ochikuie, shchob kozhen element buv tsilym chyslom vid 0 do 255 · записати-байти-файла erwartet, dass jedes Element eine Ganzzahl zwischen 0 und 255 ist",
                                span,
                            ));
                        }
                        bits.iter().fold(0u8, |byte, &bit| (byte << 1) | bit)
                    }
                    Value::Number(_, _) | Value::BinaryNumber(_) => {
                        return Err(LanguageError::new(
                            ErrorKind::Type,
                            "записати-байти-файла expects each element to be an integer between 0 and 255 · записати-байти-файла ochikuie, shchob kozhen element buv tsilym chyslom vid 0 do 255 · записати-байти-файла erwartet, dass jedes Element eine Ganzzahl zwischen 0 und 255 ist",
                            span,
                        ))
                    }
                    _ => {
                        return Err(LanguageError::new(
                            ErrorKind::Type,
                            "записати-байти-файла expects a list of integers 0-255 · записати-байти-файла ochikuie spysok tsilykh chysel 0-255 · записати-байти-файла erwartet eine Liste von Ganzzahlen 0-255",
                            span,
                        ))
                    }
                };
                bytes.push(byte);
                current = &node.tail;
            }
            _ => {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "записати-байти-файла expects a proper list of integers 0-255 · записати-байти-файла ochikuie pravylnyi spysok tsilykh chysel 0-255 · записати-байти-файла erwartet eine echte Liste von Ganzzahlen 0-255",
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
            Value::Pair(node) => {
                // Language-owned UTF-8 encoding produces exact D24+ values;
                // retain legacy host numbers only as a compatibility input.
                let byte = match &node.head {
                    Value::Number(number, _)
                        if number.fract() == 0.0 && (0.0..=255.0).contains(number) =>
                    {
                        Some(*number as u8)
                    }
                    Value::BinaryNumber(number)
                        if number.numeric_domain_width() == Some(24) =>
                    {
                        number.exact_numeric_domain_bits().and_then(|bits| {
                            if bits[0] != 0 {
                                return None;
                            }
                            let value = bits.iter().fold(0u32, |value, bit| {
                                (value << 1) | u32::from(*bit)
                            });
                            u8::try_from(value).ok()
                        })
                    }
                    _ => None,
                };
                let Some(byte) = byte else {
                    return Err(LanguageError::new(
                        ErrorKind::Type,
                        "tcp-write-raw expects each element to be an integer byte between 0 and 255, as a legacy host number or exact D24+ value · tcp-write-raw ochikuie tsilyi baity 0-255 yak host-chyslo abo tochne znachennia D24+",
                        span,
                    ));
                };
                bytes.push(byte);
                current = &node.tail;
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
            format!("записати-байти-файла: failed to write file {path}: {error}"),
            span,
        )
    })
}

#[cfg(target_arch = "wasm32")]
fn write_file_bytes(_path: &str, _bytes: &[u8], span: Span) -> Result<(), LanguageError> {
    Err(LanguageError::new(
        ErrorKind::InvalidForm,
        "записати-байти-файла: file system access is not available in this build",
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
    tcp_connection_value(stream, span)
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
    tcp_listener_value(listener, span)
}

fn evaluate_tcp_accept(
    arguments: &[(Value, Span)],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    let (listener_value, listener_span) = &arguments[0];
    let Some(listener) = listener_value.as_host_resource::<std::net::TcpListener>("tcp-listener")
    else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "tcp-accept expects a TCP listener · tcp-accept ochikuie TCP-listener · tcp-accept erwartet einen TCP-Listener",
            *listener_span,
        ));
    };
    let stream = tcp_accept(listener, span)?;
    tcp_connection_value(stream, span)
}

fn evaluate_tcp_read_raw(
    arguments: &[(Value, Span)],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    let (connection_value, connection_span) = &arguments[0];
    let Some(connection) =
        connection_value.as_host_resource::<RefCell<std::net::TcpStream>>("tcp-connection")
    else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "tcp-read-raw expects a TCP connection · tcp-read-raw ochikuie TCP-ziednannia · tcp-read-raw erwartet eine TCP-Verbindung",
            *connection_span,
        ));
    };
    let bytes = tcp_read_raw(connection, span)?;
    // The Lisp UTF-8 decoder performs D24+ arithmetic. Qualify each physical
    // byte explicitly as its nonnegative mathematical value at this boundary.
    Ok(Value::list(bytes.into_iter().map(d24_byte_value)))
}

fn evaluate_tcp_write_raw(
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_arity("tcp-write-raw", arguments, 2, span)?;
    let connection_value = eval_expr(&arguments[0], environment)?;
    let Some(connection) =
        connection_value.as_host_resource::<RefCell<std::net::TcpStream>>("tcp-connection")
    else {
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
    let Some(connection) = value.as_host_resource::<RefCell<std::net::TcpStream>>("tcp-connection")
    else {
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
    let port = match &value {
        Value::Number(port, _)
            if port.is_finite()
                && port.fract() == 0.0
                && (0.0..=u16::MAX as f64).contains(port) =>
        {
            Some(*port as u16)
        }
        Value::BinaryNumber(number) if number.numeric_domain_width().is_some() => {
            number.exact_numeric_domain_bits().and_then(|bits| {
                if bits[0] != 0 {
                    return None;
                }
                let mut port = 0u32;
                for bit in bits {
                    port = port.checked_mul(2)?.checked_add(u32::from(bit))?;
                    if port > u16::MAX as u32 {
                        return None;
                    }
                }
                Some(port as u16)
            })
        }
        _ => None,
    };
    port.ok_or_else(|| {
        LanguageError::new(
            ErrorKind::Type,
            "port must be an exact nonnegative D24+ integer or legacy host integer between 0 and 65535",
            expr.span,
        )
    })
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
    listener
        .accept()
        .map(|(stream, _)| stream)
        .map_err(|error| {
            LanguageError::new(
                ErrorKind::InvalidForm,
                format!("tcp-accept: failed to accept a connection: {error}"),
                span,
            )
        })
}

fn tcp_read_raw(
    connection: &RefCell<std::net::TcpStream>,
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
    connection: &RefCell<std::net::TcpStream>,
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

fn tcp_close(connection: &RefCell<std::net::TcpStream>, span: Span) -> Result<(), LanguageError> {
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
    register_evaluated_capability("clock-mono-raw", 0, observe_monotonic_nanoseconds);
    register_evaluated_capability("годинник-моно-сирий", 0, observe_monotonic_nanoseconds);
    #[cfg(not(target_arch = "wasm32"))]
    register_evaluated_capability("читати-енергію-у-мікроджоулях", 0, read_energy_microjoules);
    register_evaluated_capability("read-dir", 1, evaluate_read_dir);
    register_evaluated_capability("читати-каталог", 1, evaluate_read_dir);
    register_evaluated_capability("read-file-bytes", 1, evaluate_read_file_bytes);
    register_evaluated_capability("читати-байти-файла", 1, evaluate_read_file_bytes);
    register_evaluated_capability("читати-сирий-текст-файла", 1, evaluate_read_file_utf8_raw);
    register_capability("записати-байти-файла", evaluate_write_file_bytes);
    register_capability("process-run-raw", process_raw::evaluate_process_run_raw);
    register_capability("запустити-процес-сирий", process_raw::evaluate_process_run_raw);
    // Та сама сира можливість процесу для українського виконуваного Lisp.
    register_capability(
        "процес-запустити-сирий",
        process_raw::evaluate_process_run_raw,
    );
    register_evaluated_capability("load", 1, evaluate_load);
    // Українська виклична назва того самого механізму читання та обчислення файла.
    register_evaluated_capability("завантажити-файл", 1, evaluate_load);
    register_capability("tcp-connect", evaluate_tcp_connect);
    register_capability("приєднати-мережу", evaluate_tcp_connect);
    register_capability("tcp-listen-raw", evaluate_tcp_listen_raw);
    register_capability("слухати-мережу-сирий", evaluate_tcp_listen_raw);
    register_capability(
        "протокол-передавання-сире-слухання",
        evaluate_tcp_listen_raw,
    );
    register_evaluated_capability("tcp-accept", 1, evaluate_tcp_accept);
    register_evaluated_capability("прийняти-мережу", 1, evaluate_tcp_accept);
    register_evaluated_capability("tcp-read-raw", 1, evaluate_tcp_read_raw);
    register_evaluated_capability("читати-мережу-сирий", 1, evaluate_tcp_read_raw);
    register_evaluated_capability(
        "протокол-передавання-сире-читання",
        1,
        evaluate_tcp_read_raw,
    );
    register_capability("tcp-write-raw", evaluate_tcp_write_raw);
    register_capability("протокол-передавання-сирий-запис", evaluate_tcp_write_raw);
    register_evaluated_capability("tcp-close", 1, evaluate_tcp_close);
    register_evaluated_capability("закрити-мережу", 1, evaluate_tcp_close);
    // Механізм повертає лише розподіл і походження; рішення належить SENS.
    register_evaluated_capability(
        "модельний-розподіл-вибору-сире",
        5,
        system_one_model::evaluate_choice_distribution,
    );
    #[cfg(all(
        any(target_os = "linux", target_os = "windows"),
        target_arch = "x86_64"
    ))]
    register_capability(
        "native-call-u64-raw",
        native_exec::evaluate_native_call_u64_raw,
    );
}

#[cfg(test)]
mod install_tests {
    use sens::{Environment, ErrorKind, Exactness, Span, Value};
    use std::sync::atomic::AtomicU64;

    #[test]
    fn tcp_handle_token_allocator_is_atomic_and_rejects_overflow() {
        let span = Span { start: 4, end: 9 };
        let counter = AtomicU64::new(1);
        assert_eq!(super::allocate_tcp_handle_token(&counter, span).unwrap(), 1);
        assert_eq!(super::allocate_tcp_handle_token(&counter, span).unwrap(), 2);
        assert_eq!(counter.load(std::sync::atomic::Ordering::Relaxed), 3);

        let exhausted = AtomicU64::new(u64::MAX);
        let error = super::allocate_tcp_handle_token(&exhausted, span)
            .expect_err("the handle identity counter must not wrap");
        assert_eq!(error.kind, ErrorKind::NumericOverflow);
        assert_eq!(error.span, span);
        assert_eq!(
            exhausted.load(std::sync::atomic::Ordering::Relaxed),
            u64::MAX
        );
    }

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
    fn fs_raw_byte_bridge_accepts_only_exact_bounded_d24_numbers() {
        fn d24(value: u32) -> Value {
            let bits = (0..24)
                .rev()
                .map(|shift| ((value >> shift) & 1) as u8)
                .collect::<Vec<_>>();
            Value::BinaryNumber(
                sens::BinaryNumber::from_numeric_domain_bits(24, &bits).expect("exact D24 number"),
            )
        }

        let span = Span::default();
        let valid = Value::list([d24(0), d24(128), d24(255)]);
        assert_eq!(
            super::expect_byte_list(&valid, span).expect("physical 0..255 byte transport"),
            [0, 128, 255],
        );
        for invalid in [
            Value::list([d24(256)]),
            Value::list([d24((1 << 24) - 1)]),
            Value::list([Value::String("255".into())]),
        ] {
            let err = super::expect_byte_list(&invalid, span)
                .expect_err("FS bridge must reject non-byte numeric identities");
            assert_eq!(err.kind, ErrorKind::Type);
        }
    }

    #[test]
    fn mono_ns_is_an_exact_non_decreasing_d96_host_observation() {
        let env = Environment::root();
        let span = Span::default();
        let first = super::observe_monotonic_nanoseconds(&[], &env, span)
            .expect("installed raw monotonic observation");
        let second = super::observe_monotonic_nanoseconds(&[], &env, span)
            .expect("second monotonic observation");
        let (Value::BinaryNumber(a), Value::BinaryNumber(b)) = (&first, &second) else {
            panic!("mono-ns must return D96, never host Rational or float");
        };
        assert_eq!(a.numeric_domain_width(), Some(96));
        assert_eq!(b.numeric_domain_width(), Some(96));
        assert!(a <= b, "monotonic observations must not move backward");

        let error = super::observe_monotonic_nanoseconds(&[(Value::Nil, span)], &env, span)
            .expect_err("wrong arity must fail closed");
        assert_eq!(error.kind, ErrorKind::Arity);
    }

    #[test]
    fn install_registers_every_host_form() {
        super::install();
        let installed = sens::installed_capabilities();
        for name in [
            "clock-mono-raw",
            "read-dir",
            "read-file-bytes",
            "читати-сирий-текст-файла",
            "записати-байти-файла",
            "process-run-raw",
            "процес-запустити-сирий",
            "load",
            "завантажити-файл",
            "tcp-connect",
            "tcp-listen-raw",
            "протокол-передавання-сире-слухання",
            "tcp-accept",
            "tcp-read-raw",
            "протокол-передавання-сире-читання",
            "tcp-write-raw",
            "протокол-передавання-сирий-запис",
            "tcp-close",
        ] {
            assert!(installed.iter().any(|n| n == name), "{name} not registered");
        }
    }

    #[test]
    fn ukrainian_tcp_raw_names_preserve_fail_closed_arity() {
        super::install();
        for form in [
            "(протокол-передавання-сире-слухання \"0.0.0.0\")",
            "(протокол-передавання-сире-читання)",
            "(протокол-передавання-сирий-запис)",
        ] {
            let mut session = sens::Session::default();
            let error = sens::eval_program(form, &mut session)
                .expect_err("передані замало аргументів мають відхилятися до роботи з сокетом");
            assert_eq!(error.kind, ErrorKind::Arity, "{form}");
        }
    }

    #[test]
    fn ukrainian_process_raw_name_preserves_fail_closed_arity() {
        super::install();
        for form in ["(process-run-raw)", "(процес-запустити-сирий)"] {
            let mut session = sens::Session::default();
            let error = sens::eval_program(form, &mut session)
                .expect_err("недостатня кількість аргументів не має запускати зовнішній процес");
            assert_eq!(error.kind, ErrorKind::Arity, "{form}");
        }
    }

    #[test]
    fn write_file_bytes_rejects_bad_path_before_evaluating_bytes() {
        super::install();
        let mut session = sens::Session::default();
        let error = sens::eval_program(
            "(записати-байти-файла 42 definitely-missing-order-probe)",
            &mut session,
        )
        .expect_err("argument 0 type failure must short-circuit argument 1 evaluation");

        assert_eq!(error.kind, ErrorKind::Type);
    }
}
