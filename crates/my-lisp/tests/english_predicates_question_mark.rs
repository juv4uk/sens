//! #1413: кожен англійський предикат закінчується на `?`, і повернути
//! старе написання без `?` заборонено.
//!
//! Предикат — функція СЕНС, у якої українське (ук/укр) чи санскритське ім'я
//! закінчується на `?`. Список не захардкоджено: він виводиться з реєстру,
//! тож новий предикат автоматично підпадає під правило.
//!
//! Цей тест існує, бо 2026-09-25 зміну `52c35233` (atom→atom? ...) тихо
//! відкотив непов'язаний коміт `38395405` (#1387), а згенеровані файли
//! версії з `?` не отримали взагалі.

use my_lisp::{eval_program, load_core_library, Session};
use std::fs;
use std::path::{Path, PathBuf};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..").canonicalize().unwrap()
}

/// (код, en, ук, укр, sa) з джерела реєстру.
fn registry_rows() -> Vec<[String; 5]> {
    let src = fs::read_to_string(repo_root().join("lib/surface/semantic-registry.lisp")).unwrap();
    let field = |line: &str, key: &str| -> String {
        let marker = format!("({key} ");
        line.split(&marker)
            .nth(1)
            .map(|rest| rest.split(')').next().unwrap_or("").to_owned())
            .map(|v| if v == "(" { "()".to_owned() } else { v })
            .unwrap_or_default()
    };
    src.lines()
        .filter_map(|line| {
            let code = line.trim_start().strip_prefix('(')?.get(..8)?.to_owned();
            if !code.bytes().all(|b| b == b'0' || b == b'1') {
                return None;
            }
            Some([code, field(line, "en"), field(line, "ук"), field(line, "укр"), field(line, "sa")])
        })
        .collect()
}

/// Англійські предикати: (код, ім'я з `?`).
fn english_predicates() -> Vec<(String, String)> {
    registry_rows()
        .into_iter()
        .filter(|[_, en, uk, ukr, sa]| {
            en != "()" && [uk, ukr, sa].iter().any(|s| s.ends_with('?'))
        })
        .map(|[code, en, ..]| (code, en))
        .collect()
}

#[test]
fn registry_source_marks_every_english_predicate_with_question_mark() {
    let rows = registry_rows();
    assert_eq!(rows.len(), 256, "реєстр має містити всі 256 функцій");
    let missing: Vec<String> = english_predicates()
        .into_iter()
        .filter(|(_, en)| !en.ends_with('?'))
        .map(|(code, en)| format!("{code}: en {en} — бракує `?`"))
        .collect();
    assert!(missing.is_empty(), "англійські предикати без `?`:\n{}", missing.join("\n"));
}

#[test]
fn generated_registry_agrees_with_source_for_predicates() {
    let generated = fs::read_to_string(
        repo_root().join("crates/my-lisp/src/semantic_registry_generated.rs"),
    )
    .unwrap();
    let mut stale = Vec::new();
    for (code, en) in english_predicates() {
        let row = generated
            .lines()
            .find(|l| l.contains(&format!("semantic_id: 0b{code},")))
            .unwrap_or_else(|| panic!("{code}: рядка немає в згенерованому реєстрі"));
        if !row.contains(&format!("namespace: \"en\", name: \"{en}\" ")) {
            stale.push(format!("{code}: у згенерованому реєстрі не `{en}` — перегенеруйте"));
        }
    }
    assert!(stale.is_empty(), "згенерований реєстр відстав від джерела:\n{}", stale.join("\n"));
}

#[test]
fn old_spelling_without_question_mark_is_rejected_at_runtime() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core loads");
    for (code, en) in english_predicates() {
        let with_mark = eval_program(&en, &mut session)
            .map(|r| r.value.to_string())
            .unwrap_or_else(|e| format!("error: {e}"));
        let Some(old) = en.strip_suffix('?') else { continue };
        // Старе написання не повинне вести до тієї ж функції.
        if let Ok(result) = eval_program(old, &mut session) {
            assert_ne!(
                result.value.to_string(),
                code,
                "`{old}` досі веде до функції {code}; дозволено лише `{en}`"
            );
        }
        let _ = with_mark;
    }
}

#[test]
fn no_project_code_calls_an_english_predicate_without_question_mark() {
    let olds: Vec<String> = english_predicates()
        .into_iter()
        .filter_map(|(_, en)| en.strip_suffix('?').map(str::to_owned))
        .collect();
    let registry_names: std::collections::BTreeSet<String> = registry_rows()
        .into_iter()
        .flat_map(|row| row.into_iter().skip(1))
        .collect();
    // Дані та схеми, які не є викликами функцій-предикатів:
    // (var x) — логічна змінна Datalog;
    // (claim ...), (evidence ...), (observation ...), (intent ...) — епістемічні записи;
    // (string ...), (symbol ...) — специфікатори типів у контрактах та параметри lambda.
    let non_predicate_forms = ["var", "claim", "evidence", "observation", "intent", "string", "symbol"];
    let olds: Vec<String> = olds
        .into_iter()
        .filter(|o| !registry_names.contains(o) && !non_predicate_forms.contains(&o.as_str()))
        .collect();

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
    for path in files {
        let Ok(text) = fs::read_to_string(&path) else { continue };
        let stripped = strip_comments_and_strings(&text);
        for (line_no, line) in stripped.lines().enumerate() {
            for old in &olds {
                let needle = format!("({old}");
                for (pos, _) in line.match_indices(&needle) {
                    let next = line[pos + needle.len()..].chars().next();
                    if matches!(next, None | Some(' ' | '\t' | ')' | '(')) {
                        offenders.push(format!(
                            "{}:{}: ({old} ...) — має бути ({old}? ...)",
                            path.strip_prefix(&root).unwrap().display(),
                            line_no + 1
                        ));
                    }
                }
            }
        }
    }
    assert!(
        offenders.is_empty(),
        "виклики англійських предикатів без `?` ({}):\n{}",
        offenders.len(),
        offenders.iter().take(50).cloned().collect::<Vec<_>>().join("\n")
    );
}

fn strip_comments_and_strings(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    let mut in_str = false;
    let mut in_comment = false;
    let mut escaped = false;
    for c in text.chars() {
        if in_comment {
            if c == '\n' {
                in_comment = false;
                out.push('\n');
            } else {
                out.push(' ');
            }
        } else if in_str {
            if escaped {
                escaped = false;
                out.push(' ');
            } else if c == '\\' {
                escaped = true;
                out.push(' ');
            } else if c == '"' {
                in_str = false;
                out.push(' ');
            } else if c == '\n' {
                out.push('\n');
            } else {
                out.push(' ');
            }
        } else if c == '"' {
            in_str = true;
            out.push(' ');
        } else if c == ';' {
            in_comment = true;
            out.push(' ');
        } else {
            out.push(c);
        }
    }
    out
}
