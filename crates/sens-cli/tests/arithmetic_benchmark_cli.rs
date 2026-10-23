//! Виконання benchmarks/arithmetic.lisp справжнім SENS CLI, без host-семантики.
//! Цей тест доводить Lisp-eval; фізичний Zig/T5M-коридор перевіряє
//! окремий нативний push-гейт scripts/execute_changed_lisp_t5m.sh.
use std::process::Command;

#[test]
fn український_поліном_обчислюється_в_sens_а_не_в_host() {
    let source = include_str!("../../../benchmarks/arithmetic.lisp");
    let зразок = "(поліном поліном-число-сто-двадцять-три)";
    assert!(source.contains("(визначити поліном"), "чинне визначення SENS");
    assert!(source.contains(зразок), "чинний бенчмарк без цифрових літералів");

    for (індекс, (виклик, очікуване)) in [
        (зразок, Some("15505")),
        ("(поліном поліном-число-два)", Some("17")),
        ("(поліном (як-є радіо))", None),
    ]
    .into_iter()
    .enumerate()
    {
        let програма = source.replacen(зразок, виклик, 1);
        let файл = std::env::temp_dir().join(format!(
            "sens-arithmetic-benchmark-{}-{індекс}.lisp",
            std::process::id()
        ));
        std::fs::write(&файл, програма).expect("українська Lisp-програма");
        let виконання = Command::new(env!("CARGO_BIN_EXE_sens"))
            .arg(&файл)
            .output()
            .expect("нативний SENS CLI");
        let _ = std::fs::remove_file(&файл);

        if let Some(очікуваний_результат) = очікуване {
            assert!(
                виконання.status.success(),
                "SENS Lisp-eval відхилив {виклик}: {}",
                String::from_utf8_lossy(&виконання.stderr)
            );
            assert_eq!(
                String::from_utf8_lossy(&виконання.stdout).trim(),
                очікуваний_результат,
                "точна D24+ семантика {виклик}"
            );
        } else {
            assert!(
                !виконання.status.success(),
                "нечисловий аргумент не може виконатися у SENS"
            );
            assert!(
                !виконання.stderr.is_empty(),
                "SENS повинен пояснити негативну семантичну відмову"
            );
        }
    }
}
