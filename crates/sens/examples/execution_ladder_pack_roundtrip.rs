use sens::{
    pack_binary_source_tokens, parse_binary_source_words, unpack_binary_source_words,
};
use std::{env, fs, process};

fn run() -> Result<(), String> {
    let path = env::args()
        .nth(1)
        .ok_or_else(|| "usage: execution_ladder_pack_roundtrip <source-file>".to_owned())?;
    let source = fs::read_to_string(&path).map_err(|e| format!("read {path}: {e}"))?;

    let tokens = parse_binary_source_words(&source).map_err(|e| format!("{e:?}"))?;
    let widths: Vec<_> = tokens.iter().map(|token| token.word.width()).collect();
    let expected: Vec<_> = tokens.iter().map(|token| token.word).collect();

    let packed = pack_binary_source_tokens(&tokens);
    let decoded = unpack_binary_source_words(&packed, &widths)
        .ok_or_else(|| "packed payload did not decode under exact source widths".to_owned())?;

    if decoded != expected {
        return Err("pack/unpack changed exact source word sequence".to_owned());
    }

    let semantic_bits: usize = widths.iter().sum();

    println!("ROUNDTRIP=OK");
    println!("TOKENS={}", tokens.len());
    println!("SEMANTIC_BITS={semantic_bits}");
    println!("PACKED_BITS={}", packed.bit_len());
    println!("PACKED_BYTES={}", packed.byte_len());
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("ERROR: {error}");
        process::exit(2);
    }
}
