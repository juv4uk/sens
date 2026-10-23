//! Objective paired ingest benchmark: visible 0/1 source vs packed source bytes.
//! This is not a semantic authority and not a self-describing file benchmark.
//! Width boundaries are supplied to the packed reader out of band.
use sens::{
    pack_binary_source_tokens, parse_binary_source_words, parse_canonical_binary,
    parse_canonical_packed_words, Expr, ExprKind,
};
use std::fmt::Write as _;
use std::hint::black_box;
use std::time::Instant;

const MIN_SAMPLE: std::time::Duration = std::time::Duration::from_millis(25);
const MAX_BATCHES_PER_SAMPLE: usize = 100_000;

fn shape(expr: &Expr, output: &mut String) {
    match &expr.kind {
        ExprKind::DomainIdentity(id) => {
            write!(output, "D{}:{:b};", id.width(), id.packed_bits()).unwrap();
        }
        ExprKind::List(items) => {
            output.push('[');
            for item in items.iter() {
                shape(item, output);
            }
            output.push(']');
        }
        ExprKind::Pair(head, tail) => {
            output.push('(');
            shape(head, output);
            output.push('.');
            shape(tail, output);
            output.push(')');
        }
        other => {
            write!(output, "{other:?}").unwrap();
        }
    }
}

fn fingerprint(forms: &[Expr]) -> String {
    let mut output = String::new();
    for form in forms {
        shape(form, &mut output);
        output.push('|');
    }
    output
}

fn elapsed_per_program<F, T>(
    iterations: usize,
    f: &mut F,
) -> Result<(f64, u128, u64, usize), String>
where
    F: FnMut() -> T,
{
    let start = Instant::now();
    let mut operations = 0u64;
    let mut batches = 0usize;
    while start.elapsed() < MIN_SAMPLE {
        for _ in 0..iterations {
            black_box(f());
            operations += 1;
        }
        batches += 1;
        if batches >= MAX_BATCHES_PER_SAMPLE && start.elapsed() < MIN_SAMPLE {
            return Err("adaptive sample exceeded its batch budget".into());
        }
    }
    let elapsed_ns = start.elapsed().as_nanos();
    if elapsed_ns == 0 || operations == 0 {
        return Err("insufficient timer resolution".into());
    }
    Ok((
        elapsed_ns as f64 / operations as f64,
        elapsed_ns,
        operations,
        batches,
    ))
}

fn median(values: &[f64]) -> f64 {
    let mut sorted = values.to_vec();
    sorted.sort_by(|a, b| a.total_cmp(b));
    sorted[sorted.len() / 2]
}

fn percentile(values: &[f64], percent: usize) -> f64 {
    let mut sorted = values.to_vec();
    sorted.sort_by(|a, b| a.total_cmp(b));
    let index = (sorted.len() * percent).div_ceil(100).saturating_sub(1);
    sorted[index.min(sorted.len() - 1)]
}

