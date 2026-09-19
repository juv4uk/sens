//! Bootstrap registry for first-class `Value::Builtin` mechanisms. Contract
//! 2.1 introduced ordinary callable builtin values; Contract 6.0 narrows the
//! lookup rule for Canon 0+7 only. Non-Canon builtins remain ordinary lexical
//! bindings. Historical Canon bootstrap entries may still exist in the root
//! environment as implementation detail, but they are never semantic authority:
//! the immutable Canon resolver wins before `Environment` lookup for every
//! reserved Canon spelling.
//!
//! ADR-007 extends the meaning-first shape beyond Canon. Ordinary public
//! operations stay shadowable lexical values, but peer human spellings may be
//! installed as direct names of one `Value::Builtin` allocation instead of as
//! aliases through another human surface. ADD plus the stable arithmetic and
//! comparison operator peers are now proved runtime slices.
//!
//! Batch 1 (2026-08-23): car cdr cons eq atom + - * / < > =.
//! Batch 2 (2026-09-07): eager string/symbol, Unicode-codepoint, and digest
//! mechanisms are ordinary builtin values too; the evaluator does not need
//! head-name dispatch for them.
//! Batch 3 (2026-09-07): JSON decode is likewise an eager first-class builtin.
//! Batch 4 (2026-09-07): print/read/eval reflection mechanisms are ordinary
//! first-class builtins; only genuine syntax remains in evaluator dispatch.

use crate::environment::Environment;
use crate::eval::arithmetic::{
    arithmetic_on_values, comparison_on_values, division_on_values, exact_value,
};
use crate::eval::special_forms::json::json_parse_values;
use crate::eval::special_forms::{
    car_value, cdr_value, codepoint_to_string_values, cons_values, eq_values, eval_values,
    princ_values, print_values, read_all_values, read_values, sha256_hex_values,
    string_append_values, string_first_values, string_less_than_values, string_predicate_values,
    string_rest_values, string_to_codepoint_values, string_to_symbol_values,
    symbol_to_string_values, write_to_string_values,
};
use crate::{semantic_registry, Exactness, NumericBuffer, Rational, Span, Value};

type Native =
    std::rc::Rc<dyn Fn(&[Value], &Environment, Span) -> Result<Value, crate::LanguageError>>;

fn builtin(name: &'static str, func: Native) -> Value {
    Value::Builtin(std::rc::Rc::new(crate::value::Builtin { name, func }))
}

fn define_peer_builtin(
    environment: &Environment,
    diagnostic_name: &'static str,
    semantic_id: u8,
    func: Native,
) {
    let names = semantic_registry::stable_surfaces_for_semantic_id(semantic_id);
    assert!(
        !names.is_empty(),
        "peer builtin semantic identity must have at least one stable surface: {semantic_id}"
    );
    let value = builtin(diagnostic_name, func);
    for name in names {
        environment.define(name, value.clone());
    }
}

