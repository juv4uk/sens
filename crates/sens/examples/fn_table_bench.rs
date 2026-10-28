//! #1413: кожна функція таблиці мови окремо — англійське ім'я проти SENS-коду.
//!
//! Вхід — TSV від `benchmarks/sens-surface/function_table.py`
//! (`код \t англійське \t українське`). Для кожної функції:
//! 1. підбирається перший набір аргументів, з яким англійський виклик
//!    обчислюється без помилки;
//! 2. той самий виклик через SENS-код: працює / немає механізму;
//! 3. результати звіряються (для недетермінованих функцій — лише факт);
//! 4. обидва виклики, розібрані один раз, міряються по черзі.
//!
//! Помилка виконання на калібруванні чи повторі перериває вимірювання:
//! швидкий Err ніколи не зараховується як швидке обчислення.
//!
//! `cargo run --release -p sens --example fn_table_bench -- TABLE.tsv [SAMPLES] [TARGET_MS]`

use sens::{eval_parsed_expressions, load_core_library, parse, Session};
use std::{env, fs, hint::black_box, time::Instant};

/// Побічні ефекти (вивід, eval довільного коду, читання вводу) — не міряємо.
const SKIP_SIDE_EFFECTS: &[&str] = &["print", "princ", "eval", "read", "read-all", "defmacro"];

/// SENS-виклик валить процес (panic) — відтворено окремо через CLI,
/// див. #1413; позначається, не виконується.
const KNOWN_SENS_PANIC: &[&str] = &["/"];

/// Результат залежить від часу/лічильника — звіряється лише факт виклику.
const NONDETERMINISTIC: &[&str] = &[
    "mono-ns",
    "unix-time-now",
    "utc-now",
    "mono-ms",
    "elapsed-ns",
    "створити-символ",
    "env",
    "deadline-reached?",
    "deadline-reached-at?",
    "deadline-from",
    "deadline-after-ns",
    "timezone-detect",
    "timezone-name",
    "timezone-offset-seconds",
];

/// Кандидати аргументів, від порожнього до складних; береться перший,
/// з яким англійський виклик не повертає помилку.
const CANDIDATES: &[&str] = &[
    "",
    "a",
    "(t 1)",
    "(x) x",
    "bench-tmp 1",
    "1",
    "4 2",
    "9",
    "(quote (3 1 2))",
    "(quote a)",
    "\"abc\"",
    "\"abc\" \"b\"",
    "\"abc\" 1 2",
    "\"abc\" 1",
    "(quote (3 1 2)) 1",
    "1 (quote (3 1 2))",
    "(quote (3 1 2)) (quote (4 5))",
    "(lambda (x) x) (quote (1 2 3))",
    "(lambda (a b) a) 0 (quote (1 2 3))",
    "(lambda (a b) a) (quote (1 2 3)) 0",
    "(quote a) (quote ((a . 1) (b . 2)))",
    "(quote (a b)) (quote (1 2))",
    "97",
    "3 0",
    "1 2 3",
    "1000000",
];

fn median(mut xs: Vec<f64>) -> f64 {
    xs.sort_by(f64::total_cmp);
    xs[xs.len() / 2]
}

fn fresh() -> Session {
    let mut s = Session::default();
    load_core_library(&mut s).expect("core loads");
    s
}

fn try_eval(src: &str, session: &mut Session) -> Result<String, String> {
    let forms = parse(src).map_err(|e| format!("parse: {e}"))?;
    eval_parsed_expressions(&forms, session)
        .map(|r| r.value.to_string())
        .map_err(|e| e.to_string().lines().next().unwrap_or("").to_owned())
}

// Проби спільного середовища можуть створити зв'язування, яких немає
// на початку реального вимірювання. Перевіряємо ОБИДВІ форми поза таймером.
fn verify_clean_pair(src_a: &str, src_b: &str) -> Result<(String, String), String> {
    let mut en = fresh();
    let a = try_eval(src_a, &mut en).map_err(|error| format!("clean EN: {error}"))?;
    let mut sens = fresh();
    let b = try_eval(src_b, &mut sens).map_err(|error| format!("clean SENS: {error}"))?;
    Ok((a, b))
}

fn bench(
    src_a: &str,
    src_b: &str,
    samples: usize,
    target_ms: f64,
) -> (f64, f64, f64, f64) {
    let fa = parse(src_a).unwrap();
    let fb = parse(src_b).unwrap();
    // Калібрування має власне середовище: прогрів не змінює стан замірів.
    let mut calibration = fresh();
    // Калібрування на SENS-формі.
    let mut iters = 1usize;
    loop {
        let t = Instant::now();
        for _ in 0..iters {
            let result = eval_parsed_expressions(&fb, &mut calibration)
                .unwrap_or_else(|error| panic!("SENS calibration failed: {error}"));
            black_box(result.value);
        }
        let ms = t.elapsed().as_secs_f64() * 1e3;
        if ms >= target_ms / 4.0 || iters >= 1 << 24 {
            iters = ((iters as f64) * (target_ms / ms.max(1e-6)))
                .ceil()
                .max(1.0) as usize;
            break;
        }
        iters *= 4;
    }
    // Пошук аргументів і калібрування могли змінити середовище.
    // Обидві серії отримують незалежні чисті сесії лише після калібрування.
    let mut sa = fresh();
    let mut sb = fresh();
    let (mut xa, mut xb, mut ratios) = (Vec::new(), Vec::new(), Vec::new());
    for s in 0..samples {
        let run = |f: &[_], sess: &mut Session| {
            let t = Instant::now();
            for _ in 0..iters {
                let result = eval_parsed_expressions(f, sess)
                    .unwrap_or_else(|error| panic!("benchmark sample failed: {error}"));
                black_box(result.value);
            }
            t.elapsed().as_nanos() as f64 / iters as f64
        };
        let (a, b) = if s % 2 == 0 {
            let a = run(&fa, &mut sa);
            (a, run(&fb, &mut sb))
        } else {
            let b = run(&fb, &mut sb);
            (run(&fa, &mut sa), b)
        };
        xa.push(a);
        xb.push(b);
        ratios.push(a / b);
    }
    let rmin = ratios.iter().cloned().fold(f64::INFINITY, f64::min);
    let rmax = ratios.iter().cloned().fold(0.0, f64::max);
    (median(xa), median(xb), rmin, rmax)
}