fn benchmark(case: &str, form: &str, forms: usize, samples: usize) -> Result<(), String> {
    let visible = std::iter::repeat_n(form, forms)
        .collect::<Vec<_>>()
        .join("\n");
    let tokens =
        parse_binary_source_words(&visible).map_err(|e| format!("{case}: source lexing: {e:?}"))?;
    let widths: Vec<usize> = tokens.iter().map(|token| token.word.width()).collect();
    let packed = pack_binary_source_tokens(&tokens);
    let visual_ast =
        parse_canonical_binary(&visible).map_err(|e| format!("{case}: visible D2: {e:?}"))?;
    let physical_ast = parse_canonical_packed_words(&packed, &widths)
        .map_err(|e| format!("{case}: packed D2: {e:?}"))?;
    if fingerprint(&visual_ast) != fingerprint(&physical_ast) {
        return Err(format!("{case}: D2/domain AST parity failed: no performance claim"));
    }
    if visual_ast.len() != forms || physical_ast.len() != forms {
        return Err(format!("{case}: expected {forms} complete D2 forms"));
    }

    // Same grammar and exact domain AST. Width boundaries are supplied out of
    // band and intentionally excluded from the packed payload and timed loop.
    // Each closure allocates its parsed AST on every invocation.
    let mut visible_read =
        || parse_canonical_binary(black_box(&visible)).expect("preflighted visible input");
    let mut packed_read = || {
        parse_canonical_packed_words(black_box(&packed), black_box(&widths))
            .expect("preflighted packed input")
    };

    let iterations = (16_384 / forms).clamp(32, 2_048);
    for _ in 0..32 {
        black_box(visible_read());
        black_box(packed_read());
    }
    let mut visible_ns = Vec::with_capacity(samples);
    let mut packed_ns = Vec::with_capacity(samples);
    for sample in 0..samples {
        let (v, p) = if sample.is_multiple_of(2) {
            let v = elapsed_per_program(iterations, &mut visible_read)?;
            let p = elapsed_per_program(iterations, &mut packed_read)?;
            (v, p)
        } else {
            let p = elapsed_per_program(iterations, &mut packed_read)?;
            let v = elapsed_per_program(iterations, &mut visible_read)?;
            (v, p)
        };
        visible_ns.push(v.0);
        packed_ns.push(p.0);
        println!(
            "RUST_PACKED_VISIBLE_SAMPLE\tcase={case}\tforms={forms}\tsample={}\tvisible_elapsed_ns={}\tvisible_programs={}\tvisible_ns_per_program={:.2}\tvisible_batches={}\tpacked_elapsed_ns={}\tpacked_programs={}\tpacked_ns_per_program={:.2}\tpacked_batches={}\titerations_per_batch={}\ttarget_sample_ns={}",
            sample + 1,
            v.1,
            v.2,
            v.0,
            v.3,
            p.1,
            p.2,
            p.0,
            p.3,
            iterations,
            MIN_SAMPLE.as_nanos(),
        );
    }

    println!(
        "RUST_PACKED_VISIBLE_SUMMARY\tcase={case}\tforms={forms}\tsamples={samples}\tvisible_p50_ns_per_program={:.2}\tvisible_p90_ns_per_program={:.2}\tpacked_p50_ns_per_program={:.2}\tpacked_p90_ns_per_program={:.2}\tratio_visible_over_packed_p50={:.5}\tvisible_source_bytes={}\tpacked_payload_bytes={}\tsemantic_payload_bits={}\twidth_schedule_entries={}\tpreflight=same-D2-domain-AST\tboundary_policy=caller-supplied-excluded-from-payload",
        median(&visible_ns),
        percentile(&visible_ns, 90),
        median(&packed_ns),
        percentile(&packed_ns, 90),
        median(&visible_ns) / median(&packed_ns),
        visible.len(),
        packed.byte_len(),
        packed.bit_len(),
        widths.len(),
    );
    Ok(())
}

fn main() {
    let mut samples = 9usize;
    let args: Vec<String> = std::env::args().collect();
    if args.len() == 3 && args[1] == "--samples" {
        samples = args[2].parse().unwrap_or(0);
    } else if args.len() != 1 {
        eprintln!("usage: packed_vs_visible_bench [--samples 3..99]");
        std::process::exit(2);
    }
    if !(3..=99).contains(&samples) || samples.is_multiple_of(2) {
        eprintln!("samples must be odd, between 3 and 99");
        std::process::exit(2);
    }
    let cases = [
        ("quote-empty-1", "10 001 00 000 01", 1),
        ("quote-empty-64", "10 001 00 000 01", 64),
        ("quote-empty-256", "10 001 00 000 01", 256),
        ("d7-data-64", "10 1000001 00 1000010 01", 64),
        ("w9-data-64", "10 100000001 00 00000001 01", 64),
    ];
    for (name, source, count) in cases {
        if let Err(error) = benchmark(name, source, count, samples) {
            eprintln!("BLOCKED: {error}");
            std::process::exit(2);
        }
    }
}
