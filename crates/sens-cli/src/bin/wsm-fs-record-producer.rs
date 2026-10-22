//! Emit the canonical two-record WSM FS F6 witness.
//!
//! This binary deliberately bootstraps libraries through the same sequential
//! `eval_program` boundary used by the canonical Rust fixtures. It prints
//! only data-only root/object envelopes, one per line.

use sens::{eval_program, load_core_library, Environment, Session, Value};

#[cfg(feature = "zig-transport")]
use sens_cli::zig_transport;

// A host may request exact SENS source bytes only from the compiled Zig ABI.
// Zig never decides what these sources mean and no Rust fallback is permitted.
fn zig_bootstrap_sources() -> Result<[String; 8], String> {
    #[cfg(feature = "zig-transport")]
    {
        let unify = String::from_utf8(zig_transport::unify_source_bytes()?)
            .map_err(|error| format!("ZIG_F6_UNIFY_CARRIER invalid UTF-8: {error}"))?;
        let reason = String::from_utf8(zig_transport::reason_source_bytes()?)
            .map_err(|error| format!("ZIG_F6_REASON_CARRIER invalid UTF-8: {error}"))?;
        let forward = String::from_utf8(zig_transport::forward_source_bytes()?)
            .map_err(|error| format!("ZIG_F6_FORWARD_CARRIER invalid UTF-8: {error}"))?;
        let knowledge = String::from_utf8(zig_transport::knowledge_source_bytes()?)
            .map_err(|error| format!("ZIG_F6_KNOWLEDGE_CARRIER invalid UTF-8: {error}"))?;
        let persistent_map = String::from_utf8(zig_transport::persistent_map_source_bytes()?)
            .map_err(|error| format!("ZIG_F6_PERSISTENT_MAP_CARRIER invalid UTF-8: {error}"))?;
        let world = String::from_utf8(zig_transport::world_source_bytes()?)
            .map_err(|error| format!("ZIG_F6_WORLD_CARRIER invalid UTF-8: {error}"))?;
        let content_store = String::from_utf8(zig_transport::content_store_source_bytes()?)
            .map_err(|error| format!("ZIG_F6_CONTENT_STORE_CARRIER invalid UTF-8: {error}"))?;
        let lisp_fs = String::from_utf8(zig_transport::lisp_fs_source_bytes()?)
            .map_err(|error| format!("ZIG_F6_LISP_FS_CARRIER invalid UTF-8: {error}"))?;
        Ok([
            unify,
            reason,
            forward,
            knowledge,
            persistent_map,
            world,
            content_store,
            lisp_fs,
        ])
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: F6 source bootstrap requires the sterile Zig corridor; no Rust fallback".into())
    }
}

const MAX_RECORD_BYTES: usize = 64 * 1024;

fn main() {
    let mut session = Session {
        environment: Environment::root(),
    };
    if let Err(error) = load_core_library(&mut session) {
        eprintln!("wsm-fs-record-producer: core bootstrap failed: {error}");
        std::process::exit(1);
    }
    let sources = zig_bootstrap_sources().unwrap_or_else(|error| {
        eprintln!("wsm-fs-record-producer: {error}");
        std::process::exit(1);
    });
    for (path, source) in [
        ("lib/unify.lisp", sources[0].as_str()),
        ("lib/reason.lisp", sources[1].as_str()),
        ("lib/forward.lisp", sources[2].as_str()),
        ("lib/knowledge.lisp", sources[3].as_str()),
    ] {
        if let Err(error) = sens::eval_pinned_reasoning_source(path, source, &mut session) {
            eprintln!("wsm-fs-record-producer: Zig source bootstrap failed: {error}");
            std::process::exit(1);
        }
    }
    for (path, source) in [
        ("lib/persistent-map.lisp", sources[4].as_str()),
        ("lib/world.lisp", sources[5].as_str()),
        ("lib/content-store.lisp", sources[6].as_str()),
        ("lib/lisp-fs.lisp", sources[7].as_str()),
    ] {
        let result = if matches!(
            path,
            "lib/unify.lisp"
                | "lib/reason.lisp"
                | "lib/forward.lisp"
                | "lib/knowledge.lisp"
                | "lib/world.lisp"
                | "lib/persistent-map.lisp"
                | "lib/content-store.lisp"
                | "lib/lisp-fs.lisp"
        ) {
            sens::eval_pinned_reasoning_source(path, source, &mut session)
        } else {
            eval_program(source, &mut session)
        };
        if let Err(error) = result {
            eprintln!("wsm-fs-record-producer: library bootstrap failed: {error}");
            std::process::exit(1);
        }
    }

    let program = r#"
      (let* ((value (quote (hello world)))
             (written (фс-записати (фс-порожній) "code" value))
             (fs (car written))
             (root (фс-корінь-пакет fs))
             (object (фс-об'єкт-пакет value))
             (rebuilt (фс-відновити-корінь root (list object))))
        (cond
          ((not? (eq? (car rebuilt) (quote accepted)))
           (quote reconstruction-rejected))
          ((not? (equal? (second (фс-читати (second rebuilt) "code")) value))
           (quote reconstruction-mismatch))
          (t (list (фс-серіалізувати-корінь fs) (фс-серіалізувати-об'єкт value)))))
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
            Value::Pair(node) => {
                let Value::String(record) = &node.head else {
                    eprintln!("wsm-fs-record-producer: record is not a string");
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
