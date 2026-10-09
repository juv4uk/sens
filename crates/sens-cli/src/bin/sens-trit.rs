//! T5 file codec для ДВІЙКОВОЇ SENS: трит 2 — внутрішня межа, не
//! видимий символ і не частина семантики D2/D7.
//!
//! `sens-trit open file.sens` або `sens-trit file.sens` показує лише
//! точні binary words з ОДНИМ пробілом між ними. Фізично `.sens`
//! залишається packed byte file. EOF задає довжина файла, без EOS=22.
//!
//! Explicit `eval file.sens` invokes the *current pure SENS oracle*. This is
//! NOT an implicit action on opening a file, not historical Lisp equivalence,
//! and not a grant to host I/O/GPU/external processes.

use std::{env, fs, fs::OpenOptions, io::Write, path::Path, process};

const USAGE: &str =
    "usage: sens-trit (encode path.lisp | open path.sens | view path.sens | decode path.sens | explain path.sens | eval path.sens | eval-core4 path.sens | verify path.lisp)\n       sens-trit path.sens  # open only; never execute implicitly";

fn sibling_sens(path: &Path) -> Result<std::path::PathBuf, String> {
    if path.extension().and_then(|ext| ext.to_str()) != Some("lisp") {
        return Err("expected a .lisp companion path".into());
    }
    Ok(path.with_extension("sens"))
}

fn read_sens(path: &Path) -> Result<Vec<u8>, String> {
    if path.extension().and_then(|ext| ext.to_str()) != Some("sens") {
        return Err("expected a physical .sens file".into());
    }
    fs::read(path).map_err(|e| format!("read .sens: {e}"))
}

fn verify_companion(source: &str, binary: &[u8]) -> Result<(), String> {
    let canonical = sens::encode_binary_projection_ternary(source)
        .map_err(|e| format!("unadmitted .lisp projection: {e:?}"))?;
    let decoded = sens::decode_ternary_program(binary)
        .map_err(|e| format!("invalid .sens transport or grammar: {e:?}"))?;
    if canonical != binary {
        return Err("paired .lisp/.sens differs at the physical byte level".into());
    }
    let info = sens::ternary_transport_accounting(&decoded)
        .map_err(|e| format!("accounting failure: {e:?}"))?;
    println!("VERIFIED {} domain words; binary SENS={} semantic bits; transport={} trits; physical={} bytes; trailing={} trits",
             info.word_count, info.semantic_bits, info.encoded_trits,
             info.physical_bytes, info.tail_trits);
    Ok(())
}

/// Expand a rejected *structural* physical T5 stream into the exact existing
/// canonical D2 parser diagnostic. This is diagnostic-only: never substitute
/// the parser result for open_ternary_program admission. Invalid transport
/// stays invalid transport, without guessing a source width or era.
fn explain_d2_rejection(bytes: &[u8], error: sens::TernaryTransportError) -> String {
    let mut message = format!("{error:?}");
    if matches!(error, sens::TernaryTransportError::InvalidProgramSyntax) {
        if let Ok(words) = sens::decode_ternary_words(bytes) {
            let visible = sens::render_ternary_words_spaced(&words);
            if let Err(detail) = sens::parse_canonical_binary(&visible) {
                message.push_str("; canonical D2: ");
                message.push_str(&detail.render(&visible));
            }
        }
    }
    message
}

/// Run the explicitly requested SENS program on the current capability-free
/// evaluator. Transport identity, D2 structural parsing, then semantic eval
/// are independent gates; success does not prove that an old Lisp source
/// has the same behavior or that a D24+/host effect is admitted.
fn eval_t5_bytes(bytes: &[u8]) -> Result<sens::EvalResult, String> {
    eval_t5_bytes_core4(bytes, false)
}

/// An EXPLICIT opt-in Core4 bootstrap for programs that need language-owned
/// D4/D5 closures such as LIST/APPEND. Bare eval remains capability-free and
/// unchanged; loading a library is mechanism availability, NOT a new resident.
fn eval_t5_bytes_core4(
    bytes: &[u8],
    bootstrap_core: bool,
) -> Result<sens::EvalResult, String> {
    // Physical execution stays on typed words and the packed reader.
    // The visible 0/1 view is reserved for explicit open/explain operations.
    let words = sens::decode_ternary_words(bytes)
        .map_err(|e| format!("physical T5 decode rejected: {e:?}"))?;
    let forms = sens::parse_canonical_word_sequence(&words)
        .map_err(|e| format!("canonical packed SENS parser rejected: {e}"))?;
    let mut session = sens::Session::default();
    if bootstrap_core {
        sens::load_core_library(&mut session)
            .map_err(|e| format!("explicit Core4 bootstrap rejected: {e:?}"))?;
    }
    sens::eval_parsed_expressions(&forms, &mut session)
        .map_err(|e| format!("current SENS evaluator rejected: {e}"))
}

