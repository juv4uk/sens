//! Справжня парна оберненість і виконання benchmarks/closures.lisp.
//! Людський Lisp звіряємо з наявними .sens байтами через Zig/T5M.
//! Не підміняємо SENS-EVAL симуляцією host і не оголошуємо corpus GO.
use std::{
    path::Path,
    process::{Command, Output},
};

const SOURCE: &str = include_str!("../../../benchmarks/closures.lisp");
const BODY: &str = "(сполучити ліве (сполучити праве (як-є ())))";
// Фактичні ратифіковані координати D7/укр. T5M повертає доменні
// дані, а не вигаданий Symbol із текстового друку.
fn execute(args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_sens"))
        .args(args)
        .output()
        .expect("виклик справжнього SENS CLI")
}

fn temp_source(text: &str, id: usize, pair: bool) -> Output {
    let path = std::env::temp_dir().join(format!("sens-closures-{}-{id}.lisp", std::process::id()));
    std::fs::write(&path, text).expect("тимчасовий український Lisp");
    let file = path.to_str().expect("UTF-8 temp path");
    let output = if pair {
        let physical = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../benchmarks/closures.sens");
        execute(&["--t5m-pair", file, physical.to_str().unwrap()])
    } else {
        execute(&["--t5m-file", file])
    };
    let _ = std::fs::remove_file(&path);
    output
}

#[test]
fn замикання_виконується_з_реальної_фізичної_пари_через_zig_t5m() {

    // Саме відстежена фізична пара, не згенеровані host-байти.
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../benchmarks");
    let human = root.join("closures.lisp");
    let physical = root.join("closures.sens");
    assert!(
        human.is_file() && physical.is_file(),
        "джерело чи носій відсутні"
    );
    let positive = execute(&[
        "--t5m-pair",
        human.to_str().unwrap(),
        physical.to_str().unwrap(),
    ]);
    assert!(
        positive.status.success(),
        "Zig T5M paired SENS: {}",
        String::from_utf8_lossy(&positive.stderr)
    );
    // Навіть один семантичний мутант не може використовувати старий .sens.
    let malformed = SOURCE.replacen(BODY, "(перше (як-є ()))", 1);
    let drift = temp_source(&malformed, 0, true);
    assert!(
        !drift.status.success(),
        "Zig пропустив неправильний фізичний носій"
    );
    assert!(
        String::from_utf8_lossy(&drift.stderr).contains("T5M_PHYSICAL_PAIR_MISMATCH"),
        "негативний drift має зупинитися на exact-domain межі"
    );

}
