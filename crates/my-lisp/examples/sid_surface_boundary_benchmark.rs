//! #1277/#1278 evidence: where does an English surface spelling still cost
//! after the program has already been parsed?
//!
//! This benchmark deliberately separates four boundaries:
//! 1. parser cost,
//! 2. surface -> Sid8 resolution cost,
//! 3. repeated evaluation of the SAME parsed AST,
//! 4. end-to-end source evaluation.
//!
//! The key witness is "ast-lowered": it starts from the English AST and
//! mechanically replaces admitted call-head spellings with their Sid8 exactly
//! once. If ast-lowered converges with an AST parsed from bare SID source,
//! while ast-surface remains slower, the remaining gap is repeated
//! surface-resolution work in the evaluator rather than parser cost or a
//! semantic difference.

use my_lisp::{
    eval_parsed_expressions, eval_program, load_core_library, parse,
    semantic_registry_export, Expr, ExprKind, Session,
};
use std::{env, hint::black_box, rc::Rc, time::Instant};

const EQ_SURFACE: &str = "(eq 1 1)";
const EQ_SID: &str = "(00000011 1 1)";
const LIST_SURFACE: &str = "(car (cons 1 (cons 2 ())))";
const LIST_SID: &str = "(00000101 (00000100 1 (00000100 2 ())))";

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
    let warmup = (iterations / 20).clamp(200, 2_000);
    for _ in 0..warmup {
        operation();
    }
    let started = Instant::now();
    for _ in 0..iterations {
        operation();
    }
    started.elapsed().as_nanos() as f64 / iterations as f64
}

/// Alternate A/B order across samples so thermal/frequency drift is not
/// systematically charged to one side.
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

fn lower_call_heads(expression: &Expr) -> Expr {
    match &expression.kind {
        ExprKind::List(items) if !items.is_empty() => {
            let mut lowered: Vec<Expr> = items.iter().map(lower_call_heads).collect();
            if let ExprKind::Symbol(name) = &items[0].kind {
                if let Some(sid) = semantic_registry_export::semantic_id_for_admitted_surface(name) {
                    lowered[0] = Expr {
                        kind: ExprKind::Sid(sid),
                        span: items[0].span,
                    };
                }
            }
            Expr {
                kind: ExprKind::List(Rc::from(lowered.into_boxed_slice())),
                span: expression.span,
            }
        }
        ExprKind::Pair(left, right) => Expr {
            kind: ExprKind::Pair(
                Rc::new(lower_call_heads(left)),
                Rc::new(lower_call_heads(right)),
            ),
            span: expression.span,
        },
        _ => expression.clone(),
    }
}

fn lower_program(forms: &[Expr]) -> Vec<Expr> {
    forms.iter().map(lower_call_heads).collect()
}

