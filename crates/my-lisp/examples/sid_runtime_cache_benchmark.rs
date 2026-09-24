//! #1320 performance witness: after one immutable surface->SID resolution,
//! repeated evaluation of the same AST should converge toward the direct-SID path.

use my_lisp::{eval_parsed_expressions, load_core_library, parse, Session};
use std::{env, hint::black_box, time::Instant};

const SURFACE: &str = "(car (cons 1 (cons 2 ())))";
const SID: &str = "(00000101 (00000100 1 (00000100 2 ())))";

fn env_usize(name: &str, default: usize) -> usize {
    env::var(name)
        .ok()
        .and_then(|value| value.parse().ok())
        .filter(|value| *value > 0)
        .unwrap_or(default)
}

fn median_ns(mut samples: Vec<f64>) -> f64 {
    samples.sort_by(f64::total_cmp);
    samples[samples.len() / 2]
}

fn measure(iterations: usize, operation: &mut impl FnMut()) -> f64 {
    let started = Instant::now();
    for _ in 0..iterations {
        operation();
    }
    started.elapsed().as_nanos() as f64 / iterations as f64
}

fn sampled_pair(
    samples: usize,
    iterations: usize,
    mut a: impl FnMut(),
    mut b: impl FnMut(),
) -> (f64, f64) {
    let mut a_samples = Vec::with_capacity(samples);
    let mut b_samples = Vec::with_capacity(samples);
    for sample in 0..samples {
        if sample % 2 == 0 {
            a_samples.push(measure(iterations, &mut a));
            b_samples.push(measure(iterations, &mut b));
        } else {
            b_samples.push(measure(iterations, &mut b));
            a_samples.push(measure(iterations, &mut a));
        }
    }
    (median_ns(a_samples), median_ns(b_samples))
}

fn main() {
    let samples = env_usize("SID_CACHE_SAMPLES", 7);
    let iterations = env_usize("SID_CACHE_ITERATIONS", 50_000);

    let surface_forms = parse(SURFACE).expect("surface parses");
    let sid_forms = parse(SID).expect("SID parses");

    let mut surface_session = Session::default();
    let mut sid_session = Session::default();
    load_core_library(&mut surface_session).expect("surface core loads");
    load_core_library(&mut sid_session).expect("SID core loads");

    let first_surface_started = Instant::now();
    let first_surface = eval_parsed_expressions(&surface_forms, &mut surface_session)
        .expect("first surface eval");
    let first_surface_ns = first_surface_started.elapsed().as_nanos();

    let first_sid_started = Instant::now();
    let first_sid = eval_parsed_expressions(&sid_forms, &mut sid_session)
        .expect("first SID eval");
    let first_sid_ns = first_sid_started.elapsed().as_nanos();

    assert_eq!(first_surface.value, first_sid.value);
    assert_eq!(first_surface.value.to_string(), "1");

    // The first surface evaluation above is the one allowed resolution.
    // Everything sampled below is the already-resolved repeated path.
    let (warm_surface_ns, direct_sid_ns) = sampled_pair(
        samples,
        iterations,
        || {
            black_box(
                eval_parsed_expressions(&surface_forms, &mut surface_session)
                    .expect("warm surface eval"),
            );
        },
        || {
            black_box(
                eval_parsed_expressions(&sid_forms, &mut sid_session)
                    .expect("direct SID eval"),
            );
        },
    );

    println!(
        "SID_CACHE\titerations\t{iterations}\tsamples\t{samples}"
    );
    println!("SID_CACHE\tfirst-surface\t{first_surface_ns}\tns");
    println!("SID_CACHE\tfirst-direct-sid\t{first_sid_ns}\tns");
    println!("SID_CACHE\twarm-surface\t{warm_surface_ns:.2}\tns/op");
    println!("SID_CACHE\tdirect-sid\t{direct_sid_ns:.2}\tns/op");
    println!(
        "SID_CACHE\twarm-surface/direct-sid\t{:.4}\tratio",
        warm_surface_ns / direct_sid_ns
    );
}
