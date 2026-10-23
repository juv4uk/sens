//! Native process-level measurements for committed physical T5 SENS fixtures.
//! This is a mechanism benchmark, not a semantic oracle or cross-language ranking.
//! Each timing lane is admitted only after byte/view and stdout parity checks.
use std::{
    env,
    fs,
    path::{Path, PathBuf},
    process::Command,
    time::Instant,
};

const FIXTURES: &[&str] = &[
    "tests/fixtures/migration-quote-cohort-main/quote-legacy.sens",
    "tests/fixtures/migration-multiform-cohort-main/two-forms.sens",
    "tests/fixtures/migration-d1-cond-cohort/branch.sens",
    "tests/fixtures/migration-pair-cohort-main/pair-cons.sens",
    "tests/fixtures/migration-pair-cohort-main/pair-car-cdr.sens",
    "tests/fixtures/migration-d4-selector-cohort/caar.sens",
    "tests/fixtures/migration-eq-cond-cohort-main/eq-cond-select.sens",
    "tests/fixtures/migration-eq-cond-cohort-main/eq-cond-skip.sens",
];

#[derive(Clone, Copy, Debug)]
enum Lane {
    SensExec,
    TritEval,
    TritOpen,
}

impl Lane {
    const ALL: [Self; 3] = [Self::SensExec, Self::TritEval, Self::TritOpen];

    fn name(self) -> &'static str {
        match self {
            Self::SensExec => "sens-exec",
            Self::TritEval => "sens-trit-eval",
            Self::TritOpen => "sens-trit-open",
        }
    }
}

fn repository_root() -> Result<PathBuf, String> {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .map_err(|error| format!("repository root: {error}"))
}

fn required_executable(name: &str) -> Result<PathBuf, String> {
    let value = env::var_os(name).ok_or_else(|| format!("missing environment variable {name}"))?;
    let path = PathBuf::from(value)
        .canonicalize()
        .map_err(|error| format!("{name}: {error}"))?;
    if !path.is_file() {
        return Err(format!("{name} is not a file: {}", path.display()));
    }
    Ok(path)
}

fn hex_sha256(bytes: &[u8]) -> String {
    sens::sha256_source(bytes)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn current_commit(root: &Path) -> Result<String, String> {
    let output = Command::new("git")
        .args(["rev-parse", "HEAD"])
        .current_dir(root)
        .output()
        .map_err(|error| format!("git rev-parse HEAD: {error}"))?;
    if !output.status.success() {
        return Err("git rev-parse HEAD failed".into());
    }
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_owned())
}

fn visible_view_path(physical: &Path) -> Result<PathBuf, String> {
    let parent = physical
        .parent()
        .ok_or_else(|| format!("fixture has no parent: {}", physical.display()))?;
    let stem = physical
        .file_stem()
        .ok_or_else(|| format!("fixture has no file stem: {}", physical.display()))?;
    Ok(parent.join(stem))
}

