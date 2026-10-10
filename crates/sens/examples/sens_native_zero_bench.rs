//! Native Zero v1: measure the existing, physical T5 -> exact domains -> bare executor.
//! No Core4 bootstrap, legacy named Lisp, width schedule, or invented interpreter.
//! Timing numbers are observations, never part of the language contract.
use sens::{
    decode_ternary_program, encode_binary_projection_ternary, encode_ternary_words,
    eval_lowered_expressions, eval_parsed_expressions, eval_t5_program, lower_program,
    parse_canonical_binary, render_ternary_words_spaced, Session, Value,
};
use std::{hint::black_box, time::Instant};

const QUOTE_T5: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");
const SCHEMA: &str = "sens-native-zero-t5/v1";

#[derive(Clone, Copy)]
enum Answer {
    Empty,
    Yes,
}

struct Case {
    name: &'static str,
    visible: &'static str,
    physical: Vec<u8>,
    answer: Answer,
}

fn median(samples: &[f64]) -> f64 {
    let mut sorted = samples.to_vec();
    sorted.sort_by(f64::total_cmp);
    sorted[sorted.len() / 2]
}

fn once<F: FnMut()>(iterations: usize, f: &mut F) -> f64 {
    let started = Instant::now();
    for _ in 0..iterations {
        f();
    }
    started.elapsed().as_nanos() as f64 / iterations as f64
}

fn measured<F: FnMut()>(mut f: F, samples: usize, iterations: usize) -> Vec<f64> {
    for _ in 0..16 {
        f();
    }
    (0..samples).map(|_| once(iterations, &mut f)).collect()
}

fn paired<F: FnMut(), G: FnMut()>(
    mut physical: F,
    mut visible: G,
    samples: usize,
    iterations: usize,
) -> (Vec<f64>, Vec<f64>) {
    for _ in 0..16 {
        physical();
        visible();
    }
    let mut left = Vec::with_capacity(samples);
    let mut right = Vec::with_capacity(samples);
    // Alternate the order, so warm-up and thermal drift do not always favor T5.
    for batch in 0..samples {
        if batch % 2 == 0 {
            left.push(once(iterations, &mut physical));
            right.push(once(iterations, &mut visible));
        } else {
            right.push(once(iterations, &mut visible));
            left.push(once(iterations, &mut physical));
        }
    }
    (left, right)
}

fn sample_json(xs: &[f64]) -> String {
    xs.iter()
        .map(|x| format!("{x:.2}"))
        .collect::<Vec<_>>()
        .join(",")
}

struct Evidence<'a> {
    case: &'a Case,
    phase: &'static str,
    words: usize,
    semantic_bits: usize,
    decode_ns: f64,
    prepared_eval_ns: f64,
    physical_ns: &'a [f64],
    visible_ns: &'a [f64],
    iterations: usize,
}

impl Evidence<'_> {
    fn emit(&self) -> Result<(), String> {
        let p = median(self.physical_ns);
        let v = median(self.visible_ns);
        if ![p, v, self.decode_ns, self.prepared_eval_ns]
            .iter()
            .all(|n| n.is_finite() && *n > 0.0)
        {
            return Err(format!("{}: invalid timing sample", self.case.name));
        }
        println!(
            "{{\"schema\":\"{SCHEMA}\",\"case\":\"{}\",\"phase\":\"{}\",\"oracle\":\"same-bare-exact-domain-result\",\"samples\":{},\"iterations\":{},\"physical_bytes\":{},\"visible_bytes\":{},\"word_count\":{},\"semantic_bits\":{},\"physical_median_ns\":{p:.2},\"visible_median_ns\":{v:.2},\"ratio_visible_over_physical\":{:.5},\"decode_d2_median_ns\":{:.2},\"prepared_eval_median_ns\":{:.2},\"physical_samples_ns\":[{}],\"visible_samples_ns\":[{}]}}",
            self.case.name,
            self.phase,
            self.physical_ns.len(),
            self.iterations,
            self.case.physical.len(),
            self.case.visible.len(),
            self.words,
            self.semantic_bits,
            v / p,
            self.decode_ns,
            self.prepared_eval_ns,
            sample_json(self.physical_ns),
            sample_json(self.visible_ns),
        );
        Ok(())
    }
}

