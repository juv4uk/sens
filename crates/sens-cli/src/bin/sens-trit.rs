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
    "usage: sens-trit (backend | encode path.lisp | encode-d7-uk path.txt | decode-d7-uk path.sens | open path.sens | view path.sens | decode path.sens | explain path.sens | eval path.sens | eval-core4 path.sens | encode-e1 path.sens | eval-e1 path.e1 | verify path.lisp | encode-f3 path.sens | open-f3 path.senc | decode-f3 path.senc | eval-f3 path.senc | verify-f3-sha256 path.senc SHA256 | eval-f3-sha256 path.senc SHA256)\n       sens-trit path.sens  # open only; never execute implicitly";

// Compiled only in the official Zig-transport build. Rust validates SENS
// program syntax; Zig owns all physical wire bytes for these commands.
#[cfg(feature = "zig-transport")]
mod zig_transport {
    unsafe extern "C" {
        fn sens_zig_codec_abi_version() -> u32;
        fn sens_zig_t5_validate(input: *const u8, len: usize) -> i32;
        // ABI v2: caller-owned width + big-endian payload triplets.
        // Never send repr(C)/repr(Rust) structs across the language boundary.
        fn sens_zig_t5_encode_be3(
            input: *const u8, byte_len: usize, output: *mut u8, capacity: usize
        ) -> isize;
        fn sens_zig_t5_decode_be3(
            input: *const u8, byte_len: usize, output: *mut u8, capacity: usize
        ) -> isize;
        fn sens_zig_f3c_pack(
            input: *const u8, len: usize, output: *mut u8, capacity: usize
        ) -> isize;
        fn sens_zig_f3c_unpack(
            input: *const u8, len: usize, output: *mut u8, capacity: usize
        ) -> isize;
    }

    fn version() -> Result<(), String> {
        // SAFETY: zero-argument pure function from a statically linked Zig library.
        if unsafe { sens_zig_codec_abi_version() } != 2 {
            return Err("Zig codec C ABI version mismatch".into());
        }
        Ok(())
    }

    pub fn validate_t5(bytes: &[u8]) -> Result<(), String> {
        version()?;
        // SAFETY: the borrowed byte slice lives through the synchronous call.
        if unsafe { sens_zig_t5_validate(bytes.as_ptr(), bytes.len()) } != 0 {
            return Err("Zig physical T5 rejected; no SENS execution".into());
        }
        Ok(())
    }

    pub fn encode_t5(
        words: &[sens::BinarySourceWord],
        expected_bytes: &[u8],
    ) -> Result<Vec<u8>, String> {
        version()?;
        let mut physical_words = Vec::with_capacity(words.len() * 3);
        for word in words {
            let width = u8::try_from(word.width())
                .map_err(|_| "Zig T5 width out of one-byte ABI range")?;
            let bits = word.packed_bits();
            physical_words.push(width);
            physical_words.push((bits >> 8) as u8);
            physical_words.push(bits as u8);
        }
        let mut bytes = vec![0u8; expected_bytes.len()];
        // SAFETY: Zig sees only caller-owned raw bytes + exact byte length.
        let len = unsafe {
            sens_zig_t5_encode_be3(
                physical_words.as_ptr(), physical_words.len(),
                bytes.as_mut_ptr(), bytes.len()
            )
        };
        if len < 0 || len as usize != bytes.len() || bytes != expected_bytes {
            return Err("Zig T5 and admitted SENS reference differ at a physical byte".into());
        }
        Ok(bytes)
    }


