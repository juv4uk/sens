//! Linux RAPL package-energy meter: Rust measures the physical mechanism only.
//! Does not execute, reinterpret or certify SENS semantics.
//! rustc -O benchmarks/mechanism/rapl-energy-bench.rs -o /tmp/sens-rapl
//! /tmp/sens-rapl --operations 100000 -- ./my-prebatched-benchmark
use std::env;
use std::ffi::OsString;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode};
use std::time::{Duration, Instant};

// Conservative upper limit for wrap safety; NOT a measured power/TDP.
const DEFAULT_MAX_PACKAGE_POWER_WATTS: u64 = 2_000;
fn power_ceiling_watts() -> Result<u64, String> {
    match env::var("SENS_RAPL_MAX_POWER_WATTS") {
        Ok(raw) => match raw.parse::<u64>() {
            Ok(v) if (1..=100_000).contains(&v) => Ok(v),
            _ => Err("RAPL_UNRESOLVED invalid SENS_RAPL_MAX_POWER_WATTS".into()),
        },
        Err(env::VarError::NotPresent) => Ok(DEFAULT_MAX_PACKAGE_POWER_WATTS),
        Err(e) => Err(format!("RAPL_UNRESOLVED invalid SENS_RAPL_MAX_POWER_WATTS: {e}")),
    }
}

fn at_most_one_wrap(range_uj: u64, duration: Duration, max_power_watts: u64) -> bool {
    range_uj > 0 && max_power_watts > 0
        && duration.as_nanos().saturating_mul(u128::from(max_power_watts))
            < u128::from(range_uj).saturating_mul(1_000)
}


fn number(path: &Path) -> Result<u64, String> {
    let raw = fs::read_to_string(path)
        .map_err(|error| format!("cannot read {}: {error}", path.display()))?;
    raw.trim()
        .parse::<u64>()
        .map_err(|error| format!("invalid RAPL counter {}: {error}", path.display()))
}

// Validate the actual powercap domain label, not only the filename.
// An explicit --counter to DRAM/cores must never be reported as PACKAGE.
fn is_package_identity(label: &str) -> bool {
    let Some(number) = label.trim().strip_prefix("package-") else {
        return false;
    };
    !number.is_empty() && number.bytes().all(|byte| byte.is_ascii_digit())
}

