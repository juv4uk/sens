//! Справжня парна оберненість і виконання benchmarks/closures.lisp.
//! Людський Lisp звіряємо з наявними .sens байтами через Zig/T5M.
//! Не підміняємо SENS-EVAL симуляцією host і не оголошуємо corpus GO.
use std::{
    path::Path,
    process::{Command, Output},
};

const SOURCE: &str = include_str!("../../../benchmarks/closures.lisp");
const CALL: &str = "((створити-пару (як-є радіо)) (як-є антена))";
const BODY: &str = "(сполучити ліве (сполучити праве (як-є ())))";
// Фактичні ратифіковані координати D7/укр. T5M повертає доменні
// дані, а не вигаданий Symbol із текстового друку.
const RADIO_D7: &str = "(1101000 1100110 1101100 1110011 1101010)";
const ANTENNA_D7: &str = "(1100110 1111001 1101110 1110100 1111001 1100110)";
const SIGNAL_D7: &str = "(1100011 1100010 1110101 1111001 1100110 1101011)";

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
    assert!(SOURCE.contains("(визначити створити-пару"));
    assert_eq!(SOURCE.matches(CALL).count(), 1, "дрейф вихідної програми");
    assert_eq!(SOURCE.matches(BODY).count(), 1, "дрейф D3 тіла функції");

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
    assert_eq!(
        String::from_utf8_lossy(&positive.stdout).trim(),
        format!("({RADIO_D7} {ANTENNA_D7})"),
        "SENS сам формує вкладене D4 замикання з точних D7 слів"
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

    // Вживаний D3 CAR від NIL має семантично відмовити. D7-слово
    // «радіо» тепер є glyph-list, тож CAR від нього НЕ є негативним тестом.
    let invalid = temp_source(&malformed, 1, false);
    assert!(!invalid.status.success(), "CAR атома виконався без помилки");
    let stderr = String::from_utf8_lossy(&invalid.stderr);
    assert!(
        !stderr.contains("T5M_RESULT_UNSUPPORTED"),
        "відмова має бути семантичною, не відсутністю transport результату"
    );
}

#[test]
fn t5m_result_retains_proper_and_dotted_d3_pairs_without_host_shortcut() {
    // D7 — точні комірки; очікування «радіо» як host Symbol було хибним.
    // Цей тест не засвідчує атомарний носій довільних текстових символів.
    for (index, (expression, expected)) in [
        (
            "(як-є (радіо антена))",
            format!("({RADIO_D7} {ANTENNA_D7})"),
        ),
        (
            "(як-є (радіо (антена сигнал)))",
            format!("({RADIO_D7} ({ANTENNA_D7} {SIGNAL_D7}))"),
        ),
    ]
    .into_iter()
    .enumerate()
    {
        let output = temp_source(expression, index + 10, false);
        assert!(
            output.status.success(),
            "test_id=t5m-result-d7 layer=zig-sens input={expression} stderr={}",
            String::from_utf8_lossy(&output.stderr)
        );
        assert_eq!(
            String::from_utf8_lossy(&output.stdout).trim(),
            expected,
            "test_id=t5m-result-d7 layer=sens expected={expected}"
        );
    }

    // Тут tail — справжня ратифікована D3-ідентичність (атом),
    // а не D7 список glyph-ів: D2:11 має лишатися крапковою парою.
    let dotted = temp_source("(як-є (атом? . перше))", 20, false);
    assert!(
        dotted.status.success(),
        "test_id=t5m-dotted-d3 layer=sens stderr={}",
        String::from_utf8_lossy(&dotted.stderr)
    );
    let dotted_result = String::from_utf8_lossy(&dotted.stdout);
    assert!(
        dotted_result.trim().contains(" . "),
        "D2:11 втрачено при виконанні точного D3 хвоста: {dotted_result}"
    );

    // Поточний D7 не має атомарного носія для багатогліфового tail.
    // Не можна мовчки перетворити improper (радіо . антена) на список.
    let missing_atomic_carrier = temp_source("(як-є (радіо . антена))", 21, false);
    assert!(!missing_atomic_carrier.status.success());
    assert!(
        String::from_utf8_lossy(&missing_atomic_carrier.stderr)
            .contains("T5M_DOTTED_TEXT_TAIL_NOT_ATOMIC"),
        "точна втрата типу має відмовити, не видати підроблену оберненість: {}",
        String::from_utf8_lossy(&missing_atomic_carrier.stderr)
    );
}
