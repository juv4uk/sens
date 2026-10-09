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
    let words = sens::decode_ternary_program(bytes)
        .map_err(|e| format!("physical T5/D2 decode rejected: {}", explain_d2_rejection(bytes, e)))?;
    let widths: Vec<usize> = words.iter().map(|word| word.width()).collect();
    let packed = sens::pack_binary_source_words(&words);
    let forms = sens::parse_canonical_packed_words(&packed, &widths)
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
    fn public_binary_eval_commands_are_explicit_and_stay_separate_from_open() {
        // The dispatch must admit exactly the documented opt-in Core4 name.
        // Bare 'eval' never silently inherits bootstrap semantics.
        assert_eq!(USAGE.contains("eval-core4 path.sens"), true);
        assert!(!USAGE.contains("eval-core path.sens"));
    }

    #[test]
    fn canonical_quote_legacy_fixture_runs_on_current_pure_oracle() {
        // Existing SHA-independent regression fixture: migrated D3 QUOTE of
        // D3 EMPTY. The exact result is Value::Nil, not just a successful
        // decode of the transport bytes.
        let bytes = include_bytes!("../../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");
        let evaluated = eval_t5_bytes(bytes).expect("current canonical T5 oracle");
        assert!(matches!(evaluated.value, sens::Value::Nil));
    }

    #[test]
    fn two_top_level_forms_share_one_file_without_special_eos() {
        let bytes = include_bytes!("../../../../tests/fixtures/migration-multiform-cohort-main/two-forms.sens");
        let evaluated = eval_t5_bytes(bytes).expect("sequential canonical execution");
        assert!(matches!(
            evaluated.value,
            sens::Value::Pair(ref head, ref tail)
                if matches!(head.as_ref(), sens::Value::Nil)
                && matches!(tail.as_ref(), sens::Value::Nil)
        ));
    }

    #[test]
    fn explicit_core4_bootstrap_enables_d4_list_without_weakening_bare_eval() {
        // (D4 LIST (D3 QUOTE D3 EMPTY)): genuine exact words, physically
        // packed through the production T5 codec. No user-defined Text7.
        let words = sens::parse_binary_source_words(
            "10 1110 00 10 001 00 000 01 01"
        ).expect("ratified canonical D2/D3/D4 words");
        let packed = sens::encode_ternary_words(
            &words.into_iter().map(|word| word.word).collect::<Vec<_>>()
        ).expect("T5 physical bytes");

        let unbootstrapped = eval_t5_bytes(&packed)
            .expect_err("bare evaluator has no D4 LIST mechanism");
        assert!(
            unbootstrapped.contains("no admitted value-call mechanism")
                && unbootstrapped.contains("1110"),
            "unexpected missing-bootstrap error: {unbootstrapped}"
        );

        let core = eval_t5_bytes_core4(&packed, true)
            .expect("explicit Core4 must supply language-owned D4 LIST");
        assert_eq!(core.value.to_string(), "(())");
        assert_eq!(sens::open_ternary_program(&packed).unwrap(),
                   "10 1110 00 10 001 00 000 01 01");
    }

    #[test]
    fn physical_or_structural_corruption_can_never_be_executed() {
        assert!(eval_t5_bytes(&[0xf3]).is_err()); // base-3 out of range
        assert!(eval_t5_bytes(&[0xf2]).is_err()); // five excess pad trits
        let unbalanced_close = sens::encode_ternary_words(
            &sens::parse_binary_source_words("01").unwrap()
                .into_iter().map(|token| token.word).collect::<Vec<_>>()
        ).unwrap();
        assert!(eval_t5_bytes(&unbalanced_close).is_err()); // D2 CLOSE alone
    }

    #[test]
    fn explain_shows_canonical_d2_failure_with_original_word_coordinate() {
        let words = sens::parse_binary_source_words("10 001")
            .expect("physical words allowed");
        let trits = sens::encode_ternary_words(
            &words.into_iter().map(|token| token.word).collect::<Vec<_>>()
        ).expect("physically packed bytes");
        let err = explain_t5_bytes(&trits).expect_err("unbalanced D2 syntax");
        assert!(err.contains("D2 grammar rejected"), "{err}");
        assert!(err.contains("one exact typed word per line"), "{err}");
        // The canonical parser error renderer, not a new D2 parser, owns
        // the failure position. Never imply syntax PASS from valid bytes.
        assert!(!err.contains("D2 syntax PASS"), "{err}");
    }

    #[test]
    fn explain_is_read_only_and_never_semantic_oracle_admission() {
        let bytes = include_bytes!(
            "../../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens"
        );
        let receipt = explain_t5_bytes(bytes).expect("known current D2 syntax");
        assert!(receipt.contains("D2 syntax PASS"), "{receipt}");
        assert!(receipt.contains("semantic oracle NOT_VERIFIED"), "{receipt}");
        assert!(explain_t5_bytes(&[0xf3])
            .expect_err("invalid base3 byte")
            .contains("physical T5 transport rejected"));
        let bad_d2 = sens::encode_ternary_words(
            &sens::parse_binary_source_words("01").unwrap()
                .into_iter().map(|word| word.word).collect::<Vec<_>>()
        ).unwrap();
        assert!(explain_t5_bytes(&bad_d2).unwrap_err().contains("D2 grammar rejected"));
    }

    #[test]
    fn invalid_d2_close_has_exact_parser_diagnostic_but_remains_blocked() {
        let bad = sens::encode_ternary_words(&[
            sens::parse_binary_source_words("01").unwrap()[0].word,
        ]).expect("valid T5 transport can contain invalid D2 grammar");
        let open_error = sens::open_ternary_program(&bad).unwrap_err();
        let diagnostic = explain_d2_rejection(&bad, open_error);
        assert!(diagnostic.contains("InvalidProgramSyntax"));
        assert!(diagnostic.contains("unexpected D2 close word 01"), "{diagnostic}");
        assert!(eval_t5_bytes(&bad).is_err(), "explanation cannot grant execution");
    }

    #[test]
    fn invalid_d2_dot_has_parser_reason_and_bad_transport_keeps_transport_error() {
        let bad = sens::encode_ternary_words(&[
            sens::parse_binary_source_words("11").unwrap()[0].word,
        ]).unwrap();
        let diagnostic = explain_d2_rejection(&bad, sens::open_ternary_program(&bad).unwrap_err());
        assert!(diagnostic.contains("misplaced D2 dot word 11"), "{diagnostic}");

        let corrupt = [0xf3u8];
        let error = sens::open_ternary_program(&corrupt).unwrap_err();
        let transport_diagnostic = explain_d2_rejection(&corrupt, error);
        assert!(!transport_diagnostic.contains("canonical D2:"));
        assert!(eval_t5_bytes(&corrupt).is_err());
    }

    #[test]
    fn open_and_eval_are_distinct_public_operations() {
        let bytes = include_bytes!("../../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");
        assert_eq!(sens::open_ternary_program(bytes).unwrap(),
                   "10 001 00 000 01");
        assert!(matches!(eval_t5_bytes(bytes).unwrap().value, sens::Value::Nil));
    }
}