fn invoke(
    lane: Lane,
    sens: &Path,
    sens_trit: &Path,
    fixture: &Path,
    root: &Path,
) -> Result<(u128, Vec<u8>), String> {
    let mut command = match lane {
        Lane::SensExec => {
            let mut command = Command::new(sens);
            command.arg(fixture);
            command
        }
        Lane::TritEval => {
            let mut command = Command::new(sens_trit);
            command.arg("eval").arg(fixture);
            command
        }
        Lane::TritOpen => {
            let mut command = Command::new(sens_trit);
            command.arg("open").arg(fixture);
            command
        }
    };
    command.current_dir(root);
    let started = Instant::now();
    let output = command
        .output()
        .map_err(|error| format!("{} {}: {error}", lane.name(), fixture.display()))?;
    let elapsed_ns = started.elapsed().as_nanos();
    if !output.status.success() {
        return Err(format!(
            "{} failed for {} with {}: {}",
            lane.name(),
            fixture.display(),
            output.status,
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }
    Ok((elapsed_ns, output.stdout))
}

fn percentile_nearest_rank(sorted: &[u128], numerator: usize, denominator: usize) -> u128 {
    let rank = (sorted.len() * numerator).div_ceil(denominator).max(1);
    sorted[rank.saturating_sub(1).min(sorted.len() - 1)]
}

fn run_benchmark() -> Result<(), String> {
    let root = repository_root()?;
    let sens = required_executable("SENS_PHYSICAL_T5_SENS")?;
    let sens_trit = required_executable("SENS_PHYSICAL_T5_TRIT")?;
    let repetitions = env::var("SENS_PHYSICAL_T5_REPS")
        .ok()
        .and_then(|value| value.parse::<usize>().ok())
        .unwrap_or(21);
    let warmups = env::var("SENS_PHYSICAL_T5_WARMUPS")
        .ok()
        .and_then(|value| value.parse::<usize>().ok())
        .unwrap_or(4);
    if repetitions < 5 || warmups == 0 {
        return Err("repetitions must be >= 5 and warmups must be >= 1".into());
    }

    let commit = current_commit(&root)?;
    let sens_sha = hex_sha256(&fs::read(&sens).map_err(|error| error.to_string())?);
    let trit_sha = hex_sha256(&fs::read(&sens_trit).map_err(|error| error.to_string())?);

    for relative in FIXTURES {
        let physical = root.join(relative);
        let visible = visible_view_path(&physical)?;
        let physical_bytes = fs::read(&physical)
            .map_err(|error| format!("missing physical fixture {}: {error}", physical.display()))?;
        let visible_bytes = fs::read(&visible)
            .map_err(|error| format!("missing visible view {}: {error}", visible.display()))?;
        if physical_bytes.is_empty() || visible_bytes.is_empty() {
            return Err(format!("empty source/carrier in fixture {relative}"));
        }

        let mut baselines: Vec<Vec<u8>> = Vec::with_capacity(Lane::ALL.len());
        let mut first_ns: Vec<u128> = Vec::with_capacity(Lane::ALL.len());
        for lane in Lane::ALL {
            let (elapsed, stdout) = invoke(lane, &sens, &sens_trit, &physical, &root)?;
            first_ns.push(elapsed);
            baselines.push(stdout);
        }
        if baselines[0] != baselines[1] {
            return Err(format!("execution parity mismatch between sens and sens-trit for {relative}"));
        }
        if baselines[2] != visible_bytes {
            return Err(format!(
                "sens-trit open differs from the committed extensionless view for {relative}"
            ));
        }

        let physical_sha = hex_sha256(&physical_bytes);
        let visible_sha = hex_sha256(&visible_bytes);
        let fixture = Path::new(relative)
            .file_name()
            .and_then(|name| name.to_str())
            .unwrap_or(relative);
        println!(
            "RUST_PHYSICAL_T5_PREFLIGHT\tcommit={commit}\tfixture={fixture}\tphysical_bytes={}\tview_bytes={}\tphysical_sha256={physical_sha}\tview_sha256={visible_sha}\tsens_sha256={sens_sha}\tsens_trit_sha256={trit_sha}\tparity=exact",
            physical_bytes.len(),
            visible_bytes.len()
        );

        for _ in 0..warmups {
            for (index, lane) in Lane::ALL.iter().copied().enumerate() {
                let (_, output) = invoke(lane, &sens, &sens_trit, &physical, &root)?;
                if output != baselines[index] {
                    return Err(format!("warm-up stdout changed: fixture={relative} lane={}", lane.name()));
                }
            }
        }

        let mut samples = vec![Vec::<u128>::with_capacity(repetitions); Lane::ALL.len()];
        for repetition in 0..repetitions {
            // Rotate lane order to avoid always favoring the same OS-cache state.
            for offset in 0..Lane::ALL.len() {
                let index = (repetition + offset) % Lane::ALL.len();
                let lane = Lane::ALL[index];
                let (elapsed_ns, output) = invoke(lane, &sens, &sens_trit, &physical, &root)?;
                if output != baselines[index] {
                    return Err(format!(
                        "stdout changed during timing: fixture={relative} lane={}",
                        lane.name()
                    ));
                }
                samples[index].push(elapsed_ns);
                println!(
                    "RUST_PHYSICAL_T5_SAMPLE\tcommit={commit}\tfixture={fixture}\tlane={}\trepetition={}\twall_ns={elapsed_ns}\tphysical_bytes={}\tstdout_sha256={}",
                    lane.name(),
                    repetition + 1,
                    physical_bytes.len(),
                    hex_sha256(&output)
                );
            }
        }

        for (index, lane) in Lane::ALL.iter().copied().enumerate() {
            let values = &samples[index];
            let mut sorted = values.clone();
            sorted.sort_unstable();
            let median = sorted[(sorted.len() - 1) / 2];
            let p95 = percentile_nearest_rank(&sorted, 95, 100);
            println!(
                "RUST_PHYSICAL_T5_SUMMARY\tcommit={commit}\tfixture={fixture}\tlane={}\tsamples={}\tfirst_process_ns={}\tp50_wall_ns={median}\tp95_wall_ns={p95}\tmin_wall_ns={}\tmax_wall_ns={}\tphysical_bytes={}\tparity=exact",
                lane.name(),
                values.len(),
                first_ns[index],
                sorted[0],
                sorted[sorted.len() - 1],
                physical_bytes.len()
            );
        }
    }
    Ok(())
}


#[cfg(feature = "zig-transport")]
fn physical_t5_persistent_session_benchmark() {
    const TEST_ID: &str = "physical-t5-persistent-session";
    let root = repository_root().expect("repository root");
    let relative = FIXTURES[0]; // Pure quoted data: replay must not mutate bindings.
    let physical = root.join(relative);
    let bytes = fs::read(&physical).expect("tracked physical .sens fixture");
    let sens = required_executable("SENS_PHYSICAL_T5_SENS").expect("physical SENS binary");
    let sens_trit = required_executable("SENS_PHYSICAL_T5_TRIT").expect("physical transport binary");
    let (_, baseline_stdout) =
        invoke(Lane::SensExec, &sens, &sens_trit, &physical, &root)
            .expect("cold physical SENS baseline");

    // Production Zig ingress restores only transport words. SENS owns the
    // domain identities, D2 admission, and execution semantics.
    let restored = sens_cli::zig_transport::decode_t5m_exact_words(&bytes)
        .expect("real Zig T5M decode");
    let words = restored
        .into_iter()
        .map(|word| sens::ExactDomainWord::from_physical_width_bits(word.width, &word.bits))
        .collect::<Result<Vec<_>, _>>()
        .expect("exact SENS domain identities");
    let program = sens::PhysicalT5Program::from_exact_domain_words_owned(words)
        .expect("real SENS D2 admission");
    let mut session = sens::Session::bare();
    sens::install_ratified_d5_macro_mechanism(&session);

    let repetitions = env::var("SENS_PHYSICAL_T5_REPS")
        .ok()
        .and_then(|value| value.parse::<usize>().ok())
        .unwrap_or(21);
    let warmups = env::var("SENS_PHYSICAL_T5_WARMUPS")
        .ok()
        .and_then(|value| value.parse::<usize>().ok())
        .unwrap_or(4);
    assert!(repetitions >= 5 && warmups >= 1, "{TEST_ID}: insufficient samples");
    let mut samples = Vec::with_capacity(repetitions);
    for call in 0..(warmups + repetitions) {
        let started = Instant::now();
        let result = program.execute(&mut session).unwrap_or_else(|error| {
            panic!("{TEST_ID}: physical SENS execution call={call} error={error}")
        });
        let elapsed_ns = started.elapsed().as_nanos();

        // execute() exposes the session's cumulative transcript; take only
        // the output produced since the preceding call for CLI parity.
        let mut visible = Vec::new();
        for line in session.environment.output_take_new() {
            visible.extend_from_slice(line.as_bytes());
            visible.push(b'\n');
        }
        visible.extend_from_slice(result.value.to_string().as_bytes());
        visible.push(b'\n');
        assert_eq!(
            visible, baseline_stdout,
            "{TEST_ID}: observable drift call={call} fixture={relative}"
        );
        std::hint::black_box(result);
        if call >= warmups {
            samples.push(elapsed_ns);
            println!(
                "RUST_PHYSICAL_SESSION_SAMPLE\tfixture={relative}\tcall={}\texecute_ns={elapsed_ns}\tparity=exact",
                call - warmups + 1
            );
        }
    }
    let mut sorted = samples;
    sorted.sort_unstable();
    let median = sorted[(sorted.len() - 1) / 2];
    let p95 = percentile_nearest_rank(&sorted, 95, 100);
    println!(
        "RUST_PHYSICAL_SESSION_SUMMARY\tcommit={}\tfixture={relative}\tphysical_sha256={}\tsamples={}\tp50_execute_ns={median}\tp95_execute_ns={p95}\tmin_execute_ns={}\tmax_execute_ns={}\tscope=in-process-reused-session-with-d2-lowering\tparity=exact",
        current_commit(&root).expect("current commit"),
        hex_sha256(&bytes),
        sorted.len(),
        sorted[0],
        sorted[sorted.len() - 1]
    );
}

#[test]
#[ignore = "explicit native physical T5 benchmark; run from sens-performance.yml"]
fn physical_sens_runtime_benchmark() {
    run_benchmark().unwrap_or_else(|error| panic!("RUST_PHYSICAL_T5_BENCHMARK_FAILED: {error}"));
    #[cfg(feature = "zig-transport")]
    physical_t5_persistent_session_benchmark();
}
