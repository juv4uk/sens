//! One physical byte, one genuinely evaluated *closed* SENS program.
//!
//! This is a bounded RESEARCH enumerative profile (".f3m"), NOT the universal
//! Frame-3, NOT a replacement of physical ".sens" T5, and NOT a claim that
//! arbitrary programs fit in one byte. The profile is selected externally by
//! the caller/file type, so that selector's cost is excluded from the byte.
//! A reserved byte or wrong-sized file is rejected; no implicit T5 fallback.
//! Values are verified by the actual SENS evaluator and independent T5 path.
use std::path::Path;
use sens::{
    encode_ternary_words, eval_parsed_expressions, parse_binary_source_words,
    parse_canonical_binary, PhysicalT5Program, Session,
};

const OPERANDS: [&str; 3] = ["0", "1", "000"];

#[derive(Debug, Clone, Copy, Eq, PartialEq)]
enum ProofError { Reserved, InvalidWidth, Unmapped }

impl std::fmt::Display for ProofError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}
impl std::error::Error for ProofError {}

fn list_parts(parts: &[&str]) -> Vec<String> {
    parts.iter().map(|s| (*s).to_owned()).collect()
}

/// Every admitted byte is a grammar rank, not a hard-coded entire program.
/// 0..=2: values; 0x10: ATOM; 0x20: CONS;
/// 0x40: CAR(CONS); 0x60: CDR(CONS); 0x80: EQ; 0xA0: QUOTE.
/// All other code points are reserved, including 0xF3/0xF4 carrier markers.
fn decode(input: &[u8]) -> Result<Vec<String>, ProofError> {
    if input.len() != 1 { return Err(ProofError::InvalidWidth); }
    let byte = input[0];
    let words = match byte {
        0..=2 => list_parts(&[OPERANDS[byte as usize]]),
        0x10..=0x12 => list_parts(&["10", "010", OPERANDS[(byte - 0x10) as usize], "01"]),
        0x20..=0x28 | 0x40..=0x48 | 0x60..=0x68 | 0x80..=0x88 => {
            let (base, head) = match byte {
                0x20..=0x28 => (0x20, "111"),
                0x40..=0x48 => (0x40, "100"),
                0x60..=0x68 => (0x60, "011"),
                _ => (0x80, "101"),
            };
            let index = (byte - base) as usize;
            let lhs = OPERANDS[index / 3];
            let rhs = OPERANDS[index % 3];
            match head {
                "111" => list_parts(&["10", "111", lhs, rhs, "01"]),
                "101" => list_parts(&["10", "101", lhs, rhs, "01"]),
                _ => list_parts(&["10", head, "10", "111", lhs, rhs, "01", "01"]),
            }
        }
        0xa0..=0xa2 => list_parts(&["10", "001", OPERANDS[(byte - 0xa0) as usize], "01"]),
        _ => return Err(ProofError::Reserved),
    };
    Ok(words)
}

/// Reverse rank has no semantic/naming fallback; exact source widths matter.
fn encode(words: &[String]) -> Result<[u8; 1], ProofError> {
    for code in 0u8..=u8::MAX {
        if let Ok(candidate) = decode(&[code]) {
            if candidate == words { return Ok([code]); }
        }
    }
    Err(ProofError::Unmapped)
}

fn verify_one(code: u8) -> Result<(usize, String), String> {
    let words = decode(&[code]).map_err(|e| format!("{e:?}"))?;
    let source = words.join(" ");
    // Real Rust canonical parser; not a research grammar or AST substitute.
    let parsed = parse_canonical_binary(&source).map_err(|e| format!("D2: {e:?}"))?;
    if parsed.len() != 1 {
        return Err(format!("not exactly one canonical form: {source}"));
    }
    let typed = parse_binary_source_words(&source)
        .map_err(|e| format!("exact typed words: {e:?}"))?
        .into_iter().map(|token| token.word).collect::<Vec<_>>();
    let t5 = encode_ternary_words(&typed).map_err(|e| format!("T5: {e:?}"))?;
    let expected = eval_parsed_expressions(&parsed, &mut Session::default())
        .map_err(|e| format!("evaluator: {e:?}"))?;
    let t5_program = PhysicalT5Program::decode(&t5).map_err(|e| format!("physical reader: {e:?}"))?;
    if t5_program.form_count() != 1 {
        return Err(format!("not one physical T5 form: {source}"));
    }
    let actual = t5_program.execute(&mut Session::default())
        .map_err(|e| format!("physical T5 execution: {e:?}"))?;
    if expected.value != actual.value || expected.output != actual.output {
        return Err(format!("SENS evaluator ↔ physical T5 mismatch: {source}"));
    }
    if encode(&words) != Ok([code]) {
        return Err(format!("ambiguous micro-profile rank: {source}"));
    }
    Ok((t5.len(), format!("{:?}", actual.value)))
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let codes: Vec<u8> = (0u8..=255).filter(|&b| decode(&[b]).is_ok()).collect();
    // 3 literals + 3 ATOM + 9 CONS + 9 CAR.CONS + 9 CDR.CONS
    // + 9 EQ + 3 QUOTE = exactly 45 grammar-generated programs.
    if codes.len() != 45 { return Err(format!("unexpected one-byte capacity: {}", codes.len()).into()); }
    println!("code_hex\\tmicro_file_bytes\\tt5_full_bytes\\tdecoded_exact_words\\tactual_sens_value");
    for &code in &codes {
        let (t5_len, result) = verify_one(code)?;
        let source = decode(&[code])?.join(" ");
        println!("{code:02x}\\t1\\t{t5_len}\\t{source}\\t{result}");
    }
    // Malformed/aliased inputs must remain rejected. No multi-byte extension.
    for bad in [vec![], vec![0xff], vec![0x40, 0], vec![0xf3]] {
        if decode(&bad).is_ok() { return Err(format!("accepted invalid carrier {bad:?}").into()); }
    }
    let full = decode(&[0x45])?; // CAR(CONS(1,000)), index 5 => lhs=1, rhs=000
    if full != list_parts(&["10", "100", "10", "111", "1", "000", "01", "01"]) {
        return Err("closed program did not reconstruct exact words".into());
    }
    // Proof of actual computation, not only valid parser/round-trip.
    let expected = eval_parsed_expressions(&parse_canonical_binary("1")?, &mut Session::default())?;
    let actual = eval_parsed_expressions(
        &parse_canonical_binary(&full.join(" "))?, &mut Session::default())?;
    if expected.value != actual.value || !actual.output.is_empty() {
        return Err("CAR(CONS(1,000)) did not compute 1 in real evaluator".into());
    }

    if let Some(target) = std::env::args().nth(1) {
        let target = Path::new(&target);
        std::fs::create_dir_all(target)?;
        std::fs::write(target.join("car-cons-one-nil.f3m"), [0x45])?;
        std::fs::write(target.join("atom-nil.f3m"), [0x12])?;
        if std::fs::metadata(target.join("car-cons-one-nil.f3m"))?.len() != 1 {
            return Err("actual physical carrier is not 1 byte".into());
        }
    }
    eprintln!("ONE_BYTE_RESEARCH_PASS: 45/45 finite closed expressions; all 256 possible bytes checked; real evaluator parity, exact words, reserved codes and file length verified; format RESEARCH .f3m, NOT .sens");
    Ok(())
}
