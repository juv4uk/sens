//! T5 file codec для ДВІЙКОВОЇ SENS: трит 2 — внутрішня межа, не
//! видимий символ і не частина семантики D2/D7.
//!
//! `sens-trit open file.sens` або `sens-trit file.sens` показує лише
//! точні binary words з ОДНИМ пробілом між ними. Фізично `.sens`
//! залишається packed byte file. Дослідне EOS=22 не ратифіковане.

use std::{env, fs, fs::OpenOptions, io::Write, path::Path, process};

const USAGE: &str =
    "usage: sens-trit (encode path.lisp | open path.sens | view path.sens | decode path.sens | verify path.lisp)\n       sens-trit path.sens  # open as spaced binary words";

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
                .map_err(|e| format!("open .sens: {e:?}"))?;
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