fn benchmark(case: &Case, samples: usize, iterations: usize) -> Result<(), String> {
    let words = decode_ternary_program(&case.physical)
        .map_err(|e| format!("{}: physical T5/D2: {e:?}", case.name))?;
    if render_ternary_words_spaced(&words) != case.visible {
        return Err(format!("{}: physical bytes disagree with exact binary view", case.name));
    }
    if encode_ternary_words(&words).map_err(|e| format!("{e:?}"))? != case.physical {
        return Err(format!("{}: noncanonical physical encoding", case.name));
    }

    let ast = parse_canonical_binary(case.visible)
        .map_err(|e| format!("{}: visible D2: {e:?}", case.name))?;
    let physical_result = eval_t5_program(&case.physical, &mut Session::bare())
        .map_err(|e| format!("{}: bare physical eval: {e:?}", case.name))?;
    let visible_result = eval_parsed_expressions(&ast, &mut Session::bare())
        .map_err(|e| format!("{}: bare visible eval: {e:?}", case.name))?;
    if physical_result.value != visible_result.value
        || physical_result.output != visible_result.output
    {
        return Err(format!("{}: different results from physical and visible code", case.name));
    }
    if !physical_result.output.is_empty() {
        return Err(format!("{}: unexpected program output", case.name));
    }
    let expected = match case.answer {
        Answer::Empty => matches!(physical_result.value, Value::Nil),
        Answer::Yes => physical_result.value.as_predicate_bit() == Some(true),
    };
    if !expected {
        return Err(format!("{}: wrong exact D1/D3 result", case.name));
    }

    let semantic_bits: usize = words.iter().map(|w| w.width()).sum();
    let decode_samples = measured(
        || {
            black_box(decode_ternary_program(black_box(&case.physical)).expect("preflight T5"));
        },
        samples,
        iterations,
    );
    let decode_ns = median(&decode_samples);
    let lowered = lower_program(&ast);
    let mut eval_session = Session::bare();
    let prepared_samples = measured(
        || {
            let result = eval_lowered_expressions(black_box(&lowered), &mut eval_session)
                .expect("preflight bare lowered execution");
            black_box(result);
        },
        samples,
        iterations,
    );
    let prepared_eval_ns = median(&prepared_samples);

    let mut physical_session = Session::bare();
    let mut visible_session = Session::bare();
    let (warm_physical, warm_visible) = paired(
        || {
            let result = eval_t5_program(black_box(&case.physical), &mut physical_session)
                .expect("preflight physical native-zero");
            black_box(result);
        },
        || {
            let forms = parse_canonical_binary(black_box(case.visible))
                .expect("preflight visible D2");
            let result = eval_parsed_expressions(&forms, &mut visible_session)
                .expect("preflight visible native-zero");
            black_box(result);
        },
        samples,
        iterations,
    );
    Evidence {
        case,
        phase: "warm-bare-session",
        words: words.len(),
        semantic_bits,
        decode_ns,
        prepared_eval_ns,
        physical_ns: &warm_physical,
        visible_ns: &warm_visible,
        iterations,
    }
    .emit()?;

    let (fresh_physical, fresh_visible) = paired(
        || {
            let mut session = Session::bare();
            let result = eval_t5_program(black_box(&case.physical), &mut session)
                .expect("preflight fresh physical native-zero");
            black_box(result);
        },
        || {
            let mut session = Session::bare();
            let forms = parse_canonical_binary(black_box(case.visible))
                .expect("preflight fresh visible D2");
            let result = eval_parsed_expressions(&forms, &mut session)
                .expect("preflight fresh visible native-zero");
            black_box(result);
        },
        samples,
        iterations,
    );
    Evidence {
        case,
        phase: "fresh-bare-session",
        words: words.len(),
        semantic_bits,
        decode_ns,
        prepared_eval_ns,
        physical_ns: &fresh_physical,
        visible_ns: &fresh_visible,
        iterations,
    }
    .emit()
}

fn run() -> Result<(), String> {
    let args = std::env::args().collect::<Vec<_>>();
    let (samples, iterations) = match args.as_slice() {
        [_] => (9, 256),
        [_, flag1, n1, flag2, n2] if flag1 == "--samples" && flag2 == "--iterations" => (
            n1.parse::<usize>().map_err(|_| "invalid sample count")?,
            n2.parse::<usize>().map_err(|_| "invalid iteration count")?,
        ),
        _ => return Err("usage: sens_native_zero_bench [--samples ODD_3_TO_31 --iterations 16_TO_4096]".into()),
    };
    if !(3..=31).contains(&samples) || samples % 2 == 0 || !(16..=4096).contains(&iterations) {
        return Err("samples must be odd 3..31, iterations 16..4096".into());
    }
    if QUOTE_T5 != [0x63, 0x89, 0x06, 0xa1] {
        return Err("committed QUOTE fixture bytes have changed".into());
    }

    let cases = [
        Case {
            name: "d3-quote-empty",
            visible: "10 001 00 000 01",
            physical: QUOTE_T5.to_vec(),
            answer: Answer::Empty,
        },
        Case {
            name: "d1-yes",
            visible: "1",
            physical: encode_binary_projection_ternary("1")
                .map_err(|e| format!("D1 exact encoding: {e:?}"))?,
            answer: Answer::Yes,
        },
        Case {
            name: "d3-atom-empty",
            visible: "10 010 00 000 01",
            physical: encode_binary_projection_ternary("10 010 00 000 01")
                .map_err(|e| format!("D3 ATOM exact encoding: {e:?}"))?,
            answer: Answer::Yes,
        },
    ];
    // Invalid transport and malformed D2 must never produce a benchmark ratio.
    if eval_t5_program(&[243], &mut Session::bare()).is_ok() {
        return Err("invalid physical byte accepted".into());
    }
    let invalid_d2 = encode_ternary_words(
        &sens::parse_binary_source_words("10 001")
            .map_err(|e| format!("invalid D2 fixture source: {e:?}"))?
            .into_iter()
            .map(|token| token.word)
            .collect::<Vec<_>>(),
    )
    .map_err(|e| format!("invalid D2 fixture transport: {e:?}"))?;
    if eval_t5_program(&invalid_d2, &mut Session::bare()).is_ok() {
        return Err("unclosed D2 program accepted".into());
    }
    for case in &cases {
        benchmark(case, samples, iterations)?;
    }
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("NATIVE ZERO BLOCKED: {error}");
        std::process::exit(2);
    }
}
