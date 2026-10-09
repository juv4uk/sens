//! Гарячий бенчмарк чинної двійкової мови. Вимірює фазу, а не CLI startup.
//! Rust не затверджує жодного мовного закону: лише запускає вже чинні
//! T5/D2/нижчі механізми і порівнює їхні спостережувані результати.

use sens::{
    eval_lowered_expressions, eval_parsed_expressions, lower_program,
    open_ternary_program, parse_canonical_binary, Session,
};
use std::{env, fs, hint::black_box, time::Instant};

const PHASES: &[&str] = &["t5_open_d2", "d2_parse", "eval_from_ast", "eval_lowered"];

fn median_ns(mut xs: Vec<u128>) -> (u128, u128, u128) {
    xs.sort_unstable();
    let mid = xs[xs.len() / 2];
    // Найближчий ранг, не інтерпольований — p95 на фактичних замірах.
    let p95_index = (95 * xs.len()).div_ceil(100).saturating_sub(1);
    (mid, xs[p95_index], xs[0])
}

fn measure(mut f: impl FnMut(), count: usize, samples: usize) -> Vec<u128> {
    for _ in 0..count.min(100) {
        f();
    }
    let mut observations = Vec::with_capacity(samples);
    for _ in 0..samples {
        let started = Instant::now();
        for _ in 0..count {
            f();
        }
        observations.push(started.elapsed().as_nanos() / count as u128);
    }
    observations
}

fn main() {
    let args: Vec<_> = env::args().collect();
    assert_eq!(args.len(), 5, "usage: physical_sens_hot_bench FILE.sens FORMS WORK_BUDGET SAMPLES");
    let forms = args[2].parse::<usize>().expect("forms");
    let work_budget = args[3].parse::<usize>().expect("work budget");
    let samples = args[4].parse::<usize>().expect("samples");
    assert!((1..=2048).contains(&forms));
    assert!((4..=100_000_000).contains(&work_budget));
    assert!((3..=101).contains(&samples) && samples % 2 == 1);
    let count = (work_budget / forms).max(4);

    let physical = fs::read(&args[1]).expect("фізичний T5");
    let visible = open_ternary_program(&physical).expect("чинний фізичний T5/D2");
    let parsed = parse_canonical_binary(&visible).expect("канонічний D2");
    assert_eq!(parsed.len(), forms, "одна D3 QUOTE форма на один елемент");
    let lowered = lower_program(&parsed);
    let mut session = Session::default();

    // Наявні канонічні шляхи мають давати однаковий observable, до вимірювання.
    let ast_observable = eval_parsed_expressions(&parsed, &mut session)
        .expect("канонічне виконання AST");
    let lowered_observable = eval_lowered_expressions(&lowered, &mut session)
        .expect("виконання вже зниженого AST");
    assert_eq!(ast_observable, lowered_observable, "AST/lowered observable mismatch");
    let stable = ast_observable.value.to_string();
    black_box(&stable);

    for &phase in PHASES {
        let observations = match phase {
            "t5_open_d2" => measure(
                || { black_box(open_ternary_program(black_box(&physical)).expect("T5/D2")); },
                count, samples,
            ),
            "d2_parse" => measure(
                || { black_box(parse_canonical_binary(black_box(&visible)).expect("D2")); },
                count, samples,
            ),
            "eval_from_ast" => measure(
                || {
                    let result = eval_parsed_expressions(black_box(&parsed), &mut session)
                        .expect("AST execution");
                    black_box(result);
                }, count, samples,
            ),
            "eval_lowered" => measure(
                || {
                    let result = eval_lowered_expressions(black_box(&lowered), &mut session)
                        .expect("lowered execution");
                    black_box(result);
                }, count, samples,
            ),
            _ => unreachable!(),
        };
        let (median, p95, minimum) = median_ns(observations.clone());
        for (rep, elapsed_ns) in observations.iter().enumerate() {
            println!(
                "HOT_SAMPLE\tforms={forms}\tphase={phase}\trep={}\tns_op={elapsed_ns}",
                rep + 1,
            );
        }
        println!(
            "HOT_BENCH\tforms={forms}\tphase={phase}\titerations={count}\tsamples={samples}\tmedian_ns_op={median}\tp95_ns_op={p95}\tmin_ns_op={minimum}\tphysical_bytes={}\tobservable={stable:?}",
            physical.len(),
        );
    }
}
