//! Linux RAPL: energy cost of a Rust mechanism, never a SENS semantic verdict.
//! Separate from Criterion/Callgrind; stdout is raw measurements, not release GO.
use sens_measurement_triad::scan_d3_owner_residency;
use std::{
    env, fs,
    hint::black_box,
    path::{Path, PathBuf},
    process::ExitCode,
    time::{Duration, Instant},
};

struct Package {
    zone: PathBuf,
    max_uj: u64,
}

fn counter(path: &Path) -> Result<u64, String> {
    let raw = fs::read_to_string(path).map_err(|e| format!("{}: {e}", path.display()))?;
    raw.trim()
        .parse::<u64>()
        .map_err(|e| format!("{}: invalid energy counter: {e}", path.display()))
}

fn package() -> Result<Package, String> {
    // An explicit path is useful on hosts with more than one CPU package.
    let zone = match env::var_os("SENS_RAPL_PACKAGE") {
        Some(path) => PathBuf::from(path),
        None => {
            let mut zones = Vec::new();
            for entry in fs::read_dir("/sys/class/powercap")
                .map_err(|e| format!("RAPL unavailable in this Linux environment: {e}"))?
            {
                let entry = entry.map_err(|e| e.to_string())?;
                let name = entry.file_name().to_string_lossy().into_owned();
                if !name.starts_with("intel-rapl:") || name["intel-rapl:".len()..].contains(':') {
                    continue; // Package zones only; exclude DRAM/PP0 nested zones.
                }
                let path = entry.path();
                let label = fs::read_to_string(path.join("name")).unwrap_or_default();
                if label.trim().starts_with("package-") {
                    zones.push(path);
                }
            }
            if zones.len() != 1 {
                return Err(format!(
                    "expected exactly one RAPL package zone, found {}; set SENS_RAPL_PACKAGE",
                    zones.len()
                ));
            }
            zones.remove(0)
        }
    };
    let max_uj = counter(&zone.join("max_energy_range_uj"))?;
    if max_uj == 0 {
        return Err("RAPL max_energy_range_uj must be positive".into());
    }
    // Fail before benchmarking rather than reporting false zero energy.
    let initial = counter(&zone.join("energy_uj"))?;
    if initial >= max_uj {
        return Err("RAPL counter is outside its published wrap range".into());
    }
    Ok(Package { zone, max_uj })
}

fn delta_uj(before: u64, after: u64, modulus: u64) -> Option<u64> {
    if modulus == 0 || before >= modulus || after >= modulus {
        None
    } else if after >= before {
        Some(after - before)
    } else {
        Some(modulus - before + after)
    }
}

fn measure(pkg: &Package, iterations: usize) -> Result<(u64, Duration, usize), String> {
    let before = counter(&pkg.zone.join("energy_uj"))?;
    let begin = Instant::now();
    let observed = black_box(scan_d3_owner_residency(black_box(iterations)));
    let elapsed = begin.elapsed();
    let after = counter(&pkg.zone.join("energy_uj"))?;
    // A long measurement could span several counter wraps, which two reads cannot detect.
    if elapsed > Duration::from_secs(5) {
        return Err("sample exceeds 5 s; RAPL wrap count is ambiguous".into());
    }
    let uj = delta_uj(before, after, pkg.max_uj)
        .ok_or_else(|| "RAPL counter outside max_energy_range_uj".to_owned())?;
    if uj == 0 {
        return Err("zero RAPL delta: batch too short or counter did not advance".into());
    }
    Ok((uj, elapsed, observed))
}

fn positive_arg(index: usize, fallback: usize, limit: usize) -> Result<usize, String> {
    let value = match env::args().nth(index) {
        None => fallback,
        Some(raw) => raw
            .parse::<usize>()
            .map_err(|_| format!("argument {index}: expected positive integer"))?,
    };
    if value == 0 || value > limit {
        return Err(format!("argument {index}: expected 1..={limit}"));
    }
    Ok(value)
}

fn run() -> Result<(), String> {
    if !cfg!(target_os = "linux") {
        return Err("Linux RAPL is required; not a Windows/WSL2 power estimate".into());
    }
    let requested = positive_arg(1, 1_000_000, 100_000_000)?;
    let samples = positive_arg(2, 7, 31)?;
    let pkg = package()?;

    // Calibration touches the Rust owner-residency mechanism only; no language law.
    // The sensor is read twice around each timed batch, never once per operation.
    let mut iterations = requested;
    loop {
        let start = Instant::now();
        black_box(scan_d3_owner_residency(black_box(iterations)));
        if start.elapsed() >= Duration::from_millis(100) {
            break;
        }
        iterations = iterations
            .checked_mul(2)
            .filter(|&n| n <= 100_000_000)
            .ok_or_else(|| "mechanism too fast for >=100 ms batch within limit".to_owned())?;
    }

    println!(
        "RAPL_MECHANISM zone={} max_uj={} iterations={} samples={} unit=owner_lookup",
        pkg.zone.display(),
        pkg.max_uj,
        iterations,
        samples
    );
    for index in 0..samples {
        let (uj, elapsed, observed) = measure(&pkg, iterations)?;
        if elapsed < Duration::from_millis(25) {
            return Err("timed sample under 25 ms; insufficient energy resolution".into());
        }
        println!(
            "RAPL_SAMPLE index={} energy_uj={} elapsed_ns={} operations={} observed={} joules_per_op={:.12}",
            index + 1,
            uj,
            elapsed.as_nanos(),
            iterations,
            observed, // Checksum only; NOT a Rust semantic assertion.
            uj as f64 / 1_000_000.0 / iterations as f64
        );
    }
    println!("RAPL_MECHANISM_DONE status=MEASURED_NOT_SEMANTIC_PASS");
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("RAPL_MECHANISM_BLOCKED reason={e}");
            ExitCode::from(2)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::delta_uj;

    #[test]
    fn rapl_counter_delta_and_wrap_are_mechanical_only() {
        assert_eq!(delta_uj(3, 8, 20), Some(5));
        assert_eq!(delta_uj(18, 3, 20), Some(5));
        assert_eq!(delta_uj(20, 3, 20), None);
        assert_eq!(delta_uj(1, 3, 0), None);
    }
}