/// Diagnose why a physical packed T5 file fails the existing canonical D2
/// parser. No second grammar and no implicit program execution: each exact
/// binary word becomes a line so the existing error renderer's line is the
/// failed word coordinate in the physical SENS stream.
fn explain_t5_bytes(bytes: &[u8]) -> Result<String, String> {
    let words = sens::decode_ternary_words(bytes)
        .map_err(|e| format!("physical T5 transport rejected: {e:?}"))?;
    let projection = sens::render_ternary_words_vertical(&words);
    sens::parse_canonical_binary(&projection)
        .map_err(|e| format!(
            "D2 grammar rejected (one exact typed word per line): {}",
            e.render(&projection)
        ))?;
    Ok(format!(
        "D2 syntax PASS; {} typed words; current/historical semantic oracle NOT_VERIFIED",
        words.len()
    ))
}

fn execute() -> Result<(), String> {
    let args = env::args().skip(1).collect::<Vec<_>>();
    // У разі передавання одного файла .sens читаємо його як людина,
    // а не показуємо на екран внутрішні трити чи сирі байти.
    let (command, file) = match args.as_slice() {
        [path] if path.ends_with(".sens") => ("open", path.as_str()),
        [command, path] => (command.as_str(), path.as_str()),
        _ => return Err(USAGE.into()),
    };
    let path = Path::new(file);

    match command {
        "encode" => {
            let sens_path = sibling_sens(path)?;
            let projection = fs::read_to_string(path).map_err(|e| format!("read .lisp: {e}"))?;
            let bytes = sens::encode_binary_projection_ternary(&projection)
                .map_err(|e| format!("encode .lisp projection: {e:?}"))?;
            // Ніколи не перезаписувати наявний файл.
            let mut output = OpenOptions::new().create_new(true).write(true)
                .open(&sens_path).map_err(|e| format!("create .sens: {e}"))?;
            output.write_all(&bytes).map_err(|e| format!("write .sens: {e}"))?;
            verify_companion(&projection, &bytes)
        }
        "open" | "view" => {
            let bytes = read_sens(path)?;
            let human = sens::open_ternary_program(&bytes)
                .map_err(|e| format!("open .sens: {}", explain_d2_rejection(&bytes, e)))?;
            // ЄДИНИЙ видимий роздільник — ASCII space; 2 / EOS / pad сховані.
            println!("{human}");
            Ok(())
        }
        "decode" => {
            let bytes = read_sens(path)?;
            let words = sens::decode_ternary_program(&bytes)
                .map_err(|e| format!("decode .sens: {e:?}"))?;
            // Попередній вертикальний API залишаємо для інструментів.
            print!("{}", sens::render_ternary_words_vertical(&words));
            Ok(())
        }
        "explain" => {
            // Independent physical T5, then the SAME canonical D2 parser.
            // Unlike open, print a word-coordinate error on invalid grammar;
            // unlike eval, never run any expression or grant capabilities.
            let bytes = read_sens(path)?;
            println!("{}", explain_t5_bytes(&bytes)?);
            Ok(())
        }
        "eval" | "eval-core4" => {
            // Both require explicit execution. Only eval-core4 additionally
            // loads the existing language-owned Core4 module on request.
            // Neither open nor bare eval may silently acquire mechanisms.
            let bytes = read_sens(path)?;
            let result = if command == "eval-core4" {
                eval_t5_bytes_core4(&bytes, true)?
            } else {
                eval_t5_bytes(&bytes)?
            };
            for output in result.output {
                println!("{output}");
            }
            println!("{}", result.value);
            Ok(())
        }
        "verify" => {
            let sens_path = sibling_sens(path)?;
            let projection = fs::read_to_string(path).map_err(|e| format!("read .lisp: {e}"))?;
            let bytes = fs::read(&sens_path).map_err(|e| format!("read .sens: {e}"))?;
            verify_companion(&projection, &bytes)
        }
        _ => Err(USAGE.into()),
    }
}

fn main() {
    if let Err(message) = execute() {
        eprintln!("sens-trit: {message}");
        process::exit(1);
    }
}

