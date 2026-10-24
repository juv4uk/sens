//! Emit the canonical two-record WSM FS F6 witness.
//!
//! F6 libraries bootstrap from physical T5M through Zig into SENS. The small
//! record witness remains a SENS-evaluated Lisp form and prints only data-only
//! root/object envelopes, one per line.

use sens::{load_core_library, Environment, Session, Value};

const MAX_RECORD_BYTES: usize = 64 * 1024;

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
    let mut records = Vec::new();
    let mut value = result.value;
    loop {
        match &value {
            Value::Pair(node) => {
                let Value::String(record) = &node.head else {
                    eprintln!("wsm-fs-record-producer: record is not a string: {}", node.head);
                    std::process::exit(1);
                };
                records.push(record.to_string());
                value = node.tail.clone();
            }
            Value::Nil => break,
            _ => {
                eprintln!("wsm-fs-record-producer: result is not a proper list: {value}");
                std::process::exit(1);
            }
        }
    }
    if records.len() != 2 || records.iter().any(|record| record.len() > MAX_RECORD_BYTES) {
        eprintln!("wsm-fs-record-producer: invalid bounded record stream");
        std::process::exit(1);
    }
    for record in records {
        println!("{record}");
    }
}
