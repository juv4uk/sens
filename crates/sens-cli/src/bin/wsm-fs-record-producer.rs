//! Emit the canonical two-record WSM FS F6 witness.
//!
//! F6 libraries bootstrap from physical T5M through Zig into SENS. The small
//! record witness remains a SENS-evaluated Lisp form and prints only data-only
//! root/object envelopes, one per line.

use sens::{load_core_library, Environment, Session, Value};

const MAX_RECORD_BYTES: usize = 64 * 1024;

// I/O-only diagnosis: identify the actual SENS runtime carrier, but never
// coerce it into text or admit it as a valid external record.
fn f6_record_type_error(value: &Value) -> String {
    match value {
        Value::Nil => "F6_RECORD_TYPE expected=String-or-Text7 actual=Nil".to_owned(),
        Value::Bool(_) => "F6_RECORD_TYPE expected=String-or-Text7 actual=Bool".to_owned(),
        Value::Number(_, _) => "F6_RECORD_TYPE expected=String-or-Text7 actual=Number".to_owned(),
        Value::Rational(_) => "F6_RECORD_TYPE expected=String-or-Text7 actual=Rational".to_owned(),
        Value::BinaryNumber(_) => "F6_RECORD_TYPE expected=String-or-Text7 actual=BinaryNumber".to_owned(),
        Value::NumericComposition(_) => "F6_RECORD_TYPE expected=String-or-Text7 actual=NumericComposition".to_owned(),
        Value::Sid(_) => "F6_RECORD_TYPE expected=String-or-Text7 actual=LegacySlot".to_owned(),
        Value::DomainIdentity(identity) => format!(
            "F6_RECORD_TYPE expected=String-or-Text7 actual=DomainIdentity D{}:{}",
            identity.width(),
            identity
        ),
        Value::Symbol(_) => "F6_RECORD_TYPE expected=String-or-Text7 actual=Symbol".to_owned(),
        Value::Closure(_) => "F6_RECORD_TYPE expected=String-or-Text7 actual=Closure".to_owned(),
        Value::Macro(_) => "F6_RECORD_TYPE expected=String-or-Text7 actual=Macro".to_owned(),
        Value::Builtin(_) => "F6_RECORD_TYPE expected=String-or-Text7 actual=Builtin".to_owned(),
        Value::HostHandle { .. } => "F6_RECORD_TYPE expected=String-or-Text7 actual=HostHandle".to_owned(),
        Value::Vector(_) => "F6_RECORD_TYPE expected=String-or-Text7 actual=Vector".to_owned(),
        Value::NumericBuffer(_) => "F6_RECORD_TYPE expected=String-or-Text7 actual=NumericBuffer".to_owned(),
        Value::Pair(_) => "F6_RECORD_TYPE expected=String-or-Text7 actual=Pair".to_owned(),
        Value::String(_) | Value::Text7(_) => "F6_RECORD_TYPE internal-classifier-error".to_owned(),
    }
}

fn bounded_two_line_records(value: &Value) -> Result<[String; 2], String> {
    let mut records = Vec::with_capacity(2);
    let mut next = value;
    loop {
        match next {
            Value::Pair(node) => {
                // SENS визначає дані, Rust лише передає рівно два фізичні записи.
                // Перевірка ДО копіювання запобігає необмеженому накопиченню.
                if records.len() == 2 {
                    return Err("F6_RECORD_COUNT expected=2 actual=more-than-2".to_owned());
                }
                // Механізм I/O: обидва чинні носії тексту SENS мають
                // один канонічний зовнішній рядковий запис. Text7
                // декодуємо ЛИШЕ явно обраною клавіатурною проєкцією;
                // структури, символи й числові значення не серіалізуємо.
                let record = match &node.head {
                    Value::String(record) => record.to_string(),
                    Value::Text7(text) => {
                        if text.cells().len() > MAX_RECORD_BYTES {
                            return Err("F6_RECORD_SIZE expected=1..65536".to_owned());
                        }
                        sens::render_text7(text, sens::Text7Layout::En)
                            .map_err(|_| "F6_RECORD_TEXT7 unrenderable-en-layout".to_owned())?
                    }
                    Value::Pair(_) => {
                        return Err("F6_RECORD_TYPE expected=String-or-Text7 actual=Pair".to_owned())
                    }
                    other => return Err(format!("{} record_index={}", f6_record_type_error(other), records.len()))
                };
                let bytes = record.as_bytes();
                if bytes.is_empty() || bytes.len() > MAX_RECORD_BYTES {
                    return Err("F6_RECORD_SIZE expected=1..65536".to_owned());
                }
                // Зовнішній протокол — один запис на рядок. Дані SENS
                // не повинні додавати третій фізичний рядок чи NUL.
                if bytes.iter().any(|byte| matches!(*byte, b'\n' | b'\r' | b'\0')) {
                    return Err("F6_RECORD_DELIMITER expected=single-line".to_owned());
                }
                records.push(record);
                next = &node.tail;
            }
            Value::Nil => break,
            _ => return Err("F6_RECORD_LIST expected=proper-list".to_owned()),
        }
    }
    records
        .try_into()
        .map_err(|_| "F6_RECORD_COUNT expected=2 actual=fewer-than-2".to_owned())
}

fn main() {
    let mut session = Session {
        environment: Environment::root(),
    };
    if let Err(error) = load_core_library(&mut session) {
        eprintln!("wsm-fs-record-producer: core bootstrap failed: {error}");
        std::process::exit(1);
    }
    if let Err(error) = sens_cli::bootstrap_f6_t5m_libraries(&mut session) {
        eprintln!("wsm-fs-record-producer: physical F6 bootstrap failed: {error}");
        std::process::exit(1);
    }
    let result = match sens_cli::execute_f6_producer_witness(&mut session) {
        Ok(result) => result,
        Err(error) => {
            eprintln!("wsm-fs-record-producer: witness failed: {error}");
            std::process::exit(1);
        }
    };
    // SENS returns an explicit quoted marker when its own reconstruction
    // or read-back law failed. Preserve the exact marker in CI diagnostics:
    // a generic "non-string" would misclassify this *semantic* rejection
    // as a Rust record-envelope problem. Rust does not decide that law.
    if let Value::Symbol(marker) = &result.value {
        eprintln!(
            "wsm-fs-record-producer: F6_SENS_WITNESS_REJECTED marker={marker} layer=sens"
        );
        std::process::exit(1);
    }
    let records = match bounded_two_line_records(&result.value) {
        Ok(records) => records,
        Err(error) => {
            eprintln!("wsm-fs-record-producer: {error}");
            // Diagnostics only: print the exact SENS return shape on a
            // failing native F6 witness. This does not coerce or admit data.
            if std::env::var_os("SENS_EQ_TRACE").is_some() {
                eprintln!(
                    "wsm-fs-record-producer: witness-value={}",
                    result.value.to_canonical_wire_string()
                );
            }
            std::process::exit(1);
        }
    };
    for record in records {
        println!("{record}");
    }
}

