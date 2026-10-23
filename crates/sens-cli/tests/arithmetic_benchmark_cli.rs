//! Живий позитивний і негативний SENS-свідок для benchmarks/arithmetic.lisp.
//! Українська людська поверхня -> Zig T5M -> фактичний SENS eval.
//! Не видавати цей source-runtime свідок за сертифікат фізичного .sens roundtrip.
use std::process::Command;

#[test]
fn український_поліном_обчислюється_в_sens_а_не_в_host() {
    let source = include_str!("../../../benchmarks/arithmetic.lisp");
    assert!(
        source.contains("(визначити поліном"),
        "живе українське визначення"
    );

    let виклик_зразок = "(поліном поліном-число-сто-двадцять-три)";
    assert!(source.contains(виклик_зразок), "втрачене чинне викличне джерело");
    for (index, (tail, expected)) in [
        (виклик_зразок, Some("15505")),
        ("(поліном поліном-число-два)", Some("17")),
        ("(поліном (як-є радіо))", None),
    ]
    .into_iter()
    .enumerate()
    {
        // Два повноцінні позитивні D24+ виклики та негативний нечисловий аргумент.
        let program = source.replacen(виклик_зразок, tail, 1);
        assert!(
            program.contains(tail),
            "непередбачений source drift: {tail}"
        );
        let file = std::env::temp_dir().join(format!(
            "sens-arithmetic-benchmark-{}-{index}.lisp",
            std::process::id()
        ));
        std::fs::write(&file, &program).expect("тимчасовий український Lisp");
        let output = Command::new(env!("CARGO_BIN_EXE_sens"))
            .args(["--t5m-file", file.to_str().expect("UTF-8 шлях")])
            .output()
            .expect("запуск справжнього SENS CLI");
        let _ = std::fs::remove_file(&file);
        if let Some(expected) = expected {
            assert!(
                output.status.success(),
                "SENS повинен виконати {tail}: stderr={}",
                String::from_utf8_lossy(&output.stderr)
            );
            assert_eq!(
                String::from_utf8_lossy(&output.stdout).trim(),
                expected,
                "точний D24+ результат {tail}"
            );
        } else {
            assert!(
                !output.status.success(),
                "SENS не має множити нечислові дані"
            );
            assert!(
                String::from_utf8_lossy(&output.stderr).contains("T5M file execution failed"),
                "SENS має повернути точну помилку виконання, а не прихований host fallback"
            );
        }
    }
}
