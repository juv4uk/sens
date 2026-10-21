//! Справжнє виконання масивів українського Core1 у SENS CLI.
//! Транспорт Rust не обчислює Lisp і не замінює доказ виконання.
use std::process::Command;

fn definition<'a>(source: &'a str, name: &str) -> &'a str {
    let tag = format!("(визначити {name}\n");
    let start = source.find(&tag).unwrap_or_else(|| {
        panic!("у чинному lib/core1.lisp немає визначення {name}")
    });
    let following = &source[start..];
    let end = following.find("\n(визначити ").unwrap_or(following.len());
    &following[..end]
}

#[test]
fn українські_масиви_core1_виконують_перевірку_меж_у_sens() {
    let root = concat!(env!("CARGO_MANIFEST_DIR"), "/../..");
    let donor = std::fs::read_to_string(concat!(
        env!("CARGO_MANIFEST_DIR"), "/../../lib/core1.lisp"
    ))
    .expect("чинний український Lisp");
    // Реальна залежність Core1: Д1-істина/хиба надходить із виконуваного
    // lib/core.lisp, а не з текстових заглушок тесту чи host-bool.
    let mut program = String::from(include_str!("../../../lib/core.lisp"));
    program.push('\n');
    for name in [
        "ядро1-створити-помилку",
        "ядро1-зменшити-на-один",
        "ядро1-створити-масив",
        "ядро1-заповнити-масив",
        "ядро1-елемент-масиву",
        "ядро1-змінити-елемент-масиву",
    ] {
        program.push_str(definition(&donor, name));
        program.push('\n');
    }
    for (index, (expression, expected, is_error)) in [
        ("(ядро1-елемент-масиву (як-є (весна літо)) 0)", "весна", false),
        ("(ядро1-елемент-масиву (як-є (весна літо)) 1)", "літо", false),
        ("(ядро1-змінити-елемент-масиву (як-є (весна літо)) 1 (як-є осінь))", "(весна осінь)", false),
        ("(ядро1-створити-масив 2)", "(0 0)", false),
        ("(ядро1-елемент-масиву (як-є ()) 0)", "індекс-поза-масивом", true),
        ("(ядро1-елемент-масиву (як-є (весна)) 2)", "індекс-поза-масивом", true),
        ("(ядро1-елемент-масиву (як-є (весна)) -1)", "індекс-поза-масивом", true),
        ("(ядро1-змінити-елемент-масиву (як-є ()) 0 (як-є осінь))", "індекс-поза-масивом", true),
        ("(ядро1-створити-масив -1)", "відємний-розмір-масиву", true),
    ].into_iter().enumerate() {
        let file = std::env::temp_dir().join(format!(
            "sens-uk-core1-array-{}-{index}.lisp", std::process::id()
        ));
        std::fs::write(&file, format!("{program}\n{expression}\n"))
            .expect("тимчасовий Lisp-файл");
        // Жоден завислий рекурсивний Lisp не повинен займати CI безмежно.
        // Очікувані значення не змінюємо; timeout друкує конкретний вираз.
        let mut child = Command::new(env!("CARGO_BIN_EXE_sens"))
            .current_dir(root)
            .arg(&file)
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped())
            .spawn()
            .expect("справжній SENS CLI");
        let deadline = std::time::Instant::now()
            + std::time::Duration::from_secs(6);
        loop {
            if child.try_wait().expect("стан процесу SENS").is_some() {
                break;
            }
            if std::time::Instant::now() >= deadline {
                let _ = child.kill();
                let _ = child.wait();
                let _ = std::fs::remove_file(&file);
                panic!("SENS_RUNTIME_TIMEOUT: Core1 case {index} expression={expression}");
            }
            std::thread::sleep(std::time::Duration::from_millis(30));
        }
        let output = child.wait_with_output().expect("вивід процесу SENS");
        let _ = std::fs::remove_file(&file);
        assert!(
            output.status.success(),
            "SENS не виконав {expression}: stderr={} stdout={}",
            String::from_utf8_lossy(&output.stderr),
            String::from_utf8_lossy(&output.stdout),
        );
        let stdout = String::from_utf8_lossy(&output.stdout);
        if is_error {
            assert!(stdout.contains(expected),
                "очікували мовний результат {expected}, отримали {stdout}");
        } else {
            assert_eq!(stdout.trim(), expected,
                "SENS повернув інший результат для {expression}");
        }
    }
}
