//! Де в коді ще стоять англійські імена функцій з таблиці функцій.
//!
//! Джерело імен — простір `en` таблиці функцій
//! (`lib/surface/semantic-registry.lisp` через
//! `semantic_registry_generated.rs`). Код = коди СЕНС, імена — лише
//! поверхня REPL, тож кожне англійське ім'я в коді — місце, яке ще не
//! переведене на СЕНС.
//!
//! Три види місць:
//!
//! - `lisp` — токен у коді мови (`.lisp`, `.sens`, ...): голова виклику
//!   (`(car x)`), визначення (`(00001001 reverse ...)`) чи посилання на
//!   функцію (`(map car xs)`). Рядки й коментарі пропускаються.
//! - `lisp-дані` — те саме ім'я під `'`, `` ` ``, `quote` чи `00000001`:
//!   дані, а не код (окремо, щоб не заступати код).
//! - `rust` — рядковий літерал Rust, який дорівнює імені (`"car"`): Rust
//!   знає функцію за іменем, а не за кодом.
//! - `rust-lisp` / `rust-lisp-дані` — код мови (чи його дані) всередині
//!   рядкового літерала Rust (`eval("(car x)")`).
//!
//! Файли даних, які читаються через `read-all` без `quote`, сканер не
//! відрізняє від коду — вони йдуть як `lisp`.
//!
//! Сама таблиця функцій і згенеровані з неї проєкції (`*_generated.rs`,
//! `lib/generated/`) — не код, а джерело імен; вони не скануються.
//!
//! Храповик: `tests/data/english-names-baseline.tsv` (вид, файл, ім'я,
//! кількість). Тест падає, якщо місць стало більше, і показує рядки.
//! `SENS_BASELINE_UPDATE=1` переписує базу (лише свідомо).
//! Повний перелік місць (файл:рядок):
//! `cargo test -p sens --test english_names_in_code -- --ignored`.

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..").canonicalize().unwrap()
}

/// Англійські імена з таблиці функцій.
fn english_names() -> BTreeSet<String> {
    let path = repo_root().join("crates/sens/src/semantic_registry_generated.rs");
    let text = fs::read_to_string(path).unwrap();
    let names: BTreeSet<String> = text
        .split("SemanticSurface { namespace: \"en\", name: \"")
        .skip(1)
        .map(|rest| rest.chars().take_while(|c| *c != '"').collect::<String>())
        .filter(|name| !name.is_empty())
        .collect();
    assert!(names.len() > 100, "англійські імена не прочитано ({})", names.len());
    names
}

/// Таблиця функцій і її проєкції — джерело імен, не код.
fn is_table_source(rel: &str) -> bool {
    rel == "lib/surface/semantic-registry.lisp"
        || rel == "knowledge/domain-surface-registry.lisp"
        || rel == "lib/surface/function-signatures.lisp"
        || rel.starts_with("lib/generated/")
        || rel.ends_with("_generated.rs")
        || rel.starts_with("crates/sens/tests/data/")
        // Сам цей тест: імена в його перевірках сканера — вхідні дані.
        || rel == "crates/sens/tests/english_names_in_code.rs"
}

fn explicit_nonsemantic_lisp_evidence(text: &str) -> bool {
    let header = text.lines().take(24).collect::<Vec<_>>().join("\n").to_lowercase();
    header.contains("(role research-only)")
        || header.contains("(semantic-authority-change none)")
        || header.contains("inventory only")
        || header.contains("не language-contract")
}

fn rust_test_is_semantic_authority(rel: &str) -> bool {
    if !rel.starts_with("crates/sens/tests/") || !rel.ends_with(".rs") {
        return false;
    }
    let inventory = fs::read_to_string(repo_root().join("tests/authority-inventory.tsv"))
        .unwrap_or_default();
    inventory.lines().any(|line| {
        let mut fields = line.split('\t');
        let Some(path) = fields.next() else { return false };
        let _site = fields.next();
        let class = fields.next().unwrap_or_default();
        let normalized = path.replace("crates/my-lisp/", "crates/sens/");
        normalized == rel && class == "semantic-authority"
    })
}

