//! Живий SENS для непарного benchmarks/closures.lisp.
//! .lisp → Zig/T5M → SENS eval; не Python і не сертифікат фізичної .sens пари.
use std::process::Command;

const SOURCE: &str = include_str!("../../../benchmarks/closures.lisp");
const CALL: &str = "((створити-пару (як-є радіо)) (як-є антена))";

fn run_source(source: &str, id: usize) -> std::process::Output {
    let path = std::env::temp_dir().join(format!(
        "sens-closures-t5m-{}-{id}.lisp", std::process::id()
    ));
    std::fs::write(&path, source).expect("записати тимчасовий український Lisp");
    let output = Command::new(env!("CARGO_BIN_EXE_sens"))
        .args(["--t5m-file", path.to_str().expect("UTF-8 шлях")])
        .output()
        .expect("виконати реальний SENS CLI");
    let _ = std::fs::remove_file(&path);
    output
}

#[test]
fn замикання_реально_виконується_з_українського_lisp_через_t5m() {
    assert!(SOURCE.contains("(визначити створити-пару"));
    assert_eq!(SOURCE.matches(CALL).count(), 1, "змінився живий Lisp");
    for (i, (call, expected)) in [
        (CALL, "(радіо антена)"),
        ("((створити-пару (як-є радіо)) (як-є сигнал))", "(радіо сигнал)"),
    ].into_iter().enumerate() {
        let output = run_source(&SOURCE.replacen(CALL, call, 1), i);
        assert!(output.status.success(), "SENS {call}: {}",
                String::from_utf8_lossy(&output.stderr));
        assert_eq!(String::from_utf8_lossy(&output.stdout).trim(), expected,
                   "SENS має обчислити лексичне замикання без host-імітації");
    }
    // Мутант змінює лише операцію в тілі; D3 CAR атома мусить відмовити.
    let body = "(сполучити ліве (сполучити праве (як-є ())))";
    assert_eq!(SOURCE.matches(body).count(), 1);
    let bad = run_source(&SOURCE.replacen(body, "(перше ліве)", 1), 2);
    assert!(!bad.status.success(), "SENS прийняв CAR атома");
}
