//! Недорогий вимір повного інтерактивного рядка REPL: проєкція → Zig T5M → SENS.

use super::{eval_repl_step_t5m, render_repl_reply, ReplState, ReplSurface};
use ratatui::{
    style::{Color, Modifier, Style},
    text::Line,
    widgets::{Block, Borders, Paragraph, Wrap},
    Frame,
};
use std::{hint::black_box, time::Instant};

pub(super) const DEFAULT_SAMPLES: usize = 1_000;
const DEFAULT_WARMUPS: usize = 25;
const MIN_SAMPLES: usize = 100;
const MAX_SAMPLES: usize = 10_000;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct Percentiles {
    p50: u128,
    p95: u128,
    p99: u128,
}

impl Percentiles {
    fn from_samples(samples: &[u128]) -> Option<Self> {
        if samples.is_empty() {
            return None;
        }
        let mut sorted = samples.to_vec();
        sorted.sort_unstable();
        Some(Self {
            p50: nearest_rank(&sorted, 50),
            p95: nearest_rank(&sorted, 95),
            p99: nearest_rank(&sorted, 99),
        })
    }
}

fn nearest_rank(sorted: &[u128], percentile: usize) -> u128 {
    let rank = sorted.len().saturating_mul(percentile).div_ceil(100).max(1);
    sorted[rank.saturating_sub(1).min(sorted.len() - 1)]
}

fn parse_process_memory(status: &str) -> Option<ProcessMemory> {
    fn field_kib(status: &str, field: &str) -> Option<u64> {
        status.lines().find_map(|line| {
            let value = line.strip_prefix(field)?.trim();
            let mut parts = value.split_whitespace();
            let kib = parts.next()?.parse().ok()?;
            (parts.next() == Some("kB")).then_some(kib)
        })
    }

    Some(ProcessMemory {
        rss_kib: field_kib(status, "VmRSS:")?,
        peak_rss_kib: field_kib(status, "VmHWM:")?,
    })
}

fn process_memory_snapshot() -> Option<ProcessMemory> {
    let status = std::fs::read_to_string("/proc/self/status").ok()?;
    parse_process_memory(&status)
}

fn memory_delta(start: Option<ProcessMemory>, end: Option<ProcessMemory>) -> Option<MemoryDelta> {
    let (start, end) = (start?, end?);
    Some(MemoryDelta {
        start_rss_kib: start.rss_kib,
        end_rss_kib: end.rss_kib,
        peak_growth_kib: end.peak_rss_kib.saturating_sub(start.peak_rss_kib),
    })
}