fn classified_kind(rel: &str, text: &str, base_kind: &'static str) -> &'static str {
    if rel.starts_with("crates/sens/tests/")
        && rel.ends_with(".rs")
        && !rust_test_is_semantic_authority(rel)
    {
        return "rust-test-instrument";
    }
    if !rel.ends_with(".rs") && explicit_nonsemantic_lisp_evidence(text) {
        return "lisp-evidence";
    }
    base_kind
}

fn ratchet_enforced_kind(kind: &str) -> bool {
    !matches!(kind, "rust-test-instrument" | "lisp-evidence")
}

fn files() -> Vec<(PathBuf, String)> {
    fn walk(root: &Path, dir: &Path, out: &mut Vec<(PathBuf, String)>) {
        let Ok(entries) = fs::read_dir(dir) else { return };
        for entry in entries.flatten() {
            let path = entry.path();
            let name = entry.file_name().to_string_lossy().into_owned();
            if path.is_dir() {
                if name == "vendor" || name == ".git" || name == "node_modules" || name.starts_with("target") {
                    continue;
                }
                walk(root, &path, out);
            } else if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
                if ["lisp", "sens", "my", "wsm", "всм", "мій", "лісп", "rs"].contains(&ext) {
                    let rel = path.strip_prefix(root).unwrap_or(&path).display().to_string();
                    if !is_table_source(&rel) {
                        out.push((path, rel));
                    }
                }
            }
        }
    }
    let root = repo_root();
    let mut out = Vec::new();
    walk(&root, &root, &mut out);
    out.sort();
    out
}

/// Токени коду мови: (рядок, токен, у-даних). Рядки й коментарі
/// пропускаються. «У даних» — усередині `'(...)`, `` `(...) `` чи
/// `(quote ...)` / `(00000001 ...)`: там ім'я є даними, а не кодом.
fn lisp_tokens(text: &str, first_line: usize) -> Vec<(usize, String, bool)> {
    let mut out = Vec::new();
    let chars: Vec<char> = text.chars().collect();
    let (mut i, mut line) = (0, first_line);
    // Для кожної відкритої дужки: чи це дані, і чи вже прочитано голову.
    let mut stack: Vec<(bool, bool)> = Vec::new();
    let mut quote_prefix = false;
    while i < chars.len() {
        let c = chars[i];
        if c == '\n' {
            line += 1;
            i += 1;
        } else if c == ';' {
            while i < chars.len() && chars[i] != '\n' {
                i += 1;
            }
        } else if c == '"' {
            i += 1;
            while i < chars.len() && chars[i] != '"' {
                if chars[i] == '\\' {
                    i += 1;
                } else if chars[i] == '\n' {
                    line += 1;
                }
                i += 1;
            }
            i += 1;
            quote_prefix = false;
        } else if c == '\'' || c == '`' {
            quote_prefix = true;
            i += 1;
        } else if c == '(' || c == '[' {
            let data = stack.last().is_some_and(|(d, _)| *d) || quote_prefix;
            stack.push((data, false));
            quote_prefix = false;
            i += 1;
        } else if c == ')' || c == ']' {
            stack.pop();
            i += 1;
        } else if c.is_whitespace() || c == ',' || c == '@' {
            i += 1;
        } else {
            let start = i;
            while i < chars.len() && !chars[i].is_whitespace() && !"()[]\"';`,".contains(chars[i]) {
                i += 1;
            }
            let token: String = chars[start..i].iter().collect();
            let data = quote_prefix || stack.last().is_some_and(|(d, _)| *d);
            if let Some(top) = stack.last_mut() {
                if !top.1 {
                    top.1 = true;
                    if !top.0 && (token == "quote" || token == "00000001") {
                        top.0 = true;
                    }
                }
            }
            out.push((line, token, data));
            quote_prefix = false;
        }
    }
    out
}