// Select a top-level package counter, never a subdomain (cores/DRAM).
// No interpolation or TDP fallback: missing hardware remains UNAVAILABLE.
fn find_package_counter() -> Result<PathBuf, String> {
    let root = env::var_os("SENS_RAPL_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("/sys/class/powercap"));
    let entries = fs::read_dir(&root)
        .map_err(|error| format!("RAPL_UNAVAILABLE root={} reason={error}", root.display()))?;
    let mut matches = Vec::new();
    for entry in entries {
        let entry = entry.map_err(|error| format!("RAPL_UNAVAILABLE entry={error}"))?;
        let file_name = entry.file_name();
        let name = file_name.to_string_lossy();
        let Some(id) = name.strip_prefix("intel-rapl:") else { continue };
        if id.is_empty() || !id.bytes().all(|byte| byte.is_ascii_digit()) { continue; }
        let dir = entry.path();
        let Ok(domain) = fs::read_to_string(dir.join("name")) else { continue };
        if !is_package_identity(&domain) { continue; }
        let energy = dir.join("energy_uj");
        if energy.is_file() && dir.join("max_energy_range_uj").is_file() {
            matches.push(energy);
        }
    }
    matches.sort();
    match matches.len() {
        1 => Ok(matches.remove(0)),
        0 => Err(format!(
            "RAPL_UNAVAILABLE no package energy_uj under {}", root.display()
        )),
        count => Err(format!(
            "RAPL_UNAVAILABLE {count} packages detected; refusing to report one socket as whole-machine energy"
        )),
    }
}

// RAPL counters are modular. This supports zero or one wrap; a second wrap
// cannot be inferred from only two reads and requires a shorter batch.
fn delta_uj(start: u64, end: u64, max: u64) -> Result<(u64, bool), String> {
    if max == 0 || start >= max || end >= max {
        return Err("RAPL_UNAVAILABLE invalid max_energy_range_uj or sample".into());
    }
    if end >= start {
        Ok((end - start, false))
    } else {
        Ok((max - start + end, true))
    }
}

fn run() -> Result<(), String> {
    let mut args = env::args_os().skip(1);
    let mut counter: Option<PathBuf> = None;
    let mut declared_operations: Option<u64> = None;
    let mut command = Vec::<OsString>::new();
    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--counter") => {
                counter = Some(PathBuf::from(args.next()
                    .ok_or("USAGE --counter requires an energy_uj path")?));
            }
            Some("--operations") => {
                let count = args.next().ok_or("USAGE --operations requires N")?;
                let count = count.to_str().ok_or("USAGE N must be UTF-8 decimal")?
                    .parse::<u64>().map_err(|_| "USAGE N must be a positive integer")?;
                if count == 0 { return Err("USAGE N must be positive".into()); }
                declared_operations = Some(count);
            }
            Some("--") => {
                command.extend(args);
                break;
            }
            _ => return Err("USAGE [--counter /path/energy_uj] [--operations N] -- command [args]".into()),
        }
    }
    if command.is_empty() {
        return Err("USAGE [--counter /path/energy_uj] [--operations N] -- command [args]".into());
    }
    let counter = match counter {
        Some(path) => path,
        None => find_package_counter()?,
    };
    if counter.file_name().and_then(|x| x.to_str()) != Some("energy_uj") {
        return Err("RAPL_UNAVAILABLE --counter must name energy_uj".into());
    }
    let domain_path = counter.parent().ok_or(
        "RAPL_UNAVAILABLE energy_uj counter has no domain parent"
    )?;
    let domain_name = fs::read_to_string(domain_path.join("name"))
        .map_err(|error| format!(
            "RAPL_UNAVAILABLE no verified powercap domain label for {}: {error}",
            counter.display()
        ))?;
    if !is_package_identity(&domain_name) {
        return Err(format!(
            "RAPL_UNAVAILABLE {} has domain '{}', not package-N; refuse mislabeled package energy",
            counter.display(), domain_name.trim()
        ));
    }
    let max = number(&counter.with_file_name("max_energy_range_uj"))?;
    let ceiling = power_ceiling_watts()?;
    // Include sensor I/O in the ambiguity window, not merely child elapsed time.
    let sensor_started = Instant::now();
    let start = number(&counter)?;
    let began = Instant::now();
    // Exactly one subprocess launch. N is supplied by the already-batched
    // workload, not silently emulated with N costly process startups.
    let mut child = Command::new(&command[0]);
    child.args(&command[1..]);
    let status = child.status().map_err(|error| format!("CHILD_FAILED spawn={error}"))?;
    let elapsed = began.elapsed();
    let end = number(&counter)?;
    let sensor_window = sensor_started.elapsed();
    if !status.success() {
        return Err(format!("CHILD_FAILED exit={status}; energy result withheld"));
    }
    if !at_most_one_wrap(max, sensor_window, ceiling) {
        return Err(format!("RAPL_UNRESOLVED ambiguous counter wrap range_uj={max} window_ns={} power_ceiling_w={ceiling}", sensor_window.as_nanos()));
    }
    let (energy_uj, wrapped) = delta_uj(start, end, max)?;
    if energy_uj == 0 {
        return Err("RAPL_UNRESOLVED zero observed counter delta; enlarge the batch".into());
    }
    println!(
        "RUST_RAPL_PACKAGE energy_uj={} energy_j={:.6} elapsed_ns={} elapsed_s={:.6} wrapped_once={} scope=whole_package_not_process counter={} status=MEASURED",
        energy_uj, energy_uj as f64 / 1_000_000.0, elapsed.as_nanos(), elapsed.as_secs_f64(),
        wrapped, counter.display()
    );
    if let Some(operations) = declared_operations {
        println!(
            "RUST_RAPL_NORMALIZED declared_operations={} uj_per_declared_operation={:.9} joules_per_declared_operation={:.9} scope=physical_only status=DECLARED_COUNT_NOT_VERIFIED",
            operations, energy_uj as f64 / operations as f64, energy_uj as f64 / 1_000_000.0 / operations as f64
        );
    }
    eprintln!("RAPL_NOTE package includes idle/background energy; no SENS semantic verdict; two samples cannot detect multiple wraps");
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(reason) => {
            eprintln!("{reason}");
            ExitCode::from(2)
        }
    }
}

#[cfg(test)]
mod mechanism_tests {
    use super::{at_most_one_wrap, delta_uj, is_package_identity};
    use std::time::Duration;

    #[test]
    fn wrap_window_requires_strict_energy_bound() {
        assert!(at_most_one_wrap(100_000_000, Duration::from_millis(40), 2_000));
        assert!(!at_most_one_wrap(100_000_000, Duration::from_millis(50), 2_000));
        assert!(!at_most_one_wrap(0, Duration::from_millis(1), 2_000));
    }

    #[test]
    fn monotonic_counter_delta() {
        assert_eq!(delta_uj(100, 140, 1000).unwrap(), (40, false));
    }

    #[test]
    fn one_wrap_delta() {
        assert_eq!(delta_uj(980, 20, 1000).unwrap(), (40, true));
    }

    #[test]
    fn invalid_hardware_reading_rejected() {
        assert!(delta_uj(1000, 10, 1000).is_err());
        assert!(delta_uj(1, 1, 0).is_err());
    }

    #[test]
    fn powercap_package_name_is_not_a_dram_or_core_domain() {
        assert!(is_package_identity("package-0\n"));
        assert!(is_package_identity("package-12"));
        assert!(!is_package_identity("dram\n"));
        assert!(!is_package_identity("core"));
        assert!(!is_package_identity("uncore"));
        assert!(!is_package_identity("package-"));
        assert!(!is_package_identity("package-unknown"));
    }
}
