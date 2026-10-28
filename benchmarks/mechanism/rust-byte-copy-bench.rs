//! Rust: механічне копіювання байтів без SENS-оракулів.
//! rustc -O benchmarks/mechanism/rust-byte-copy-bench.rs -o /tmp/sens-rust-bench
//! /tmp/sens-rust-bench [--rapl]
//!
//! --rapl: опційний вимір енергії всього CPU package через Linux powercap.
//! Немає RAPL — немає чисел джоулів; TDP не підставляємо.
use std::fs;
use std::hint::black_box;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

const SOURCE: &[u8] = include_bytes!("../../lib/core4.sens");
const SAMPLES: usize = 11;
const BATCH: usize = 512;
const RAPL_MIN_INTERVAL: Duration = Duration::from_millis(300);

struct PackageRapl {
    directory: PathBuf,
    max_energy_uj: u64,
}

impl PackageRapl {
    fn detect() -> Result<Self, String> {
        let root = Path::new("/sys/class/powercap");
        let mut candidates = Vec::new();
        for entry in fs::read_dir(root).map_err(|e| format!("powercap unavailable: {e}"))? {
            let path = entry.map_err(|e| e.to_string())?.path();
            let Ok(name) = fs::read_to_string(path.join("name")) else {
                continue;
            };
            if name.trim().starts_with("package-") {
                candidates.push(path);
            }
        }
        // A single package is required: reporting one of several sockets as
        // total CPU energy would silently undercount a multi-socket machine.
        if candidates.len() != 1 {
            return Err(format!("expected one accessible RAPL package, found {}", candidates.len()));
        }
        let directory = candidates.remove(0);
        let max_energy_uj = read_counter(&directory.join("max_energy_range_uj"))?;
        if max_energy_uj == 0 {
            return Err("RAPL max_energy_range_uj is zero".into());
        }
        Ok(Self { directory, max_energy_uj })
    }

    fn energy_uj(&self) -> Result<u64, String> {
        let value = read_counter(&self.directory.join("energy_uj"))?;
        if value >= self.max_energy_uj {
            return Err("RAPL counter exceeds documented energy range".into());
        }
        Ok(value)
    }

    fn delta_uj(&self, before: u64, after: u64) -> u64 {
        // One rollover is supported. The measured 300 ms window must remain
        // far shorter than the hardware counter rollover interval.
        if after >= before {
            after - before
        } else {
            self.max_energy_uj - before + after
        }
    }
}

fn read_counter(path: &Path) -> Result<u64, String> {
    let raw = fs::read_to_string(path).map_err(|e| format!("{}: {e}", path.display()))?;
    raw.trim().parse::<u64>().map_err(|e| format!("{}: {e}", path.display()))
}

fn measure_package_energy(dest: &mut [u8]) -> Result<(), String> {
    let meter = PackageRapl::detect()?;
    let before = meter.energy_uj()?;
    let start = Instant::now();
    let mut copies = 0u64;
    let mut observed = 0u64;
    // Adapt the number of physical copies so two RAPL readings bracket a
    // measurable batch rather than a single sub-millisecond program call.
    while start.elapsed() < RAPL_MIN_INTERVAL {
        for offset in 0..BATCH {
            black_box(&mut *dest).copy_from_slice(black_box(SOURCE));
            observed = observed.wrapping_add(u64::from(black_box(dest[offset])));
        }
        copies += BATCH as u64;
    }
    let elapsed = start.elapsed();
    let after = meter.energy_uj()?;
    if dest.as_ref() != SOURCE {
        return Err("Rust mechanism changed source bytes".into());
    }
    if observed == 0 || copies == 0 {
        return Err("Rust workload has no observed copies".into());
    }
    let energy_uj = meter.delta_uj(before, after);
    if energy_uj == 0 {
        return Err("RAPL resolution insufficient for this batch (delta=0)".into());
    }
    println!(
        "RUST_MECHANISM_RAPL domain=package source={} measured_uj={} copies={} measured_uj_per_copy={:.6} elapsed_ns={} scope=whole_cpu_package_including_other_processes",
        meter.directory.display(),
        energy_uj,
        copies,
        energy_uj as f64 / copies as f64,
        elapsed.as_nanos(),
    );
    Ok(())
}

fn main() {
    let mut args = std::env::args().skip(1);
    let energy_requested = match (args.next().as_deref(), args.next()) {
        (None, None) => false,
        (Some("--rapl"), None) => true,
        _ => {
            eprintln!("Використання: sens-rust-bench [--rapl]");
            std::process::exit(2);
        }
    };
    assert!(SOURCE.len() >= BATCH, "source must contain a full observation batch");
    let mut dest = vec![0u8; SOURCE.len()];
    let mut samples = [0u128; SAMPLES];
    let mut checksum = 0u64;
    for sample in 0..=SAMPLES {
        let start = Instant::now();
        for offset in 0..BATCH {
            black_box(dest.as_mut_slice()).copy_from_slice(black_box(SOURCE));
            checksum = checksum.wrapping_add(u64::from(black_box(dest[offset])));
        }
        let elapsed = start.elapsed().as_nanos();
        assert_eq!(dest.as_slice(), SOURCE, "Rust mechanism lost bytes");
        if sample > 0 {
            samples[sample - 1] = elapsed;
        }
    }
    assert_ne!(checksum, 0, "benchmark observations cancelled unexpectedly");
    samples.sort_unstable();
    assert!(samples[0] > 0, "clock resolution too coarse");
    println!(
        "RUST_BYTE_COPY_BENCH source=lib/core4.sens bytes={} batch={} samples={} p50_ns={} p90_ns={} min_ns={} max_ns={} checksum={} scope=mechanism_only",
        SOURCE.len(), BATCH, SAMPLES, samples[5], samples[9], samples[0], samples[10], checksum
    );
    if energy_requested {
        if let Err(reason) = measure_package_energy(&mut dest) {
            eprintln!("RAPL: енергію не виміряно: {reason}");
        }
    }
}
