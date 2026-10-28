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
    max_power_watts: u64,
}

// An explicit *upper bound*, not a measured TDP. Used only to reject
// measurements in which more than one counter wrap could be hidden.
const DEFAULT_MAX_PACKAGE_POWER_WATTS: u64 = 2_000;

fn power_ceiling_watts() -> Result<u64, String> {
    match env::var("SENS_RAPL_MAX_POWER_WATTS") {
        Ok(raw) => match raw.parse::<u64>() {
            Ok(watts) if (1..=100_000).contains(&watts) => Ok(watts),
            _ => Err("SENS_RAPL_MAX_POWER_WATTS must be in 1..=100000".into()),
        },
        Err(env::VarError::NotPresent) => Ok(DEFAULT_MAX_PACKAGE_POWER_WATTS),
        Err(e) => Err(format!("invalid SENS_RAPL_MAX_POWER_WATTS: {e}")),
    }
}

/// Two counter reads are only sufficient if the entire read-to-read window
/// cannot consume the full advertised counter range. The power ceiling is
/// an external upper bound and must not be misrepresented as a measurement.
fn at_most_one_wrap(range_uj: u64, window: Duration, ceiling_watts: u64) -> bool {
    range_uj > 0
        && ceiling_watts > 0
        && window.as_nanos().saturating_mul(u128::from(ceiling_watts))
            < u128::from(range_uj).saturating_mul(1_000)
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
    Ok(Package { zone, max_uj, max_power_watts: power_ceiling_watts()? })
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
    // Include both sysfs reads in the wrap-safety window, not just the CPU loop.
    let sensor_window_start = Instant::now();
    let before = counter(&pkg.zone.join("energy_uj"))?;
    let begin = Instant::now();
    let observed = black_box(scan_d3_owner_residency(black_box(iterations)));
    let elapsed = begin.elapsed();
    let after = counter(&pkg.zone.join("energy_uj"))?;
    let sensor_window = sensor_window_start.elapsed();
    if !at_most_one_wrap(pkg.max_uj, sensor_window, pkg.max_power_watts) {
        return Err(format!(
            "RAPL wrap ambiguity: sensor window {} ns may consume >= {} uJ at ceiling {} W",
            sensor_window.as_nanos(), pkg.max_uj, pkg.max_power_watts
        ));
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
        "RAPL_MECHANISM zone={} max_uj={} power_ceiling_watts={} iterations={} samples={} unit=owner_lookup",
        pkg.zone.display(),
        pkg.max_uj,
        pkg.max_power_watts,
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
    use super::{at_most_one_wrap, delta_uj};
    use std::time::Duration;

    #[test]
    fn rapl_counter_delta_and_wrap_are_mechanical_only() {
        assert_eq!(delta_uj(3, 8, 20), Some(5));
        assert_eq!(delta_uj(18, 3, 20), Some(5));
        assert_eq!(delta_uj(20, 3, 20), None);
        assert_eq!(delta_uj(1, 3, 0), None);
    }

    #[test]
    fn reject_power_ceiling_windows_that_can_hide_full_counter_wrap() {
        let max = 100_000_000; // 100 J
        assert!(at_most_one_wrap(max, Duration::from_millis(40), 2_000));
        assert!(!at_most_one_wrap(max, Duration::from_millis(50), 2_000));
        assert!(!at_most_one_wrap(max, Duration::from_millis(90), 2_000));
        assert!(!at_most_one_wrap(0, Duration::from_nanos(1), 2_000));
        assert!(!at_most_one_wrap(max, Duration::from_nanos(1), 0));
    }
}