#[cfg(test)]
mod eval_tests {
    use super::*;

    #[test]
    fn public_binary_eval_commands_are_explicit_and_separate_from_open() {
        assert!(USAGE.contains("eval path.sens"));
        assert!(USAGE.contains("eval-core4 path.sens"));
        assert!(!USAGE.contains("eval-core path.sens"));
    }

    #[test]
    fn physical_quote_fixture_preserves_t5_and_exact_d2_structure() {
        let bytes = include_bytes!("../../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");
        let words = sens::decode_ternary_program(bytes).expect("canonical physical T5");
        let visible = sens::render_ternary_words_spaced(&words);
        assert_eq!(visible, "10 001 00 000 01");
        assert_eq!(sens::open_ternary_program(bytes).unwrap(), visible);
        assert_eq!(sens::encode_binary_projection_ternary(&visible).unwrap(), bytes);

        let widths = words.iter().map(|word| word.width()).collect::<Vec<_>>();
        let packed = sens::pack_binary_source_words(&words);
        let forms = sens::parse_canonical_packed_words(&packed, &widths)
            .expect("exact-width packed reader accepts the D2 boundary");
        assert_eq!(forms.len(), 1);
    }

    #[test]
    fn two_top_level_forms_share_one_physical_file_and_keep_d2_boundaries() {
        let bytes = include_bytes!("../../../../tests/fixtures/migration-multiform-cohort-main/two-forms.sens");
        let words = sens::decode_ternary_program(bytes).expect("canonical physical T5");
        let widths = words.iter().map(|word| word.width()).collect::<Vec<_>>();
        let packed = sens::pack_binary_source_words(&words);
        let forms = sens::parse_canonical_packed_words(&packed, &widths)
            .expect("two exact D2 forms parse from one packed stream");
        assert_eq!(forms.len(), 2);
        assert_eq!(sens::encode_ternary_words(&words).unwrap(), bytes);
    }

    #[test]
    fn physical_or_structural_corruption_fails_closed_before_execution() {
        assert!(sens::decode_ternary_program(&[0xf3]).is_err());
        assert!(sens::decode_ternary_program(&[0xf2]).is_err());
        let unbalanced_close = sens::encode_ternary_words(&[
            sens::parse_binary_source_words("01").unwrap()[0].word,
        ]).unwrap();
        assert!(sens::decode_ternary_program(&unbalanced_close).is_err());
    }

    #[test]
    fn explain_shows_canonical_d2_failure_without_creating_a_second_parser() {
        let words = sens::parse_binary_source_words("10 001")
            .expect("physical words allowed");
        let trits = sens::encode_ternary_words(
            &words.into_iter().map(|token| token.word).collect::<Vec<_>>(),
        ).expect("physically packed bytes");
        let err = explain_t5_bytes(&trits).expect_err("unbalanced D2 syntax");
        assert!(err.contains("D2 grammar rejected"), "{err}");
        assert!(err.contains("one exact typed word per line"), "{err}");
        assert!(!err.contains("D2 syntax PASS"), "{err}");
    }

    #[test]
    fn explain_distinguishes_bad_transport_from_bad_d2_grammar() {
        let bytes = include_bytes!(
            "../../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens"
        );
        let receipt = explain_t5_bytes(bytes).expect("known current D2 syntax");
        assert!(receipt.contains("D2 syntax PASS"), "{receipt}");
        assert!(receipt.contains("semantic oracle NOT_VERIFIED"), "{receipt}");
        assert!(explain_t5_bytes(&[0xf3])
            .expect_err("invalid base3 byte")
            .contains("physical T5 transport rejected"));
        let bad_d2 = sens::encode_ternary_words(&[
            sens::parse_binary_source_words("01").unwrap()[0].word,
        ]).unwrap();
        assert!(explain_t5_bytes(&bad_d2).unwrap_err().contains("D2 grammar rejected"));
    }

    #[test]
    fn physical_eval_path_uses_packed_words_not_visible_text() {
        let source = include_str!("sens-trit.rs");
        let start = source.find("fn eval_t5_bytes_core4(").expect("physical eval route");
        let end = source[start..].find("\n}\n").expect("route body") + start + 3;
        let route = &source[start..end];
        assert!(route.contains("sens::decode_ternary_words(bytes)"));
        assert!(route.contains("sens::parse_canonical_word_sequence(&words)"));
        assert!(!route.contains("sens::open_ternary_program(bytes)"));
        assert!(!route.contains("sens::parse_canonical_binary(&visible)"));
    }
}
