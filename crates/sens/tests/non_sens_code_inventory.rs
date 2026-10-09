//! #1413: де в проєкті ще є код, написаний не на СЕНС.
//!
//! Два незалежні виміри:
//!
//! 1. **Вихідний код мови** (`.lisp`, `.sens`, ...): кожна голова виклику,
//!    яка є ім'ям функції СЕНС (`car`, `+`, `перше`, `aṇu` ...), а не її
//!    8-бітовим кодом (`00000101`), — рядок коду не на СЕНС.
//! 2. **Виконання**: кожне ім'я з реєстру СЕНС, яке під час виконання
//!    веде не до 1-байтової функції (`Value::Sid`), а до окремої
//!    Rust-функції за іменем (`#<builtin +>`) чи Lisp-замикання, — функція,
//!    що існує поза СЕНС.
//!
//! Храповик: `tests/data/non-sens-code-baseline.tsv` фіксує поточну
//! кількість на файл. Тест падає, якщо десь стало більше або з'явився
//! новий файл. `SENS_BASELINE_UPDATE=1` переписує базу (лише свідомо).
//! Суворі тести `#[ignore]` вимагають нуля:
//! `cargo test -p sens --test non_sens_code_inventory -- --ignored`.

use sens::{eval_program, load_core_library, Session, Value};
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..").canonicalize().unwrap()
}

/// (код, простір, ім'я) з реєстру СЕНС.
fn registry() -> Vec<(String, String, String)> {
    let path = repo_root().join("crates/sens/src/semantic_registry_generated.rs");
    let text = fs::read_to_string(path).unwrap();
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
    assert!(rows.len() > 256, "реєстр не прочитано ({} імен)", rows.len());
    rows
}

fn language_files() -> Vec<PathBuf> {
    fn walk(dir: &Path, out: &mut Vec<PathBuf>) {
        let Ok(entries) = fs::read_dir(dir) else { return };
        for entry in entries.flatten() {
            let path = entry.path();
            let name = entry.file_name().to_string_lossy().into_owned();
            if path.is_dir() {
                if name == "vendor" || name == ".git" || name == "node_modules" || name.starts_with("target") {
                    continue;
                }
                walk(&path, out);
            } else if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
                if ["lisp", "sens", "my", "wsm", "всм", "мій", "лісп"].contains(&ext) {
                    out.push(path);
                }
            }
        }
    }
    let mut out = Vec::new();
    walk(&repo_root(), &mut out);
    out.sort();
    out
}

fn rel(path: &Path) -> String {
    path.strip_prefix(repo_root()).unwrap_or(path).display().to_string()
}

/// Lisp-shaped artifacts that are data/evidence, not executable language source.
/// Keep this exact and fail-closed: future research artifacts must be classified separately.
fn is_non_executable_lisp_artifact(file: &str) -> bool {
    matches!(
        file,
        "docs/research/1556-sens-runtime-lookup-inventory.lisp"
            | "knowledge/sens-primary.lisp"
    )
}

/// Голови викликів: токен одразу після `(`. Коментарі й рядки пропускаються.
fn call_heads(text: &str) -> Vec<String> {
    let mut out = Vec::new();
    let chars: Vec<char> = text.chars().collect();
    let (mut i, mut in_string, mut in_comment) = (0, false, false);
    while i < chars.len() {
        let c = chars[i];
        if in_comment {
            if c == '\n' {
                in_comment = false;
            }
        } else if in_string {
            if c == '\\' {
                i += 1;
            } else if c == '"' {
                in_string = false;
            }
        } else if c == '"' {
            in_string = true;
        } else if c == ';' {
            in_comment = true;
        } else if c == '(' {
            let mut j = i + 1;
            while j < chars.len() && (chars[j] == ' ' || chars[j] == '\t') {
                j += 1;
            }
            let start = j;
            while j < chars.len() && !chars[j].is_whitespace() && !"()\"';".contains(chars[j]) {
                j += 1;
            }
            if j > start {
                out.push(chars[start..j].iter().collect());
            }
        }
        i += 1;
    }
    out
}

fn is_sens_code(token: &str) -> bool {
    token.len() == 8 && token.bytes().all(|b| b == b'0' || b == b'1')
}

/// Файл -> (викликів іменем функції СЕНС, викликів 8-бітовим кодом).
fn source_inventory() -> BTreeMap<String, (usize, usize)> {
    let names: BTreeSet<String> = registry().into_iter().map(|(_, _, name)| name).collect();
    let mut out = BTreeMap::new();
    for path in language_files() {
        let file = rel(&path);
        if is_non_executable_lisp_artifact(&file) {
            continue;
        }
        let Ok(text) = fs::read_to_string(&path) else { continue };
        let (mut named, mut sens) = (0, 0);
        for head in call_heads(&text) {
            if is_sens_code(&head) {
                sens += 1;
            } else if names.contains(&head) {
                named += 1;
            }
        }
        if named + sens > 0 {
            out.insert(file, (named, sens));
        }
    }
    out
}