fn ntp_query_raw_value(
    host: &str,
    timeout_ms: u64,
    span: Span,
) -> Result<Value, crate::LanguageError> {
    use std::net::{ToSocketAddrs, UdpSocket};
    use std::time::Duration;
    let timeout_ms = timeout_ms.min(5_000);
    let address = (host, 123)
        .to_socket_addrs()
        .map_err(|_| {
            crate::LanguageError::new(
                crate::ErrorKind::Type,
                "ntp-query-raw cannot resolve host",
                span,
            )
        })?
        .next()
        .ok_or_else(|| {
            crate::LanguageError::new(
                crate::ErrorKind::Type,
                "ntp-query-raw host has no address",
                span,
            )
        })?;
    let socket = UdpSocket::bind("0.0.0.0:0")
        .and_then(|socket| {
            socket.set_read_timeout(Some(Duration::from_millis(timeout_ms)))?;
            socket.set_write_timeout(Some(Duration::from_millis(timeout_ms)))?;
            socket.connect(address)?;
            Ok(socket)
        })
        .map_err(|_| {
            crate::LanguageError::new(
                crate::ErrorKind::Type,
                "ntp-query-raw socket unavailable",
                span,
            )
        })?;
    let mut request = [0u8; 48];
    request[0] = 0x23;
    if socket.send(&request).is_err() {
        return Ok(Value::list([
            Value::Symbol(std::rc::Rc::from("rejected")),
            Value::Symbol(std::rc::Rc::from("send-failed")),
        ]));
    }
    let mut response = [0u8; 512];
    let size = match socket.recv(&mut response) {
        Ok(size) => size,
        Err(_) => {
            return Ok(Value::list([
                Value::Symbol(std::rc::Rc::from("rejected")),
                Value::Symbol(std::rc::Rc::from("receive-failed")),
            ]));
        }
    };
    if size < 48 {
        return Ok(Value::list([
            Value::Symbol(std::rc::Rc::from("rejected")),
            Value::Symbol(std::rc::Rc::from("short-response")),
        ]));
    }

    let mode = response[0] & 0x07;
    let stratum = response[1];
    let seconds = u32::from_be_bytes([response[40], response[41], response[42], response[43]]);
    let fraction = u32::from_be_bytes([response[44], response[45], response[46], response[47]]);

    Ok(Value::list([
        Value::Symbol(std::rc::Rc::from("ntp-fields")),
        Value::String(std::rc::Rc::from(host)),
        exact_value(Rational::integer(i64::from(mode))),
        exact_value(Rational::integer(i64::from(stratum))),
        exact_value(Rational::integer(i64::from(seconds))),
        exact_value(Rational::integer(i64::from(fraction))),
    ]))
}

