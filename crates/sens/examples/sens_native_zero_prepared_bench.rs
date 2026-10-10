//! SENS Native Zero v2: one-time physically validated program vs repeated decode.
//! These are DIFFERENT workloads: preparation is explicitly excluded from
//! reuse timings and reported separately. No Core4 or named-Lisp round-trip.
use sens::{
    encode_binary_projection_ternary, eval_t5_program, prepare_t5_program, Session, Value,
};
use std::{hint::black_box, time::Instant};

const QUOTE_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");
const SCHEMA: &str = "sens-native-zero-prepared/v1";

fn median(samples: &[f64]) -> f64 {
    let mut sorted = samples.to_vec();
    sorted.sort_by(f64::total_cmp);
    sorted[sorted.len() / 2]
}

fn sample<F: FnMut()>(iterations: usize, mut f: F) -> f64 {
    let start = Instant::now();
    for _ in 0..iterations {
        f();
    }
    start.elapsed().as_nanos() as f64 / iterations as f64
}

fn paired<F: FnMut(), G: FnMut()>(
    mut direct: F,
    mut prepared: G,
    samples: usize,
    iterations: usize,
) -> (Vec<f64>, Vec<f64>) {
    for _ in 0..24 {
        direct();
        prepared();
    }
    let mut a = Vec::with_capacity(samples);
    let mut b = Vec::with_capacity(samples);
    for i in 0..samples {
        if i % 2 == 0 {
            a.push(sample(iterations, &mut direct));
            b.push(sample(iterations, &mut prepared));
        } else {
            b.push(sample(iterations, &mut prepared));
            a.push(sample(iterations, &mut direct));
        }
    }
    (a, b)
}

fn series(xs: &[f64]) -> String {
    xs.iter().map(|x| format!("{x:.2}")).collect::<Vec<_>>().join(",")
}

fn run_case(
    name: &str,
    physical: &[u8],
    exact_yes: bool,
    samples: usize,
    iterations: usize,
) -> Result<(), String> {
    let prep_started = Instant::now();
    let executable = prepare_t5_program(physical)
        .map_err(|e| format!("{name}: T5 preparation BLOCKED: {e:?}"))?;
    let prep_ns = prep_started.elapsed().as_nanos();
    if prep_ns == 0 {
        return Err("preparation timer resolution insufficient".into());
    }
    let mut warm_direct = Session::bare();
    let mut warm_prepared = Session::bare();
    // Compare value plus output, not their printed presentation.
    let expected = eval_t5_program(physical, &mut Session::bare())
        .map_err(|e| format!("{name}: physical oracle: {e:?}"))?;
    let actual = executable.execute(&mut Session::bare())
        .map_err(|e| format!("{name}: prepared oracle: {e:?}"))?;
    if actual != expected || !actual.output.is_empty() {
        return Err(format!("{name}: prepared result/output differs from physical oracle"));
    }
    let correct = if exact_yes {
        actual.value.as_predicate_bit() == Some(true)
    } else {
        matches!(actual.value, Value::Nil)
    };
    if !correct {
        return Err(format!("{name}: wrong exact D1:YES or structural D3:EMPTY"));
    }
    for phase in ["warm-bare", "fresh-bare"] {
        let (direct, prepared) = match phase {
            "warm-bare" => paired(
                || {
                    black_box(eval_t5_program(black_box(physical), &mut warm_direct)
                        .expect("preflighted physical T5"));
                },
                || {
                    black_box(executable.execute(&mut warm_prepared)
                        .expect("preflighted immutable prepared T5"));
                },
                samples,
                iterations,
            ),
            _ => paired(
                || {
                    let mut session = Session::bare();
                    black_box(eval_t5_program(black_box(physical), &mut session)
                        .expect("preflighted fresh physical T5"));
                },
                || {
                    let mut session = Session::bare();
                    black_box(executable.execute(&mut session)
                        .expect("preflighted fresh prepared T5"));
                },
                samples,
                iterations,
            ),
        };
        let a = median(&direct);
        let b = median(&prepared);
        if ![a,b].iter().all(|x| x.is_finite() && *x > 0.0) {
            return Err(format!("{name}: invalid wall timings"));
        }
        println!(
            "{{\"schema\":\"{SCHEMA}\",\"case\":\"{name}\",\"phase\":\"{phase}\",\"oracle\":\"physical-and-prepared-exact-value-output-parity\",\"physical_bytes\":{},\"form_count\":{},\"samples\":{samples},\"iterations\":{iterations},\"preparation_once_ns\":{prep_ns},\"direct_median_ns\":{a:.2},\"prepared_median_ns\":{b:.2},\"ratio_direct_over_prepared\":{:.5},\"direct_samples_ns\":[{}],\"prepared_samples_ns\":[{}]}}",
            physical.len(), executable.form_count(), a / b, series(&direct), series(&prepared),
        );
    }
    Ok(())
}

fn run() -> Result<(), String> {
    let args = std::env::args().collect::<Vec<_>>();
    let (samples, iterations) = match args.as_slice() {
        [_] => (9, 128),
        [_, mode, count, reps, repeat]
            if mode == "--samples" && reps == "--iterations" =>
        {
            (count.parse::<usize>().map_err(|_| "invalid samples")?,
             repeat.parse::<usize>().map_err(|_| "invalid iterations")?)
        }
        _ => return Err("usage: sens_native_zero_prepared_bench [--samples ODD_3_TO_31 --iterations 16_TO_4096]".into()),
    };
    if !(3..=31).contains(&samples) || samples % 2 == 0 || !(16..=4096).contains(&iterations) {
        return Err("samples odd 3..31, iterations 16..4096 required".into());
    }
    if QUOTE_T5 != [0x63, 0x89, 0x06, 0xa1] {
        return Err("committed physical D3 QUOTE fixture changed".into());
    }
    // Fail-closed preparation is mandatory; no "cache" may adopt invalid bytes.
    if prepare_t5_program(&[243]).is_ok() {
        return Err("invalid physical byte admitted by prepared mechanism".into());
    }
    run_case("d3-quote-empty", QUOTE_T5, false, samples, iterations)?;
    let yes = encode_binary_projection_ternary("1")
        .map_err(|e| format!("D1 byte encoding: {e:?}"))?;
    run_case("d1-yes", &yes, true, samples, iterations)?;
    let atom = encode_binary_projection_ternary("10 010 00 000 01")
        .map_err(|e| format!("D3 ATOM byte encoding: {e:?}"))?;
    run_case("d3-atom-empty", &atom, true, samples, iterations)
}

fn main() {
    if let Err(error) = run() {
        eprintln!("PREPARED NATIVE ZERO BLOCKED: {error}");
        std::process::exit(2);
    }
}