/// Рядкові літерали Rust: (рядок початку, вміст). Коментарі й символьні
/// літерали пропускаються; сирі рядки `r#"..."#` підтримуються.
fn rust_strings(text: &str) -> Vec<(usize, String)> {
    let mut out = Vec::new();
    let chars: Vec<char> = text.chars().collect();
    let (mut i, mut line) = (0, 1);
    while i < chars.len() {
        let c = chars[i];
        let next = chars.get(i + 1).copied();
        if c == '\n' {
            line += 1;
            i += 1;
        } else if c == '/' && next == Some('/') {
            while i < chars.len() && chars[i] != '\n' {
                i += 1;
            }
        } else if c == '/' && next == Some('*') {
            i += 2;
            while i + 1 < chars.len() && !(chars[i] == '*' && chars[i + 1] == '/') {
                if chars[i] == '\n' {
                    line += 1;
                }
                i += 1;
            }
            i += 2;
        } else if c == '\'' {
            // Символьний літерал ('x', '\n', '"') або час життя ('a).
            if next == Some('\\') {
                i += 2;
                while i < chars.len() && chars[i] != '\'' {
                    i += 1;
                }
                i += 1;
            } else if chars.get(i + 2) == Some(&'\'') {
                i += 3;
            } else {
                i += 1;
            }
        } else if c == 'r' && (next == Some('"') || next == Some('#'))
            && (i == 0 || !(chars[i - 1].is_alphanumeric() || chars[i - 1] == '_'))
        {
            let mut j = i + 1;
            let mut hashes = 0;
            while j < chars.len() && chars[j] == '#' {
                hashes += 1;
                j += 1;
            }
            if chars.get(j) != Some(&'"') {
                i += 1;
                continue;
            }
            let start_line = line;
            j += 1;
            let start = j;
            loop {
                if j >= chars.len() {
                    break;
                }
                if chars[j] == '"' && (0..hashes).all(|k| chars.get(j + 1 + k) == Some(&'#')) {
                    break;
                }
                if chars[j] == '\n' {
                    line += 1;
                }
                j += 1;
            }
            out.push((start_line, chars[start..j.min(chars.len())].iter().collect()));
            i = j + 1 + hashes;
        } else if c == '"' {
            let start_line = line;
            let mut value = String::new();
            i += 1;
            while i < chars.len() && chars[i] != '"' {
                if chars[i] == '\\' {
                    match chars.get(i + 1) {
                        Some('n') => value.push('\n'),
                        Some('\n') => line += 1,
                        Some(other) => value.push(*other),
                        None => {}
                    }
                    i += 2;
                    continue;
                }
                if chars[i] == '\n' {
                    line += 1;
                }
                value.push(chars[i]);
                i += 1;
            }
            i += 1;
            out.push((start_line, value));
        } else {
            i += 1;
        }
    }
    out
}

/// Одне місце: (вид, файл, рядок, ім'я).
type Place = (&'static str, String, usize, String);

fn places() -> Vec<Place> {
    let names = english_names();
    let mut out = Vec::new();
    for (path, rel) in files() {
        let Ok(text) = fs::read_to_string(&path) else { continue };
        if rel.ends_with(".rs") {
            for (line, literal) in rust_strings(&text) {
                if names.contains(literal.as_str()) {
                    let kind = classified_kind(&rel, &text, "rust");
                    out.push((kind, rel.clone(), line, literal));
                } else if literal.contains('(') {
                    for (l, token, data) in lisp_tokens(&literal, line) {
                        if names.contains(&token) {
                            let base_kind = if data { "rust-lisp-дані" } else { "rust-lisp" };
                            let kind = classified_kind(&rel, &text, base_kind);
                            out.push((kind, rel.clone(), l, token));
                        }
                    }
                }
            }
        } else {
            for (line, token, data) in lisp_tokens(&text, 1) {
                if names.contains(&token) {
                    let base_kind = if data { "lisp-дані" } else { "lisp" };
                    let kind = classified_kind(&rel, &text, base_kind);
                    out.push((kind, rel.clone(), line, token));
                }
            }
        }
    }
    out
}

fn counts(places: &[Place]) -> BTreeMap<String, usize> {
    let mut out = BTreeMap::new();
    for (kind, file, _, name) in places {
        if !ratchet_enforced_kind(kind) {
            continue;
        }
        *out.entry(format!("{kind}\t{file}\t{name}")).or_insert(0) += 1;
    }
    out
}

fn baseline_path() -> PathBuf {
    repo_root().join("crates/sens/tests/data/english-names-baseline.tsv")
}

fn read_baseline() -> BTreeMap<String, usize> {
    let text = fs::read_to_string(baseline_path()).unwrap_or_default();
    text.lines()
        .filter(|l| !l.starts_with('#'))
        .filter_map(|l| {
            let (key, count) = l.rsplit_once('\t')?;
            Some((key.to_owned(), count.parse().ok()?))
        })
        .collect()
}

fn summary(places: &[Place]) -> String {
    let mut by_kind: BTreeMap<&str, usize> = BTreeMap::new();
    let mut by_name: BTreeMap<&str, usize> = BTreeMap::new();
    let files: BTreeSet<&str> = places.iter().map(|(_, f, _, _)| f.as_str()).collect();
    for (kind, _, _, name) in places {
        *by_kind.entry(kind).or_insert(0) += 1;
        *by_name.entry(name).or_insert(0) += 1;
    }
    let mut top: Vec<_> = by_name.into_iter().collect();
    top.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(b.0)));
    let top: Vec<String> = top.iter().take(15).map(|(n, c)| format!("{n} {c}")).collect();
    format!(
        "англійських імен у коді: {} місць у {} файлах; за видом: {:?}; найчастіші: {}",
        places.len(),
        files.len(),
        by_kind,
        top.join(", ")
    )
}