fn eval_ast_ns(
    source_surface: &str,
    source_sid: &str,
    samples: usize,
    iterations: usize,
) -> (f64, f64, f64, f64) {
    let surface_forms = parse(source_surface).expect("surface source parses");
    let lowered_forms = lower_program(&surface_forms);
    let sid_forms = parse(source_sid).expect("SID source parses");

    let mut verify_surface = Session::default();
    load_core_library(&mut verify_surface).expect("core library loads");
    let surface_value = eval_parsed_expressions(&surface_forms, &mut verify_surface)
        .expect("surface AST evaluates")
        .value;

    let mut verify_lowered = Session::default();
    load_core_library(&mut verify_lowered).expect("core library loads");
    let lowered_value = eval_parsed_expressions(&lowered_forms, &mut verify_lowered)
        .expect("lowered AST evaluates")
        .value;

    let mut verify_sid = Session::default();
    load_core_library(&mut verify_sid).expect("core library loads");
    let sid_value = eval_parsed_expressions(&sid_forms, &mut verify_sid)
        .expect("SID AST evaluates")
        .value;

    assert_eq!(surface_value, lowered_value, "lowering must preserve value");
    assert_eq!(surface_value, sid_value, "surface and SID programs must agree");

    let mut surface_session = Session::default();
    let mut lowered_session = Session::default();
    let mut sid_session = Session::default();
    load_core_library(&mut surface_session).expect("surface core loads");
    load_core_library(&mut lowered_session).expect("lowered core loads");
    load_core_library(&mut sid_session).expect("SID core loads");

    let (surface_ns, lowered_ns) = sampled_pair(
        samples,
        iterations,
        || {
            black_box(
                eval_parsed_expressions(&surface_forms, &mut surface_session)
                    .expect("surface AST evaluation"),
            );
        },
        || {
            black_box(
                eval_parsed_expressions(&lowered_forms, &mut lowered_session)
                    .expect("lowered AST evaluation"),
            );
        },
    );

    let (lowered_again_ns, sid_ns) = sampled_pair(
        samples,
        iterations,
        || {
            black_box(
                eval_parsed_expressions(&lowered_forms, &mut lowered_session)
                    .expect("lowered AST evaluation"),
            );
        },
        || {
            black_box(
                eval_parsed_expressions(&sid_forms, &mut sid_session)
                    .expect("SID AST evaluation"),
            );
        },
    );

    (
        surface_ns,
        (lowered_ns + lowered_again_ns) / 2.0,
        sid_ns,
        surface_value.to_string().len() as f64,
    )
}

