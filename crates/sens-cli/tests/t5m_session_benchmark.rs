//! Діагностичний Rust-бенчмарк ціни запуску SENS: N процесів проти N форм в одній сесії.
//! Обидві смуги виконують той самий Lisp через реальні Zig T5M і SENS.
//! Це вимір механізму, а не новий семантичний оракул чи обіцянка прискорення.

use std::{
    fs::{self, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
    process::{Command, Output},
    time::{Instant, SystemTime, UNIX_EPOCH},
};

const CALLS: usize = 16;
const ROUNDS: usize = 5;
const EXPECTED: &[u8] = b"42\n";

struct TempLisp(PathBuf);

impl TempLisp {
    fn new() -> Self {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("system clock")
            .as_nanos();
        let path = std::env::temp_dir().join(format!(
            "sens-t5m-session-{}-{nonce}.lisp",
            std::process::id()
        ));
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&path)
            .expect("create unique temporary Lisp source");
        file.write_all(b"(\xd0\xb4\xd0\xbe\xd0\xb4\xd0\xb0\xd1\x82\xd0\xb8 20 22)\n")
            .expect("write real SENS source");
        Self(path)
    }

    fn path(&self) -> &Path {
        &self.0
    }
}

impl Drop for TempLisp {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.0);
    }
}

fn assert_sens_result(output: &Output, lane: &str) {
    assert!(
        output.status.success(),
        "T5M_SESSION_BENCH_FAIL lane={lane} status={} stderr={}",
        output.status,
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        output.stdout, EXPECTED,
        "T5M_SESSION_BENCH_FAIL lane={lane} layer=real-SENS-result stderr={}",
        String::from_utf8_lossy(&output.stderr)
    );
}

fn cold_batch(source: &Path) -> u128 {
    let started = Instant::now();
    let outputs = (0..CALLS)
        .map(|_| {
            Command::new(env!("CARGO_BIN_EXE_sens"))
                .arg("--t5m-file")
                .arg(source)
                .output()
                .expect("launch cold SENS process")
        })
        .collect::<Vec<_>>();
    let wall_ns = started.elapsed().as_nanos();
    for output in &outputs {
        assert_sens_result(output, "cold");
    }
    wall_ns
}

fn warm_batch(source: &Path) -> u128 {
    let mut command = Command::new(env!("CARGO_BIN_EXE_sens"));
    command.arg("--t5m-files");
    for _ in 0..CALLS {
        command.arg(source);
    }
    let started = Instant::now();
    let output = command.output().expect("launch shared-session SENS process");
    let wall_ns = started.elapsed().as_nanos();
    assert_sens_result(&output, "warm");
    wall_ns
}

fn median(mut values: [u128; ROUNDS]) -> u128 {
    values.sort_unstable();
    values[ROUNDS / 2]
}

#[test]
#[ignore = "явний cold/warm процесний бенчмарк; без порогу швидкодії"]
fn zig_t5m_one_session_vs_process_per_form() {
    let source = TempLisp::new();

    // Ті самі форми та очікуваний результат спочатку проходять реальний SENS.
    assert_sens_result(
        &Command::new(env!("CARGO_BIN_EXE_sens"))
            .arg("--t5m-file")
            .arg(source.path())
            .output()
            .expect("cold preflight"),
        "cold-preflight",
    );
    assert_sens_result(
        &{
            let mut command = Command::new(env!("CARGO_BIN_EXE_sens"));
            command.arg("--t5m-files");
            for _ in 0..CALLS {
                command.arg(source.path());
            }
            command.output().expect("warm preflight")
        },
        "warm-preflight",
    );

    let mut cold_ns = [0_u128; ROUNDS];
    let mut warm_ns = [0_u128; ROUNDS];
    for round in 0..ROUNDS {
        // Чергування порядку зменшує систематичний ефект кешу ОС.
        if round % 2 == 0 {
            cold_ns[round] = cold_batch(source.path());
            warm_ns[round] = warm_batch(source.path());
        } else {
            warm_ns[round] = warm_batch(source.path());
            cold_ns[round] = cold_batch(source.path());
        }
        for (lane, wall_ns) in [("cold", cold_ns[round]), ("warm", warm_ns[round])] {
            eprintln!(
                "T5M_SESSION_SAMPLE lane={lane} round={} forms={CALLS} wall_ns={wall_ns} amortized_ns={} parity=42 scope=process-wall",
                round + 1,
                wall_ns / CALLS as u128
            );
        }
    }
    let cold_p50 = median(cold_ns) / CALLS as u128;
    let warm_p50 = median(warm_ns) / CALLS as u128;
    eprintln!(
        "T5M_SESSION_BENCH cold_p50_amortized_ns={cold_p50} warm_p50_amortized_ns={warm_p50} forms={CALLS} rounds={ROUNDS} path=Zig-T5M-SENS parity=42 scope=process-wall claim=measurement-only"
    );
}