#[test]
fn english_names_in_code_never_grow() {
    let places = places();
    let current = counts(&places);
    if std::env::var("SENS_BASELINE_UPDATE").as_deref() == Ok("1") {
        let mut text = String::from(
            "# Англійські імена з таблиці функцій у коді — храповик (див. tests/english_names_in_code.rs)\n\
             # вид\tфайл\tім'я\tкількість\n",
        );
        for (key, count) in &current {
            text.push_str(&format!("{key}\t{count}\n"));
        }
        fs::create_dir_all(baseline_path().parent().unwrap()).unwrap();
        fs::write(baseline_path(), text).unwrap();
        return;
    }
    let baseline = read_baseline();
    assert!(!baseline.is_empty(), "бази немає: SENS_BASELINE_UPDATE=1 cargo test ...");
    let mut grown = Vec::new();
    for (key, count) in &current {
        let base = baseline.get(key).copied().unwrap_or(0);
        if *count > base {
            let mut parts = key.splitn(3, '\t');
            let (kind, file, name) = (parts.next().unwrap(), parts.next().unwrap(), parts.next().unwrap());
            let lines: Vec<String> = places
                .iter()
                .filter(|(k, f, _, n)| *k == kind && f == file && n == name)
                .map(|(_, _, l, _)| l.to_string())
                .collect();
            grown.push(format!("{file}:{} {name} ({kind}): {base} -> {count}", lines.join(",")));
        }
    }
    eprintln!("{}", summary(&places));
    assert!(
        grown.is_empty(),
        "англійських імен у коді стало більше — пишіть кодами СЕНС:\n{}",
        grown.join("\n")
    );
}

#[test]
#[ignore = "мета: у коді немає англійських імен — лише коди СЕНС"]
fn no_english_names_in_code() {
    let places = places();
    let listing: Vec<String> = places
        .iter()
        .map(|(kind, file, line, name)| format!("{file}:{line}\t{name}\t{kind}"))
        .collect();
    assert!(places.is_empty(), "{}\n{}", summary(&places), listing.join("\n"));
}

#[test]
fn scanners_find_names_in_lisp_and_rust() {
    let lisp = lisp_tokens("(map car xs) ; cdr\n\"cons\" '(length 1) (quote (list)) (00000001 reverse) (f x)", 1);
    let tokens: Vec<(&str, bool)> = lisp.iter().map(|(_, t, d)| (t.as_str(), *d)).collect();
    assert_eq!(
        tokens,
        [
            ("map", false), ("car", false), ("xs", false),
            ("length", true), ("1", true),
            ("quote", false), ("list", true),
            ("00000001", false), ("reverse", true),
            ("f", false), ("x", false),
        ]
    );
    assert_eq!(lisp[3].0, 2);

    assert_eq!(
        classified_kind("crates/sens/tests/numeric_wire.rs", "", "rust-lisp"),
        "rust-test-instrument"
    );
    assert_eq!(
        classified_kind("crates/sens/tests/mccarthy.rs", "", "rust-lisp"),
        "rust-lisp",
        "explicit semantic-authority test must stay inside the executable-name ratchet"
    );
    assert!(explicit_nonsemantic_lisp_evidence(
        "; Inventory only: mechanism evidence, no semantic authority\n(foo car)"
    ));
    assert_eq!(
        classified_kind("lib/core1.lisp", "", "lisp-дані"),
        "lisp-дані",
        "production Core1 data that drives compatibility must remain enforced"
    );

    let rust = rust_strings("let a = \"car\"; // \"cdr\"\nlet c = '\"'; let s = r#\"(cons 1 ())\"#;");
    let literals: Vec<&str> = rust.iter().map(|(_, s)| s.as_str()).collect();
    assert_eq!(literals, ["car", "(cons 1 ())"]);
    assert_eq!(rust[1].0, 2);
}