    /// Zig is the only physical T5 decoder on the feature-gated eval ingress.
    /// ABI v2 carries only [width, MSB, LSB] bytes, never Rust enum layout.
    /// Exact words are subsequently admitted by SENS's existing D2 reader.
    pub fn decode_t5_words(bytes: &[u8]) -> Result<Vec<sens::BinarySourceWord>, String> {
        // Zig first: physical validation also caps carrier size before allocation.
        validate_t5(bytes)?;
        let trits = bytes.len().checked_mul(5)
            .ok_or("T5 input length overflow")?;
        let max_words = trits.checked_add(1)
            .ok_or("T5 word count overflow")? / 2;
        let capacity = max_words.checked_mul(3)
            .ok_or("T5 BE3 capacity overflow")?;
        let mut be3 = vec![0u8; capacity];
        // SAFETY: caller-owned slices outlive this synchronous Zig v2 ABI.
        let written = unsafe {
            sens_zig_t5_decode_be3(
                bytes.as_ptr(), bytes.len(), be3.as_mut_ptr(), be3.len()
            )
        };
        if written <= 0 || usize::try_from(written).ok().filter(|&n| n <= be3.len()).is_none()
            || written % 3 != 0
        {
            return Err(format!("Zig physical T5 decode rejected: code={written}"));
        }
        be3.truncate(written as usize);
        let mut words = Vec::with_capacity(be3.len() / 3);
        for triple in be3.chunks_exact(3) {
            let width = triple[0];
            let payload = (u16::from(triple[1]) << 8) | u16::from(triple[2]);
            // A host integer here is only the bounded carrier of exact bits.
            // Type + width are preserved; neither assigns a language meaning.
            if width < 9 && payload > u16::from(u8::MAX) {
                return Err("Zig BE3 payload exceeds declared narrow width".into());
            }
            let low = payload as u8;
            let word = match width {
                1 => sens::Bit1::new(low).map(sens::BinarySourceWord::W1),
                2 => sens::Bit2::new(low).map(sens::BinarySourceWord::W2),
                3 => sens::Bit3::new(low).map(sens::BinarySourceWord::W3),
                4 => sens::Bit4::new(low).map(sens::BinarySourceWord::W4),
                5 => sens::Bit5::new(low).map(sens::BinarySourceWord::W5),
                6 => sens::Bit6::new(low).map(sens::BinarySourceWord::W6),
                7 => sens::Bit7::new(low).map(sens::BinarySourceWord::W7),
                8 => sens::Bit8::new(low).map(sens::BinarySourceWord::W8),
                9 => sens::Bit9::new(payload).map(sens::BinarySourceWord::W9),
                _ => None,
            }.ok_or_else(|| format!("Zig BE3 invalid exact word width={width}"))?;
            words.push(word);
        }
        Ok(words)
    }

    pub fn encode_f3(t5: &[u8]) -> Result<Option<Vec<u8>>, String> {
        version()?;
        if t5.len() > 16 { return Ok(None); }
        let mut bytes = vec![0u8; 16];
        // SAFETY: Zig writes at most the provided capacity.
        let len = unsafe {
            sens_zig_f3c_pack(t5.as_ptr(), t5.len(), bytes.as_mut_ptr(), bytes.len())
        };
        if len == -3 { return Ok(None); } // not smaller: T5 remains production
        if len <= 0 { return Err(format!("Zig F3C pack rejected: code={len}")); }
        bytes.truncate(len as usize);
        if bytes.len() >= t5.len() { return Err("Zig F3C did not save bytes".into()); }
        Ok(Some(bytes))
    }

    pub fn decode_f3(carrier: &[u8]) -> Result<Vec<u8>, String> {
        version()?;
        let mut output = vec![0u8; 16];
        // SAFETY: caller owns valid input/output slices until call returns.
        let len = unsafe {
            sens_zig_f3c_unpack(
                carrier.as_ptr(), carrier.len(), output.as_mut_ptr(), output.len()
            )
        };
        if len <= 0 { return Err(format!("explicit Zig F3C rejected: code={len}")); }
        output.truncate(len as usize);
        // Zig first, then the existing SENS canonical parser/evaluator.
        validate_t5(&output)?;
        Ok(output)
    }
}

