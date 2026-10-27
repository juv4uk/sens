//! T5M file codec для ДВІЙКОВОЇ SENS: трит 2 — внутрішня межа, не
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
    "usage: sens-trit (backend | encode path.bits | verify-view path.sens | encode-d7-uk path.txt | decode-d7-uk path.sens | open path.sens | view path.sens | decode path.sens | explain path.sens | eval path.sens | eval-core4 path.sens | encode-e1 path.sens | eval-e1 path.e1 | verify path.bits | encode-f3 path.sens | open-f3 path.senc | decode-f3 path.senc | eval-f3 path.senc | verify-f3-sha256 path.senc SHA256 | eval-f3-sha256 path.senc SHA256)\n       sens-trit path.sens  # open only; never execute implicitly";

// Compiled only in the official Zig-transport build. Rust validates SENS
// program syntax; Zig owns all physical wire bytes for these commands.
#[cfg(feature = "zig-transport")]
use sens_cli::zig_transport;

fn decode_f3_carrier(bytes: &[u8]) -> Result<Vec<u8>, String> {
    #[cfg(feature = "zig-transport")]
    {
        let restored = zig_transport::decode_f3(bytes)?;
        let words = zig_transport::decode_t5m_words(&restored)?;
        let parsed = sens::PhysicalT5Program::from_exact_words(&words)
            .map_err(|e| format!("Zig F3C restored inadmissible SENS program: {e:?}"))?;
        if parsed.form_count() != 1 {
            return Err("Zig F3C restored more than one root".into());
        }
        Ok(restored)
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        let _ = bytes;
        Err("F3C physical decode requires Zig; no Rust fallback".into())
    }
}

fn encode_f3_carrier(bytes: &[u8]) -> Result<Option<Vec<u8>>, String> {
    #[cfg(feature = "zig-transport")]
    {
        let words = zig_transport::decode_t5m_words(bytes)?;
        let parsed = sens::PhysicalT5Program::from_exact_words(&words)
            .map_err(|e| format!("SENS input is not an executable canonical T5M program: {e:?}"))?;
        if parsed.form_count() != 1 || bytes.len() > 16 {
            return Ok(None);
        }
        zig_transport::encode_f3(bytes)
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        let _ = bytes;
        Err("F3C physical encode requires Zig; no Rust fallback".into())
    }
}

fn sibling_sens(path: &Path) -> Result<std::path::PathBuf, String> {
    // Exact-bit source is .bits. Historical test inputs may still use .lisp;
    // both must retain the same exact-width D2 words, not host Lisp semantics.
    match path.extension().and_then(|ext| ext.to_str()) {
        Some("bits" | "lisp") => Ok(path.with_extension("sens")),
        _ => Err("expected .bits exact-word or legacy .lisp companion path".into()),
    }
}

#[cfg(test)]
#[test]
fn exact_bit_view_maps_to_its_existing_sens_physical_companion() {
    let bits = Path::new("tests/semantic/x86-lowering-d1-law.bits");
    let legacy = Path::new("tests/fixtures/migration-quote-cohort/quote-legacy.lisp");
    assert_eq!(
        sibling_sens(bits).unwrap().as_path(),
        Path::new("tests/semantic/x86-lowering-d1-law.sens")
    );
    assert_eq!(
        sibling_sens(legacy).unwrap().as_path(),
        Path::new("tests/fixtures/migration-quote-cohort/quote-legacy.sens")
    );
    assert!(sibling_sens(Path::new("fake.txt")).is_err());
    assert!(sibling_sens(Path::new("unnamed")).is_err());
}

/// Physical T5M is decoded in Zig for normal CLI builds. Structural D2
/// admission remains the SAME SENS canonical word reader, with no visible
/// source reconstruction or implicit execution in read-only commands.
#[cfg_attr(not(feature = "zig-transport"), allow(dead_code))]
fn decode_canonical_t5m_words(bytes: &[u8]) -> Result<Vec<sens::BinarySourceWord>, String> {
    #[cfg(not(feature = "zig-transport"))]
    {
        let _ = bytes;
        Err("RUST_ZIG_ONLY: T5M read requires the Zig corridor; no Rust fallback".into())
    }
    #[cfg(feature = "zig-transport")]
    {
        let words = zig_transport::decode_t5m_words(bytes)?;
        sens::parse_canonical_word_sequence(&words)
            .map_err(|e| format!("SENS canonical D2 rejected: {e}"))?;
        Ok(words)
    }
}

#[cfg(all(test, feature = "zig-transport"))]
fn eval_t5m_fixture(bytes: &[u8]) -> Result<sens::EvalResult, String> {
    let words = zig_transport::decode_t5m_words(bytes)?;
    let program = sens::PhysicalT5Program::from_exact_words(&words)
        .map_err(|e| format!("canonical SENS D2/admission rejected: {e}"))?;
    program
        .execute(&mut sens::Session::default())
        .map_err(|e| format!("current SENS evaluator rejected: {e}"))
}

