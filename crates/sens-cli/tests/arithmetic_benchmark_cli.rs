//! Справжній позитивний і негативний SENS-свідок benchmarks/arithmetic.lisp.
//! Українське Lisp → нативний SENS mint → Zig/T5M → SENS physical pair.
//! Не подавати людський .lisp як фізичний --t5m-file.
use std::process::Command;

#[test]
fn український_поліном_обчислюється_в_sens_а_не_в_host() {
    let source = include_str!("../../../benchmarks/arithmetic.lisp");
    let зразок = "(поліном поліном-число-сто-двадцять-три)";
    assert!(source.contains("(визначити поліном"), "живе українське визначення");
    assert!(source.contains(зразок), "чинний виклик бенчмарка");

    for (індекс, (виклик, очікуване)) in [
        (зразок, Some("15505")),
        ("(поліном поліном-число-два)", Some("17")),
        ("(поліном (як-є радіо))", None),
    ]
    .into_iter()
    .enumerate()
    {
        let програма = source.replacen(зразок, виклик, 1);
        let основа = std::env::temp_dir().join(format!(
            "sens-arithmetic-t5m-{}-{індекс}", std::process::id()
        ));
        let людський = основа.with_extension("lisp");
        let фізичний = основа.with_extension("sens");
        assert!(!фізичний.exists(), "не перезаписувати чужу фізичну пару");
        std::fs::write(&людський, програма).expect("запис українського Lisp");
        let л = людський.to_str().expect("UTF-8 шлях Lisp");
        let ф = фізичний.to_str().expect("UTF-8 шлях T5M");

        // Mint використовує реальний SENS reader та єдиний Zig/T5M кодек.
        let mint = Command::new(env!("CARGO_BIN_EXE_sens"))
            .args(["--t5m-mint", л, ф])
            .output()
            .expect("нативний SENS mint");
        if let Some(очікуваний_результат) = очікуване {
            assert!(
                mint.status.success(),
                "SENS/Zig mint відхилив {виклик}: {}",
                String::from_utf8_lossy(&mint.stderr)
            );
            assert!(
                фізичний.is_file() && фізичний.metadata().unwrap().len() > 0,
                "відсутні фізичні Zig/T5M байти"
            );
            let обернення = Command::new(env!("CARGO_BIN_EXE_sens-trit"))
                .args(["verify-view", ф])
                .output()
                .expect("читач фізичного Zig/T5M");
            assert!(
                обернення.status.success(),
                "T5M оберненість {виклик}: {}",
                String::from_utf8_lossy(&обернення.stderr)
            );
            let виконання = Command::new(env!("CARGO_BIN_EXE_sens"))
                .args(["--t5m-pair", л, ф])
                .output()
                .expect("нативне парне SENS виконання");
            assert!(
                виконання.status.success(),
                "SENS pair відхилив {виклик}: {}",
                String::from_utf8_lossy(&виконання.stderr)
            );
            assert_eq!(
                String::from_utf8_lossy(&виконання.stdout).trim(),
                очікуваний_результат,
                "точне D24+ обчислення {виклик}"
            );
        } else if mint.status.success() {
            let виконання = Command::new(env!("CARGO_BIN_EXE_sens"))
                .args(["--t5m-pair", л, ф])
                .output()
                .expect("негативний SENS pair");
            assert!(
                !виконання.status.success(),
                "нечисловий аргумент не може виконатися у SENS"
            );
        } else {
            assert!(
                !mint.stderr.is_empty(),
                "негативний приклад мусить мати діагностику reader/lowering"
            );
        }
        let _ = std::fs::remove_file(&людський);
        let _ = std::fs::remove_file(&фізичний);
    }
}