fn main() {
    let samples = env_usize("SID_BENCH_SAMPLES", 7);
    let iterations = env_usize("SID_BENCH_ITERATIONS", 30_000);
    let resolution_iterations = env_usize("SID_RESOLUTION_ITERATIONS", 500_000);

    let car_sid = semantic_registry_export::semantic_id_for_admitted_surface("car")
        .expect("car has admitted SID");
    let cons_sid = semantic_registry_export::semantic_id_for_admitted_surface("cons")
        .expect("cons has admitted SID");
    assert_eq!(car_sid, my_lisp::sid!(00000101));
    assert_eq!(cons_sid, my_lisp::sid!(00000100));

    let (resolve_surface_ns, ready_sid_ns) = sampled_pair(
        samples,
        resolution_iterations,
        || {
            black_box(
                semantic_registry_export::semantic_id_for_admitted_surface(black_box("car"))
                    .expect("car resolves"),
            );
            black_box(
                semantic_registry_export::semantic_id_for_admitted_surface(black_box("cons"))
                    .expect("cons resolves"),
            );
        },
        || {
            black_box(car_sid);
            black_box(cons_sid);
        },
    );

    let (parse_surface_ns, parse_sid_ns) = sampled_pair(
        samples,
        iterations,
        || {
            black_box(parse(black_box(LIST_SURFACE)).expect("surface parses"));
        },
        || {
            black_box(parse(black_box(LIST_SID)).expect("SID parses"));
        },
    );

    let surface_forms = parse(LIST_SURFACE).expect("surface parses");
    let (lower_once_ns, parse_sid_again_ns) = sampled_pair(
        samples,
        iterations,
        || {
            black_box(lower_program(black_box(&surface_forms)));
        },
        || {
            black_box(parse(black_box(LIST_SID)).expect("SID parses"));
        },
    );

    let (eq_surface_ast_ns, eq_lowered_ast_ns, eq_sid_ast_ns, _) =
        eval_ast_ns(EQ_SURFACE, EQ_SID, samples, iterations);
    let (list_surface_ast_ns, list_lowered_ast_ns, list_sid_ast_ns, _) =
        eval_ast_ns(LIST_SURFACE, LIST_SID, samples, iterations);

    let mut surface_source_session = Session::default();
    let mut sid_source_session = Session::default();
    load_core_library(&mut surface_source_session).expect("surface core loads");
    load_core_library(&mut sid_source_session).expect("SID core loads");
    let (source_surface_ns, source_sid_ns) = sampled_pair(
        samples,
        iterations,
        || {
            black_box(
                eval_program(LIST_SURFACE, &mut surface_source_session)
                    .expect("surface source evaluates"),
            );
        },
        || {
            black_box(eval_program(LIST_SID, &mut sid_source_session).expect("SID source evaluates"));
        },
    );

    println!(
        "SID_BOUNDARY\titerations\t{iterations}\tsamples\t{samples}\tresolution_iterations\t{resolution_iterations}"
    );
    println!(
        "SID_BOUNDARY\tsource-bytes\tsurface\t{}\tsid\t{}",
        LIST_SURFACE.len(),
        LIST_SID.len()
    );
    println!(
        "SID_BOUNDARY\tresolution-surface-2-lookups\t{resolve_surface_ns:.2}\tns/op"
    );
    println!("SID_BOUNDARY\tresolution-ready-2-sids\t{ready_sid_ns:.2}\tns/op");
    println!(
        "SID_BOUNDARY\tresolution-delta\t{:.2}\tns/op",
        resolve_surface_ns - ready_sid_ns
    );
    println!("SID_BOUNDARY\tparse-surface\t{parse_surface_ns:.2}\tns/op");
    println!("SID_BOUNDARY\tparse-sid\t{parse_sid_ns:.2}\tns/op");
    println!(
        "SID_BOUNDARY\tparse-sid/surface\t{:.4}\tratio",
        parse_sid_ns / parse_surface_ns
    );
    println!("SID_BOUNDARY\tlower-once\t{lower_once_ns:.2}\tns/op");
    println!(
        "SID_BOUNDARY\tparse-sid-repeat-control\t{parse_sid_again_ns:.2}\tns/op"
    );

    println!("SID_BOUNDARY\teq-ast-surface\t{eq_surface_ast_ns:.2}\tns/op");
    println!("SID_BOUNDARY\teq-ast-lowered\t{eq_lowered_ast_ns:.2}\tns/op");
    println!("SID_BOUNDARY\teq-ast-direct-sid\t{eq_sid_ast_ns:.2}\tns/op");
    println!(
        "SID_BOUNDARY\teq-lowered/surface\t{:.4}\tratio",
        eq_lowered_ast_ns / eq_surface_ast_ns
    );
    println!(
        "SID_BOUNDARY\teq-direct-sid/lowered\t{:.4}\tratio",
        eq_sid_ast_ns / eq_lowered_ast_ns
    );

    println!(
        "SID_BOUNDARY\tlist-ast-surface\t{list_surface_ast_ns:.2}\tns/op"
    );
    println!(
        "SID_BOUNDARY\tlist-ast-lowered\t{list_lowered_ast_ns:.2}\tns/op"
    );
    println!(
        "SID_BOUNDARY\tlist-ast-direct-sid\t{list_sid_ast_ns:.2}\tns/op"
    );
    println!(
        "SID_BOUNDARY\tlist-lowered/surface\t{:.4}\tratio",
        list_lowered_ast_ns / list_surface_ast_ns
    );
    println!(
        "SID_BOUNDARY\tlist-direct-sid/lowered\t{:.4}\tratio",
        list_sid_ast_ns / list_lowered_ast_ns
    );

    println!("SID_BOUNDARY\tsource-surface\t{source_surface_ns:.2}\tns/op");
    println!("SID_BOUNDARY\tsource-sid\t{source_sid_ns:.2}\tns/op");
    println!(
        "SID_BOUNDARY\tsource-sid/surface\t{:.4}\tratio",
        source_sid_ns / source_surface_ns
    );

    let saved_per_list_eval = list_surface_ast_ns - list_lowered_ast_ns;
    if saved_per_list_eval > 0.0 {
        println!(
            "SID_BOUNDARY\tlowering-break-even-list-evals\t{:.2}\tevals",
            lower_once_ns / saved_per_list_eval
        );
    } else {
        println!("SID_BOUNDARY\tlowering-break-even-list-evals\tn/a");
    }
}
