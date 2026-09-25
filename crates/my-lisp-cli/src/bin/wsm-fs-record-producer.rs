//! Emit the canonical two-record WSM FS F6 witness.
//!
//! This binary deliberately bootstraps libraries through the same sequential
//! `eval_program` boundary used by the canonical Rust fixtures. It prints
//! only data-only root/object envelopes, one per line.

use my_lisp::{eval_program, load_core_library, Environment, Session, Value};

const MAX_RECORD_BYTES: usize = 64 * 1024;

fn main() {
    let mut session = Session {
        environment: Environment::root(),
    };
    if let Err(error) = load_core_library(&mut session) {
        eprintln!("wsm-fs-record-producer: core bootstrap failed: {error}");
        std::process::exit(1);
    }
    for source in [
        include_str!("../../../../lib/unify.lisp"),
        include_str!("../../../../lib/reason.lisp"),
        include_str!("../../../../lib/forward.lisp"),
        include_str!("../../../../lib/knowledge.lisp"),
        include_str!("../../../../lib/persistent-map.lisp"),
        include_str!("../../../../lib/world.lisp"),
        include_str!("../../../../lib/content-store.lisp"),
        include_str!("../../../../lib/lisp-fs.lisp"),
    ] {
        if let Err(error) = eval_program(source, &mut session) {
            eprintln!("wsm-fs-record-producer: library bootstrap failed: {error}");
            std::process::exit(1);
        }
    }

    let program = r#"
      (let* ((value (quote (hello world)))
             (written (fs-write (fs-empty) "code" value))
             (fs (car written))
             (root (fs-root-package fs))
             (object (fs-object-package value))
             (rebuilt (fs-reconstruct-root root (list object))))
        (cond
          ((not? (eq? (car rebuilt) (quote accepted)))
           (quote reconstruction-rejected))
          ((not? (equal? (second (fs-read (second rebuilt) "code")) value))
           (quote reconstruction-mismatch))
          (t (list (fs-serialize-root fs) (fs-serialize-object value)))))
    "#;
    let result = match eval_program(program, &mut session) {
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
            Value::Pair(head, tail) => {
                let Value::String(record) = &**head else {
                    eprintln!("wsm-fs-record-producer: record is not a string");
                    std::process::exit(1);
                };
                records.push(record.to_string());
                value = (**tail).clone();
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