/// Ім'я -> що воно дає під час виконання, якщо не 1-байтова функція СЕНС.
fn runtime_non_sens() -> BTreeMap<String, String> {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core loads");
    let mut out = BTreeMap::new();
    for (code, namespace, name) in registry() {
        let kind = match eval_program(&name, &mut session) {
            Ok(result) => match &result.value {
                Value::Sid(sid) if sid.to_string() == code => continue,
                Value::Sid(sid) => format!("інша функція СЕНС {sid}"),
                Value::Builtin(_) => "Rust-функція за іменем (builtin)".to_owned(),
                Value::Closure(_) => "Lisp-замикання".to_owned(),
                Value::Macro(_) => "макрос".to_owned(),
                other => format!("значення {other}"),
            },
            // Синтаксис (quote/cond/lambda/def) і непідключені імена
            // не є значенням-функцією — тут не рахуються.
            Err(_) => continue,
        };
        out.insert(format!("{code}\t{namespace}\t{name}"), kind);
    }
    out
}

fn baseline_path() -> PathBuf {
    repo_root().join("crates/sens/tests/data/non-sens-code-baseline.tsv")
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

fn current_counts() -> BTreeMap<String, usize> {
    let mut counts: BTreeMap<String, usize> = source_inventory()
        .into_iter()
        .filter(|(_, (named, _))| *named > 0)
        .map(|(file, (named, _))| (format!("source\t{file}"), named))
        .collect();
    for (key, kind) in runtime_non_sens() {
        counts.insert(format!("runtime\t{key}\t{kind}"), 1);
    }
    counts
}

#[test]
fn non_sens_code_never_grows() {
    let current = current_counts();
    if std::env::var("SENS_BASELINE_UPDATE").as_deref() == Ok("1") {
        let mut text = String::from(
            "# #1413: код не на СЕНС — храповик (див. tests/non_sens_code_inventory.rs)\n\
             # вид\tфайл-або-функція\tкількість\n",
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
        match baseline.get(key) {
            None => grown.push(format!("НОВЕ {key}: {count}")),
            Some(base) if count > base => grown.push(format!("БІЛЬШЕ {key}: {base} -> {count}")),
            _ => {}
        }
    }
    let (named, sens) = source_inventory()
        .values()
        .fold((0, 0), |(a, b), (n, s)| (a + n, b + s));
    let runtime = current.keys().filter(|k| k.starts_with("runtime")).count();
    eprintln!(
        "вихідний код: викликів іменем {named}, кодом СЕНС {sens}; \
         імен, що виконуються не як СЕНС: {runtime}"
    );
    assert!(grown.is_empty(), "коду не на СЕНС стало більше:\n{}", grown.join("\n"));
}

#[test]
#[ignore = "мета: увесь вихідний код мови написаний кодами СЕНС"]
fn all_language_source_is_written_in_sens() {
    let offenders: Vec<String> = source_inventory()
        .into_iter()
        .filter(|(_, (named, _))| *named > 0)
        .map(|(file, (named, sens))| format!("{file}: іменем {named}, СЕНС {sens}"))
        .collect();
    assert!(offenders.is_empty(), "файлів із кодом не на СЕНС: {}\n{}", offenders.len(), offenders.join("\n"));
}

#[test]
#[ignore = "мета: кожне ім'я з реєстру виконується як 1-байтова функція СЕНС"]
fn every_registry_name_executes_as_sens() {
    let offenders: Vec<String> = runtime_non_sens()
        .into_iter()
        .map(|(key, kind)| format!("{key}: {kind}"))
        .collect();
    assert!(offenders.is_empty(), "імен поза СЕНС: {}\n{}", offenders.len(), offenders.join("\n"));
}


#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct Coverage {
    files: usize,
    named: usize,
    sens: usize,
}

impl Coverage {
    fn total(self) -> usize {
        self.named + self.sens
    }

    fn basis_points(self) -> usize {
        let total = self.total();
        (self.sens * 10_000).checked_div(total).unwrap_or(10_000)
    }
}

fn coverage_for<F>(inventory: &BTreeMap<String, (usize, usize)>, include: F) -> Coverage
where
    F: Fn(&str) -> bool,
{
    inventory
        .iter()
        .filter(|(file, _)| include(file))
        .fold(
            Coverage {
                files: 0,
                named: 0,
                sens: 0,
            },
            |mut acc, (_, (named, sens))| {
                acc.files += 1;
                acc.named += named;
                acc.sens += sens;
                acc
            },
        )
}

/// Live language library source. Explicit exclusions are projection/evidence
/// artifacts, not runtime/library code. Keep this list narrow and reviewable:
/// adding an exclusion raises the reported percentage and therefore requires
/// explicit review rather than a broad path heuristic.
fn is_active_lib_source(file: &str) -> bool {
    if !file.starts_with("lib/") || !file.ends_with(".lisp") {
        return false;
    }
    if file.starts_with("lib/generated/") {
        return false;
    }
    !matches!(
        file,
        "lib/machine/encoding/coverage.lisp"
            | "lib/machine/dispatch/native-first-coverage.lisp"
            | "lib/surface/uk-acceptance.lisp"
            | "lib/surface/ukr-acceptance.lisp"
            | "lib/surface/uk-sa-coverage.lisp"
            | "lib/surface/peer-identity-acceptance.lisp"
            | "lib/surface/uk-inventory.lisp"
    )
}

/// Exact authored Lisp sources embedded by the core crate as current
/// runtime/library inputs (`include_str!` constants in crates/sens/src/lib.rs).
/// Core1 is intentionally not in this view because it is not an embedded
/// runtime source there. This deliberately excludes generated registry
/// projections: they are
/// runtime inputs, but are generated evidence rather than authored language
/// source and would dominate this human-authored migration metric.
fn is_runtime_embedded_source(file: &str) -> bool {
    matches!(
        file,
        "lib/macro.lisp"
            | "lib/core2.lisp"
            | "lib/core3.lisp"
            | "lib/core4.lisp"
            | "lib/meta-eval.lisp"
            | "lib/time.lisp"
            | "lib/utf8.lisp"
            | "lib/process.lisp"
            | "lib/tcp.lisp"
            | "lib/fs.lisp"
    )
}


fn active_coverage_baseline_path() -> PathBuf {
    repo_root().join("crates/sens/tests/data/active-sens-coverage-baseline.tsv")
}

fn read_active_coverage_baseline() -> BTreeMap<String, usize> {
    let text = fs::read_to_string(active_coverage_baseline_path())
        .expect("active SENS coverage baseline must exist");
    text.lines()
        .filter(|line| !line.is_empty() && !line.starts_with('#'))
        .map(|line| {
            let columns: Vec<&str> = line.split('\t').collect();
            assert_eq!(
                columns.len(),
                6,
                "active coverage baseline row must have 6 TSV columns: {line}"
            );
            let view = columns[0].to_owned();
            let named_max = columns[2]
                .parse::<usize>()
                .expect("named_max must be an integer");
            (view, named_max)
        })
        .collect()
}

#[test]
fn active_sens_coverage_never_regresses_1673() {
    let inventory = source_inventory();
    let current = BTreeMap::from([
        ("repository-source".to_owned(), coverage_for(&inventory, |_| true)),
        ("active-lib".to_owned(), coverage_for(&inventory, is_active_lib_source)),
        (
            "runtime-embedded".to_owned(),
            coverage_for(&inventory, is_runtime_embedded_source),
        ),
    ]);
    let baseline = read_active_coverage_baseline();

    assert_eq!(
        current.keys().collect::<Vec<_>>(),
        baseline.keys().collect::<Vec<_>>(),
        "coverage views changed: update classification and baseline explicitly"
    );

    let mut regressions = Vec::new();
    // The hard ratchet is absolute admitted-name residue. A percentage floor
    // adds no independent protection against new named authority, but it does
    // punish deletion of exact-SENS calls because the denominator shrinks.
    // Keep basis points as evidence in the report below; gate only named growth.
    for (view, coverage) in current {
        let named_max = baseline[&view];
        if coverage.named > named_max {
            regressions.push(format!(
                "{view}: named call-heads grew {named_max} -> {}",
                coverage.named
            ));
        }
    }

    assert!(
        regressions.is_empty(),
        "active SENS coverage regressed:\n{}",
        regressions.join("\n")
    );
}

/// #1707: host Bool is not language predicate authority.
///
/// JSON/adapters may carry host booleans privately, but the shared
/// predicate/control foundation must never consume or produce `Value::Bool`.
#[test]
fn predicate_foundation_never_uses_host_bool_1707() {
    let core = fs::read_to_string(
        repo_root().join("crates/sens/src/eval/special_forms/core.rs"),
    )
    .expect("read predicate/control foundation");

    assert_eq!(
        core.matches("Value::Bool").count(),
        0,
        "binary-only regression: predicate/control foundation must not use host Value::Bool"
    );
}

#[test]
fn active_sens_coverage_report_1673() {
    let inventory = source_inventory();
    let repository = coverage_for(&inventory, |_| true);
    let active_lib = coverage_for(&inventory, is_active_lib_source);
    let runtime = coverage_for(&inventory, is_runtime_embedded_source);

    eprintln!(
        "SENS_COVERAGE\tview\tfiles\tnamed\tsens\ttotal\tbasis_points"
    );
    for (view, coverage) in [
        ("repository-source", repository),
        ("active-lib", active_lib),
        ("runtime-embedded", runtime),
    ] {
        eprintln!(
            "SENS_COVERAGE\t{view}\t{}\t{}\t{}\t{}\t{}",
            coverage.files,
            coverage.named,
            coverage.sens,
            coverage.total(),
            coverage.basis_points()
        );
    }

    for (file, (named, sens)) in inventory
        .iter()
        .filter(|(file, (named, _))| is_active_lib_source(file) && *named > 0)
    {
        let total = named + sens;
        let basis_points = (sens * 10_000).checked_div(total).unwrap_or(10_000);
        eprintln!(
            "SENS_COVERAGE_FILE\tactive-lib\t{file}\t{named}\t{sens}\t{basis_points}"
        );
    }

    assert!(
        active_lib.total() > 0 && runtime.total() > 0,
        "active SENS coverage views must contain admitted call-heads"
    );
}