fn render_exact_t5m_words(bytes: &[u8], separator: &str) -> Result<String, String> {
    #[cfg(not(feature = "zig-transport"))]
    {
        let _ = (bytes, separator);
        return Err(
            "RUST_ZIG_ONLY: T5M rendering requires the Zig corridor; no Rust fallback".into(),
        );
    }
    #[cfg(feature = "zig-transport")]
    {
        let words = zig_transport::decode_t5m_exact_words(bytes)?;
        Ok(words
            .into_iter()
            .map(|word| {
                word.bits
                    .into_iter()
                    .map(|bit| if bit == 0 { '0' } else { '1' })
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join(separator))
    }
}

/// Механічне обернення фізичного перегляду без семантичних припущень.
/// Довільні T5M-ширини не пропускаємо через обмежений source fast path.
#[cfg(feature = "zig-transport")]
fn verify_exact_t5m_view(physical: &[u8], view: &[u8]) -> Result<(), String> {
    let canonical = format!("{}\n", render_exact_t5m_words(physical, " ")?);
    if view != canonical.as_bytes() {
        return Err(
            "T5M_VIEW_NOT_CANONICAL: expected one space between exact words and one final LF"
                .into(),
        );
    }
    let exact = zig_transport::decode_t5m_exact_words(physical)?;
    if zig_transport::encode_t5m_exact_words(&exact)? != physical {
        return Err("T5M_VIEW_PHYSICAL_ROUNDTRIP_MISMATCH: Zig did not restore exact bytes".into());
    }
    Ok(())
}

#[cfg(all(test, feature = "zig-transport"))]
#[test]
fn t5m_view_inverse_preserves_d24_and_rejects_noncanonical_view() {
    // Один фізичний потік перевіряє всі ширини D1–D10 і числові D24+:
    // неоднакова довжина слів не повинна стирати доменні межі.
    // Це виключно Zig/T5M транспорт, не host-реалізація законів SENS.
    let words = (1usize..=10)
        .chain([24, 48, 96])
        .map(|width| {
            let bits = (0..width)
                .map(|index| ((index + width) % 2) as u8)
                .collect();
            zig_transport::ExactT5MWord::new(width, bits).unwrap()
        })
        .collect::<Vec<_>>();
    let physical = zig_transport::encode_t5m_exact_words(&words).unwrap();
    let restored = zig_transport::decode_t5m_exact_words(&physical).unwrap();
    assert_eq!(
        restored, words,
        "Zig T5M змінив точні біти або ширини D1–D10/D24+"
    );

    let canonical_view = format!(
        "{}\n",
        words
            .iter()
            .map(|word| {
                word.bits()
                    .iter()
                    .map(|&bit| if bit == 0 { '0' } else { '1' })
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join(" ")
    );
    verify_exact_t5m_view(&physical, canonical_view.as_bytes())
        .expect("Zig відновлює рівно ті самі слова й канонічний перегляд");

    // Негативи не змінюють фізичний носій: жодного мовчазного
    // прийняття обрізаного слова, підміненого біта чи зайвого пробілу.
    let mut changed_bit = canonical_view.as_bytes().to_vec();
    changed_bit[0] = if changed_bit[0] == b'0' { b'1' } else { b'0' };
    assert!(verify_exact_t5m_view(&physical, &changed_bit).is_err());

    let mut shortened = canonical_view.as_bytes().to_vec();
    shortened.remove(shortened.len() - 2); // біт перед кінцевим LF
    assert!(verify_exact_t5m_view(&physical, &shortened).is_err());
    assert!(verify_exact_t5m_view(&physical, canonical_view.trim_end().as_bytes()).is_err());
    assert!(
        verify_exact_t5m_view(&physical, canonical_view.replace(' ', "  ").as_bytes()).is_err()
    );

    // Контроль зі схожими бітами, але РІЗНИМИ ідентичностями:
    // D1:0 («ні») не є структурним D3:000 («()»).
    // Zig лише відновлює фізичні межі; тлумачення належить SENS.
    let distinct_domains = vec![
        zig_transport::ExactT5MWord::new(1, vec![0]).unwrap(),
        zig_transport::ExactT5MWord::new(3, vec![0, 0, 0]).unwrap(),
    ];
    let exact_carrier = zig_transport::encode_t5m_exact_words(&distinct_domains).unwrap();
    assert_eq!(
        zig_transport::decode_t5m_exact_words(&exact_carrier).unwrap(),
        distinct_domains,
        "D1:0 та D3:000 мусять зберігати окремі точні ширини"
    );
    verify_exact_t5m_view(&exact_carrier, b"0 000\n").unwrap();
    assert!(
        verify_exact_t5m_view(&exact_carrier, b"000 0\n").is_err(),
        "перестановка доменних слів не є оборотним переглядом"
    );
    assert!(
        verify_exact_t5m_view(&exact_carrier, b"0000\n").is_err(),
        "злиття різних доменних слів заборонено"
    );
}

/// SENS owns exact source words and D2 admission. The host does not create
/// physical T5M bytes; it forwards admitted width+bits to Zig ABI v2.
#[cfg(feature = "zig-transport")]
fn admitted_source_words(source: &str) -> Result<Vec<sens::BinarySourceWord>, String> {
    let tokens = sens::parse_binary_source_words(source)
        .map_err(|e| format!("SENS exact binary source rejected: {}", e.render(source)))?;
    if tokens.is_empty() {
        return Err("SENS exact binary source rejected: empty program".into());
    }
    let words = tokens
        .into_iter()
        .map(|token| token.word)
        .collect::<Vec<_>>();
    sens::parse_canonical_word_sequence(&words)
        .map_err(|e| format!("SENS canonical D2 rejected: {e}"))?;
    Ok(words)
}

fn read_sens(path: &Path) -> Result<Vec<u8>, String> {
    #[cfg(not(feature = "zig-transport"))]
    {
        let _ = path;
        return Err("RUST_ZIG_ONLY: .sens read requires the Zig corridor; no Rust fallback".into());
    }
    #[cfg(feature = "zig-transport")]
    {
        if path.extension().and_then(|ext| ext.to_str()) != Some("sens") {
            return Err("expected a physical .sens file".into());
        }
        let bytes = fs::read(path).map_err(|e| format!("read .sens: {e}"))?;
        zig_transport::validate_t5m(&bytes)?;
        Ok(bytes)
    }
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
fn encode_e1_from_t5m(physical_t5: &[u8]) -> Result<Vec<u8>, String> {
    #[cfg(not(feature = "zig-transport"))]
    {
        // Fail BEFORE decoding physical bytes: there is no Rust transport
        // bypass, even if a caller asks for the explicit E1 carrier.
        let _ = physical_t5;
        Err("E1 physical export requires Zig; no Rust fallback".into())
    }
    #[cfg(feature = "zig-transport")]
    {
        // Zig T5M ingress -> SENS-owned D2 admission -> Zig E1 egress.
        let words = decode_canonical_t5m_words(physical_t5)
            .map_err(|e| format!("SENS canonical T5M/D2 rejected: {e}"))?;
        zig_transport::encode_e1_direct(&words)
    }
}

/// Explicit E1 physical ingress: Zig canonical E1 -> exact words ->
/// SENS-owned D2 admission and execution. No Rust E1 codec fallback.
fn eval_e1_bytes(bytes: &[u8]) -> Result<sens::EvalResult, String> {
    #[cfg(not(feature = "zig-transport"))]
    {
        let _ = bytes;
        Err("E1 physical execution requires Zig; no Rust fallback".into())
    }
    #[cfg(feature = "zig-transport")]
    {
        let words = zig_transport::decode_e1_words(bytes)?;
        let program = sens::PhysicalT5Program::from_exact_words(&words)
            .map_err(|e| format!("E1 -> SENS canonical D2 rejected: {e}"))?;
        let mut session = sens::Session::default();
        program
            .execute(&mut session)
            .map_err(|e| format!("E1 -> current SENS evaluator rejected: {e}"))
    }
}

fn read_explicit_f3(path: &Path) -> Result<Vec<u8>, String> {
    if path.extension().and_then(|ext| ext.to_str()) != Some("senc") {
        return Err("explicit F3 command requires a physical .senc file".into());
    }
    let framed = fs::read(path).map_err(|e| format!("read explicit F3 .senc: {e}"))?;
    // The bounded F3 decoder restores physically canonical T5M; all SENS
    // parsing and execution stays in the same production D2/T5M pipeline.
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
    if expected_hex.len() != 64
        || !expected_hex
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
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
    let mismatch = actual
        .iter()
        .zip(expected.iter())
        .fold(0u8, |acc, (a, b)| acc | (a ^ b));
    if mismatch != 0 {
        return Err("F3 SHA-256 mismatch: no decoding or execution permitted".into());
    }
    decode_f3_carrier(&bytes)
        .map_err(|e| format!("SHA-256 verified but F3 canonical decode rejected: {e}"))
}

fn write_explicit_small_f3(path: &Path) -> Result<(), String> {
    // Operator-requested only: never change the normal T5M .sens source.
    let original = read_sens(path)?;
    let framed = encode_f3_carrier(&original)?
        .ok_or("this .sens program is not a smaller valid original F3 file")?;
    let dest = path.with_extension("senc");
    let mut out = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(&dest)
        .map_err(|e| format!("create-new .senc: {e}"))?;
    out.write_all(&framed)
        .map_err(|e| format!("write .senc: {e}"))?;
    out.sync_all().map_err(|e| format!("sync .senc: {e}"))?;
    if fs::read(&dest).map_err(|e| format!("read-back .senc: {e}"))? != framed
        || read_explicit_f3(&dest)? != original
    {
        return Err("physical tiny F3 write did not verify against input T5M bytes".into());
    }
    println!(
        "{} F3 {}B <- T5M {}B; source unchanged",
        dest.display(),
        framed.len(),
        original.len()
    );
    Ok(())
}

fn verify_companion(source: &str, binary: &[u8]) -> Result<(), String> {
    #[cfg(not(feature = "zig-transport"))]
    {
        let _ = (source, binary);
        return Err("RUST_ZIG_ONLY: companion verification requires Zig; no Rust fallback".into());
    }
    #[cfg(feature = "zig-transport")]
    {
        // SENS supplies the admitted exact-width words; Zig owns their physical bytes.
        let expected_words = admitted_source_words(source)?;
        let decoded = decode_canonical_t5m_words(binary)
            .map_err(|e| format!("invalid .sens transport or grammar: {e}"))?;
        if decoded != expected_words {
            return Err("paired .lisp/.sens differs in exact domain words".into());
        }
        zig_transport::verify_t5m_encoding(&expected_words, binary)
            .map_err(|e| format!("Zig physical companion replay rejected: {e}"))?;
        let semantic_bits = decoded
            .iter()
            .try_fold(0usize, |n, word| n.checked_add(word.width()))
            .ok_or("SENS physical accounting length overflow")?;
        let encoded_trits = semantic_bits
            .checked_add(decoded.len() - 1)
            .ok_or("SENS physical accounting separator overflow")?;
        let physical_trits = binary
            .len()
            .checked_mul(5)
            .ok_or("SENS physical accounting carrier overflow")?;
        let trailing = physical_trits
            .checked_sub(encoded_trits)
            .ok_or("SENS physical accounting invalid carrier length")?;
        println!("VERIFIED {} domain words; binary SENS={} semantic bits; transport={} trits; physical={} bytes; trailing={} trits",
                 decoded.len(), semantic_bits, encoded_trits, binary.len(), trailing);
        Ok(())
    }
}

/// Run the explicitly requested SENS program on the current capability-free
/// evaluator. Transport identity, D2 structural parsing, then semantic eval
/// are independent gates; success does not prove that an old Lisp source
/// has the same behavior or that a D24+/host effect is admitted.
fn eval_t5m_bytes(bytes: &[u8]) -> Result<sens::EvalResult, String> {
    eval_t5m_bytes_core4(bytes, false)
}

/// An EXPLICIT opt-in Core4 bootstrap for programs that need language-owned
/// D4/D5 closures such as LIST/APPEND. Bare eval remains capability-free and
/// unchanged; loading a library is mechanism availability, NOT a new resident.
fn eval_t5m_bytes_core4(bytes: &[u8], bootstrap_core: bool) -> Result<sens::EvalResult, String> {
    #[cfg(not(feature = "zig-transport"))]
    {
        // The reference-only build may compare codec fixtures, but cannot
        // execute a physical program by bypassing the Zig turnstile.
        // Refuse before parsing, starting a session, or loading Core4.
        let _ = (bytes, bootstrap_core);
        Err("physical T5M execution requires Zig; no Rust fallback".into())
    }
    #[cfg(feature = "zig-transport")]
    {
        // Zig restores exact word widths; SENS maps only ratified D1–D10 and
        // D24+ identities, parses D2, and owns execution/bootstrap policy.
        let words = zig_transport::decode_t5m_exact_words(bytes)?
            .into_iter()
            .map(|word| sens::ExactDomainWord::from_physical_width_bits(word.width, &word.bits))
            .collect::<Result<Vec<_>, _>>()?;
        let program = sens::PhysicalT5Program::from_exact_domain_words_owned(words)
            .map_err(|e| format!("exact SENS domain admission rejected: {e}"))?;
        let mut session = sens::Session::default();
        if bootstrap_core {
            sens::load_core_library(&mut session)
                .map_err(|e| format!("explicit Core4 bootstrap rejected: {e:?}"))?;
        }
        program
            .execute(&mut session)
            .map_err(|e| format!("current SENS evaluator rejected: {e}"))
    }
}
/// Diagnose a physical packed T5M file without converting typed words to
/// textual source. Zig owns T5M bytes; SENS owns D2 structure and diagnostics.
/// Report virtual packed-word byte spans, NEVER pretend they are file offsets.
fn explain_t5m_bytes(bytes: &[u8]) -> Result<String, String> {
    // Keep physical failures separate from SENS D2 grammar diagnostics:
    // unlike open/decode, explain must see the words before D2 admission.
    #[cfg(not(feature = "zig-transport"))]
    {
        let _ = bytes;
        return Err("RUST_ZIG_ONLY: T5M diagnostics require Zig; no Rust fallback".into());
    }
    #[cfg(feature = "zig-transport")]
    {
        // Keep exact widths from Zig through SENS domain admission. Do not
        // project these words into the bounded source adapter; the exact route
        // preserves every admitted D1–24+ identity or numeric value.
        let words = zig_transport::decode_t5m_exact_words(bytes)
            .map_err(|e| format!("physical T5M transport rejected: {e}"))?;
        let exact = words
            .iter()
            .map(|word| {
                sens::ExactDomainWord::from_physical_width_bits(word.width, &word.bits)
                    .map_err(|error| format!("SENS exact-domain admission rejected: {error}"))
            })
            .collect::<Result<Vec<_>, _>>()?;
        let program =
            sens::PhysicalT5Program::from_exact_domain_words_owned(exact).map_err(|e| {
                format!(
                "D2 grammar rejected (exact domain words; virtual payload byte span {}..{}): {e}",
                e.span.start, e.span.end
            )
            })?;
        Ok(format!(
            "D2 syntax PASS; {} exact domain words; {} forms; semantic oracle NOT_VERIFIED",
            words.len(),
            program.form_count()
        ))
    }
}

/// Fail before file access, output creation or language bootstrap when Zig is
/// unavailable. A Rust-only build is not a second physical SENS backend.
fn require_zig_transport(command: &str) -> Result<(), String> {
    #[cfg(not(feature = "zig-transport"))]
    if command != "backend" {
        return Err(format!(
            "RUST_ZIG_ONLY: sens-trit {command} requires Zig; no Rust physical fallback"
        ));
    }
    let _ = command;
    Ok(())
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
        {
            (command.as_str(), path.as_str(), Some(expected.as_str()))
        }
        _ => return Err(USAGE.into()),
    };
    let path = Path::new(file);
    require_zig_transport(command)?;

    match command {
        "backend" => {
            #[cfg(feature = "zig-transport")]
            println!("transport=zig codec=T5M abi=2 semantic_authority=SENS");
            #[cfg(not(feature = "zig-transport"))]
            println!("transport=unavailable zig_required=true semantic_authority=SENS");
            Ok(())
        }
        "encode-d7-uk" => {
            // Physical T5M record; no D2 source grammar and NO execution.
            if path.extension().and_then(|ext| ext.to_str()) != Some("txt") {
                return Err("encode-d7-uk requires an explicit UTF-8 .txt source".into());
            }
            #[cfg(feature = "zig-transport")]
            let text = fs::read_to_string(path)
                .map_err(|e| format!("read UTF-8 D7 keyboard text: {e}"))?;
            #[cfg(feature = "zig-transport")]
            let bytes = {
                // The ratified D7 table maps glyphs to W7 data, not D2 code.
                let words = sens::encode_d7_uk_words(&text)
                    .map_err(|e| format!("D7 keyboard projection rejected: {e:?}"))?;
                zig_transport::encode_t5m_direct(&words)?
            };
            #[cfg(not(feature = "zig-transport"))]
            let bytes = Err::<Vec<u8>, String>(
                "RUST_ZIG_ONLY: D7 T5M encoding requires Zig; no Rust fallback".into(),
            )?;
            let output_path = path.with_extension("sens");
            let mut output = OpenOptions::new()
                .create_new(true)
                .write(true)
                .open(&output_path)
                .map_err(|e| format!("create T5 text record: {e}"))?;
            output
                .write_all(&bytes)
                .map_err(|e| format!("write D7 T5M text record: {e}"))?;
            println!("D7-T5M keyboard record: {} bytes", bytes.len());
            Ok(())
        }
        "decode-d7-uk" => {
            #[cfg(feature = "zig-transport")]
            let bytes = read_sens(path)?;
            #[cfg(feature = "zig-transport")]
            let text = {
                // Zig validates and decodes only physical T5M; SENS owns D7
                // glyph identity and explicitly rejects non-W7 data.
                let words = zig_transport::decode_t5m_words(&bytes)?;
                sens::decode_d7_uk_words(&words)
                    .map_err(|e| format!("D7 keyboard W7 projection rejected: {e:?}"))?
            };
            #[cfg(not(feature = "zig-transport"))]
            let text = Err::<String, String>(
                "RUST_ZIG_ONLY: D7 T5M decoding requires Zig; no Rust fallback".into(),
            )?;
            println!("{text}");
            Ok(())
        }
        "encode" => {
            let sens_path = sibling_sens(path)?;
            let projection = fs::read_to_string(path)
                .map_err(|e| format!("read binary source .bits/.lisp: {e}"))?;
            // SENS validates exact words and D2; Zig alone packs default T5M bytes.
            // No optional Rust physical encoder exists on this CLI route.
            #[cfg(feature = "zig-transport")]
            let bytes = zig_transport::encode_t5m_direct(&admitted_source_words(&projection)?)?;
            #[cfg(not(feature = "zig-transport"))]
            let bytes = Err::<Vec<u8>, String>(
                "RUST_ZIG_ONLY: .lisp projection encoding requires Zig; no Rust fallback".into(),
            )?;
            // Ніколи не перезаписувати наявний файл.
            let mut output = OpenOptions::new()
                .create_new(true)
                .write(true)
                .open(&sens_path)
                .map_err(|e| format!("create .sens: {e}"))?;
            output
                .write_all(&bytes)
                .map_err(|e| format!("write .sens: {e}"))?;
            verify_companion(&projection, &bytes)
        }
        "open" | "view" => {
            let bytes = read_sens(path)?;
            // Physical inspection retains every T5M word's exact width and
            // bits; neither width nor this projection grants D1–24+ identity
            // or callability.
            let human = render_exact_t5m_words(&bytes, " ")?;
            println!("{human}");
            Ok(())
        }
        "verify-view" => {
            let bytes = read_sens(path)?;
            #[cfg(feature = "zig-transport")]
            {
                let view_path = path.with_extension("");
                let view = fs::read(&view_path)
                    .map_err(|e| format!("read T5M exact-bit view {}: {e}", view_path.display()))?;
                verify_exact_t5m_view(&bytes, &view)?;
                println!(
                    "T5M_VIEW_ROUNDTRIP_PASS file={} physical=ZIG_VERIFIED semantic=NOT_CERTIFIED",
                    path.display()
                );
                Ok(())
            }
            #[cfg(not(feature = "zig-transport"))]
            {
                let _ = bytes;
                Err("T5M view inversion requires Zig; no Rust fallback".into())
            }
        }
        "decode" => {
            let bytes = read_sens(path)?;
            let human = render_exact_t5m_words(&bytes, "\n")?;
            print!("{human}");
            Ok(())
        }
        "explain" => {
            // Independent physical T5M, then the SAME canonical D2 parser.
            // Unlike open, print a word-coordinate error on invalid grammar;
            // unlike eval, never run any expression or grant capabilities.
            let bytes = read_sens(path)?;
            println!("{}", explain_t5m_bytes(&bytes)?);
            Ok(())
        }
        "eval" | "eval-core4" => {
            // Both require explicit execution. Only eval-core4 additionally
            // loads the existing language-owned Core4 module on request.
            // Neither open nor bare eval may silently acquire mechanisms.
            let bytes = read_sens(path)?;
            let result = if command == "eval-core4" {
                eval_t5m_bytes_core4(&bytes, true)?
            } else {
                eval_t5m_bytes(&bytes)?
            };
            for output in result.output {
                println!("{output}");
            }
            println!("{}", result.value);
            Ok(())
        }
        "encode-e1" => {
            let bytes = read_sens(path)?;
            let e1 = encode_e1_from_t5m(&bytes)?;
            // A new, explicit physical carrier only; never replace the .sens.
            let target = path.with_extension("e1");
            let mut output = OpenOptions::new()
                .create_new(true)
                .write(true)
                .open(&target)
                .map_err(|e| format!("create explicit E1 (will not overwrite): {e}"))?;
            output
                .write_all(&e1)
                .map_err(|e| format!("write E1: {e}"))?;
            println!(
                "E1_PHYSICAL_ENCODED bytes={} semantic_authority=SENS",
                e1.len()
            );
            Ok(())
        }
        "eval-e1" => {
            // Explicit SENS execution only: CRC/E1 decoding followed by the
            // SAME ratified exact-domain admission/evaluator used by T5.
            let e1 = read_explicit_e1(path)?;
            let result = eval_e1_bytes(&e1)?;
            for output in result.output {
                println!("{output}");
            }
            println!("{}", result.value);
            Ok(())
        }
        "encode-f3" => write_explicit_small_f3(path),
        "verify-f3-sha256" => {
            let restored =
                read_explicit_f3_sha256(path, trusted_hash.ok_or("missing trusted F3 SHA-256")?)?;
            println!("F3_SHA256_VERIFIED canonical_t5_bytes={}", restored.len());
            Ok(())
        }
        "eval-f3-sha256" => {
            let restored =
                read_explicit_f3_sha256(path, trusted_hash.ok_or("missing trusted F3 SHA-256")?)?;
            let result = eval_t5m_bytes(&restored)?;
            for output in result.output {
                println!("{output}");
            }
            println!("{}", result.value);
            Ok(())
        }

        "open-f3" => {
            let canonical_t5 = read_explicit_f3(path)?;
            println!("{}", render_exact_t5m_words(&canonical_t5, " ")?);
            Ok(())
        }
        "decode-f3" => {
            let canonical_t5 = read_explicit_f3(path)?;
            print!("{}", render_exact_t5m_words(&canonical_t5, "\n")?);
            Ok(())
        }
        "eval-f3" => {
            // Never execute on opening; explicit eval only, bare pure session.
            let canonical_t5 = read_explicit_f3(path)?;
            let result = eval_t5m_bytes(&canonical_t5)?;
            for output in result.output {
                println!("{output}");
            }
            println!("{}", result.value);
            Ok(())
        }
        "verify" => {
            let sens_path = sibling_sens(path)?;
            let projection = fs::read_to_string(path)
                .map_err(|e| format!("read binary source .bits/.lisp: {e}"))?;
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
fn zig_test_fixture(name: &'static str) -> &'static [u8] {
    // Tests are host-side consumers, not compile-time owners of SENS bytes.
    // Resolve only these four tracked fixtures; arbitrary paths are rejected.
    use std::sync::OnceLock;
    static QUOTE: OnceLock<Vec<u8>> = OnceLock::new();
    static SELFTEST: OnceLock<Vec<u8>> = OnceLock::new();
    static MUTANT: OnceLock<Vec<u8>> = OnceLock::new();
    static MULTIFORM: OnceLock<Vec<u8>> = OnceLock::new();
    let slot = match name {
        "migration-quote-cohort-main/quote-legacy.sens" => &QUOTE,
        "semantic/exact-d3-logic-selftest.sens" => &SELFTEST,
        "semantic/exact-d3-logic-mutant.sens" => &MUTANT,
        "migration-multiform-cohort-main/two-forms.sens" => &MULTIFORM,
        _ => panic!("unapproved SENS test fixture: {name}"),
    };
    slot.get_or_init(|| {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../../tests/fixtures")
            .join(name);
        let bytes =
            std::fs::read(&path).unwrap_or_else(|e| panic!("SENS fixture {}: {e}", path.display()));
        // These tracked vectors are historical T5 fixtures. Convert their
        // exact words to the current T5M wire in memory; never rewrite them.
        #[cfg(feature = "zig-transport")]
        {
            let legacy_words = zig_transport::decode_legacy_t5_words(&bytes)
                .unwrap_or_else(|e| panic!("legacy T5 fixture decode {name}: {e:?}"));
            let t5m = zig_transport::encode_t5m_direct(&legacy_words)
                .unwrap_or_else(|e| panic!("T5M fixture carry {name}: {e}"));
            let restored = zig_transport::decode_t5m_words(&t5m)
                .unwrap_or_else(|e| panic!("T5M fixture read {name}: {e}"));
            assert_eq!(restored, legacy_words, "fixture word identity {name}");
            t5m
        }
        #[cfg(not(feature = "zig-transport"))]
        bytes
    })
    .as_slice()
}

#[cfg(test)]
mod rust_zig_only_cutover_tests {
    use super::*;

    #[test]
    fn production_sens_trit_never_calls_rust_physical_codecs() {
        // Test the entire production section, not just the feature branch.
        let source = include_str!("sens-trit.rs");
        let start = source
            .find("fn require_zig_transport(")
            .expect("physical CLI guard");
        let runtime = source[start..]
            .split("#[cfg(test)]")
            .next()
            .expect("production CLI section");
        for forbidden in [
            "sens::decode_ternary_words(",
            "sens::encode_binary_projection_ternary(",
            "sens::encode_d7_uk_t5(",
            "sens::decode_d7_uk_t5(",
            "transport=rust-reference",
        ] {
            assert!(
                !runtime.contains(forbidden),
                "Rust physical bypass: {forbidden}"
            );
        }
        assert!(runtime.contains("require_zig_transport(command)?"));
        assert!(runtime.contains("eval_t5m_bytes(&bytes)"));
        assert!(runtime
            .contains("zig_transport::encode_t5m_direct(&admitted_source_words(&projection)?)"));

        let fixture_start = source
            .find("fn zig_test_fixture(")
            .expect("fixture adapter");
        let fixture_adapter = source[fixture_start..]
            .split("#[cfg(test)]\nmod rust_zig_only_cutover_tests")
            .next()
            .expect("fixture adapter section");
        assert!(
            !fixture_adapter.contains("sens::decode_ternary_words(&bytes)"),
            "historical fixture transport must not use the Rust T5 codec"
        );
        assert!(fixture_adapter.contains("zig_transport::decode_legacy_t5_words(&bytes)"));
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn all_physical_cli_modes_fail_closed_without_zig() {
        for command in [
            "encode",
            "verify",
            "open",
            "view",
            "decode",
            "explain",
            "eval",
            "eval-core4",
            "encode-d7-uk",
            "decode-d7-uk",
            "encode-e1",
            "eval-e1",
            "encode-f3",
            "open-f3",
            "decode-f3",
            "eval-f3",
            "verify-f3-sha256",
            "eval-f3-sha256",
        ] {
            let error = require_zig_transport(command)
                .expect_err("Zig-less CLI must reject BEFORE accessing files");
            assert!(error.contains("RUST_ZIG_ONLY"), "{command}: {error}");
            assert!(error.contains("no Rust physical fallback"));
        }
        assert!(require_zig_transport("backend").is_ok());
        assert!(decode_canonical_t5m_words(&[0x63, 0x89, 0x06, 0xa1]).is_err());
        assert!(read_sens(Path::new("unreadable.sens")).is_err());
        assert!(verify_companion("10 001 00 000 01", &[0x63, 0x89, 0x06, 0xa1]).is_err());
        assert!(explain_t5m_bytes(&[0x63, 0x89, 0x06, 0xa1]).is_err());
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_transport_is_the_only_admitted_cli_mode() {
        for command in [
            "encode",
            "verify",
            "open",
            "eval",
            "encode-d7-uk",
            "decode-f3",
        ] {
            require_zig_transport(command).expect("Zig-enabled CLI admits physical commands");
        }
        let physical = zig_test_fixture("migration-quote-cohort-main/quote-legacy.sens");
        // Real physical fixture, restored by the linked Zig ABI (not a mock).
        let words =
            decode_canonical_t5m_words(physical).expect("Zig decode and SENS D2 acceptance");
        assert_eq!(
            words.iter().map(|word| word.width()).collect::<Vec<_>>(),
            vec![2, 3, 2, 3, 2]
        );
        let replay = zig_transport::encode_t5m_direct(&words)
            .expect("Zig egress preserves the original physical bytes");
        assert_eq!(replay.as_slice(), physical);
        assert!(decode_canonical_t5m_words(&[0xf3]).is_err());
    }
}

#[cfg(test)]
mod e1_cli_mechanism_tests {
    use super::*;

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn e1_export_cannot_bypass_missing_zig_corridor() {
        let physical = zig_test_fixture("migration-quote-cohort-main/quote-legacy.sens");
        let error = encode_e1_from_t5m(physical).expect_err("Zig is mandatory for E1 output");
        assert!(error.contains("no Rust fallback"));
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn e1_encoder_uses_zig_t5_ingress_then_sens_d2_without_rust_physical_bypass() {
        let physical = zig_test_fixture("migration-quote-cohort-main/quote-legacy.sens");
        let words = zig_transport::decode_t5m_words(physical)
            .expect("Zig mechanically restores exact D1-D9 words");
        let expected = sens::envelope_e1::encode(&words)
            .expect("existing E1 encoder, not another semantic law");
        assert_eq!(encode_e1_from_t5m(physical).unwrap(), expected);
        assert_eq!(
            words.iter().map(|word| word.width()).collect::<Vec<_>>(),
            vec![2, 3, 2, 3, 2]
        );

        // A physically valid T5M carrier may still violate SENS D2 structure.
        let lone_close_word = sens::parse_binary_source_words("01").unwrap()[0].word;
        let lone_close = zig_transport::encode_t5m_direct(&[lone_close_word]).unwrap();
        assert!(encode_e1_from_t5m(&lone_close)
            .unwrap_err()
            .contains("SENS canonical D2 rejected"));
        for invalid in [&[0xf3][..], &[0xf2][..], &[0x00, 0x00][..]] {
            assert!(
                encode_e1_from_t5m(invalid).is_err(),
                "malformed T5 must not produce an E1 carrier"
            );
        }

        // Guard precisely this production entry, excluding unrelated Rust
        // reference tests and explicitly selected non-Zig transport.
        let source = include_str!("sens-trit.rs");
        let start = source.find("fn encode_e1_from_t5m(").unwrap();
        let route = &source[start..];
        let route = &route[..route.find("\n}\n").unwrap()];
        assert!(route.contains("decode_canonical_t5m_words(physical_t5)"));
        assert!(!route.contains("sens::decode_ternary_program(physical_t5)"));
        assert!(!route.contains("sens::decode_ternary_words(physical_t5)"));
        assert!(route.contains("zig_transport::encode_e1_direct(&words)"));
        assert!(!route.contains("sens::envelope_e1::encode(&words)"));
    }

    #[cfg(feature = "zig-transport")]
    #[cfg(feature = "zig-transport")]
    #[test]
    fn e1_execution_uses_zig_physical_reader_then_native_sens_d2() {
        let positive = zig_test_fixture("semantic/exact-d3-logic-selftest.sens");
        let reference =
            eval_t5m_fixture(positive).expect("SENS owns semantics after T5M physical ingress");
        let e1 = encode_e1_from_t5m(positive).expect("Zig canonical E1 output");
        let actual = eval_e1_bytes(&e1).expect("Zig E1 ingress then SENS semantic evaluator");
        assert_eq!(
            actual.value.as_predicate_bit(),
            reference.value.as_predicate_bit()
        );
        assert_eq!(actual.output, reference.output);

        // A forged CRC result is not a semantic D1:NO or an allowed fallback.
        let mut damaged = e1.clone();
        *damaged.last_mut().expect("E1 CRC suffix") ^= 1;
        assert!(eval_e1_bytes(&damaged).is_err());

        let source = include_str!("sens-trit.rs");
        let start = source
            .find("fn eval_e1_bytes(")
            .expect("E1 executable ingress");
        let routine = &source[start..source[start..].find("\n}\n").unwrap() + start];
        assert!(routine.contains("zig_transport::decode_e1_words(bytes)"));
        assert!(routine.contains("sens::PhysicalT5Program::from_exact_words(&words)"));
        assert!(!routine.contains("sens::eval_e1_program("));
        let arm = source
            .find("\n        \"eval-e1\" => {\n")
            .expect("E1 command");
        let route = &source[arm..source[arm..].find("\n        \"encode-f3\" =>").unwrap() + arm];
        assert!(route.contains("eval_e1_bytes(&e1)?"));
        assert!(!route.contains("sens::eval_e1_program("));
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn e1_execution_refuses_rust_physical_decoder_without_zig() {
        let input = [0x53, 0x33, 1, 0, 0xc7, 0xca, 0x15, 0xd8];
        let error = eval_e1_bytes(&input).expect_err("without Zig E1 must not execute");
        assert!(error.contains("no Rust fallback"));
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn explicit_e1_cli_uses_exact_native_sens_semantic_verdict() {
        let positive = zig_test_fixture("semantic/exact-d3-logic-selftest.sens");
        let mutant = zig_test_fixture("semantic/exact-d3-logic-mutant.sens");
        for source in [positive, mutant] {
            let packed = encode_e1_from_t5m(source).expect("T5M->E1 physical encoding");
            let mut e1_session = sens::Session::default();
            let from_t5 = eval_t5m_fixture(source).expect("SENS native exact T5M source verdict");
            let from_e1 = sens::eval_e1_program(&packed, &mut e1_session)
                .expect("SENS native verdict after E1 bytes");
            assert_eq!(
                from_t5.value.as_predicate_bit(),
                from_e1.value.as_predicate_bit()
            );
            assert_eq!(from_t5.output, from_e1.output);
            let mut damaged = packed;
            *damaged.last_mut().expect("CRC suffix") ^= 1;
            assert!(
                matches!(
                    sens::eval_e1_program(&damaged, &mut sens::Session::default()),
                    Err(sens::E1ExecutionError::Transport(
                        sens::universal_frame3::Frame3Error::Integrity
                    ))
                ),
                "CRC corruption must be rejected before evaluator"
            );
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

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn f3c_physical_ingress_and_egress_require_zig_even_for_valid_bytes() {
        // No fallback to the Rust physical codec even for a previously valid
        // carrier. The host only delegates physical transport to Zig.
        let good_carrier = [0xf3, 0x40, 0x60];
        let good_t5 = zig_test_fixture("migration-quote-cohort-main/quote-legacy.sens");
        for carrier in [&good_carrier[..], &[0xf3u8][..]] {
            let err = decode_f3_carrier(carrier)
                .expect_err("Rust F3C decoding is not allowed without Zig");
            assert_eq!(err, "F3C physical decode requires Zig; no Rust fallback");
        }
        for carrier in [&good_t5[..], &[0xf3u8][..]] {
            let err = encode_f3_carrier(carrier)
                .expect_err("Rust F3C encoding is not allowed without Zig");
            assert_eq!(err, "F3C physical encode requires Zig; no Rust fallback");
        }
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn explicit_f3_codec_roundtrip_is_zig_owned() {
        let legacy_path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");
        let t5 = std::fs::read(legacy_path).unwrap();
        let carrier = encode_f3_carrier(&t5)
            .expect("Zig owns explicit F3C encoding")
            .expect("fixture fits the explicit compact carrier");
        let restored = decode_f3_carrier(&carrier).expect("Zig owns explicit F3C decoding");
        assert_eq!(restored, t5, "F3C must preserve the canonical T5M bytes");
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
        assert_ne!(
            sens::sha256_source(&good),
            sens::sha256_source(&[0x63, 0x89, 0x06, 0xa1])
        );
        assert!(USAGE.contains("eval-f3-sha256 path.senc SHA256"));
    }

    #[test]
    fn physical_quote_fixture_preserves_t5m_and_exact_d2_structure() {
        let bytes = zig_test_fixture("migration-quote-cohort-main/quote-legacy.sens");
        let words = zig_transport::decode_t5m_words(bytes).expect("canonical physical T5M");
        let visible = sens::render_binary_words_spaced(&words);
        assert_eq!(visible, "10 001 00 000 01");
        assert_eq!(zig_transport::encode_t5m_direct(&words).unwrap(), bytes);

        let forms = sens::parse_canonical_word_sequence(&words)
            .expect("typed T5M words reach the D2 reader without Rust repacking");
        assert_eq!(forms.len(), 1);
    }

    #[test]
    fn two_top_level_forms_share_one_physical_file_and_keep_d2_boundaries() {
        let bytes = zig_test_fixture("migration-multiform-cohort-main/two-forms.sens");
        let words = zig_transport::decode_t5m_words(bytes).expect("canonical physical T5M");
        let forms = sens::parse_canonical_word_sequence(&words)
            .expect("two exact D2 forms parse directly from typed T5M words");
        assert_eq!(forms.len(), 2);
        assert_eq!(zig_transport::encode_t5m_direct(&words).unwrap(), bytes);
    }

    #[test]
    fn physical_or_structural_corruption_fails_closed_before_execution() {
        assert!(zig_transport::decode_t5m_exact_words(&[0xf3]).is_err());
        assert!(zig_transport::decode_t5m_exact_words(&[0xf2]).is_err());
        let unbalanced_close = zig_transport::encode_t5m_direct(&[
            sens::parse_binary_source_words("01").unwrap()[0].word,
        ])
        .unwrap();
        let words = zig_transport::decode_t5m_words(&unbalanced_close).unwrap();
        assert!(sens::parse_canonical_word_sequence(&words).is_err());
    }

    #[test]
    fn explain_shows_canonical_d2_failure_without_creating_a_second_parser() {
        let words = sens::parse_binary_source_words("10 001").expect("physical words allowed");
        let typed = words
            .into_iter()
            .map(|token| token.word)
            .collect::<Vec<_>>();
        let trits = zig_transport::encode_t5m_direct(&typed).expect("physically packed T5M bytes");
        let err = explain_t5m_bytes(&trits).expect_err("unbalanced D2 syntax");
        assert!(err.contains("D2 grammar rejected"), "{err}");
        assert!(
            err.contains("exact domain words; virtual payload byte span"),
            "{err}"
        );
        assert!(!err.contains("D2 syntax PASS"), "{err}");
    }

    #[test]
    fn explain_distinguishes_bad_transport_from_bad_d2_grammar() {
        let bytes = zig_test_fixture("migration-quote-cohort-main/quote-legacy.sens");
        let receipt = explain_t5m_bytes(bytes).expect("known current D2 syntax");
        assert!(receipt.contains("D2 syntax PASS"), "{receipt}");
        assert!(
            receipt.contains("semantic oracle NOT_VERIFIED"),
            "{receipt}"
        );
        assert!(explain_t5m_bytes(&[0xf3])
            .expect_err("invalid base3 byte")
            .contains("physical T5M transport rejected"));
        let bad_d2_word = sens::parse_binary_source_words("01").unwrap()[0].word;
        let bad_d2 = zig_transport::encode_t5m_direct(&[bad_d2_word]).unwrap();
        assert!(explain_t5m_bytes(&bad_d2)
            .unwrap_err()
            .contains("D2 grammar rejected"));
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn explain_accepts_ratified_numeric_widths_through_exact_zig_ingress() {
        let exact = [24usize, 48, 96]
            .into_iter()
            .map(|width| {
                let mut bits = vec![0; width];
                bits[0] = 1;
                zig_transport::ExactT5MWord::new(width, bits).unwrap()
            })
            .collect::<Vec<_>>();
        let bytes = zig_transport::encode_t5m_exact_words(&exact).unwrap();

        let receipt = explain_t5m_bytes(&bytes).expect("D24+ exact words are valid SENS forms");
        assert!(receipt.contains("3 exact domain words"), "{receipt}");
        assert!(receipt.contains("3 forms"), "{receipt}");
        assert!(
            receipt.contains("semantic oracle NOT_VERIFIED"),
            "{receipt}"
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_verify_and_explain_share_physical_ingress_but_keep_d2_diagnostics() {
        let golden = zig_test_fixture("migration-quote-cohort-main/quote-legacy.sens");
        verify_companion("10 001 00 000 01", golden)
            .expect("Zig T5 physical decode and SENS D2 companion admission");
        assert!(explain_t5m_bytes(golden)
            .unwrap()
            .contains("D2 syntax PASS"));

        let bad_physical = verify_companion("10 001 00 000 01", &[0xf3])
            .expect_err("bad Zig physical byte must reject");
        assert!(
            bad_physical.contains("invalid .sens transport or grammar"),
            "{bad_physical}"
        );
        assert!(explain_t5m_bytes(&[0xf3])
            .unwrap_err()
            .contains("physical T5M transport rejected"));

        // Physically valid, structurally inadmissible: preserve the current
        // SENS D2 diagnostic rather than reporting a physical T5M failure.
        let lone_close_word = sens::parse_binary_source_words("01").unwrap()[0].word;
        let lone_close = zig_transport::encode_t5m_direct(&[lone_close_word]).unwrap();
        assert!(explain_t5m_bytes(&lone_close)
            .unwrap_err()
            .contains("D2 grammar rejected"));

        // Regression guard: the feature-default production helpers must not
        // silently fall back to Rust's physical T5M decoder.
        let source = include_str!("sens-trit.rs");
        let verify_start = source.find("fn verify_companion(").unwrap();
        let verify_end = source[verify_start..].find("\n}\n").unwrap() + verify_start + 3;
        let verify_body = &source[verify_start..verify_end];
        assert!(verify_body.contains("decode_canonical_t5m_words(binary)"));
        assert!(!verify_body.contains("sens::decode_ternary_program(binary)"));

        let explain_start = source.find("fn explain_t5m_bytes(").unwrap();
        let explain_end = source[explain_start..].find("\n}\n").unwrap() + explain_start + 3;
        let explain_body = &source[explain_start..explain_end];
        let feature_branch = explain_body
            .split("#[cfg(feature = \"zig-transport\")]")
            .nth(1)
            .expect("Zig-active explain route");
        assert!(feature_branch.contains("zig_transport::decode_t5m_exact_words(bytes)"));
        assert!(feature_branch.contains("sens::ExactDomainWord::from_physical_width_bits"));
        assert!(feature_branch
            .contains("sens::PhysicalT5Program::from_exact_domain_words_owned(exact)"));
        assert!(!feature_branch.contains("sens::decode_ternary_words(bytes)"));
        assert!(!feature_branch.contains("sens::parse_canonical_binary("));
        assert!(!feature_branch.contains("sens::render_ternary_words_vertical("));
        assert!(explain_body.contains("D2 grammar rejected"));
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_read_only_t5_open_and_decode_preserve_words_and_reject_invalid_d2() {
        let carrier = zig_test_fixture("migration-quote-cohort-main/quote-legacy.sens");
        let words = decode_canonical_t5m_words(carrier)
            .expect("Zig physical T5M -> current SENS D2 reader");
        assert_eq!(sens::render_binary_words_spaced(&words), "10 001 00 000 01");
        assert_eq!(words.len(), 5);
        assert_eq!(sens::render_binary_words_spaced(&words), "10 001 00 000 01");
        assert_eq!(zig_transport::encode_t5m_direct(&words).unwrap(), carrier);

        let multi = zig_test_fixture("migration-multiform-cohort-main/two-forms.sens");
        let multi_words = decode_canonical_t5m_words(multi).unwrap();
        let multi_program = sens::PhysicalT5Program::from_exact_words(&multi_words)
            .expect("T5M exact words parse through current SENS D2 reader");
        assert_eq!(multi_program.form_count(), 2);
        assert_eq!(
            zig_transport::encode_t5m_direct(&multi_words).unwrap(),
            multi
        );

        // Physical validity must not automatically imply a valid D2 program.
        let lone_close_word = sens::parse_binary_source_words("01").unwrap()[0].word;
        let lone_close = zig_transport::encode_t5m_direct(&[lone_close_word]).unwrap();
        let err = decode_canonical_t5m_words(&lone_close).expect_err("invalid D2 close");
        assert!(err.contains("SENS canonical D2 rejected"), "{err}");
        for invalid in [&[0xf3][..], &[0xf2][..], &[0x00, 0x00][..]] {
            assert!(
                decode_canonical_t5m_words(invalid).is_err(),
                "malformed T5 must not reach SENS D2"
            );
        }
        // A simple source audit prevents a regression to the Rust physical
        // T5M decoder in the human-facing open/decode commands.
        let source = include_str!("sens-trit.rs");
        for marker in [
            "\"open\" | \"view\" => {",
            "\"decode\" => {",
            "\"open-f3\" => {",
            "\"decode-f3\" => {",
        ] {
            let start = source.find(marker).expect("read-only route exists");
            let body = &source[start..];
            let end = body.find("\n        }").expect("route ends");
            let route = &body[..end];
            assert!(
                route.contains("decode_canonical_t5m_words"),
                "read-only route bypasses Zig ingress: {marker}"
            );
            assert!(
                !route.contains("sens::decode_ternary_program("),
                "read-only route uses Rust physical decode: {marker}"
            );
            assert!(
                !route.contains("sens::open_ternary_program("),
                "read-only route uses Rust physical open: {marker}"
            );
        }
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_encode_route_uses_t5m_by_default_without_rust_physical_decoder() {
        // SENS owns source parsing and D2 admission, Zig owns default T5M bytes.
        let projection = "10 001 00 000 01";
        let expected_wire = [0x63, 0x89, 0x06, 0xa1];
        let expected = sens::parse_binary_source_words(projection)
            .unwrap()
            .into_iter()
            .map(|token| token.word)
            .collect::<Vec<_>>();
        let actual =
            admitted_source_words(projection).expect("SENS-owned exact words and D2 admission");
        assert_eq!(actual, expected);
        assert_eq!(
            actual.iter().map(|w| w.width()).collect::<Vec<_>>(),
            [2, 3, 2, 3, 2]
        );
        let zig_bytes =
            zig_transport::encode_t5m_direct(&actual).expect("Zig sole default T5M encoder");
        assert_eq!(zig_bytes, [0x63, 0x89, 0x06, 0xa1]);
        assert_eq!(
            zig_bytes, expected_wire,
            "T5M default uses the canonical five-trits-per-byte wire"
        );
        assert_eq!(zig_transport::decode_t5m_words(&zig_bytes).unwrap(), actual);
        verify_companion(projection, &zig_bytes).expect("Zig replay + SENS D2");
        // A one-bit D2-close on its own cannot be published as a program.
        assert!(admitted_source_words("01")
            .unwrap_err()
            .contains("SENS canonical D2"));
        assert!(admitted_source_words("10 001").is_err());
        assert!(admitted_source_words("10 001 2").is_err());
        let mut mutant = zig_bytes.clone();
        mutant[0] ^= 1;
        assert!(verify_companion(projection, &mutant).is_err());

        // Fail closed before the Zig encoder can publish malformed bytes.
        for invalid in [&[0xf3][..], &[0xf2][..], &[0x00, 0x00][..]] {
            assert!(decode_canonical_t5m_words(invalid).is_err());
        }
        let lone_close_word = sens::parse_binary_source_words("01").unwrap()[0].word;
        let lone_close = zig_transport::encode_t5m_direct(&[lone_close_word]).unwrap();
        assert!(decode_canonical_t5m_words(&lone_close)
            .unwrap_err()
            .contains("SENS canonical D2 rejected"));

        // Scope the audit to the actual production encode command, excluding
        // intentional Rust reference-only tests and unrelated library code.
        let source = include_str!("sens-trit.rs");
        let start = source.find("\"encode\" => {").expect("CLI encode command");
        let block = &source[start..];
        let route = &block[..block.find("\n        }").expect("encode command closes")];
        let zig_branch = route
            .split("#[cfg(not(feature = \"zig-transport\"))]")
            .next()
            .expect("default Zig branch");
        assert!(zig_branch
            .contains("zig_transport::encode_t5m_direct(&admitted_source_words(&projection)?)"));
        assert!(!zig_branch.contains("sens::encode_binary_projection_ternary("));
        assert!(!zig_branch.contains("decode_canonical_t5m_words(&reference)"));
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn zig_ingress_be3_preserves_exact_width_and_rejects_invalid_transport() {
        let carrier = zig_test_fixture("migration-quote-cohort-main/quote-legacy.sens");
        let actual = zig_transport::decode_t5m_words(carrier)
            .expect("Zig physical ingress on admitted binary program");
        let independent_reference = sens::parse_binary_source_words("10 001 00 000 01")
            .unwrap()
            .into_iter()
            .map(|token| token.word)
            .collect::<Vec<_>>();
        assert_eq!(actual, independent_reference);
        assert_eq!(
            actual.iter().map(|w| w.width()).collect::<Vec<_>>(),
            vec![2, 3, 2, 3, 2]
        );
        let program = sens::PhysicalT5Program::from_exact_words(&actual)
            .expect("SENS-owned D2 reading, not Zig semantic verdict");
        assert_eq!(program.form_count(), 1);
        let d1_word = sens::parse_binary_source_words("1").unwrap()[0].word;
        let d1_carrier = zig_transport::encode_t5m_direct(&[d1_word]).unwrap();
        assert_eq!(
            zig_transport::decode_t5m_words(&d1_carrier).unwrap()[0].width(),
            1
        );
        let d2_word = sens::parse_binary_source_words("01").unwrap()[0].word;
        let d2_carrier = zig_transport::encode_t5m_direct(&[d2_word]).unwrap();
        assert_eq!(
            zig_transport::decode_t5m_words(&d2_carrier).unwrap()[0].width(),
            2
        );
        assert!(zig_transport::decode_t5m_words(&[0xf3]).is_err());
        assert!(zig_transport::decode_t5m_words(&[0xf2]).is_err());
        assert!(zig_transport::decode_t5m_words(&[0, 0]).is_err());
    }

    #[cfg(not(feature = "zig-transport"))]
    #[test]
    fn physical_t5_eval_and_explicit_core4_refuse_without_zig() {
        let bytes = zig_test_fixture("migration-quote-cohort-main/quote-legacy.sens");
        for bootstrap_core in [false, true] {
            let error = eval_t5m_bytes_core4(bytes, bootstrap_core)
                .expect_err("physical T5M cannot execute without Zig");
            assert!(error.contains("no Rust fallback"), "{error}");
            // Even malformed physical bytes fail for the SAME missing
            // corridor; no Rust physical parser or SENS executor is called.
            let malformed = eval_t5m_bytes_core4(&[0xf3], bootstrap_core)
                .expect_err("no fallback for malformed bytes");
            assert_eq!(error, malformed);
        }
    }

    #[test]
    fn physical_eval_path_uses_packed_words_not_visible_text() {
        let source = include_str!("sens-trit.rs");
        let start = source
            .find("fn eval_t5m_bytes_core4(")
            .expect("physical eval route");
        let end = source[start..]
            .find("\n/// Diagnose a physical packed T5M file")
            .expect("next production route")
            + start;
        let route = &source[start..end];
        #[cfg(feature = "zig-transport")]
        {
            let zig_branch = route
                .split("#[cfg(feature = \"zig-transport\")]")
                .nth(1)
                .expect("Zig ingress block");
            assert!(zig_branch.contains("zig_transport::decode_t5m_exact_words(bytes)"));
            assert!(zig_branch
                .contains("sens::PhysicalT5Program::from_exact_domain_words_owned(words)"));
            assert!(!zig_branch.contains("sens::PhysicalT5Program::decode(bytes)"));
        }
        #[cfg(not(feature = "zig-transport"))]
        {
            assert!(route.contains("physical T5M execution requires Zig; no Rust fallback"));
            assert!(!route.contains("sens::PhysicalT5Program::decode(bytes)"));
        }
        assert!(route.contains(".execute(&mut session)"));
        assert!(!route.contains("sens::pack_binary_source_words("));
        assert!(!route.contains("sens::parse_canonical_packed_words("));
        assert!(!route.contains("sens::open_ternary_program(bytes)"));
        assert!(!route.contains("sens::parse_canonical_binary(&visible)"));
    }
}

#[cfg(all(test, feature = "zig-transport"))]
mod d7_zig_cli_boundary_tests {
    use super::*;

    #[test]
    fn keyboard_w7_is_sens_owned_zig_carries_exact_bytes_and_rejects_non_d7() {
        let text = "Кіт! (.)\n";
        let words = sens::encode_d7_uk_words(text).expect("ratified D7 Ukrainian glyphs");
        assert_eq!(words.len(), text.chars().count());
        assert!(words.iter().all(|w| w.width() == 7));
        let carrier =
            zig_transport::encode_t5m_direct(&words).expect("Zig-only physical T5M output");
        let source_trits = words.iter().map(|word| word.width()).sum::<usize>() + words.len() - 1;
        assert_eq!(carrier.len(), source_trits.div_ceil(5));
        let restored =
            zig_transport::decode_t5m_words(&carrier).expect("Zig-only physical T5M ingress");
        assert_eq!(restored, words);
        assert_eq!(sens::decode_d7_uk_words(&restored).unwrap(), text);

        let error = sens::encode_d7_uk_words("Кі🙂").unwrap_err();
        assert_eq!(
            error,
            sens::D7ProjectionError::UnassignedKeyboardGlyph { byte_offset: 4 }
        );
        let d2_word = sens::parse_binary_source_words("01").unwrap()[0].word;
        let d2_carrier = zig_transport::encode_t5m_direct(&[d2_word]).unwrap();
        let d2 = zig_transport::decode_t5m_words(&d2_carrier)
            .expect("valid D2:01 T5M physical word, not D7");
        assert_eq!(
            sens::decode_d7_uk_words(&d2),
            Err(sens::D7ProjectionError::NonD7Word)
        );
        for invalid in [&[0xf3][..], &[0xf2][..], &[0x00, 0x00][..]] {
            assert!(zig_transport::decode_t5m_words(invalid).is_err());
        }
        assert!(zig_transport::encode_t5m_direct(&[]).is_err());
    }

    #[test]
    fn d7_default_cli_routes_do_not_decode_or_encode_t5_in_rust() {
        let source = include_str!("sens-trit.rs");
        let e = source.find("\"encode-d7-uk\" => {").unwrap();
        let segment = &source[e..];
        let encode = &segment[..segment.find("\n        }").unwrap()];
        let feature_encode = encode
            .split("#[cfg(not(feature = \"zig-transport\"))]")
            .next()
            .unwrap();
        assert!(feature_encode.contains("sens::encode_d7_uk_words(&text)"));
        assert!(feature_encode.contains("zig_transport::encode_t5m_direct(&words)"));
        assert!(!feature_encode.contains("sens::encode_d7_uk_t5(&text)"));

        let d = source.find("\"decode-d7-uk\" => {").unwrap();
        let segment = &source[d..];
        let decode = &segment[..segment.find("\n        }").unwrap()];
        let feature_decode = decode
            .split("#[cfg(not(feature = \"zig-transport\"))]")
            .next()
            .unwrap();
        assert!(feature_decode.contains("zig_transport::decode_t5m_words(&bytes)"));
        assert!(feature_decode.contains("sens::decode_d7_uk_words(&words)"));
        assert!(!feature_decode.contains("sens::decode_d7_uk_t5(&bytes)"));
    }
}



#[cfg(test)]
mod sterile_f3c_corridor_guard_tests {
    const TRIT_SOURCE: &str = include_str!("sens-trit.rs");
    const ZIG_SOURCE: &str = include_str!("../zig_transport.rs");

    // Mask comments and literal payloads while preserving byte offsets. This
    // keeps comment-only examples and string contents from satisfying source
    // checks, and prevents braces inside format strings from ending a route.
    fn mask_non_code(source: &str) -> String {
        let bytes = source.as_bytes();
        let mut masked = bytes.to_vec();
        let mut i = 0usize;

        fn mask(masked: &mut [u8], bytes: &[u8], start: usize, end: usize) {
            for p in start..end {
                if bytes[p] != b'\n' && bytes[p] != b'\r' {
                    masked[p] = b' ';
                }
            }
        }

        fn raw_string_end(bytes: &[u8], start: usize) -> Option<usize> {
            let prefix = if bytes.get(start) == Some(&b'r') {
                start
            } else if bytes.get(start) == Some(&b'b')
                && bytes.get(start + 1) == Some(&b'r')
            {
                start + 1
            } else {
                return None;
            };
            let mut quote = prefix + 1;
            while bytes.get(quote) == Some(&b'#') {
                quote += 1;
            }
            if bytes.get(quote) != Some(&b'"') {
                return None;
            }
            let hashes = quote - (prefix + 1);
            let mut p = quote + 1;
            while p < bytes.len() {
                if bytes[p] == b'"'
                    && p + 1 + hashes <= bytes.len()
                    && bytes[p + 1..p + 1 + hashes]
                        .iter()
                        .all(|&byte| byte == b'#')
                {
                    return Some(p + 1 + hashes);
                }
                p += 1;
            }
            Some(bytes.len())
        }

        fn quoted_string_end(bytes: &[u8], quote: usize) -> usize {
            let mut p = quote + 1;
            while p < bytes.len() {
                match bytes[p] {
                    b'\\' => p = (p + 2).min(bytes.len()),
                    b'"' => return p + 1,
                    b'\n' => return p,
                    _ => p += 1,
                }
            }
            bytes.len()
        }

        fn char_literal_end(bytes: &[u8], quote: usize) -> Option<usize> {
            let next = *bytes.get(quote + 1)?;
            if next == b'\\' {
                let mut p = quote + 2;
                while p < bytes.len() && p - quote <= 16 {
                    if bytes[p] == b'\'' {
                        return Some(p + 1);
                    }
                    if bytes[p] == b'\n' {
                        return None;
                    }
                    p += 1;
                }
                return None;
            }
            let width = if next < 0x80 {
                1
            } else if next < 0xe0 {
                2
            } else if next < 0xf0 {
                3
            } else {
                4
            };
            let end = quote + 1 + width;
            (bytes.get(end) == Some(&b'\'')).then_some(end + 1)
        }

        while i < bytes.len() {
            if bytes.get(i..i + 2) == Some(b"//") {
                let mut end = i + 2;
                while end < bytes.len() && bytes[end] != b'\n' {
                    end += 1;
                }
                mask(&mut masked, bytes, i, end);
                i = end;
                continue;
            }
            if bytes.get(i..i + 2) == Some(b"/*") {
                let mut depth = 1usize;
                let mut end = i + 2;
                while end < bytes.len() && depth > 0 {
                    if bytes.get(end..end + 2) == Some(b"/*") {
                        depth += 1;
                        end += 2;
                    } else if bytes.get(end..end + 2) == Some(b"*/") {
                        depth -= 1;
                        end += 2;
                    } else {
                        end += 1;
                    }
                }
                mask(&mut masked, bytes, i, end);
                i = end;
                continue;
            }
            if let Some(end) = raw_string_end(bytes, i) {
                mask(&mut masked, bytes, i, end);
                i = end;
                continue;
            }
            if bytes[i] == b'"' {
                let end = quoted_string_end(bytes, i);
                mask(&mut masked, bytes, i, end);
                i = end;
                continue;
            }
            let quote = if bytes[i] == b'\'' {
                Some(i)
            } else if bytes[i] == b'b' && bytes.get(i + 1) == Some(&b'\'') {
                Some(i + 1)
            } else {
                None
            };
            if let Some(quote) = quote {
                if let Some(end) = char_literal_end(bytes, quote) {
                    mask(&mut masked, bytes, i, end);
                    i = end;
                    continue;
                }
            }
            i += 1;
        }

        String::from_utf8(masked).expect("masking preserves valid UTF-8")
    }

    fn matching_brace(source: &str, open: usize) -> Result<usize, String> {
        let bytes = source.as_bytes();
        if bytes.get(open) != Some(&b'{') {
            return Err("відсутня відкрита дужка маршруту".into());
        }
        let mut depth = 0usize;
        for (offset, byte) in bytes.iter().enumerate().skip(open) {
            match byte {
                b'{' => depth += 1,
                b'}' => {
                    depth = depth
                        .checked_sub(1)
                        .ok_or("зайва закривна дужка маршруту")?;
                    if depth == 0 {
                        return Ok(offset);
                    }
                }
                _ => {}
            }
        }
        Err("маршрут не має закривної дужки".into())
    }

    fn function_body<'a>(source: &'a str, signature: &str) -> Result<&'a str, String> {
        let clean = mask_non_code(source);
        let starts = clean.match_indices(signature).map(|(i, _)| i).collect::<Vec<_>>();
        if starts.len() != 1 {
            return Err(format!(
                "очікував одне живе визначення {signature:?}, знайдено {}",
                starts.len()
            ));
        }
        let start = starts[0];
        let open = clean[start..]
            .find('{')
            .map(|offset| start + offset)
            .ok_or_else(|| format!("відсутнє тіло {signature:?}"))?;
        let close = matching_brace(&clean, open)?;
        Ok(&source[open + 1..close])
    }

    fn cfg_body<'a>(body: &'a str, attribute: &str) -> Result<&'a str, String> {
        let clean = mask_non_code(body);
        for (start, _) in body.match_indices(attribute) {
            // An identical spelling in a comment is not an active cfg branch.
            if !clean[start..].starts_with("#[cfg(") {
                continue;
            }
            let open = clean[start..]
                .find('{')
                .map(|offset| start + offset)
                .ok_or_else(|| format!("відсутнє тіло {attribute:?}"))?;
            let close = matching_brace(&clean, open)?;
            return Ok(&body[open + 1..close]);
        }
        Err(format!("відсутня жива гілка {attribute:?}"))
    }

    fn compact_code(source: &str) -> String {
        mask_non_code(source)
            .chars()
            .filter(|character| !character.is_whitespace())
            .collect()
    }

    fn verify_routes(trit_source: &str, zig_source: &str) -> Result<(), String> {
        let decode = function_body(trit_source, "fn decode_f3_carrier(")?;
        let encode = function_body(trit_source, "fn encode_f3_carrier(")?;

        let decode_zig = compact_code(cfg_body(decode, "#[cfg(feature = \"zig-transport\")]")?);
        let decode_no_zig = cfg_body(decode, "#[cfg(not(feature = \"zig-transport\"))]")?;
        let decode_no_zig_code = compact_code(decode_no_zig);
        if !decode_zig.contains("zig_transport::decode_f3(bytes)?")
            || !decode_zig.contains("zig_transport::decode_t5m_words(&restored)?")
            || decode_zig.find("zig_transport::decode_f3(bytes)?")
                >= decode_zig.find("zig_transport::decode_t5m_words(&restored)?")
            || !decode_zig.contains("sens::PhysicalT5Program::from_exact_words(&words)")
        {
            return Err("F3C ingress не проходить Zig F3 → Zig T5M → точний SENS admission".into());
        }
        if !decode_no_zig.contains("no Rust fallback")
            || !decode_no_zig_code.contains("Err(")
            || decode_no_zig_code.contains("Ok(")
            || decode_no_zig_code.contains("zig_transport::")
            || decode_no_zig_code.contains("sens::")
        {
            return Err("F3C ingress без Zig не відмовляється fail-closed".into());
        }

        let encode_zig = cfg_body(encode, "#[cfg(feature = \"zig-transport\")]")?;
        let encode_code = compact_code(encode_zig);
        let decode_at = encode_code.find("zig_transport::decode_t5m_words(bytes)?");
        let encode_at = encode_code.find("zig_transport::encode_f3(bytes)");
        if decode_at.is_none()
            || encode_at.is_none()
            || decode_at >= encode_at
            || !encode_code.contains("sens::PhysicalT5Program::from_exact_words(&words)")
            || !(encode_code.ends_with("zig_transport::encode_f3(bytes)")
                || encode_code.ends_with("returnzig_transport::encode_f3(bytes);"))
        {
            return Err("F3C egress не має живого валідованого T5M → Zig tail/return".into());
        }
        let encode_no_zig = cfg_body(encode, "#[cfg(not(feature = \"zig-transport\"))]")?;
        let encode_no_zig_code = compact_code(encode_no_zig);
        if !encode_no_zig.contains("no Rust fallback")
            || !encode_no_zig_code.contains("Err(")
            || encode_no_zig_code.contains("Ok(")
            || encode_no_zig_code.contains("zig_transport::")
            || encode_no_zig_code.contains("sens::")
        {
            return Err("F3C egress без Zig не відмовляється fail-closed".into());
        }

        let zig_encode = compact_code(function_body(zig_source, "pub fn encode_f3(")?);
        let validate = zig_encode.find("decode_t5m_words(t5)?");
        let pack = zig_encode.find("sens_zig_f3c_pack(");
        if validate.is_none()
            || pack.is_none()
            || validate >= pack
            || !zig_encode.contains("encode_legacy_t5(&logical_words)?")
        {
            return Err("Zig F3C pack не перевіряє T5M до фізичного кодування".into());
        }

        let zig_decode = compact_code(function_body(zig_source, "pub fn decode_f3(")?);
        let unpack = zig_decode.find("sens_zig_f3c_unpack(");
        let validate_legacy = zig_decode.find("decode_legacy_t5_words(&output)?");
        let restore_t5m = zig_decode.find("encode_t5m_direct(&words)");
        if unpack.is_none()
            || validate_legacy.is_none()
            || restore_t5m.is_none()
            || unpack >= validate_legacy
            || validate_legacy >= restore_t5m
        {
            return Err("Zig F3C unpack не перевіряє legacy T5 і не відновлює T5M".into());
        }
        Ok(())
    }

    #[test]
    fn sterile_f3c_corridor_checks_live_t5m_ingress_and_zig_egress() {
        verify_routes(TRIT_SOURCE, ZIG_SOURCE)
            .unwrap_or_else(|error| panic!("стерильний F3C/T5M-коридор: {error}"));
        println!("Перевірено живі T5M ingress та Zig F3C egress із fail-closed гілками.");
    }

    #[test]
    fn sterile_f3c_corridor_rejects_comment_unused_encode_and_rust_fallback_mutants() {
        let comment_only = TRIT_SOURCE.replacen(
            "        zig_transport::encode_f3(bytes)\n",
            "        // zig_transport::encode_f3(bytes)\n        Ok(None)\n",
            1,
        );
        assert_ne!(comment_only, TRIT_SOURCE, "anchor коментарного мутанта має існувати");
        assert!(verify_routes(&comment_only, ZIG_SOURCE).is_err());

        let unused_encode = TRIT_SOURCE.replacen(
            "        zig_transport::encode_f3(bytes)\n",
            "        let _ignored = zig_transport::encode_f3(bytes)?;\n        Ok(None)\n",
            1,
        );
        assert_ne!(unused_encode, TRIT_SOURCE, "anchor невикористаного encode має існувати");
        assert!(verify_routes(&unused_encode, ZIG_SOURCE).is_err());

        let rust_fallback = TRIT_SOURCE.replacen(
            "Err(\"F3C physical encode requires Zig; no Rust fallback\".into())",
            "Ok(Some(bytes.to_vec()))",
            1,
        );
        assert_ne!(rust_fallback, TRIT_SOURCE, "anchor Rust fallback мутанта має існувати");
        assert!(verify_routes(&rust_fallback, ZIG_SOURCE).is_err());

        let missing_ingress = TRIT_SOURCE.replacen(
            "let restored = zig_transport::decode_f3(bytes)?;",
            "// let restored = zig_transport::decode_f3(bytes)?;\n        let restored = bytes.to_vec();",
            1,
        );
        assert_ne!(missing_ingress, TRIT_SOURCE, "anchor ingress мутанта має існувати");
        assert!(verify_routes(&missing_ingress, ZIG_SOURCE).is_err());
    }
}
