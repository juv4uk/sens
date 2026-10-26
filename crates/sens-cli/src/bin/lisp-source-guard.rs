//! Структурна перевірка Lisp-файлів і цілісності машинних джерел.
//! Rust відповідає лише за введення-виведення та лексичну структуру.
//! Семантика й допуск виконуваних форм належать СЕНС.

use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process;

const LOWERING: &str = "lib/machine/lowering/semantic-x86-64.lisp";
const ENCODING: &str = "lib/machine/encoding/x86-64.lisp";
const ADMISSION: &str = "lib/machine/admission/x86-64.lisp";

const FORBIDDEN: &[&str] = &[
    "PLACEHOLDER",
    "SEE_LOCAL_FIX_",
    "RESTORED_FULL_FILE",
    "LOAD_FROM_FILE:",
    "/tmp/sem_join.lisp",
    "see next",
];

const LOWERING_FORMS: &[&str] = &[
    "(визначити машина-знизити-додавання-беззнакових-64-до-форм",
    "(визначити знизити-складену-пару-до-машинних-форм",
    "(визначити машина-викликати-семантичне-перше-64",
    "(визначити машина-кодувати-поточну-рівність-та-умову-64",
];
const ENCODING_FORMS: &[&str] = &[
    "(визначити машина-код-регістра",
    "(визначити машина-байт-із-восьми-бітів",
    "(визначити машина-кодувати-повернення",
    "(визначити машина-кодувати-зчитування-памяті-зі-зсувом-8",
    "(визначити машина-кодувати-запис-у-память-зі-зсувом-8",
];
const ADMISSION_FORMS: &[&str] = &[
    "(визначити машина-програма-допущена?",
    "(визначити машина-команда-допущена?",
    "(визначити машина-перша-недопущена-форма",
    "(визначити машина-кодувати-допущену-команду",
    "(визначити машина-кодувати-допущену-програму-або-відхилити",
];

#[derive(Debug, PartialEq, Eq)]
struct Balance {
    depth: i64,
    first_negative_line: Option<usize>,
    unclosed_string: bool,
}

/// Лексичний обхід: рядки з екрануванням і коментарі ";" не є дужками.
/// Це не читач і не інтерпретатор Lisp.
fn balance(bytes: &[u8]) -> Balance {
    let (mut depth, mut first_negative_line) = (0_i64, None);
    let (mut in_string, mut in_comment, mut escaped) = (false, false, false);
    let mut line = 1_usize;
    for &byte in bytes {
        if byte == b'\n' {
            line += 1;
            if in_comment {
                in_comment = false;
            }
        }
        if in_comment {
            continue;
        }
        if in_string {
            if escaped {
                escaped = false;
            } else if byte == b'\\' {
                escaped = true;
            } else if byte == b'"' {
                in_string = false;
            }
        } else {
            match byte {
                b';' => in_comment = true,
                b'"' => in_string = true,
                b'(' => depth += 1,
                b')' => {
                    depth -= 1;
                    if depth < 0 && first_negative_line.is_none() {
                        first_negative_line = Some(line);
                    }
                }
                _ => {}
            }
        }
    }
    Balance {
        depth,
        first_negative_line,
        unclosed_string: in_string,
    }
}

fn critical_contract(relative: &str) -> Option<(usize, &'static [&'static str])> {
    match relative {
        LOWERING => Some((20_000, LOWERING_FORMS)),
        ENCODING => Some((50_000, ENCODING_FORMS)),
        ADMISSION => Some((20_000, ADMISSION_FORMS)),
        _ => None,
    }
}

fn check_critical(relative: &str, source: &str) -> Vec<String> {
    let Some((minimum, forms)) = critical_contract(relative) else {
        return vec![];
    };
    let mut errors = Vec::new();
    if source.len() < minimum {
        errors.push(format!(
            "critical source unexpectedly short ({} bytes)",
            source.len()
        ));
    }
    for marker in FORBIDDEN {
        if source.contains(*marker) {
            errors.push(format!("forbidden intermediate marker {marker:?}"));
        }
    }
    for form in forms {
        if !source.contains(*form) {
            errors.push(format!("missing required entry point {form}"));
        }
    }
    if relative == LOWERING && source.contains("00100010") {
        errors.push("legacy W8 EQ head remains in current D3 lowering".into());
    }
    errors
}

fn collect(base: &Path, files: &mut Vec<PathBuf>, errors: &mut Vec<String>) {
    let metadata = match fs::symlink_metadata(base) {
        Ok(metadata) => metadata,
        Err(e) => {
            errors.push(format!(
                "{}: requested scan path missing: {e}",
                base.display()
            ));
            return;
        }
    };
    if metadata.file_type().is_symlink() {
        // Сумісність із попереднім обходом: звичайні Lisp-файли можуть
        // бути символічними посиланнями. Три машинні авторитети нижче
        // перевіряються окремо й залишаються забороненими посиланнями.
        if base.is_file() {
            files.push(base.to_path_buf());
        } else {
            errors.push(format!("{}: dangling or non-file symlink", base.display()));
        }
    } else if metadata.is_file() {
        files.push(base.to_path_buf());
    } else if metadata.is_dir() {
        let entries = match fs::read_dir(base) {
            Ok(entries) => entries,
            Err(e) => {
                errors.push(format!("{}: cannot read directory: {e}", base.display()));
                return;
            }
        };
        let mut children = Vec::new();
        for entry in entries {
            match entry {
                Ok(entry) => children.push(entry.path()),
                Err(e) => errors.push(format!(
                    "{}: unreadable directory entry: {e}",
                    base.display()
                )),
            }
        }
        children.sort();
        for child in children {
            if (child.is_dir() && !child.is_symlink())
                || child.extension().and_then(|x| x.to_str()) == Some("lisp")
            {
                collect(&child, files, errors);
            }
        }
    } else {
        errors.push(format!("{}: not a regular file/directory", base.display()));
    }
}

