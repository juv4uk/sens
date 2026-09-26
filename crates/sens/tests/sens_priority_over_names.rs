//! #1413: СЕНС має пріоритет над будь-яким написанням коду.
//!
//! Жорсткі правила (без `#[ignore]` — червоні, доки код не приведено у
//! відповідність):
//!
//! 1. кожне ім'я з реєстру під час виконання веде до 1-байтової функції
//!    СЕНС свого коду — не до Rust-функції за іменем і не до Lisp-замикання;
//! 2. жодне ім'я з реєстру не можна перевизначити (`(def + 5)`) — ім'я
//!    не може стати вищим за функцію СЕНС;
//! 3. увесь вихідний код мови написаний кодами СЕНС: виклик функції з
//!    реєстру за іменем — порушення.
//!
//! Повний перелік порушень — `tests/non_sens_code_inventory.rs`.

use sens::{eval_program, load_core_library, Session, Value};
use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..").canonicalize().unwrap()
}

/// (код, простір, ім'я) зі згенерованого реєстру, яким користується виконання.
fn registry() -> Vec<(String, String, String)> {
    let text = fs::read_to_string(
        repo_root().join("crates/sens/src/semantic_registry_generated.rs"),
    )
    .unwrap();
    let mut rows = Vec::new();
    for line in text.lines() {
        let Some(rest) = line.split("semantic_id: 0b").nth(1) else { continue };
        let code: String = rest.chars().take_while(|c| *c == '0' || *c == '1').collect();
        for surface in rest.split("SemanticSurface { namespace: \"").skip(1) {
            let mut parts = surface.splitn(2, "\", name: \"");
            let namespace = parts.next().unwrap_or("").to_owned();
            let name: String = parts.next().unwrap_or("").chars().take_while(|c| *c != '"').collect();
            if !name.is_empty() {
                rows.push((code.clone(), namespace, name));
            }
        }
    }
    rows
}

fn report(title: &str, offenders: &[String]) {
    assert!(
        offenders.is_empty(),
        "{title}: {}\n{}",
        offenders.len(),
        offenders.iter().take(60).cloned().collect::<Vec<_>>().join("\n")
    );
}

#[test]
fn every_registry_name_resolves_to_its_one_byte_sens_function() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core loads");
    let mut offenders = Vec::new();
    for (code, namespace, name) in registry() {
        match eval_program(&name, &mut session).map(|r| r.value) {
            Ok(Value::Sid(sid)) if sid.to_string() == code => {}
            Ok(Value::Builtin(_)) => offenders.push(format!("{code} {namespace} {name}: Rust-функція за іменем")),
            Ok(Value::Closure(_)) => offenders.push(format!("{code} {namespace} {name}: Lisp-замикання за іменем")),
            Ok(Value::Macro(_)) => offenders.push(format!("{code} {namespace} {name}: макрос за іменем")),
            Ok(other) => offenders.push(format!("{code} {namespace} {name}: {other}")),
            // Синтаксис (quote/cond/lambda/def) — голова виклику, не значення.
            Err(_) => {}
        }
    }
    report("імена, що ведуть не до функції СЕНС", &offenders);
}

#[test]
fn no_registry_name_can_be_rebound_above_sens() {
    let mut offenders = Vec::new();
    let names: BTreeSet<(String, String)> =
        registry().into_iter().map(|(code, _, name)| (code, name)).collect();
    for (code, name) in names {
        let mut session = Session::default();
        load_core_library(&mut session).expect("core loads");
        if eval_program(&format!("(def {name} 1)"), &mut session).is_ok() {
            offenders.push(format!("{code} {name}: (def {name} 1) дозволено"));
        }
    }
    report("імена функцій СЕНС, які можна перевизначити", &offenders);
}

#[test]
fn all_language_source_is_written_in_sens_codes() {
    let names: BTreeSet<String> = registry().into_iter().map(|(_, _, name)| name).collect();
    fn walk(dir: &Path, root: &Path, out: &mut Vec<PathBuf>) {
        let Ok(entries) = fs::read_dir(dir) else { return };
        for entry in entries.flatten() {
            let path = entry.path();
            let name = entry.file_name().to_string_lossy().into_owned();
            if path.is_dir() {
                let rel = path.strip_prefix(root).unwrap();
                if ["vendor", ".git", "node_modules", "archive"].contains(&name.as_str())
                    || name.starts_with("target")
                    || (name == "results" && rel.starts_with("benchmarks"))
                {
                    continue;
                }
                walk(&path, root, out);
            } else if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
                if ["lisp", "sens", "my", "wsm", "всм", "мій", "лісп"].contains(&ext) {
                    out.push(path);
                }
            }
        }
    }
    let root = repo_root();
    let mut files = Vec::new();
    walk(&root, &root, &mut files);

    let mut offenders = Vec::new();
    let mut total = 0usize;
    for path in files {
        let Ok(text) = fs::read_to_string(&path) else { continue };
        let mut count = 0usize;
        let mut first = None;
        for (line_no, line) in text.lines().enumerate() {
            let code = line.split(';').next().unwrap_or("");
            let mut rest = code;
            while let Some(pos) = rest.find('(') {
                let after = rest[pos + 1..].trim_start();
                let head: String = after
                    .chars()
                    .take_while(|c| !c.is_whitespace() && !"()\"';".contains(*c))
                    .collect();
                if names.contains(&head) {
                    count += 1;
                    first.get_or_insert(line_no + 1);
                }
                rest = &rest[pos + 1..];
            }
        }
        if count > 0 {
            total += count;
            offenders.push(format!(
                "{}: {count} викликів іменем (перший — рядок {})",
                path.strip_prefix(&root).unwrap().display(),
                first.unwrap()
            ));
        }
    }
    offenders.sort();
    offenders.insert(0, format!("разом викликів іменем: {total}"));
    if offenders.len() == 1 {
        offenders.clear();
    }
    report("файли з кодом не на СЕНС", &offenders);
}
