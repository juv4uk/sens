//! Linux RAPL energy benchmark of an existing command; not a SENS semantic oracle.
//! Standalone Rust, no external dependencies or replacement of native SENS witnesses.

use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::Instant;

const POWERCAP: &str = "/sys/class/powercap";

struct Options {
    domain: Option<PathBuf>,
    units: u64,
    samples: usize,
    warmup: usize,
    command: Vec<String>,
}

fn usage() -> &'static str {
    "Linux RAPL: вимірювання енергії готового пакета SENS (не мовний оракул)\n\
     rustc --edition=2021 -O benchmarks/mechanism/rapl-energy-bench.rs -o /tmp/sens-rapl\n\
     /tmp/sens-rapl --units N [--samples 11] [--warmup 2] [--domain PATH] -- COMMAND [ARGS...]\n\
     --units N   кількість ФАКТИЧНО виконаних робочих одиниць за ОДИН запуск COMMAND;\n\
                 інструмент не перевіряє N і не запускає команду N разів\n\
     --domain    каталог RAPL із energy_uj та max_energy_range_uj;\n\
                 без параметра шукається єдиний package-* у /sys/class/powercap\n\
     --samples   непарна кількість виміряних запусків (1..=101)\n\
     --warmup    кількість невиміряних запусків (0..=100)\n\
     --help      ця довідка\n\
     Без лічильника RAPL / доступу до нього => помилка, НЕ нуль джоулів і НЕ PASS.\n"
}

fn arguments() -> Result<Options, String> {
    let mut iter = env::args().skip(1);
    let mut domain = None;
    let mut units = None;
    let mut samples = 11usize;
    let mut warmup = 2usize;
    let mut command = Vec::new();
    while let Some(arg) = iter.next() {
        if arg == "--" {
            command.extend(iter);
            break;
        }
        let value = match arg.as_str() {
            "--domain" | "--units" | "--samples" | "--warmup" => iter
                .next()
                .ok_or_else(|| format!("немає значення для {arg}"))?,
            _ => return Err(format!("невідомий параметр {arg}; див. --help")),
        };
        match arg.as_str() {
            "--domain" => domain = Some(PathBuf::from(value)),
            "--units" => {
                units = Some(value.parse::<u64>()
                    .map_err(|_| "--units мусить бути додатним цілим числом".to_owned())?)
            }
            "--samples" => {
                samples = value.parse::<usize>()
                    .map_err(|_| "--samples мусить бути цілим числом".to_owned())?
            }
            "--warmup" => {
                warmup = value.parse::<usize>()
                    .map_err(|_| "--warmup мусить бути цілим числом".to_owned())?
            }
            _ => unreachable!(),
        }
    }
    let units = units.ok_or("не вказано --units N")?;
    if units == 0 {
        return Err("--units мусить бути більшим за нуль".into());
    }
    if !(1..=101).contains(&samples) || samples % 2 == 0 {
        return Err("--samples має бути непарним числом від 1 до 101".into());
    }
    if warmup > 100 {
        return Err("--warmup має бути від 0 до 100".into());
    }
    if command.is_empty() {
        return Err("після -- очікується виконувана команда".into());
    }
    Ok(Options { domain, units, samples, warmup, command })
}

fn read_counter(path: &Path) -> Result<u64, String> {
    let raw = fs::read_to_string(path)
        .map_err(|e| format!("не вдалося читати {}: {e}", path.display()))?;
    raw.trim().parse::<u64>()
        .map_err(|e| format!("некоректне число в {}: {e}", path.display()))
}

fn locate_package() -> Result<PathBuf, String> {
    let entries = fs::read_dir(POWERCAP).map_err(|e| format!("{POWERCAP}: {e}"))?;
    let mut packages = Vec::new();
    for entry in entries {
        let entry = entry.map_err(|e| format!("powercap: {e}"))?;
        let name = entry.file_name();
        let Some(name) = name.to_str() else { continue };
        // Package-level directories only; nested PP0/DRAM have another ':'.
        if !name.starts_with("intel-rapl:") || name.matches(':').count() != 1 {
            continue;
        }
        let path = entry.path();
        let label = fs::read_to_string(path.join("name")).unwrap_or_default();
        if label.trim().starts_with("package-") && path.join("energy_uj").is_file() {
            packages.push(path);
        }
    }
    packages.sort();
    match packages.len() {
        1 => Ok(packages.remove(0)),
        0 => Err("не знайдено доступного package-* RAPL; задайте --domain PATH або використайте bare-metal Linux".into()),
        n => Err(format!("знайдено {n} package-доменів; задайте --domain PATH явно")),
    }
}

