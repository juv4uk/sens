//! Emit the canonical two-record WSM FS F6 witness.
//!
//! F6 libraries bootstrap from physical T5M through Zig into SENS. The small
//! record witness remains a SENS-evaluated Lisp form and prints only data-only
//! root/object envelopes, one per line.

use sens::{load_core_library, Environment, Session, Value};

const MAX_RECORD_BYTES: usize = 64 * 1024;

// The SENS witness can return its rejection marker either as the whole
// result or as one of the two record positions. Surface known markers before
// applying the external text-record contract; never serialize a Pair here.
fn f6_sens_rejection_marker(value: &Value) -> Option<String> {
    fn known(marker: &str) -> bool {
        marker.starts_with("f6-")
            || matches!(
                marker,
                "reconstruction-rejected"
                    | "reconstruction-mismatch"
                    | "root-format-not-symbol"
                    | "object-format-not-symbol"
                    | "valid-root-rejected"
                    | "serialized-root-rejected"
                    | "serialized-object-rejected"
                    | "empty-root-rejected"
                    | "empty-value-rejected"
                    | "missing-objects-accepted"
                    | "missing-bindings-accepted"
                    | "missing-value-accepted"
            )
    }

    let mut next = value;
    loop {
        match next {
            Value::Symbol(marker) if known(marker.as_str()) => {
                return Some(marker.to_string());
            }
            Value::Pair(node) => {
                // Markers are carried in record positions (the pair head),
                // not only as the entire result or as a list tail.
                if let Value::Symbol(marker) = &node.head {
                    if known(marker.as_str()) {
                        return Some(marker.to_string());
                    }
                }
                next = &node.tail;
            }
            _ => return None,
        }
    }
}

