//! Дослідний фізичний трійковий кодек для ДВІЙКОВОЇ мови SENS.
//! Не трактувати транспортну цифру 2 як нову функцію чи домен.

use std::{env, fs, fs::OpenOptions, io::Write, path::Path, process};

fn sibling_sens(path: &Path) -> Result<std::path::PathBuf, String> {
    if path.extension().and_then(|ext| ext.to_str()) != Some("lisp") {
        return Err("expected a .lisp companion path".into());
    }
    Ok(path.with_extension("sens"))
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

fn execute() -> Result<(), String> {
    let mut args = env::args().skip(1);
    let command = args.next().ok_or("usage: sens-trit (encode|decode|verify) path")?;
    let file = args.next().ok_or("missing path")?;
    if args.next().is_some() {
        return Err("usage: sens-trit (encode|decode|verify) path".into());
    }
    let path = Path::new(&file);

    match command.as_str() {
        "encode" => {
            let sens_path = sibling_sens(path)?;
            let projection = fs::read_to_string(path).map_err(|e| format!("read .lisp: {e}"))?;
            let bytes = sens::encode_binary_projection_ternary(&projection)
                .map_err(|e| format!("encode .lisp projection: {e:?}"))?;
            // Захист чинного файла: автоматично нічого не перезаписувати.
            let mut output = OpenOptions::new().create_new(true).write(true)
                .open(&sens_path).map_err(|e| format!("create .sens: {e}"))?;
            output.write_all(&bytes).map_err(|e| format!("write .sens: {e}"))?;
            verify_companion(&projection, &bytes)
        }
        "decode" => {
            let bytes = fs::read(path).map_err(|e| format!("read .sens: {e}"))?;
            let words = sens::decode_ternary_program(&bytes)
                .map_err(|e| format!("decode .sens: {e:?}"))?;
            print!("{}", sens::render_ternary_words_vertical(&words));
            Ok(())
        }
        "verify" => {
            let sens_path = sibling_sens(path)?;
            let projection = fs::read_to_string(path).map_err(|e| format!("read .lisp: {e}"))?;
            let bytes = fs::read(&sens_path).map_err(|e| format!("read .sens: {e}"))?;
            verify_companion(&projection, &bytes)
        }
        _ => Err("usage: sens-trit (encode|decode|verify) path".into()),
    }
}

fn main() {
    if let Err(message) = execute() {
        eprintln!("sens-trit: {message}");
        process::exit(1);
    }
}