#[derive(Clone, Debug)]
struct BenchmarkRow {
    name: &'static str,
    source: String,
    expected: &'static str,
    percentiles: Percentiles,
    footprint: ProgramFootprint,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct ProgramFootprint {
    domain_words: usize,
    domain_bits: usize,
    t5m_bytes: usize,
}

fn program_footprint(
    words: &[crate::zig_transport::ExactT5MWord],
    physical_t5m: &[u8],
) -> Result<ProgramFootprint, String> {
    if words.is_empty() || physical_t5m.is_empty() {
        return Err("empty SENS program has no measurable footprint".into());
    }
    let domain_bits = words.iter().try_fold(0usize, |total, word| {
        if word.width == 0 || word.bits.len() != word.width || word.bits.iter().any(|bit| *bit > 1)
        {
            return None;
        }
        total.checked_add(word.width)
    });
    let domain_bits = domain_bits.ok_or("invalid or oversized exact SENS program")?;
    Ok(ProgramFootprint {
        domain_words: words.len(),
        domain_bits,
        t5m_bytes: physical_t5m.len(),
    })
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct ProcessMemory {
    rss_kib: u64,
    peak_rss_kib: u64,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct MemoryDelta {
    start_rss_kib: u64,
    end_rss_kib: u64,
    peak_growth_kib: u64,
}

#[derive(Clone, Debug)]
struct BenchmarkReport {
    surface: ReplSurface,
    warmups: usize,
    samples: usize,
    rows: Vec<BenchmarkRow>,
    memory: Option<MemoryDelta>,
}

#[derive(Clone, Debug)]
struct BenchmarkCase {
    name: &'static str,
    setup: Option<String>,
    source: String,
    expected: &'static str,
}

fn benchmark_surface(surface: ReplSurface) -> ReplSurface {
    if surface == ReplSurface::Core {
        ReplSurface::UkrainianFull
    } else {
        surface
    }
}

fn projected_name(surface: ReplSurface, ukr_name: &str) -> Result<String, String> {
    let identity = super::surface_catalog::identity_for_surface_name("укр", ukr_name)?
        .ok_or_else(|| format!("укр проєкція не має резидента {ukr_name}"))?;
    super::surface_catalog::name_for_identity(surface.code(), &identity)?.ok_or_else(|| {
        format!(
            "проєкція {} не має назви для чинної identity {identity}",
            surface.code()
        )
    })
}

fn cases_for(surface: ReplSurface) -> Result<Vec<BenchmarkCase>, String> {
    let add = projected_name(surface, "додати")?;
    let car = projected_name(surface, "перше")?;
    let cons = projected_name(surface, "сполучити")?;
    Ok(vec![
        BenchmarkCase {
            name: "арифметика",
            setup: None,
            source: format!("({add} 123 456)"),
            expected: "579",
        },
        BenchmarkCase {
            name: "доступ-до-пари",
            setup: None,
            source: format!("({car} ({cons} 123 456))"),
            expected: "123",
        },
        BenchmarkCase {
            name: "вкладені-виклики",
            setup: None,
            source: format!("({add} ({car} ({cons} 123 456)) ({car} ({cons} 789 101)))"),
            expected: "912",
        },
    ])
}

fn isolated_repl_state(parent: &ReplState, surface: ReplSurface) -> ReplState {
    let user_environment = parent.user_environment.child();
    let mut session = parent.session.clone();
    session.environment = user_environment.clone();
    ReplState {
        session,
        base_environment: parent.base_environment.clone(),
        user_environment,
        surface,
        sens_loop: parent.sens_loop,
        sens_repl_bootstrapped: parent.sens_repl_bootstrapped,
    }
}

fn evaluate_visible(state: &mut ReplState, source: &str) -> Result<String, String> {
    let result = eval_repl_step_t5m(state, source)?;
    if !result.output.is_empty() {
        return Err(format!(
            "benchmark workload unexpectedly wrote output: {:?}",
            result.output
        ));
    }
    Ok(render_repl_reply(
        &result.value,
        state.surface.presentation(),
    ))
}

fn run_suite(
    parent: &ReplState,
    requested_samples: usize,
    warmups: usize,
) -> Result<BenchmarkReport, String> {
    if !(MIN_SAMPLES..=MAX_SAMPLES).contains(&requested_samples) {
        return Err(format!(
            "sample count must be {MIN_SAMPLES}..={MAX_SAMPLES}"
        ));
    }
    let surface = benchmark_surface(parent.surface);
    let mut rows = Vec::new();
    let memory_start = process_memory_snapshot();

    for case in cases_for(surface)? {
        let mut state = isolated_repl_state(parent, surface);
        if let Some(setup) = &case.setup {
            evaluate_visible(&mut state, setup)?;
        }
        let exact_words = super::prepare_t5m_repl_words(&case.source, surface, &state.session)?;
        let carrier_words = super::exact_t5m_carrier_words(&exact_words)?;
        let physical_t5m = crate::zig_transport::encode_t5m_exact_words(&carrier_words)?;
        let footprint = program_footprint(&carrier_words, &physical_t5m)?;
        let baseline = evaluate_visible(&mut state, &case.source)?;
        if baseline != case.expected {
            return Err(format!(
                "{} result mismatch: expected {:?}, got {:?}",
                case.name, case.expected, baseline
            ));
        }

        for _ in 0..warmups {
            let visible = evaluate_visible(&mut state, black_box(&case.source))?;
            if visible != baseline {
                return Err(format!("{} changed during warm-up", case.name));
            }
        }

        let mut samples = Vec::with_capacity(requested_samples);
        for _ in 0..requested_samples {
            let started = Instant::now();
            let visible = evaluate_visible(&mut state, black_box(&case.source))?;
            let elapsed_ns = started.elapsed().as_nanos();
            if visible != baseline {
                return Err(format!("{} changed during measurement", case.name));
            }
            black_box(&visible);
            samples.push(elapsed_ns);
        }
        let percentiles = Percentiles::from_samples(&samples)
            .ok_or_else(|| format!("{} produced no timing samples", case.name))?;
        rows.push(BenchmarkRow {
            name: case.name,
            source: case.source,
            expected: case.expected,
            percentiles,
            footprint,
        });
    }

    Ok(BenchmarkReport {
        surface,
        warmups,
        samples: requested_samples,
        rows,
        memory: memory_delta(memory_start, process_memory_snapshot()),
    })
}

pub(super) fn render_in_repl(parent: &ReplState, samples: usize) -> Result<(), String> {
    let report = run_suite(parent, samples, DEFAULT_WARMUPS)?;
    let width = std::env::var("COLUMNS")
        .ok()
        .and_then(|value| value.parse::<u16>().ok())
        .unwrap_or(80)
        .clamp(80, 160);
    let height = 24u16;
    let backend = ratatui::backend::TestBackend::new(width, height);
    let mut terminal = ratatui::Terminal::new(backend)
        .map_err(|error| format!("Помилка термінала Ratatui: {error}"))?;
    terminal
        .draw(|frame| draw_report(frame, &report))
        .map_err(|error| format!("Помилка відображення Ratatui: {error}"))?;

    let buffer = terminal.backend().buffer();
    for row in 0..height {
        let start = usize::from(row) * usize::from(width);
        let end = start + usize::from(width);
        let line = buffer.content()[start..end]
            .iter()
            .map(|cell| cell.symbol())
            .collect::<String>();
        println!("{}", line.trim_end());
    }
    Ok(())
}

fn draw_report(frame: &mut Frame, report: &BenchmarkReport) {
    let mut lines = vec![
        Line::from(format!(
            "Шлях: {} → Zig T5M → двійкові слова → виконання REPL/SENS",
            report.surface.code()
        )),
        Line::from(format!(
            "Профіль: {} · прогрів: {} · вимірів на випадок: {} · архітектура: {}",
            if cfg!(debug_assertions) {
                "налагоджувальна збірка (не для порівняння швидкодії)"
            } else {
                "випускна збірка"
            },
            report.warmups,
            report.samples,
            std::env::consts::ARCH
        )),
        Line::from("Час на рядок REPL (нс); вивід у термінал не міряється."),
        Line::from("Розмір: точні доменні біти та фізичний T5M-носій кожної програми."),
        Line::from(match report.memory {
            Some(memory) => format!(
                "Пам'ять RSS процесу: {}→{} KiB · приріст нового піку +{} KiB.",
                memory.start_rss_kib, memory.end_rss_kib, memory.peak_growth_kib
            ),
            None => "Пам'ять RSS недоступна на цій платформі.".to_string(),
        }),
        Line::from(
            "RSS охоплює REPL; нульовий приріст пікового використання не означає відсутності виділень пам'яті.",
        ),
        Line::from(""),
        Line::from(format!(
            "{:<18} {:>9} {:>9} {:>9} {:>9}  {:<8}",
            "випадок", "p50 нс", "p95 нс", "p99 нс", "операцій/с", "результат"
        )),
    ];
    for row in &report.rows {
        let p = row.percentiles;
        let throughput = 1_000_000_000u128.checked_div(p.p50).unwrap_or(0);
        lines.push(Line::from(format!(
            "{:<18} {:>9} {:>9} {:>9} {:>9}  {:<8}",
            row.name, p.p50, p.p95, p.p99, throughput, row.expected
        )));
        lines.push(Line::from(format!("  {}", row.source)));
        lines.push(Line::from(format!(
            "  код: {} слів · {} доменних бітів · T5M: {} байт",
            row.footprint.domain_words, row.footprint.domain_bits, row.footprint.t5m_bytes
        )));
    }
    lines.push(Line::from(""));
    lines.push(Line::from(
        "Мікровимірювання: порівнюй те саме обладнання, профіль збірки й SHA.",
    ));
    lines.push(Line::from("Звіт виведено без зміни стану REPL."));

    let block = Block::default()
        .title(" SENS REPL · звіт вимірювання ")
        .borders(Borders::ALL)
        .border_style(
            Style::default()
                .fg(Color::Cyan)
                .add_modifier(Modifier::BOLD),
        );
    frame.render_widget(
        Paragraph::new(lines).wrap(Wrap { trim: true }).block(block),
        frame.area(),
    );
}

#[cfg(test)]
mod tests {
    use super::{
        draw_report, memory_delta, parse_process_memory, program_footprint, run_suite,
        BenchmarkReport, BenchmarkRow, MemoryDelta, Percentiles, ProcessMemory, ProgramFootprint,
    };
    use crate::repl::{ReplState, ReplSurface};
    use ratatui::{backend::TestBackend, Terminal};
    use sens::Session;

    fn test_state(surface: ReplSurface) -> ReplState {
        let mut session = Session::default();
        let base_environment = session.environment.clone();
        let user_environment = base_environment.child();
        session.environment = user_environment.clone();
        ReplState {
            session,
            base_environment,
            user_environment,
            surface,
            sens_loop: false,
            sens_repl_bootstrapped: false,
        }
    }

    #[test]
    fn percentiles_use_nearest_rank_and_empty_input_has_no_summary() {
        let values = (1..=100).collect::<Vec<u128>>();
        assert_eq!(
            Percentiles::from_samples(&values),
            Some(Percentiles {
                p50: 50,
                p95: 95,
                p99: 99,
            })
        );
        assert_eq!(Percentiles::from_samples(&[]), None);
        assert_eq!(
            Percentiles::from_samples(&[17]),
            Some(Percentiles {
                p50: 17,
                p95: 17,
                p99: 17,
            })
        );
    }

    #[test]
    fn proc_status_parser_reads_current_and_peak_rss_without_assuming_field_order() {
        let status = "Name:\tsens\nVmHWM:\t24576 kB\nThreads:\t1\nVmRSS:\t16384 kB\n";
        assert_eq!(
            parse_process_memory(status),
            Some(ProcessMemory {
                rss_kib: 16_384,
                peak_rss_kib: 24_576,
            })
        );
        assert_eq!(parse_process_memory("Name:\tsens\nVmRSS:\t10 kB\n"), None);
        assert_eq!(parse_process_memory("Name:\tsens\nVmHWM:\tbad kB\n"), None);
    }

    #[test]
    fn memory_delta_reports_new_process_peak_only() {
        let start = Some(ProcessMemory {
            rss_kib: 10_000,
            peak_rss_kib: 12_000,
        });
        let end = Some(ProcessMemory {
            rss_kib: 10_500,
            peak_rss_kib: 12_256,
        });
        assert_eq!(
            memory_delta(start, end),
            Some(MemoryDelta {
                start_rss_kib: 10_000,
                end_rss_kib: 10_500,
                peak_growth_kib: 256,
            })
        );
        assert_eq!(memory_delta(start, None), None);
    }

    #[test]
    fn program_footprint_counts_exact_domain_bits_and_physical_t5m_bytes() {
        let words = [
            crate::zig_transport::ExactT5MWord::new(2, vec![1, 0]).unwrap(),
            crate::zig_transport::ExactT5MWord::new(7, vec![1, 0, 0, 0, 0, 0, 1]).unwrap(),
            crate::zig_transport::ExactT5MWord::new(
                24,
                (0..24).map(|bit| (bit % 2) as u8).collect(),
            )
            .unwrap(),
        ];

        assert_eq!(
            program_footprint(&words, &[0; 7]).unwrap(),
            ProgramFootprint {
                domain_words: 3,
                domain_bits: 33,
                t5m_bytes: 7,
            }
        );
        assert!(program_footprint(&[], &[]).is_err());
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn benchmark_workloads_keep_expected_results_and_do_not_change_repl_surface() {
        let state = test_state(ReplSurface::UkrainianFull);
        let report = run_suite(&state, 100, 1).expect("100 low-cost timing samples");
        assert_eq!(report.rows.len(), 3);
        assert_eq!(
            report
                .rows
                .iter()
                .map(|row| row.expected)
                .collect::<Vec<_>>(),
            ["579", "123", "912"]
        );
    }

    #[cfg(feature = "zig-transport")]
    #[test]
    fn benchmark_workloads_follow_selected_projection() {
        for surface in [ReplSurface::English, ReplSurface::Lisp] {
            let state = test_state(surface);
            let report = run_suite(&state, 100, 0).expect("same laws on selected surface");
            assert_eq!(report.surface, surface);
            assert_eq!(report.rows[0].expected, "579");
            assert_eq!(report.rows[1].expected, "123");
            assert_eq!(report.rows[2].expected, "912");
        }
    }

    #[test]
    fn ratatui_dashboard_shows_latency_distribution_scope_and_results() {
        let report = BenchmarkReport {
            surface: ReplSurface::UkrainianFull,
            warmups: 25,
            samples: 1_000,
            rows: vec![BenchmarkRow {
                name: "арифметика",
                source: "(додати 123 456)".into(),
                expected: "579",
                percentiles: Percentiles {
                    p50: 100,
                    p95: 200,
                    p99: 300,
                },
                footprint: ProgramFootprint {
                    domain_words: 3,
                    domain_bits: 33,
                    t5m_bytes: 7,
                },
            }],
            memory: Some(MemoryDelta {
                start_rss_kib: 16_384,
                end_rss_kib: 16_512,
                peak_growth_kib: 128,
            }),
        };
        let mut terminal = Terminal::new(TestBackend::new(120, 24)).unwrap();
        terminal.draw(|frame| draw_report(frame, &report)).unwrap();
        let visible = terminal
            .backend()
            .buffer()
            .content()
            .iter()
            .map(|cell| cell.symbol())
            .collect::<Vec<_>>()
            .join("");
        assert!(visible.contains("SENS REPL"), "{visible}");
        assert!(visible.contains("p50 нс"), "{visible}");
        assert!(visible.contains("p95 нс"), "{visible}");
        assert!(visible.contains("p99 нс"), "{visible}");
        assert!(visible.contains("RSS"), "{visible}");
        assert!(
            visible.contains("нульовий приріст пікового використання"),
            "{visible}"
        );
        assert!(visible.contains("Мікровимірювання"), "{visible}");
        assert!(visible.contains("налагоджувальна збірка"), "{visible}");
        assert!(!visible.contains("Ratatui benchmark"), "{visible}");
        assert!(!visible.contains("debug"), "{visible}");
        assert!(visible.contains("579"), "{visible}");
        assert!(visible.contains("Zig T5M"), "{visible}");
        assert!(visible.contains("33 доменних бітів"), "{visible}");
        assert!(visible.contains("T5M: 7 байт"), "{visible}");
    }
}