fn check_sources(root: &Path, selected: &[String]) -> (usize, Vec<String>) {
    let mut errors = Vec::new();
    let mut files = Vec::new();
    for path in selected {
        collect(&root.join(path), &mut files, &mut errors);
    }
    files.sort();
    files.dedup();
    if selected
        .iter()
        .any(|p| p.trim_end_matches('/') == "lib" || p == ".")
    {
        for path in [LOWERING, ENCODING, ADMISSION] {
            let target = root.join(path);
            match fs::symlink_metadata(&target) {
                Ok(m) if m.file_type().is_symlink() => errors.push(format!(
                    "{path}: mandatory machine authority cannot be a symlink"
                )),
                Ok(m) if m.is_file() => {}
                _ => errors.push(format!("{path}: mandatory machine authority file missing")),
            }
        }
    }
    for path in &files {
        let relative = path
            .strip_prefix(root)
            .unwrap_or(path)
            .to_string_lossy()
            .replace('\\', "/");
        let data = match fs::read(path) {
            Ok(data) => data,
            Err(e) => {
                errors.push(format!("{}: cannot read file: {e}", path.display()));
                continue;
            }
        };
        let source = match std::str::from_utf8(&data) {
            Ok(source) => source,
            Err(_) => {
                errors.push(format!("{relative}: invalid UTF-8"));
                continue;
            }
        };
        let b = balance(&data);
        if b.depth != 0 || b.unclosed_string || b.first_negative_line.is_some() {
            errors.push(format!(
                "{relative}: unbalanced; depth={} first-negative-line={:?} unclosed-string={}",
                b.depth, b.first_negative_line, b.unclosed_string
            ));
        }
        for error in check_critical(&relative, source) {
            errors.push(format!("{relative}: {error}"));
        }
    }
    (files.len(), errors)
}

fn run() -> Result<(), String> {
    let args: Vec<String> = env::args().skip(1).collect();
    let mut root = PathBuf::from(".");
    let mut selected: Vec<String> = vec![];
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--root" => {
                i += 1;
                root = PathBuf::from(args.get(i).ok_or("--root requires a directory")?);
            }
            "--paths" => {
                i += 1;
                while i < args.len() && !args[i].starts_with("--") {
                    selected.push(args[i].clone());
                    i += 1;
                }
                continue;
            }
            other => {
                return Err(format!(
                    "unknown argument: {other}; use --root DIR --paths PATH..."
                ))
            }
        }
        i += 1;
    }
    if selected.is_empty() {
        selected.push("lib".to_owned());
    }
    let root = root
        .canonicalize()
        .map_err(|e| format!("cannot open root: {e}"))?;
    let (count, errors) = check_sources(&root, &selected);
    println!("lisp-source-guard: scanned {count} file(s)");
    for error in &errors {
        eprintln!("INTEGRITY-FAIL {error}");
    }
    if errors.is_empty() {
        println!("lisp-source-guard: PASS");
        Ok(())
    } else {
        Err(format!(
            "lisp-source-guard: FAIL ({} defect(s))",
            errors.len()
        ))
    }
}

fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lexical_balance_ignores_comments_and_escaped_strings() {
        assert_eq!(
            balance(b"(a \"; not a comment (\\\"ok\\\")\" ; ) ignored\n (b))"),
            Balance {
                depth: 0,
                first_negative_line: None,
                unclosed_string: false
            }
        );
        let b = balance(b"(a))");
        assert_eq!(b.first_negative_line, Some(1));
        assert_eq!(b.depth, -1);
        assert!(balance(b"(\"unfinished").unclosed_string);
    }

    #[test]
    fn rejects_every_historical_placeholder_and_missing_entry_point() {
        for (relative, (minimum, forms)) in [
            (LOWERING, critical_contract(LOWERING).unwrap()),
            (ENCODING, critical_contract(ENCODING).unwrap()),
            (ADMISSION, critical_contract(ADMISSION).unwrap()),
        ] {
            let baseline = format!("{}\n{}", forms.join("\n"), "; чинний код\n".repeat(minimum));
            assert!(check_critical(relative, &baseline).is_empty(), "{relative}");
            for marker in FORBIDDEN {
                let changed = format!("{baseline}\n; {marker}");
                assert!(check_critical(relative, &changed)
                    .iter()
                    .any(|e| e.contains(*marker)));
            }
            for form in forms {
                let changed = baseline.replacen(*form, "ВИЛУЧЕНО", 1);
                assert!(check_critical(relative, &changed)
                    .iter()
                    .any(|e| e.contains("missing required entry point")));
            }
            assert!(check_critical(relative, "()")
                .iter()
                .any(|e| e.contains("unexpectedly short")));
        }
    }

    #[test]
    fn missing_authority_file_fails_closed() {
        let root = env::temp_dir().join(format!("sens-source-guard-test-{}", process::id()));
        let _ = fs::remove_dir_all(&root);
        fs::create_dir_all(root.join("lib")).unwrap();
        let (_, errors) = check_sources(&root, &["lib".into()]);
        assert_eq!(
            errors
                .iter()
                .filter(|e| e.contains("mandatory machine authority file missing"))
                .count(),
            3
        );
        fs::remove_dir_all(&root).unwrap();
    }
}
