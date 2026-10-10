//! Independent explicit file-runner for physical SENS without Core4 bootstrap.
//! The physical stream is mandatory: no invisible English/Lisp translation,
//! no defaults that infer an external width schedule, no implicit I/O hooks.
use sens::{prepare_t5_program, Session};
use std::{env, fs, path::Path, process};

fn run() -> Result<(), String> {
    let args = env::args().skip(1).collect::<Vec<_>>();
    let [file] = args.as_slice() else {
        return Err("usage: sens_native_zero_file PATH.sens".into());
    };
    let path = Path::new(file);
    if path.extension().and_then(|ext| ext.to_str()) != Some("sens") {
        return Err("only real physical .sens bytes are accepted".into());
    }
    let bytes = fs::read(path).map_err(|err| format!("read physical T5: {err}"))?;
    let prepared = prepare_t5_program(&bytes)
        .map_err(|err| format!("physical T5/D2 admission rejected: {err:?}"))?;
    let result = prepared.execute(&mut Session::bare())
        .map_err(|err| format!("exact-domain evaluation rejected: {err}"))?;
    for message in &result.output {
        println!("OUTPUT={message}");
    }
    println!("VALUE={}", result.value);
    println!(
        "KIND={}",
        match result.value.as_predicate_bit() {
            Some(true) => "D1:YES",
            Some(false) => "D1:NO",
            None => "NON-D1",
        }
    );
    Ok(())
}

fn main() {
    if let Err(err) = run() {
        eprintln!("NATIVE ZERO BLOCKED: {err}");
        process::exit(2);
    }
}