/// Difference of a bounded monotonic hardware counter, allowing ONE wrap.
/// More than one wrap cannot be detected from two reads; keep batches shorter
/// than the counter's full wrap interval.
fn energy_delta_uj(before: u64, after: u64, range: u64) -> Result<u64, String> {
    if range == 0 || before >= range || after >= range {
        return Err(format!("RAPL counter outside range: before={before}, after={after}, range={range}"));
    }
    Ok(if after >= before {
        after - before
    } else {
        (range - before) + after
    })
}

fn run_command(command: &[String]) -> Result<(), String> {
    let status = Command::new(&command[0])
        .args(&command[1..])
        .stdout(Stdio::null())
        .stderr(Stdio::inherit())
        .status()
        .map_err(|e| format!("не вдалося запустити {}: {e}", command[0]))?;
    if !status.success() {
        return Err(format!("програма завершилася з кодом {status}; вимір не приймається"));
    }
    Ok(())
}

fn main_measure() -> Result<(), String> {
    if env::consts::OS != "linux" {
        return Err("RAPL powercap потребує Linux".into());
    }
    let opts = arguments()?;
    let domain = match opts.domain {
        Some(ref domain) => domain.clone(),
        None => locate_package().map_err(rapl_unavailable)?,
    };
    let label = fs::read_to_string(domain.join("name"))
        .map_err(|e| rapl_unavailable(format!("{}: {e}", domain.display())))?;
    let range = read_counter(&domain.join("max_energy_range_uj"))
        .map_err(rapl_unavailable)?;
    // Fail early on permission errors rather than printing a fabricated zero.
    let initial = read_counter(&domain.join("energy_uj")).map_err(rapl_unavailable)?;
    energy_delta_uj(initial, initial, range)?;

    for _ in 0..opts.warmup {
        run_command(&opts.command)?;
    }

    eprintln!(
        "RAPL_ДЖЕРЕЛО domain={} name={} range_uj={} units_per_command={} warmup={} samples={}",
        domain.display(), label.trim(), range, opts.units, opts.warmup, opts.samples
    );
    let mut energies = Vec::with_capacity(opts.samples);
    for i in 0..opts.samples {
        let before = read_counter(&domain.join("energy_uj")).map_err(rapl_unavailable)?;
        let started = Instant::now();
        run_command(&opts.command)?;
        let elapsed = started.elapsed().as_nanos();
        let after = read_counter(&domain.join("energy_uj")).map_err(rapl_unavailable)?;
        let delta = energy_delta_uj(before, after, range)?;
        if delta == 0 || elapsed == 0 {
            return Err("нульова енергія/тривалість: збільште пакет роботи; це НЕ успішний вимір".into());
        }
        energies.push(delta);
        println!(
            "RAPL_ПРОБА index={} energy_uj={} duration_ns={} units={} uj_per_unit={:.6}",
            i + 1, delta, elapsed, opts.units, delta as f64 / opts.units as f64
        );
    }
    energies.sort_unstable();
    let median = energies[energies.len() / 2];
    let p90 = energies[(energies.len() * 9).div_ceil(10) - 1];
    println!(
        "RAPL_ПІДСУМОК name={} samples={} units={} median_energy_uj={} p90_energy_uj={} median_uj_per_unit={:.6} scope=system_package_or_selected_domain semantic_verdict=NOT_TESTED",
        label.trim(), opts.samples, opts.units, median, p90,
        median as f64 / opts.units as f64
    );
    Ok(())
}

fn rapl_unavailable(error: impl std::fmt::Display) -> String {
    let release = fs::read_to_string("/proc/sys/kernel/osrelease").unwrap_or_default();
    let hint = if release.to_ascii_lowercase().contains("microsoft") {
        "WSL2 зазвичай не надає апаратний RAPL; використайте bare-metal Linux"
    } else {
        "перевірте драйвер intel_rapl, каталог powercap, права на energy_uj"
    };
    format!("{error}; {hint}")
}

fn main() {
    if env::args().nth(1).as_deref() == Some("--help") {
        print!("{}", usage());
        return;
    }
    if let Err(error) = main_measure() {
        eprintln!("RAPL_ПОМИЛКА: {error}");
        std::process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::energy_delta_uj;

    #[test]
    fn physical_counter_without_wrap() {
        assert_eq!(energy_delta_uj(100, 220, 1000).unwrap(), 120);
    }

    #[test]
    fn physical_counter_single_wrap() {
        assert_eq!(energy_delta_uj(980, 20, 1000).unwrap(), 40);
    }

    #[test]
    fn physical_counter_bounds_fail_closed() {
        assert!(energy_delta_uj(1000, 20, 1000).is_err());
        assert!(energy_delta_uj(10, 20, 0).is_err());
        assert!(energy_delta_uj(10, 1000, 1000).is_err());
    }
}