fn bounded_two_line_records(value: &Value) -> Result<[String; 2], &'static str> {
    let mut records = Vec::with_capacity(2);
    let mut next = value;
    loop {
        match next {
            Value::Pair(node) => {
                // SENS визначає дані, Rust лише передає рівно два фізичні записи.
                // Перевірка ДО копіювання запобігає необмеженому накопиченню.
                if records.len() == 2 {
                    return Err("F6_RECORD_COUNT expected=2 actual=more-than-2");
                }
                // Механізм I/O: обидва чинні носії тексту SENS мають
                // один канонічний зовнішній рядковий запис. Text7
                // декодуємо ЛИШЕ явно обраною клавіатурною проєкцією;
                // структури, символи й числові значення не серіалізуємо.
                let record = match &node.head {
                    Value::String(record) => record.to_string(),
                    Value::Text7(text) => {
                        if text.cells().len() > MAX_RECORD_BYTES {
                            return Err("F6_RECORD_SIZE expected=1..65536");
                        }
                        sens::render_text7(text, sens::Text7Layout::En)
                            .map_err(|_| "F6_RECORD_TEXT7 unrenderable-en-layout")?
                    }
                    Value::Pair(_) => {
                        return Err("F6_RECORD_TYPE expected=String-or-Text7 actual=Pair")
                    }
                    _ => {
                        return Err("F6_RECORD_TYPE expected=String-or-Text7 actual=non-text")
                    }
                };
                let bytes = record.as_bytes();
                if bytes.is_empty() || bytes.len() > MAX_RECORD_BYTES {
                    return Err("F6_RECORD_SIZE expected=1..65536");
                }
                // Зовнішній протокол — один запис на рядок. Дані SENS
                // не повинні додавати третій фізичний рядок чи NUL.
                if bytes.iter().any(|byte| matches!(*byte, b'\n' | b'\r' | b'\0')) {
                    return Err("F6_RECORD_DELIMITER expected=single-line");
                }
                records.push(record);
                next = &node.tail;
            }
            Value::Nil => break,
            _ => return Err("F6_RECORD_LIST expected=proper-list"),
        }
    }
    records
        .try_into()
        .map_err(|_| "F6_RECORD_COUNT expected=2 actual=fewer-than-2")
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
    if let Some(marker) = f6_sens_rejection_marker(&result.value) {
        eprintln!(
            "wsm-fs-record-producer: F6_SENS_WITNESS_REJECTED marker={marker} layer=sens"
        );
        std::process::exit(1);
    }
    let records = match bounded_two_line_records(&result.value) {
        Ok(records) => records,
        Err(error) => {
            eprintln!("wsm-fs-record-producer: {error}");
            std::process::exit(1);
        }
    };
    for record in records {
        println!("{record}");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn records(lines: &[&str]) -> Value {
        Value::list(lines.iter().map(|line| Value::String((*line).into())))
    }

    #[test]
    fn f6_surfaces_sens_rejection_marker_at_record_position() {
        let nested = Value::list([
            Value::Symbol("root-format-not-symbol".into()),
            Value::String("object".into()),
        ]);
        assert_eq!(
            f6_sens_rejection_marker(&nested).as_deref(),
            Some("root-format-not-symbol")
        );

        let direct = Value::Symbol("reconstruction-rejected".into());
        assert_eq!(
            f6_sens_rejection_marker(&direct).as_deref(),
            Some("reconstruction-rejected")
        );

        // Ordinary symbols are still rejected by the text-only envelope
        // validator rather than mislabeled as an explicit SENS witness marker.
        let ordinary = Value::list([
            Value::Symbol("a".into()),
            Value::String("object".into()),
        ]);
        assert_eq!(f6_sens_rejection_marker(&ordinary), None);
    }

    #[test]
    fn f6_accepts_exactly_two_bounded_single_line_records() {
        assert_eq!(
            bounded_two_line_records(&records(&["root", "object"])).unwrap(),
            ["root".to_owned(), "object".to_owned()]
        );
        let maximum = "x".repeat(MAX_RECORD_BYTES);
        let exact = Value::list([
            Value::String(maximum.into()),
            Value::String("object".into()),
        ]);
        assert!(bounded_two_line_records(&exact).is_ok());
    }

    #[test]
    fn f6_rejects_unbounded_list_before_cloning_a_third_record() {
        let too_many = records(&["root", "object", "third"]);
        assert_eq!(
            bounded_two_line_records(&too_many).unwrap_err(),
            "F6_RECORD_COUNT expected=2 actual=more-than-2"
        );
        assert!(bounded_two_line_records(&records(&["root"])).is_err());
        assert!(bounded_two_line_records(&Value::Bool(true)).is_err());
    }

    #[test]
    fn f6_accepts_exact_d7_text_projection_for_external_records() {
        let root = sens::encode_text7("(root)", sens::Text7Layout::En).unwrap();
        let object = sens::encode_text7("(object)", sens::Text7Layout::En).unwrap();
        let actual = Value::list([Value::Text7(root), Value::Text7(object)]);
        assert_eq!(
            bounded_two_line_records(&actual).unwrap(),
            ["(root)".to_owned(), "(object)".to_owned()]
        );
    }

    #[test]
    fn f6_rejects_structural_values_instead_of_forging_text_records() {
        let not_text = Value::list([
            Value::list([Value::Symbol("root".into())]),
            Value::String("object".into()),
        ]);
        assert_eq!(
            bounded_two_line_records(&not_text).unwrap_err(),
            "F6_RECORD_TYPE expected=String-or-Text7 actual=Pair"
        );
    }

    #[test]
    fn f6_rejects_oversize_and_injected_line_delimiters() {
        let too_long = Value::list([
            Value::String("x".repeat(MAX_RECORD_BYTES + 1).into()),
            Value::String("object".into()),
        ]);
        assert_eq!(
            bounded_two_line_records(&too_long).unwrap_err(),
            "F6_RECORD_SIZE expected=1..65536"
        );
        for injected in ["root\nextra", "root\rextra", "root\0extra"] {
            assert_eq!(
                bounded_two_line_records(&records(&[injected, "object"])).unwrap_err(),
                "F6_RECORD_DELIMITER expected=single-line"
            );
        }
        assert!(bounded_two_line_records(&records(&["", "object"])).is_err());
    }
}
