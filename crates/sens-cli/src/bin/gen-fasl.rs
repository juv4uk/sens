//! Regenerate a FASL snapshot from a WSM source file.
//! Usage: gen-fasl <source.wsm> <output.fasl>
//! The snapshot embeds sha256(source); the loader refuses snapshots whose
//! embedded hash does not match the compiled-in source bytes.
use sens::{fasl_encode, parse, parse_mixed_exact_domain_core_source, sha256_source};
use std::{fs, process};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 3 {
        eprintln!("usage: gen-fasl <source.wsm> <output.fasl>");
        process::exit(2);
    }
    let source = fs::read(&args[1]).expect("read source");
    let source_text = std::str::from_utf8(&source).expect("utf-8 source");
    let expressions = if args[1] == "lib/core4.lisp" {
        parse_mixed_exact_domain_core_source(&args[1], source_text)
            .expect("parse Core4 source with its ratified exact-domain heads")
    } else {
        parse(source_text).expect("parse source")
    };
    let hash = sha256_source(&source);
    let encoded = fasl_encode(&expressions, &hash);
    fs::write(&args[2], &encoded).expect("write fasl");
    println!(
        "{} -> {} ({} bytes, {} top-level forms)",
        args[1],
        args[2],
        encoded.len(),
        expressions.len()
    );
}
