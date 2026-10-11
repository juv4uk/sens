//! Direct transport-control benchmark: SENS wire decoding vs serde_json decoding.
//!
//! Both inputs are generated from the same deterministic semantic corpus by
//! benchmarks/agent-messages/run.py. This benchmark isolates decode cost:
//! file I/O and process startup are outside the timed loop.
//!
//! Usage:
//!   transport_decode_bench wire RECORDS [rounds]
//!   transport_decode_bench json RECORDS [rounds]

use sens::wire_decode_program;
use std::{env, fs, process::ExitCode, time::Instant};

fn records(bytes: &[u8]) -> Vec<&[u8]> {
    let mut out = Vec::new();
    let mut at = 0usize;
    while at < bytes.len() {
        let len = u32::from_le_bytes(
            bytes[at..at + 4].try_into().expect("record length"),
        ) as usize;
        at += 4;
        let end = at.checked_add(len).expect("record end");
        assert!(end <= bytes.len(), "truncated record");
        out.push(&bytes[at..end]);
        at = end;
    }
    out
}

fn decode_one(form: &str, bytes: &[u8]) {
    match form {
        "wire" => {
            let expr = wire_decode_program(bytes).expect("valid SENS wire");
            std::hint::black_box(expr);
        }
        "json" => {
            let value: serde_json::Value =
                serde_json::from_slice(bytes).expect("valid JSON");
            std::hint::black_box(value);
        }
        other => panic!("unknown form {other}; expected wire|json"),
    }
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    if args.len() < 3 {
        eprintln!("usage: transport_decode_bench wire|json RECORDS [rounds]");
        return ExitCode::from(2);
    }

    let form = &args[1];
    let bytes = fs::read(&args[2]).expect("read records");
    let records = records(&bytes);
    assert!(!records.is_empty(), "empty corpus");

    let rounds: usize = args.get(3).map_or(1, |s| s.parse().expect("rounds"));
    assert!(rounds > 0);

    // Warm up caches and allocator paths before the measured section.
    for record in &records {
        decode_one(form, record);
    }

    let start = Instant::now();
    for _ in 0..rounds {
        for record in &records {
            decode_one(form, record);
        }
    }
    let elapsed = start.elapsed();
    let messages = records.len() * rounds;
    let ns_per_message = elapsed.as_secs_f64() * 1e9 / messages as f64;
    let msg_per_sec = messages as f64 / elapsed.as_secs_f64();

    println!(
        "form={form} messages={messages} elapsed_ns={:.0} ns_per_message={:.3} msg_per_sec={:.3}",
        elapsed.as_secs_f64() * 1e9,
        ns_per_message,
        msg_per_sec
    );

    ExitCode::SUCCESS
}
