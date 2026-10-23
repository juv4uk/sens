//! Механічна перевірка sens CLI: шлях, stdout/stderr, статус процесу.
//! Очікувані закони арифметики належать .lisp у tests/semantic/, а не Rust.
use std::path::PathBuf;
use std::process::{Command, Output};

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn run_sens(path: &str) -> Output {
    Command::new(env!("CARGO_BIN_EXE_sens"))
        .current_dir(repo_root())
        .arg(path)
        .output()
        .expect("механізм запуску sens CLI повинен бути доступний")
}

#[test]
fn cli_returns_observable_utf8_stdout_for_readable_lisp_source() {
    let output = run_sens("benchmarks/arithmetic.lisp");
    assert!(
        output.status.success(),
        "CLI не виконав вхідний файл: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(!output.stdout.is_empty(), "CLI не передав результат у stdout");
    String::from_utf8(output.stdout).expect("CLI повертає коректний текст у stdout");
}

#[test]
fn cli_returns_error_status_and_stderr_for_missing_input_file() {
    // Перевіряємо саме механізм файлового вводу, а не будь-яку відмову
    // попереднього Core4/process bootstrap. Інакше цей тест був би
    // хибно-зеленим навіть тоді, коли CLI ще не дійшов до читання шляху.
    let requested = "tests/semantic/__missing_cli_io_input__.lisp";
    assert!(
        !repo_root().join(requested).exists(),
        "фікстура відсутнього файлу не повинна існувати"
    );
    let output = run_sens(requested);
    assert!(!output.status.success(), "відсутній файл має дати ненульовий статус");
    let stderr = String::from_utf8(output.stderr)
        .expect("механічна діагностика CLI повинна бути UTF-8");
    assert!(
        stderr.contains(&format!("Error reading file {requested}:")),
        "CLI завершився не на читанні відсутнього файла, а раніше: {stderr}"
    );
}