fn decode_f3_carrier(bytes: &[u8]) -> Result<Vec<u8>, String> {
    #[cfg(feature = "zig-transport")]
    {
        let restored = zig_transport::decode_f3(bytes)?;
        let words = zig_transport::decode_t5_words(&restored)?;
        let parsed = sens::PhysicalT5Program::from_exact_words(&words)
            .map_err(|e| format!("Zig F3C restored inadmissible SENS program: {e:?}"))?;
        if parsed.form_count() != 1 {
            return Err("Zig F3C restored more than one root".into());
        }
        return Ok(restored);
    }
    #[cfg(not(feature = "zig-transport"))]
    { sens::frame3_small::decode_explicit_small_f3(bytes)
        .map_err(|e| format!("explicit small F3 rejected: {e:?}")) }
}

fn encode_f3_carrier(bytes: &[u8]) -> Result<Option<Vec<u8>>, String> {
    #[cfg(feature = "zig-transport")]
    {
        let words = zig_transport::decode_t5_words(bytes)?;
        let parsed = sens::PhysicalT5Program::from_exact_words(&words)
            .map_err(|e| format!("SENS input is not an executable canonical T5 program: {e:?}"))?;
        if parsed.form_count() != 1 || bytes.len() > 16 {
            return Ok(None);
        }
        return zig_transport::encode_f3(bytes);
    }
    #[cfg(not(feature = "zig-transport"))]
    { sens::frame3_small::encode_explicit_small_f3(bytes)
        .map_err(|e| format!("tiny F3 encode rejected: {e:?}")) }
}

fn sibling_sens(path: &Path) -> Result<std::path::PathBuf, String> {
    if path.extension().and_then(|ext| ext.to_str()) != Some("lisp") {
        return Err("expected a .lisp companion path".into());
    }
    Ok(path.with_extension("sens"))
}

/// Physical T5 is decoded in Zig for normal CLI builds. Structural D2
/// admission remains the SAME SENS canonical word reader, with no visible
/// source reconstruction or implicit execution in read-only commands.
fn decode_canonical_t5_words(bytes: &[u8]) -> Result<Vec<sens::BinarySourceWord>, String> {
    #[cfg(feature = "zig-transport")]
    let words = zig_transport::decode_t5_words(bytes)?;
    #[cfg(not(feature = "zig-transport"))]
    let words = sens::decode_ternary_words(bytes)
        .map_err(|e| format!("reference physical T5 rejected: {e:?}"))?;
    sens::parse_canonical_word_sequence(&words)
        .map_err(|e| format!("SENS canonical D2 rejected: {e}"))?;
    Ok(words)
}

fn read_sens(path: &Path) -> Result<Vec<u8>, String> {
    if path.extension().and_then(|ext| ext.to_str()) != Some("sens") {
        return Err("expected a physical .sens file".into());
    }
    let bytes = fs::read(path).map_err(|e| format!("read .sens: {e}"))?;
    #[cfg(feature = "zig-transport")]
    zig_transport::validate_t5(&bytes)?;
    Ok(bytes)
}


/// E1 has an explicit experimental .e1 carrier. Neither .sens nor .senc
/// changes its meaning, and opening any path never implicitly runs SENS.
fn read_explicit_e1(path: &Path) -> Result<Vec<u8>, String> {
    if path.extension().and_then(|ext| ext.to_str()) != Some("e1") {
        return Err("E1 requires an explicit .e1 file; no T5/F3C autodetection".into());
    }
    fs::read(path).map_err(|e| format!("read explicit E1: {e}"))
}

/// Mechanical E1 encoding only. The currently ratified canonical D2 reader
/// checks exact words; the E1 codec does not grant any semantic identity.
fn encode_e1_from_t5(physical_t5: &[u8]) -> Result<Vec<u8>, String> {
    let words = sens::decode_ternary_program(physical_t5)
        .map_err(|e| format!("SENS canonical T5/D2 rejected: {e:?}"))?;
    sens::envelope_e1::encode(&words)
        .map_err(|e| format!("E1 physical encode rejected: {e:?}"))
}