fn require_measurements(measured_ok: usize) -> Result<(), &'static str> {
    if measured_ok == 0 {
        Err("FN_TABLE_NO_VALID_MEASUREMENTS")
    } else {
        Ok(())
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let table = fs::read_to_string(args.get(1).expect("TABLE.tsv")).expect("read table");
    let samples: usize = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(7);
    let target_ms: f64 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(40.0);

    println!("FN\tcode\ten\tstatus\targs\ten_ns\tsens_ns\ten/sens\tratio_min\tratio_max\tnote");
    let mut measured_ok = 0usize;
    for line in table.lines() {
        let cols: Vec<&str> = line.split('\t').collect();
        let (code, en) = (cols[0], cols[1]);
        let row = |status: &str, a: &str, note: &str| {
            println!("FN\t{code}\t{en}\t{status}\t{a}\t\t\t\t\t\t{note}");
        };
        if en == "()" {
            row("no-english-surface", "", "");
            continue;
        }
        if SKIP_SIDE_EFFECTS.contains(&en) {
            row("skipped-side-effect", "", "");
            continue;
        }
        if KNOWN_SENS_PANIC.contains(&en) {
            row(
                "sens-panics",
                "4 2",
                "arithmetic.rs:237 unreachable!(known arithmetic operator)",
            );
            continue;
        }
        let mut sa = fresh();
        let mut sb = fresh();
        // Перший набір аргументів, з яким працюють ОБИДВІ форми; інакше —
        // запам'ятати першу помилку SENS для набору, що працює англійською.
        let mut en_ok_any = false;
        let mut first_sens_err: Option<(&str, String)> = None;
        let mut first_dirty_probe: Option<(&str, String)> = None;
        let mut found: Option<(&str, String, String)> = None;
        for a in CANDIDATES {
            let en_src = format!("({en} {a})");
            let sens_src = format!("({code} {a})");
            if try_eval(&en_src, &mut sa).is_err() {
                continue;
            }
            en_ok_any = true;
            match try_eval(&sens_src, &mut sb) {
                Ok(_) => match verify_clean_pair(&en_src, &sens_src) {
                    Ok((ev, sv)) => {
                        found = Some((a, ev, sv));
                        break;
                    }
                    Err(error) => {
                        // Dirty probe succeeded; fresh execution did not.
                        // Never turn this into a benchmark sample or a false PASS.
                        if first_dirty_probe.is_none() {
                            first_dirty_probe = Some((a, error));
                        }
                    }
                },
                Err(error) => {
                    if first_sens_err.is_none() {
                        first_sens_err = Some((a, error));
                    }
                }
            }
        }
        let Some((a, en_value, sens_value)) = found else {
            if let Some((args, error)) = first_dirty_probe {
                row("probe-state-dependent", args, &error.replace('\t', " "));
            } else if !en_ok_any {
                row(
                    "no-working-args",
                    "",
                    "жоден кандидат аргументів не підійшов англійській формі",
                );
            } else {
                let (a, e) = first_sens_err.unwrap();
                let status = if e.contains("no callable mechanism") {
                    "sens-no-mechanism"
                } else {
                    "sens-fails-other"
                };
                row(status, a, &e.replace('\t', " "));
            }
            continue;
        };
        let sens_src = format!("({code} {a})");
        if sens_value != en_value && !NONDETERMINISTIC.contains(&en) {
            row(
                "results-differ",
                a,
                &format!("en={en_value} sens={sens_value}").replace('\t', " "),
            );
            continue;
        }
        let (en_ns, sens_ns, rmin, rmax) = bench(
            &format!("({en} {a})"),
            &sens_src,
            samples,
            target_ms,
        );
        println!(
            "FN\t{code}\t{en}\tok\t{a}\t{en_ns:.1}\t{sens_ns:.1}\t{:.3}\t{rmin:.3}\t{rmax:.3}\t{}",
            en_ns / sens_ns,
            if NONDETERMINISTIC.contains(&en) {
                "nondeterministic"
            } else {
                ""
            }
        );
        measured_ok += 1;
    }
    if let Err(reason) = require_measurements(measured_ok) {
        eprintln!("{reason}");
        std::process::exit(2);
    }
}

