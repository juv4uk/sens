//! Physical-only byte-copy experiment, not a SENS language-law oracle.
use std::{env, fs, hint::black_box, process::ExitCode};

fn run() -> Result<(), String> {
    let mut args = env::args().skip(1);
    let path = args.next().ok_or("usage: copy-rust CORPUS COPIES")?;
    let copies: usize = args.next().ok_or("missing COPIES")?
        .parse().map_err(|_| "bad COPIES")?;
    if args.next().is_some() || !(1..=5_000_000).contains(&copies) {
        return Err("invalid COPIES".into());
    }
    let source = fs::read(path).map_err(|e| e.to_string())?;
    if source.is_empty() || source.len() > 64 * 1024 * 1024 {
        return Err("invalid corpus size".into());
    }
    let mut dest = vec![0u8; source.len()];
    let mut observed = 0u64;
    for i in 0..copies {
        // Re-copying source must repair a changed destination every round.
        dest[i % source.len()] ^= 1;
        dest.copy_from_slice(black_box(&source));
        observed += u64::from(black_box(dest[i % source.len()]));
        black_box(&dest);
    }
    if dest != source {
        return Err("PHYSICAL_COPY_FAIL byte-parity".into());
    }
    println!("PHYSICAL_COPY\tbytes={}\tcopies={}\tobserved={}", source.len(), copies, observed);
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => { eprintln!("{e}"); ExitCode::FAILURE }
    }
}