fn read_explicit_f3(path: &Path) -> Result<Vec<u8>, String> {
    if path.extension().and_then(|ext| ext.to_str()) != Some("senc") {
        return Err("explicit F3 command requires a physical .senc file".into());
    }
    let framed = fs::read(path).map_err(|e| format!("read explicit F3 .senc: {e}"))?;
    // The bounded F3 decoder restores physically canonical T5; all SENS
    // parsing and execution stays in the same production D2/T5 pipeline.
    decode_f3_carrier(&framed)
}



/// Require a trusted *external* 64-hex-character SHA-256 of the RAW F3 file
/// before returning any decoded program. Hash is an integrity check only:
/// its provenance must be trusted (e.g. pinned manifest or publisher sig).
/// Read the file just once so a racing file replacement cannot bypass hashing.
fn read_explicit_f3_sha256(path: &Path, expected_hex: &str) -> Result<Vec<u8>, String> {
    if path.extension().and_then(|ext| ext.to_str()) != Some("senc") {
        return Err("sha256-verified F3 requires explicit .senc".into());
    }
    if expected_hex.len() != 64 ||
        !expected_hex.bytes().all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    {
        return Err("expected SHA-256 must be exactly 64 lowercase hex characters".into());
    }
    let mut expected = [0u8; 32];
    for (i, slot) in expected.iter_mut().enumerate() {
        *slot = u8::from_str_radix(&expected_hex[i * 2..i * 2 + 2], 16)
            .map_err(|_| "invalid SHA-256 hex")?;
    }
    let bytes = fs::read(path).map_err(|e| format!("read F3 for SHA-256 verification: {e}"))?;
    let actual = sens::sha256_source(&bytes);
    let mismatch = actual.iter().zip(expected.iter()).fold(0u8, |acc, (a, b)| acc | (a ^ b));
    if mismatch != 0 {
        return Err("F3 SHA-256 mismatch: no decoding or execution permitted".into());
    }
    decode_f3_carrier(&bytes)
        .map_err(|e| format!("SHA-256 verified but F3 canonical decode rejected: {e}"))
}

fn write_explicit_small_f3(path: &Path) -> Result<(), String> {
    // Operator-requested only: never change the normal T5 .sens source.
    let original = read_sens(path)?;
    let framed = encode_f3_carrier(&original)?
        .ok_or("this .sens program is not a smaller valid original F3 file")?;
    let dest = path.with_extension("senc");
    let mut out = OpenOptions::new().create_new(true).write(true)
        .open(&dest).map_err(|e| format!("create-new .senc: {e}"))?;
    out.write_all(&framed).map_err(|e| format!("write .senc: {e}"))?;
    out.sync_all().map_err(|e| format!("sync .senc: {e}"))?;
    if fs::read(&dest).map_err(|e| format!("read-back .senc: {e}"))? != framed
        || read_explicit_f3(&dest)? != original
    {
        return Err("physical tiny F3 write did not verify against input T5 bytes".into());
    }
    println!("{} F3 {}B <- T5 {}B; source unchanged",
             dest.display(), framed.len(), original.len());
    Ok(())
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
    // In the normal build Zig decodes physical T5 to exact-width words.
    // The SENS-owned D2 reader/evaluator alone determines admissibility.
    // The Rust physical T5 decoder remains only in the explicit
    // --no-default-features reference build, never a silent fallback.
    #[cfg(feature = "zig-transport")]
    let program = {
        let words = zig_transport::decode_t5_words(bytes)?;
        sens::PhysicalT5Program::from_exact_words(&words)
            .map_err(|e| format!("canonical SENS D2/admission rejected: {e}"))?
    };
    #[cfg(not(feature = "zig-transport"))]
    let program = sens::PhysicalT5Program::decode(bytes).map_err(|e| match e {
        sens::T5ExecutionError::Transport(error) =>
            format!("physical T5 decode rejected: {error:?}"),
        sens::T5ExecutionError::Language(error) =>
            format!("canonical packed SENS parser rejected: {error}"),
    })?;
    let mut session = sens::Session::default();
    if bootstrap_core {
        sens::load_core_library(&mut session)
            .map_err(|e| format!("explicit Core4 bootstrap rejected: {e:?}"))?;
    }
    program.execute(&mut session)
        .map_err(|e| format!("current SENS evaluator rejected: {e}"))
}

