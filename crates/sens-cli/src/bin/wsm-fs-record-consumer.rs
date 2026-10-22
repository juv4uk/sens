//! Consume the bounded F6 record stream and reconstruct its WSM root.
//! Stored envelopes are quoted data; this binary never evaluates their payload.

use sens::{eval_program, load_core_library, Environment, Session, Value};
use std::io::{self, Read};

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

fn string_literal(value: &str) -> String {
    format!("\"{}\"", value.replace('\\', "\\\\").replace('"', "\\\""))
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let records: Vec<_> = input
        .lines()
        .filter(|line| !line.trim().is_empty())
        .collect();
    if records.len() != 2 {
        eprintln!("expected exactly two records");
        std::process::exit(2);
    }
    let mut session = Session {
        environment: Environment::root(),
    };
    load_core_library(&mut session).unwrap();
    let sources = zig_bootstrap_sources().unwrap_or_else(|error| {
        eprintln!("wsm-fs-record-consumer: {error}");
        std::process::exit(1);
    });
    for (path, source) in [
        ("lib/unify.lisp", sources[0].as_str()),
        ("lib/reason.lisp", sources[1].as_str()),
        ("lib/forward.lisp", sources[2].as_str()),
        ("lib/knowledge.lisp", sources[3].as_str()),
    ] {
        sens::eval_pinned_reasoning_source(path, source, &mut session)
            .expect("Zig-owned F6 bootstrap source must load in SENS");
    }
    for (path, source) in [
        ("lib/persistent-map.lisp", sources[4].as_str()),
        ("lib/world.lisp", sources[5].as_str()),
        ("lib/content-store.lisp", sources[6].as_str()),
        ("lib/lisp-fs.lisp", sources[7].as_str()),
    ] {
        if matches!(
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
            sens::eval_pinned_reasoning_source(path, source, &mut session).unwrap();
        } else {
            eval_program(source, &mut session).unwrap();
        }
    }
    let root = eval_program(
        &format!("(фс-десеріалізувати-корінь {})", string_literal(records[0])),
        &mut session,
    )
    .unwrap()
    .value;
    let _object = eval_program(
        &format!("(фс-десеріалізувати-об'єкт {})", string_literal(records[1])),
        &mut session,
    )
    .unwrap()
    .value;
    let Value::Pair(root_node) = &root else {
        std::process::exit(1)
    };
    let Value::Symbol(tag) = &root_node.head else {
        std::process::exit(1)
    };
    if &**tag != "accepted" {
        std::process::exit(1);
    }
    let expr = format!(
        "(фс-відновити-корінь (quote {}) (list (quote {})))",
        records[0], records[1]
    );
    let rebuilt = eval_program(&expr, &mut session).unwrap().value;
    let Value::Pair(ref node) = rebuilt else {
        std::process::exit(1)
    };
    if !matches!(&node.head, Value::Symbol(name) if &**name == "accepted") {
        std::process::exit(1);
    }
    println!("f6-semantic-consumer-ok records=2");
}
