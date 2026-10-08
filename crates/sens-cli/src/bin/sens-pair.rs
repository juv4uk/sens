//! Тимчасова утиліта парних .lisp + .sens із захистом від розходження.
//! Підтримує лише вже перевірену точну двійкову проєкцію в .lisp.
//! Українські людські імена потребують окремого semantic translator.

use std::{env, fs, fs::OpenOptions, io::Write, path::{Path, PathBuf}, process};

fn sibling_sens(path: &Path) -> Result<PathBuf, String> {
    if path.extension().and_then(|x| x.to_str()) != Some("lisp") {
        return Err("expected .lisp companion, not an arbitrary file".into());
    }
    Ok(path.with_extension("sens"))
}

fn run() -> Result<(), String> {
    let mut args = env::args().skip(1);
    let mode = args.next().ok_or("usage: sens-pair (encode|verify) path.lisp")?;
    let lisp_arg = args.next().ok_or("missing path.lisp")?;
    if args.next().is_some() {
        return Err("usage: sens-pair (encode|verify) path.lisp".into());
    }
    let lisp_path = Path::new(&lisp_arg);
    let sens_path = sibling_sens(lisp_path)?;
    let source = fs::read_to_string(lisp_path).map_err(|e| format!("read .lisp: {e}"))?;

    match mode.as_str() {
        "encode" => {
            let bytes = sens::sens_bytes_from_binary_lisp(&source)
                .map_err(|e| format!("not convertible yet (do not invent translations): {e:?}"))?;
            // Never clobber existing authority or changes from another agent.
            let mut file = OpenOptions::new().write(true).create_new(true)
                .open(&sens_path).map_err(|e| format!("cannot create .sens without overwriting: {e}"))?;
            file.write_all(&bytes).map_err(|e| format!("write .sens: {e}"))?;
            let proof = sens::verify_sens_with_binary_lisp(&source, &bytes)
                .map_err(|e| format!("post-encode verification: {e:?}"))?;
            println!("created {}: {} semantic bits, {} physical bytes, {} tail bits",
                     sens_path.display(), proof.semantic_bits, proof.physical_bytes,
                     proof.tail_unused_bits);
            Ok(())
        }
        "verify" => {
            let bytes = fs::read(&sens_path).map_err(|e| format!("read .sens: {e}"))?;
            let proof = sens::verify_sens_with_binary_lisp(&source, &bytes)
                .map_err(|e| format!("pair mismatch: {e:?}"))?;
            println!("VERIFIED {} ⇔ {}: {} domain words, {} semantic bits, {} physical bits, {} tail bits",
                     lisp_path.display(), sens_path.display(), proof.word_widths.len(),
                     proof.semantic_bits, proof.physical_bits, proof.tail_unused_bits);
            Ok(())
        }
        _ => Err("usage: sens-pair (encode|verify) path.lisp".into()),
    }
}

fn main() {
    if let Err(message) = run() {
        eprintln!("sens-pair: {message}");
        process::exit(1);
    }
}