/// Пояснити негативний результат без іншого парсера чи текстового fallback.
/// Первинним рішенням назавжди лишається encode_binary_projection_ternary.
fn explain_encode_failure(source: &str, error: sens::TernaryTransportError) -> String {
    let mut message = format!("encode .lisp projection: {error:?}");
    let source_error = match &error {
        sens::TernaryTransportError::InvalidBinaryProjection =>
            sens::parse_binary_source_words(source).map(|_| ()),
        sens::TernaryTransportError::InvalidProgramSyntax =>
            sens::parse_canonical_binary(source).map(|_| ()),
        _ => return message,
    };
    if let Err(detail) = source_error {
        message.push_str("; ");
        message.push_str(&detail.render(source));
    }
    message
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
    let (command, file, trusted_hash) = match args.as_slice() {
        [arg] if arg == "backend" => ("backend", "", None),
        [path] if path.ends_with(".sens") => ("open", path.as_str(), None),
        [command, path] => (command.as_str(), path.as_str(), None),
        [command, path, expected]
            if matches!(command.as_str(), "verify-f3-sha256" | "eval-f3-sha256") =>
                (command.as_str(), path.as_str(), Some(expected.as_str())),
        _ => return Err(USAGE.into()),
    };
    let path = Path::new(file);

    match command {
        "backend" => {
            #[cfg(feature = "zig-transport")]
            println!("transport=zig abi=2 semantic_authority=SENS");
            #[cfg(not(feature = "zig-transport"))]
            println!("transport=rust-reference semantic_authority=SENS");
            Ok(())
        }
        "encode-d7-uk" => {
            // Physical T5 record; no D2 source grammar and NO execution.
            if path.extension().and_then(|ext| ext.to_str()) != Some("txt") {
                return Err("encode-d7-uk requires an explicit UTF-8 .txt source".into());
            }
            let text = fs::read_to_string(path)
                .map_err(|e| format!("read UTF-8 D7 keyboard text: {e}"))?;
            let bytes = sens::encode_d7_uk_t5(&text)
                .map_err(|e| format!("D7 keyboard T5 rejected: {e:?}"))?;
            let output_path = path.with_extension("sens");
            let mut output = OpenOptions::new().create_new(true).write(true)
                .open(&output_path).map_err(|e| format!("create T5 text record: {e}"))?;
            output.write_all(&bytes)
                .map_err(|e| format!("write D7 T5 text record: {e}"))?;
            println!("D7-T5 keyboard record: {} bytes", bytes.len());
            Ok(())
        }
        "decode-d7-uk" => {
            let bytes = read_sens(path)?;
            let text = sens::decode_d7_uk_t5(&bytes)
                .map_err(|e| format!("D7 keyboard T5 rejected: {e:?}"))?;
            println!("{text}");
            Ok(())
        }
        "encode" => {
            let sens_path = sibling_sens(path)?;
            let projection = fs::read_to_string(path).map_err(|e| format!("read .lisp: {e}"))?;
            let reference = sens::encode_binary_projection_ternary(&projection)
                .map_err(|e| explain_encode_failure(&projection, e))?;
            // SENS owns the grammar/semantic admission; physical bytes are
            // produced by Zig in the official zig-transport variant.
            #[cfg(feature = "zig-transport")]
            let bytes = {
                let typed = sens::decode_ternary_words(&reference)
                    .map_err(|e| format!("canonical T5 words rejected: {e:?}"))?;
                zig_transport::encode_t5(&typed, &reference)?
            };
            #[cfg(not(feature = "zig-transport"))]
            let bytes = reference;
            // Ніколи не перезаписувати наявний файл.
            let mut output = OpenOptions::new().create_new(true).write(true)
                .open(&sens_path).map_err(|e| format!("create .sens: {e}"))?;
            output.write_all(&bytes).map_err(|e| format!("write .sens: {e}"))?;
            verify_companion(&projection, &bytes)
        }
        "open" | "view" => {
            let bytes = read_sens(path)?;
            let words = decode_canonical_t5_words(&bytes)
                .map_err(|e| format!("open .sens: {e}"))?;
            // View is an external projection of exact SENS words; it never
            // becomes the source consumed by the canonical D2 reader.
            let human = sens::render_ternary_words_spaced(&words);
            println!("{human}");
            Ok(())
        }
        "decode" => {
            let bytes = read_sens(path)?;
            let words = decode_canonical_t5_words(&bytes)
                .map_err(|e| format!("decode .sens: {e}"))?;
            // Vertical human projection; no Rust physical T5 decoder in Zig build.
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
        "encode-e1" => {
            let bytes = read_sens(path)?;
            let e1 = encode_e1_from_t5(&bytes)?;
            // A new, explicit physical carrier only; never replace the .sens.
            let target = path.with_extension("e1");
            let mut output = OpenOptions::new().create_new(true).write(true)
                .open(&target)
                .map_err(|e| format!("create explicit E1 (will not overwrite): {e}"))?;
            output.write_all(&e1).map_err(|e| format!("write E1: {e}"))?;
            println!("E1_PHYSICAL_ENCODED bytes={} semantic_authority=SENS", e1.len());
            Ok(())
        }
        "eval-e1" => {
            // Explicit SENS execution only: CRC/E1 decoding followed by the
            // SAME ratified exact-domain admission/evaluator used by T5.
            let e1 = read_explicit_e1(path)?;
            let mut session = sens::Session::default();
            let result = sens::eval_e1_program(&e1, &mut session)
                .map_err(|e| format!("E1 -> current SENS rejected: {e:?}"))?;
            for output in result.output { println!("{output}"); }
            println!("{}", result.value);
            Ok(())
        }
        "encode-f3" => write_explicit_small_f3(path),
        "verify-f3-sha256" => {
            let restored = read_explicit_f3_sha256(
                path,
                trusted_hash.ok_or("missing trusted F3 SHA-256")?
            )?;
            println!("F3_SHA256_VERIFIED canonical_t5_bytes={}", restored.len());
            Ok(())
        }
        "eval-f3-sha256" => {
            let restored = read_explicit_f3_sha256(
                path,
                trusted_hash.ok_or("missing trusted F3 SHA-256")?
            )?;
            let result = eval_t5_bytes(&restored)?;
            for output in result.output {
                println!("{output}");
            }
            println!("{}", result.value);
            Ok(())
        }

        "open-f3" => {
            let canonical_t5 = read_explicit_f3(path)?;
            let words = decode_canonical_t5_words(&canonical_t5)
                .map_err(|e| format!("SENS canonical reader after F3: {e}"))?;
            println!("{}", sens::render_ternary_words_spaced(&words));
            Ok(())
        }
        "decode-f3" => {
            let canonical_t5 = read_explicit_f3(path)?;
            let words = decode_canonical_t5_words(&canonical_t5)
                .map_err(|e| format!("canonical words after F3: {e}"))?;
            print!("{}", sens::render_ternary_words_vertical(&words));
            Ok(())
        }
        "eval-f3" => {
            // Never execute on opening; explicit eval only, bare pure session.
            let canonical_t5 = read_explicit_f3(path)?;
            let result = eval_t5_bytes(&canonical_t5)?;
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
mod e1_cli_mechanism_tests {
    use super::*;

    #[test]
    fn explicit_e1_cli_uses_exact_native_sens_semantic_verdict() {
        let positive = include_bytes!("../../../../tests/fixtures/semantic/exact-d3-logic-selftest.sens");
        let mutant = include_bytes!("../../../../tests/fixtures/semantic/exact-d3-logic-mutant.sens");
        for source in [positive.as_slice(), mutant.as_slice()] {
            let packed = encode_e1_from_t5(source).expect("T5->E1 physical encoding");
            let mut original = sens::Session::default();
            let mut e1_session = sens::Session::default();
            let from_t5 = sens::eval_t5_program(source, &mut original)
                .expect("SENS native exact source verdict");
            let from_e1 = sens::eval_e1_program(&packed, &mut e1_session)
                .expect("SENS native verdict after E1 bytes");
            assert_eq!(from_t5.value.as_predicate_bit(),
                       from_e1.value.as_predicate_bit());
            assert_eq!(from_t5.output, from_e1.output);
            let mut damaged = packed;
            *damaged.last_mut().expect("CRC suffix") ^= 1;
            assert!(matches!(
                sens::eval_e1_program(&damaged, &mut sens::Session::default()),
                Err(sens::E1ExecutionError::Transport(
                    sens::universal_frame3::Frame3Error::Integrity
                ))
            ), "CRC corruption must be rejected before evaluator");
        }
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
    fn original_tiny_f3_requires_explicit_route_and_preserves_quote_execution() {
        let bytes = [0xf3, 0x40, 0x60];
        let canonical = sens::frame3_small::decode_explicit_small_f3(&bytes).unwrap();
        let t5 = include_bytes!("../../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");
        assert_eq!(&canonical, t5);
        let direct = eval_t5_bytes(t5).unwrap();
        let framed = eval_t5_bytes(&canonical).unwrap();
        assert_eq!(direct.value, framed.value);
        assert_eq!(direct.output, framed.output);
        assert!(sens::decode_ternary_program(&bytes).is_err());
        assert!(USAGE.contains("eval-f3 path.senc"));
        assert!(USAGE.contains("encode-f3 path.sens"));
    }

    #[test]
    fn sha256_integrity_verdict_requires_trusted_exact_physical_f3_bytes() {
        let good = [0xf3, 0x40, 0x60];
        let trusted = "19b495e17cd0522c1af4863704b92751df5e5769ee0bfe3c9844aedbc0a57406";
        assert_eq!(
            sens::sha256_source(&good)
                .iter()
                .map(|byte| format!("{byte:02x}"))
                .collect::<String>(),
            trusted
        );
        // The digest attests to the actual physical carrier, not decoded T5.
        assert_ne!(sens::sha256_source(&good), sens::sha256_source(&[0x63, 0x89, 0x06, 0xa1]));
        assert!(USAGE.contains("eval-f3-sha256 path.senc SHA256"));
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

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_read_only_t5_open_and_decode_preserve_words_and_reject_invalid_d2() {
        let carrier = include_bytes!(
            "../../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens"
        );
        let words = decode_canonical_t5_words(carrier)
            .expect("Zig physical T5 -> current SENS D2 reader");
        assert_eq!(sens::render_ternary_words_spaced(&words), "10 001 00 000 01");
        assert_eq!(
            sens::render_ternary_words_vertical(&words),
            "10\n001\n00\n000\n01\n"
        );
        // Test-only reference: not a runtime fallback in the feature build.
        assert_eq!(words, sens::decode_ternary_program(carrier).unwrap());

        let multi = include_bytes!(
            "../../../../tests/fixtures/migration-multiform-cohort-main/two-forms.sens"
        );
        assert_eq!(
            decode_canonical_t5_words(multi).unwrap(),
            sens::decode_ternary_program(multi).unwrap()
        );

        // Physical validity must not automatically imply a valid D2 program.
        let lone_close = sens::encode_ternary_words(&[
            sens::parse_binary_source_words("01").unwrap()[0].word,
        ]).unwrap();
        let err = decode_canonical_t5_words(&lone_close).expect_err("invalid D2 close");
        assert!(err.contains("SENS canonical D2 rejected"), "{err}");
        for invalid in [&[0xf3][..], &[0xf2][..], &[0x00, 0x00][..]] {
            assert!(decode_canonical_t5_words(invalid).is_err(),
                "malformed T5 must not reach SENS D2");
        }
        // A simple source audit prevents a regression to the Rust physical
        // T5 decoder in the human-facing open/decode commands.
        let source = include_str!("sens-trit.rs");
        for marker in ["\"open\" | \"view\" => {", "\"decode\" => {",
                       "\"open-f3\" => {", "\"decode-f3\" => {"] {
            let start = source.find(marker).expect("read-only route exists");
            let body = &source[start..];
            let end = body.find("\n        }").expect("route ends");
            let route = &body[..end];
            assert!(route.contains("decode_canonical_t5_words"),
                "read-only route bypasses Zig ingress: {marker}");
            assert!(!route.contains("sens::decode_ternary_program("),
                "read-only route uses Rust physical decode: {marker}");
            assert!(!route.contains("sens::open_ternary_program("),
                "read-only route uses Rust physical open: {marker}");
        }
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_ingress_be3_preserves_exact_width_and_rejects_invalid_transport() {
        let carrier = include_bytes!(
            "../../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens"
        );
        let actual = zig_transport::decode_t5_words(carrier)
            .expect("Zig physical ingress on admitted binary program");
        let independent_reference = sens::decode_ternary_words(carrier)
            .expect("test-only Rust reference, not production fallback");
        assert_eq!(actual, independent_reference);
        assert_eq!(actual.iter().map(|w| w.width()).collect::<Vec<_>>(),
                   vec![2, 3, 2, 3, 2]);
        let program = sens::PhysicalT5Program::from_exact_words(&actual)
            .expect("SENS-owned D2 reading, not Zig semantic verdict");
        assert_eq!(program.form_count(), 1);
        assert_eq!(zig_transport::decode_t5_words(&[0xa1])
            .unwrap()[0].width(), 1);
        assert_eq!(zig_transport::decode_t5_words(&[0x35])
            .unwrap()[0].width(), 2);
        assert!(zig_transport::decode_t5_words(&[0xf3]).is_err());
        assert!(zig_transport::decode_t5_words(&[0xf2]).is_err());
        assert!(zig_transport::decode_t5_words(&[0, 0]).is_err());
    }

    #[test]
    fn physical_eval_path_uses_packed_words_not_visible_text() {
        let source = include_str!("sens-trit.rs");
        let start = source.find("fn eval_t5_bytes_core4(").expect("physical eval route");
        let end = source[start..].find("\n}\n").expect("route body") + start + 3;
        let route = &source[start..end];
        #[cfg(feature = "zig-transport")]
        {
            let zig_branch = route.split("#[cfg(not(feature = \"zig-transport\"))]")
                .next().expect("Zig ingress block");
            assert!(zig_branch.contains("zig_transport::decode_t5_words(bytes)"));
            assert!(zig_branch.contains("sens::PhysicalT5Program::from_exact_words(&words)"));
            assert!(!zig_branch.contains("sens::PhysicalT5Program::decode(bytes)"));
        }
        #[cfg(not(feature = "zig-transport"))]
        assert!(route.contains("sens::PhysicalT5Program::decode(bytes)"));
        assert!(route.contains("program.execute(&mut session)"));
        assert!(!route.contains("sens::pack_binary_source_words("));
        assert!(!route.contains("sens::parse_canonical_packed_words("));
        assert!(!route.contains("sens::open_ternary_program(bytes)"));
        assert!(!route.contains("sens::parse_canonical_binary(&visible)"));
    }
}
