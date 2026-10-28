//! Linux RAPL package-energy metrology for a pre-verified native benchmark.
//! Rust owns mechanism/counters, Zig owns physical transport, SENS owns laws.
//! This is NOT a semantic oracle and does NOT grant a release or contest PASS.
//! No Python, JSON, TDP estimate, root escalation, or new semantic registry.

use std::{
    env, fs, io,
    path::{Path, PathBuf},
    process::{self, Command},
    time::Instant,
};

const POWERCAP_ROOT: &str = "/sys/class/powercap";

#[derive(Debug)]
struct PackageMeter {
    name: String,
    energy: PathBuf,
    max_range_uj: u64,
}

fn read_u64(path: &Path) -> io::Result<u64> {
    let text = fs::read_to_string(path)?;
    text.trim()
        .parse::<u64>()
        .map_err(|error| io::Error::new(io::ErrorKind::InvalidData, error))
}

fn discover_package() -> Result<PackageMeter, String> {
    let entries = fs::read_dir(POWERCAP_ROOT)
        .map_err(|error| format!("ENERGY_NOT_MEASURED reason=powercap_unavailable detail={error}"))?;
    let mut packages = Vec::new();
    for entry in entries {
        let entry = entry.map_err(|error| format!("ENERGY_NOT_MEASURED reason=enumeration_failed detail={error}"))?;
        let file_name = entry.file_name();
        let key = file_name.to_string_lossy();
        // Top-level packages only. Subdomains such as intel-rapl:0:0 are
        // not summed with their parent (which would double-count energy).
        if !key.starts_with("intel-rapl:") || key.matches(':').count() != 1 {
            continue;
        }
        let base = entry.path();
        let name = match fs::read_to_string(base.join("name")) {
            Ok(value) => value.trim().to_string(),
            Err(_) => continue,
        };
        if !name.starts_with("package") {
            continue;
        }
        let max_range_uj = read_u64(&base.join("max_energy_range_uj"))
            .map_err(|error| format!("ENERGY_NOT_MEASURED reason=range_unavailable detail={error}"))?;
        if max_range_uj == 0 {
            return Err("ENERGY_NOT_MEASURED reason=zero_counter_range".into());
        }
        packages.push(PackageMeter {
            name,
            energy: base.join("energy_uj"),
            max_range_uj,
        });
    }
    match packages.len() {
        0 => Err("ENERGY_NOT_MEASURED reason=no_package_rapl_counter".into()),
        1 => Ok(packages.remove(0)),
        count => Err(format!(
            "ENERGY_NOT_MEASURED reason=multiple_packages count={count} select_an_explicit_meter_first"
        )),
    }
}

// Two readings can compensate for at most one counter wrap. Caller must
// reject a run long enough for more wraps to become plausible.
fn delta_uj(before: u64, after: u64, max_range_uj: u64) -> Result<u64, String> {
    if max_range_uj == 0 || before >= max_range_uj || after >= max_range_uj {
        return Err("ENERGY_NOT_MEASURED reason=counter_out_of_range".into());
    }
    if after >= before {
        Ok(after - before)
    } else {
        Ok(max_range_uj - before + after)
    }
}

fn run() -> Result<(), String> {
    let mut args = env::args().skip(1);
    let unit_flag = args.next().ok_or("ENERGY_BENCH_INVALID reason=missing_mode")?;
    if unit_flag != "--operations" && unit_flag != "--runs" {
        return Err("ENERGY_BENCH_INVALID usage=rapl_mechanism_bench (--operations N | --runs N) -- PROGRAM [ARGS...]".into());
    }
    let count = args
        .next()
        .ok_or("ENERGY_BENCH_INVALID reason=missing_operation_count")?
        .parse::<u64>()
        .map_err(|_| "ENERGY_BENCH_INVALID reason=invalid_operation_count")?;
    if count == 0 {
        return Err("ENERGY_BENCH_INVALID reason=zero_operations".into());
    }
    if args.next().as_deref() != Some("--") {
        return Err("ENERGY_BENCH_INVALID reason=missing_double_dash".into());
    }
    let program = args
        .next()
        .ok_or("ENERGY_BENCH_INVALID reason=missing_program")?;
    let program_args: Vec<String> = args.collect();
    let child_launches = if unit_flag == "--runs" { count } else { 1 };
    let unit_type = if unit_flag == "--runs" { "process_launch" } else { "declared_internal_operation" };
    // Powercap can be inaccessible under WSL2, non-privileged containers
    // and some Linux hosts. Do not silently substitute watts or TDP.
    let meter = discover_package()?;
    let before = read_u64(&meter.energy)
        .map_err(|error| format!("ENERGY_NOT_MEASURED reason=read_before_failed detail={error}"))?;
    let clock = Instant::now();
    for launch in 0..child_launches {
        let status = Command::new(&program)
            .args(&program_args)
            .status()
            .map_err(|error| format!("ENERGY_NOT_MEASURED reason=program_launch_failed detail={error}"))?;
        if !status.success() {
            return Err(format!("ENERGY_BENCH_NOT_VERIFIED reason=program_failed launch={} status={status}", launch + 1));
        }
    }
    let after = read_u64(&meter.energy)
        .map_err(|error| format!("ENERGY_NOT_MEASURED reason=read_after_failed detail={error}"))?;
    let elapsed_ns = clock.elapsed().as_nanos();
    // At a very conservative 1 kW package bound, elapsed_ns numerically
    // equals the possible energy in uJ. This rejects long runs where two
    // RAPL reads cannot rule out multiple counter wraps; not a power claim.
    if elapsed_ns >= u128::from(meter.max_range_uj) {
        return Err("ENERGY_NOT_MEASURED reason=counter_wrap_ambiguous shorten_batch".into());
    }
    let used_uj = delta_uj(before, after, meter.max_range_uj)?;
    if used_uj == 0 {
        return Err("ENERGY_NOT_MEASURED reason=counter_did_not_advance increase_batch".into());
    }
    let joules = used_uj as f64 / 1_000_000.0;
    let joules_per_op = joules / count as f64;
    let ops_per_joule = count as f64 / joules;
    eprintln!(
        "RAPL_PACKAGE_SAMPLE scope=whole_cpu_package zone={} energy_uj={} elapsed_ns={} units={} unit_type={} child_launches={} joules_per_unit={:.12} units_per_joule={:.6} attribution=NOT_PROCESS_SPECIFIC release=NOT_CERTIFIED",
        meter.name, used_uj, elapsed_ns, count, unit_type, child_launches, joules_per_op, ops_per_joule
    );
    Ok(())
}

fn main() {
    if let Err(message) = run() {
        eprintln!("{message}");
        process::exit(2);
    }
}

#[cfg(test)]
mod mechanical_tests {
    use super::delta_uj;

    #[test]
    fn package_counter_no_wrap_and_single_wrap() {
        assert_eq!(delta_uj(100, 125, 1000).unwrap(), 25);
        assert_eq!(delta_uj(997, 3, 1000).unwrap(), 6);
    }

    #[test]
    fn invalid_physical_counter_range_is_rejected() {
        assert!(delta_uj(1, 2, 0).is_err());
        assert!(delta_uj(1000, 1, 1000).is_err());
        assert!(delta_uj(1, 1000, 1000).is_err());
    }
}