pub(crate) fn install(environment: &Environment) {
    macro_rules! define {
        ($env:expr, $name:expr, $f:expr) => {
            $env.define($name, builtin($name, std::rc::Rc::new($f)));
        };
    }

    define!(environment, "car", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("car", args, 1, span)?;
        car_value(&args[0], span)
    });
    define!(environment, "cdr", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("cdr", args, 1, span)?;
        cdr_value(&args[0], span)
    });
    define!(environment, "cons", |args: &[Value], env: &Environment, span: Span| {
        exact_args("cons", args, 2, span)?;
        cons_values(args[0].clone(), args[1].clone(), env, span)
    });
    define!(environment, "eq", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("eq", args, 2, span)?;
        eq_values(args[0].clone(), args[1].clone(), span)
    });

    // abs/min-list/max-list/min/max migrated to lib/core.my (owner
    // directive 2026-09-11: "Lisp owns meaning, Rust owns only
    // irreducible mechanism" -- none of the five touch OS/host
    // capability). See lib/core.lisp's own comment at the definitions for
    // the real bugs (eq-on-non-atom, atom-vs-equal? sentinel confusion)
    // found and fixed during migration, and
    // docs/BUILTIN-IDENTITY-MIGRATION-MAP-2026-09-11.md for the wider
    // migration this is the first vertical slice of.

    define!(environment, "make-vector", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("make-vector", args, 1, span)?;
        match &args[0] {
            Value::Number(f, Exactness::Exact) if *f >= 0.0 && f.fract() == 0.0 =>
                Ok(Value::vector(std::iter::repeat_n(Value::Nil, *f as usize))),
            _ => Err(crate::LanguageError::new(crate::ErrorKind::Type,
                "make-vector expects an exact non-negative integer · make-vector ochikuie tochnyi nenulevyi tsilyi · make-vector erwartet eine exakte nichtnegative ganze Zahl", span)),
        }
    });
    define!(environment, "vector", |args: &[Value], _env: &Environment, _span: Span| {
        Ok(Value::vector(args.iter().cloned()))
    });

    define!(environment, "mono-ns", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("mono-ns", args, 0, span)?;
        static START: std::sync::OnceLock<std::time::Instant> = std::sync::OnceLock::new();
        let elapsed = START.get_or_init(std::time::Instant::now).elapsed();
        Ok(exact_value(Rational::integer(elapsed.as_nanos() as i64)))
    });
    define!(environment, "unix-time-now", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("unix-time-now", args, 0, span)?;
        let duration = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)
            .map_err(|_| crate::LanguageError::new(crate::ErrorKind::Type,
                "unix-time-now is unavailable before the Unix epoch", span))?;
        let seconds = i64::try_from(duration.as_secs()).map_err(|_| {
            crate::LanguageError::new(crate::ErrorKind::NumericOverflow,
                "unix-time-now seconds exceed the signed 64-bit range", span)
        })?;
        Ok(Value::list([
            Value::Symbol(std::rc::Rc::from("unix-time")),
            exact_value(Rational::integer(seconds)),
            exact_value(Rational::integer(duration.subsec_nanos() as i64)),
        ]))
    });
    define!(environment, "ntp-query-raw", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("ntp-query-raw", args, 2, span)?;
        let host = match &args[0] {
            Value::String(value) => value.as_ref(),
            _ => return Err(crate::LanguageError::new(crate::ErrorKind::Type,
                "ntp-query-raw expects host string", span)),
        };
        let timeout = match &args[1] {
            Value::Number(value, Exactness::Exact) if *value >= 0.0 && value.fract() == 0.0 => *value as u64,
            _ => return Err(crate::LanguageError::new(crate::ErrorKind::Type,
                "ntp-query-raw expects exact timeout milliseconds", span)),
        };
        ntp_query_raw_value(host, timeout, span)
    });
    define!(environment, "timezone-declarations-raw", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("timezone-declarations-raw", args, 0, span)?;
        let tz_value = std::env::var("TZ").ok().filter(|value| !value.is_empty())
            .map(|value| Value::String(std::rc::Rc::from(value))).unwrap_or(Value::Nil);
        let etc_timezone_value = std::fs::read_to_string("/etc/timezone").ok()
            .map(|value| value.trim().to_string()).filter(|value| !value.is_empty())
            .map(|value| Value::String(std::rc::Rc::from(value))).unwrap_or(Value::Nil);
        Ok(Value::list([
            Value::Symbol(std::rc::Rc::from("timezone-declarations")), tz_value, etc_timezone_value,
        ]))
    });

    define!(environment, "vector-length", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("vector-length", args, 1, span)?;
        match &args[0] {
            Value::Vector(vec) => Ok(Value::Number(vec.borrow().len() as f64, Exactness::Exact)),
            _ => Err(crate::LanguageError::new(crate::ErrorKind::Type, "vector-length expects a vector", span)),
        }
    });
    define!(environment, "vector-ref", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("vector-ref", args, 2, span)?;
        let index = match &args[1] {
            Value::Number(f, Exactness::Exact) if *f >= 0.0 && f.fract() == 0.0 && *f <= usize::MAX as f64 => *f as usize,
            _ => return Err(crate::LanguageError::new(crate::ErrorKind::Type,
                "vector-ref expects an exact non-negative integer index", span)),
        };
        match &args[0] {
            Value::Vector(vec) => vec.borrow().get(index).cloned().ok_or_else(|| {
                crate::LanguageError::new(crate::ErrorKind::InvalidForm,
                    format!("vector-ref index {index} out of bounds for length {}", vec.borrow().len()), span)
            }),
            _ => Err(crate::LanguageError::new(crate::ErrorKind::Type, "vector-ref expects a vector", span)),
        }
    });
    define!(environment, "vector-set!", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("vector-set!", args, 3, span)?;
        let index = match &args[1] {
            Value::Number(f, Exactness::Exact) if *f >= 0.0 && f.fract() == 0.0 && *f <= usize::MAX as f64 => *f as usize,
            _ => return Err(crate::LanguageError::new(crate::ErrorKind::Type,
                "vector-set! expects an exact non-negative integer index", span)),
        };
        match &args[0] {
            Value::Vector(vec) => {
                let mut vec = vec.borrow_mut();
                if index >= vec.len() {
                    let len = vec.len();
                    return Err(crate::LanguageError::new(crate::ErrorKind::InvalidForm,
                        format!("vector-set! index {index} out of bounds for length {len}"), span));
                }
                vec[index] = args[2].clone();
                Ok(Value::Nil)
            }
            _ => Err(crate::LanguageError::new(crate::ErrorKind::Type, "vector-set! expects a vector", span)),
        }
    });

    define!(environment, "i32-buffer", |args: &[Value], _env: &Environment, span: Span| {
        let mut values = Vec::with_capacity(args.len());
        for value in args {
            let integer = match value {
                Value::Number(number, Exactness::Exact) if number.fract() == 0.0 => *number as i64,
                Value::Rational(rational) if rational.is_integer() => rational.as_precise_i64().ok_or_else(|| {
                    crate::LanguageError::new(crate::ErrorKind::NumericOverflow,
                        "i32-buffer element is outside the signed 32-bit range", span)
                })?,
                _ => return Err(crate::LanguageError::new(crate::ErrorKind::Type,
                    "i32-buffer expects exact integer elements", span)),
            };
            values.push(i32::try_from(integer).map_err(|_| {
                crate::LanguageError::new(crate::ErrorKind::NumericOverflow,
                    "i32-buffer element is outside the signed 32-bit range", span)
            })?);
        }
        Ok(Value::NumericBuffer(NumericBuffer::I32(values.into())))
    });
    define!(environment, "f32-buffer", |args: &[Value], _env: &Environment, span: Span| {
        let mut values = Vec::with_capacity(args.len());
        for value in args {
            let number = match value {
                Value::Number(number, _) => *number,
                Value::Rational(rational) => rational.as_f64(),
                _ => return Err(crate::LanguageError::new(crate::ErrorKind::Type,
                    "f32-buffer expects numeric elements", span)),
            };
            let narrowed = number as f32;
            if !number.is_finite() || !narrowed.is_finite() {
                return Err(crate::LanguageError::new(crate::ErrorKind::NumericOverflow,
                    "f32-buffer element is outside the finite binary32 domain", span));
            }
            values.push(narrowed);
        }
        Ok(Value::NumericBuffer(NumericBuffer::F32(values.into())))
    });

    define!(environment, "string-slice", |args: &[Value], _env: &Environment, span: Span| {
        super::special_forms::evaluate_string_slice(args, span)
    });
    define!(environment, "string-append", |args: &[Value], _env: &Environment, span: Span| string_append_values(args, span));
    define!(environment, "string<?", |args: &[Value], _env: &Environment, span: Span| string_less_than_values(args, span));
    define!(environment, "string?", |args: &[Value], _env: &Environment, span: Span| string_predicate_values(args, span));
    define!(environment, "symbol->string", |args: &[Value], _env: &Environment, span: Span| symbol_to_string_values(args, span));
    define!(environment, "string->symbol", |args: &[Value], _env: &Environment, span: Span| string_to_symbol_values(args, span));
    define!(environment, "string-first", |args: &[Value], _env: &Environment, span: Span| string_first_values(args, span));
    define!(environment, "string-rest", |args: &[Value], _env: &Environment, span: Span| string_rest_values(args, span));
    define!(environment, "codepoint->string", |args: &[Value], _env: &Environment, span: Span| codepoint_to_string_values(args, span));
    define!(environment, "string->codepoint", |args: &[Value], _env: &Environment, span: Span| string_to_codepoint_values(args, span));
    define!(environment, "sha256-hex", |args: &[Value], _env: &Environment, span: Span| sha256_hex_values(args, span));
    define!(environment, "json-parse", |args: &[Value], _env: &Environment, span: Span| json_parse_values(args, span));

    define!(environment, "print", |args: &[Value], env: &Environment, span: Span| print_values(args, env, span));
    define!(environment, "princ", |args: &[Value], env: &Environment, span: Span| princ_values(args, env, span));
    define!(environment, "write-to-string", |args: &[Value], env: &Environment, span: Span| write_to_string_values(args, env, span));
    define!(environment, "read", |args: &[Value], env: &Environment, span: Span| read_values(args, env, span));
    define!(environment, "read-all", |args: &[Value], env: &Environment, span: Span| read_all_values(args, env, span));
    define!(environment, "eval", |args: &[Value], env: &Environment, span: Span| eval_values(args, env, span));

    define!(environment, "numeric-buffer?", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("numeric-buffer?", args, 1, span)?;
        Ok(if matches!(args[0], Value::NumericBuffer(_)) { Value::truth(true) } else { Value::Nil })
    });
    define!(environment, "numeric-buffer-type", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("numeric-buffer-type", args, 1, span)?;
        let name = match &args[0] {
            Value::NumericBuffer(NumericBuffer::I32(_)) => "i32",
            Value::NumericBuffer(NumericBuffer::F32(_)) => "f32",
            _ => return Err(crate::LanguageError::new(crate::ErrorKind::Type,
                "numeric-buffer-type expects a numeric buffer", span)),
        };
        Ok(Value::Symbol(name.into()))
    });
    define!(environment, "numeric-buffer-length", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("numeric-buffer-length", args, 1, span)?;
        let length = match &args[0] {
            Value::NumericBuffer(NumericBuffer::I32(values)) => values.len(),
            Value::NumericBuffer(NumericBuffer::F32(values)) => values.len(),
            _ => return Err(crate::LanguageError::new(crate::ErrorKind::Type,
                "numeric-buffer-length expects a numeric buffer", span)),
        };
        Ok(Value::Number(length as f64, Exactness::Exact))
    });
    define!(environment, "numeric-buffer-ref", |args: &[Value], _env: &Environment, span: Span| {
        exact_args("numeric-buffer-ref", args, 2, span)?;
        let index = match args[1] {
            Value::Number(number, Exactness::Exact)
                if number >= 0.0 && number.fract() == 0.0 && number <= usize::MAX as f64 => number as usize,
            _ => return Err(crate::LanguageError::new(crate::ErrorKind::Type,
                "numeric-buffer-ref expects an exact non-negative integer index", span)),
        };
        match &args[0] {
            Value::NumericBuffer(NumericBuffer::I32(values)) => values.get(index)
                .map(|value| Value::Number(f64::from(*value), Exactness::Exact)),
            Value::NumericBuffer(NumericBuffer::F32(values)) => values.get(index)
                .map(|value| Value::Number(f64::from(*value), Exactness::Inexact)),
            _ => return Err(crate::LanguageError::new(crate::ErrorKind::Type,
                "numeric-buffer-ref expects a numeric buffer", span)),
        }.ok_or_else(|| crate::LanguageError::new(crate::ErrorKind::InvalidForm,
            "numeric-buffer-ref index is out of bounds", span))
    });
    define!(environment, "numeric-buffer-map", |args: &[Value], env: &Environment, span: Span| {
        exact_args("numeric-buffer-map", args, 2, span)?;
        match &args[1] {
            Value::NumericBuffer(NumericBuffer::I32(input)) => {
                let mut output = Vec::with_capacity(input.len());
                for element in input.iter() {
                    let result = super::invoke_value(&args[0],
                        &[Value::Number(f64::from(*element), Exactness::Exact)], env, span)?;
                    let integer = match &result {
                        Value::Number(number, Exactness::Exact) if number.fract() == 0.0 => *number as i64,
                        Value::Rational(rational) if rational.is_integer() => rational.as_precise_i64().ok_or_else(|| {
                            crate::LanguageError::new(crate::ErrorKind::NumericOverflow,
                                "numeric-buffer-map i32 result is outside the signed 32-bit range", span)
                        })?,
                        _ => return Err(crate::LanguageError::new(crate::ErrorKind::Type,
                            "numeric-buffer-map over i32 requires exact integer results", span)),
                    };
                    output.push(i32::try_from(integer).map_err(|_| {
                        crate::LanguageError::new(crate::ErrorKind::NumericOverflow,
                            "numeric-buffer-map i32 result is outside the signed 32-bit range", span)
                    })?);
                }
                Ok(Value::NumericBuffer(NumericBuffer::I32(output.into())))
            }
            Value::NumericBuffer(NumericBuffer::F32(input)) => {
                let mut output = Vec::with_capacity(input.len());
                for bits in input.iter() {
                    let result = super::invoke_value(&args[0],
                        &[Value::Number(f64::from(*bits), Exactness::Inexact)], env, span)?;
                    let number = match &result {
                        Value::Number(number, _) => *number,
                        Value::Rational(rational) => rational.as_f64(),
                        _ => return Err(crate::LanguageError::new(crate::ErrorKind::Type,
                            "numeric-buffer-map over f32 requires numeric results", span)),
                    };
                    let narrowed = number as f32;
                    if !number.is_finite() || !narrowed.is_finite() {
                        return Err(crate::LanguageError::new(crate::ErrorKind::NumericOverflow,
                            "numeric-buffer-map f32 result is outside the finite binary32 domain", span));
                    }
                    output.push(narrowed);
                }
                Ok(Value::NumericBuffer(NumericBuffer::F32(output.into())))
            }
            _ => Err(crate::LanguageError::new(crate::ErrorKind::Type,
                "numeric-buffer-map expects a numeric buffer", span)),
        }
    });

    // ADR-007/008 runtime peer slices: each identity below allocates one
    // callable value, then binds every ratified stable spelling projected from
    // the numeric semantic registry. Human spellings are not duplicated here.
    // The builtin diagnostic token remains the historical symbolic spelling
    // for Contract 2.1 display compatibility; it is NOT semantic identity.
    define_peer_builtin(
        environment,
        "+",
        12,
        std::rc::Rc::new(|args: &[Value], env: &Environment, span: Span| {
            arithmetic_on_values("+", args, env, span)
        }),
    );
    define_peer_builtin(
        environment,
        "-",
        13,
        std::rc::Rc::new(|args: &[Value], env: &Environment, span: Span| {
            arithmetic_on_values("-", args, env, span)
        }),
    );
    define_peer_builtin(
        environment,
        "*",
        14,
        std::rc::Rc::new(|args: &[Value], env: &Environment, span: Span| {
            arithmetic_on_values("*", args, env, span)
        }),
    );
    define_peer_builtin(
        environment,
        "/",
        15,
        std::rc::Rc::new(|args: &[Value], env: &Environment, span: Span| {
            division_on_values(args, args.len(), env, span)
        }),
    );
    define!(environment, "env", |args: &[Value], env: &Environment, span: Span| {
        exact_args("env", args, 0, span)?;
        let mut items = Vec::new();
        for (name, value) in env.snapshot() {
            items.push(Value::Pair(std::rc::Rc::new(Value::String(name)), std::rc::Rc::new(value)));
        }
        let mut list = Value::Nil;
        for item in items.into_iter().rev() {
            list = Value::Pair(std::rc::Rc::new(item), std::rc::Rc::new(list));
        }
        Ok(list)
    });
    define_peer_builtin(
        environment,
        "<",
        26,
        std::rc::Rc::new(|args: &[Value], _env: &Environment, span: Span| {
            comparison_on_values("<", args, span)
        }),
    );
    define_peer_builtin(
        environment,
        ">",
        27,
        std::rc::Rc::new(|args: &[Value], _env: &Environment, span: Span| {
            comparison_on_values(">", args, span)
        }),
    );
    define_peer_builtin(
        environment,
        "=",
        28,
        std::rc::Rc::new(|args: &[Value], _env: &Environment, span: Span| {
            comparison_on_values("=", args, span)
        }),
    );
}

fn exact_args(
    name: &'static str,
    args: &[Value],
    expected: usize,
    span: Span,
) -> Result<(), crate::LanguageError> {
    if args.len() != expected {
        return Err(crate::LanguageError::new(
            crate::ErrorKind::Arity,
            format!("{name} expects exactly {expected} argument(s)"),
            span,
        ));
    }
    Ok(())
}