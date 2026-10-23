//! Нативний Rust-охоронець власності мовних тестів.
//! Тільки механіка CI/шляхів; семантику й вердикт доводить Lisp → Zig/T5M → SENS.
use std::{collections::BTreeSet, env, fs, path::Path, process::{self, Command}};
const PREFIX: &str = "tests/semantic/";
const RUNNER: &str = "scripts/prove-lisp-semantic-t5m.sh";
const CI: &str = ".github/workflows/ci.yml";

fn commands(source: &str) -> Vec<String> {
    let mut result = Vec::new();
    let mut pending = String::new();
    for raw in source.lines() {
        let line = raw.split('#').next().unwrap_or("").trim();
        if line.is_empty() { continue; }
        let continued = line.ends_with('\\');
        let fragment = if continued { line.trim_end_matches('\\').trim_end() } else { line };
        if !pending.is_empty() { pending.push(' '); }
        pending.push_str(fragment);
        if !continued { result.push(std::mem::take(&mut pending)); }
    }
    result
}

fn paths_in(line: &str) -> BTreeSet<String> {
    let mut paths = BTreeSet::new();
    let mut offset = 0;
    while let Some(index) = line[offset..].find(PREFIX) {
        let start = offset + index;
        let n = line[start..].chars().take_while(|ch|
            ch.is_alphanumeric() || matches!(ch, '_' | '-' | '.' | '/')
        ).map(char::len_utf8).sum::<usize>();
        let path = &line[start..start+n];
        if path.ends_with(".lisp") { paths.insert(path.into()); }
        offset = start + n;
        if offset >= line.len() { break; }
    }
    paths
}

fn routed(script: &str) -> BTreeSet<String> {
    let lines = commands(script);
    let calls: Vec<&String> = lines.iter().filter(|s|
        s.starts_with("run_case run_law ")
            || s.starts_with("run_case run_bound_law ")
            || s.starts_with("run_case run_type_rejection ")
            || s.starts_with("run_case run_error_rejection ")
            || s.starts_with("run_case run_division_by_zero_rejection ")
    ).collect();
    let mut result = BTreeSet::new();
    for call in &calls { result.extend(paths_in(call)); }
    for line in lines.iter().filter(|s| s.starts_with("cat ")) {
        let Some((_, dest)) = line.rsplit_once('>') else { continue };
        let name = dest.trim().trim_matches('"').trim_matches('\'')
            .strip_prefix('$').unwrap_or("");
        let name = name.trim_start_matches('{').trim_end_matches('}');
        if name.is_empty() || !name.chars().all(|ch|
            ch.is_ascii_alphanumeric() || ch == '_') { continue }
        let plain = "$".to_string() + name;
        let braced = "$".to_string() + "{" + name + "}";
        // $bundle_extra — інша змінна Bash, а не живий маршрут $bundle.
        // Приймаємо $bundle і ${bundle}, звіряючи точну межу ідентифікатора.
        if calls.iter().any(|call| {
            let call = call.as_str();
            call.contains(&braced) || call.match_indices(plain.as_str()).any(|(at, _)| {
                !call[at + plain.len()..].chars().next().is_some_and(|ch|
                    ch.is_ascii_alphanumeric() || ch == '_')
            })
        }) {
            result.extend(paths_in(line));
        }
    }
    result
}

fn counterpart(path: &str) -> Option<String> {
    if let Some(stem) = path.strip_prefix("tests/semantic/language-law-") {
        return Some(format!("tests/semantic/language-mutant-{stem}"));
    }
    path.strip_suffix("-law.lisp").or_else(|| path.strip_suffix("-laws.lisp"))
        .map(|stem| format!("{stem}-mutant.lisp"))
}

fn positives(path: &str) -> Vec<String> {
    if let Some(stem) = path.strip_prefix("tests/semantic/language-mutant-") {
        return vec![format!("tests/semantic/language-law-{stem}")];
    }
    path.strip_suffix("-mutant.lisp").map(|stem|
        ["-law.lisp", "-laws.lisp", "-positive.lisp"].iter()
            .map(|s| format!("{stem}{s}")).collect()
    ).unwrap_or_default()
}

fn host_oracle(s: &str) -> bool {
    ["eval(", "eval_str(", "eval_source(", "evaluate(", "execute_lisp(", "run_lisp("]
        .iter().any(|x| s.contains(x))
        && ["assert_eq!(", "assert_ne!(", "assert!("].iter().any(|x| s.contains(x))
        && ["Value::", "PredicateBit", "is_truthy", "truth_value"]
            .iter().any(|x| s.contains(x))
}

fn audit(added: &[String], runner: &str, ci: &str,
         exists: impl Fn(&str) -> bool, read: impl Fn(&str) -> Result<String,String>) -> Vec<String> {
    let routes = routed(runner);
    let mut errs = Vec::new();
    if !ci.contains("bash scripts/prove-lisp-semantic-t5m.sh") {
        errs.push("NATIVE_LANGUAGE_RUNNER_NOT_IN_CI".into());
    }
    for stage in ["--t5m-mint", "verify-view", "--t5m-pair", "sens-standalone"] {
        if !runner.contains(stage) { errs.push(format!("NATIVE_LANGUAGE_CORRIDOR_MISSING stage={stage}")); }
    }
    for path in added.iter().collect::<BTreeSet<_>>() {
        if path.starts_with(PREFIX) && [".py",".json",".rs"].iter().any(|suffix| path.ends_with(suffix)) {
            errs.push(format!("HOST_SEMANTIC_TEST_ADDED source={path} use=Lisp-T5M-SENS"));
        }
        if path.starts_with(PREFIX) && path.ends_with(".lisp") {
            if !exists(path) { errs.push(format!("SENS_LAW_SOURCE_MISSING source={path}")); continue; }
            if !routes.contains(path.as_str()) {
                errs.push(format!("SENS_LAW_NOT_REGISTERED source={path}"));
            }
            if let Some(other) = counterpart(path) {
                if !exists(&other) { errs.push(format!("SENS_LAW_MUTANT_MISSING source={path} expected={other}")); }
                else if !routes.contains(&other) { errs.push(format!("SENS_LAW_MUTANT_NOT_ROUTED source={path} expected={other}")); }
            }
            let ps = positives(path);
            if !ps.is_empty() {
                let installed: Vec<_> = ps.iter().filter(|name| exists(name)).collect();
                if installed.is_empty() { errs.push(format!("SENS_LAW_POSITIVE_MISSING source={path}")); }
                else if !installed.iter().any(|name| routes.contains(name.as_str())) {
                    errs.push(format!("SENS_LAW_POSITIVE_NOT_ROUTED source={path}"));
                }
            }
        }
        if path.starts_with("crates/") && path.contains("/tests/") && path.ends_with(".rs") && exists(path) {
            match read(path) {
                Ok(text) if host_oracle(&text) =>
                    errs.push(format!("HOST_SEMANTIC_ORACLE_ADDED source={path} move=tests/semantic/*.lisp")),
                Err(e) => errs.push(format!("GUARD_READ_FAILURE source={path} actual={e}")),
                _ => {}
            }
        }
    }
    errs
}

fn file_exists(path: &str) -> bool {
    Path::new(path).symlink_metadata().is_ok_and(|m| m.is_file() && !m.file_type().is_symlink())
}

// Той самий набір змін, що й у native-semantic кроці CI.
// M важливий: перероблений існуючий Rust-тест теж може стати host-оракулом.
// R важливий: перейменування не скасовує вимоги реального SENS-маршруту.
fn changed_since_in(repo: &Path, base: &str, head: &str) -> Result<Vec<String>,String> {
    let out = Command::new("git").current_dir(repo)
        .args(["diff", "--no-ext-diff", "--name-only", "-z",
            "--diff-filter=ACMRT", base, head, "--", "tests/semantic/", "crates/"])
        .output().map_err(|e| e.to_string())?;
    if !out.status.success() { return Err(format!("git diff {}: {}",
        out.status, String::from_utf8_lossy(&out.stderr))); }
    out.stdout.split(|b| *b==0).filter(|part| !part.is_empty())
        .map(|part| String::from_utf8(part.to_vec()).map_err(|e| e.to_string())).collect()
}

fn changed_since(base: &str, head: &str) -> Result<Vec<String>,String> {
    changed_since_in(Path::new("."), base, head)
}

// Механічний Rust-свідок: старий diff-filter=A пропускав ОБИДВА змінені файли.
// Тест створює тимчасовий Git-репозиторій; мовних значень не обчислює.
fn test_git_change_filter() -> Result<(),String> {
    let nanos = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH).map_err(|e| e.to_string())?.as_nanos();
    let dir = env::temp_dir().join(format!("sens-native-guard-{}-{nanos}", process::id()));
    fs::create_dir(&dir).map_err(|e| e.to_string())?;
    let tested = (|| -> Result<(),String> {
        let git = |args: &[&str]| -> Result<String,String> {
            let out = Command::new("git").current_dir(&dir).args(args)
                .output().map_err(|e| e.to_string())?;
            if !out.status.success() {
                return Err(format!("тест git {:?}: {}", args,
                    String::from_utf8_lossy(&out.stderr)));
            }
            String::from_utf8(out.stdout).map(|s| s.trim().to_string())
                .map_err(|e| e.to_string())
        };
        git(&["init", "-q"])?;
        fs::create_dir_all(dir.join("tests/semantic")).map_err(|e| e.to_string())?;
        fs::create_dir_all(dir.join("crates/sens/tests")).map_err(|e| e.to_string())?;
        fs::write(dir.join("tests/semantic/old-law.lisp"), "(первинний-закон)\n")
            .map_err(|e| e.to_string())?;
        fs::write(dir.join("crates/sens/tests/carrier.rs"), "// механізм\n")
            .map_err(|e| e.to_string())?;
        git(&["add", "."])?;
        git(&["-c", "user.name=SensGuard", "-c",
            "user.email=sens-guard@example.invalid", "commit", "-qm", "base"])?;
        let base = git(&["rev-parse", "HEAD"])?;
        fs::write(dir.join("tests/semantic/old-law.lisp"), "(змінений-закон)\n")
            .map_err(|e| e.to_string())?;
        fs::write(dir.join("crates/sens/tests/carrier.rs"), "// змінений механізм\n")
            .map_err(|e| e.to_string())?;
        fs::write(dir.join("tests/semantic/новий-law.lisp"), "(новий-закон)\n")
            .map_err(|e| e.to_string())?;
        git(&["add", "."])?;
        git(&["-c", "user.name=SensGuard", "-c",
            "user.email=sens-guard@example.invalid", "commit", "-qm", "change"])?;
        let changed = changed_since_in(&dir, &base, "HEAD")?;
        for path in [
            "tests/semantic/old-law.lisp",
            "crates/sens/tests/carrier.rs",
            "tests/semantic/новий-law.lisp",
        ] {
            if !changed.iter().any(|item| item == path) {
                return Err(format!("Не побачено Git-зміну: {path}; знайдено={changed:?}"));
            }
        }
        if changed.len() != 3 {
            return Err(format!("Неочікуваний набір Git-змін: {changed:?}"));
        }
        Ok(())
    })();
    let cleaned = fs::remove_dir_all(&dir).map_err(|e| e.to_string());
    tested?;
    cleaned?;
    Ok(())
}

fn self_test() -> Result<(),String> {
    test_git_change_filter()?;
    let runner = "cat -- tests/semantic/sample-law.lisp > \"$bundle\"\n\
run_case run_law sample \"$bundle\" 1\n\
run_case run_law sample-mut tests/semantic/sample-mutant.lisp 0\n\
--t5m-mint verify-view --t5m-pair sens-standalone\n";
    let ci = "bash scripts/prove-lisp-semantic-t5m.sh";
    let valid = audit(&["tests/semantic/sample-law.lisp".into(),
        "tests/semantic/sample-mutant.lisp".into()], runner, ci, |_| true, |_| Ok(String::new()));
    if !valid.is_empty() { return Err(format!("valid native witnesses: {valid:?}")); }

    // Verify Unicode Lisp paths, source-bundle registration, and law/mutant matching.
    let mut unicode_runner = runner.to_string();
    unicode_runner.push_str(concat!(
        "\ncat -- tests/semantic/усі-за-предикатом-law.lisp > \"$all_law_bundle\"\n",
        "run_case run_law all-predicate-law \"$all_law_bundle\" 1\n",
        "cat -- tests/semantic/усі-за-предикатом-mutant.lisp > \"$all_mutant_bundle\"\n",
        "run_case run_law all-predicate-mutant \"$all_mutant_bundle\" 0\n",
        "cat -- tests/semantic/існує-за-предикатом-law.lisp > \"$any_law_bundle\"\n",
        "run_case run_law exists-predicate-law \"$any_law_bundle\" 1\n",
        "cat -- tests/semantic/існує-за-предикатом-mutant.lisp > \"$any_mutant_bundle\"\n",
        "run_case run_law exists-predicate-mutant \"$any_mutant_bundle\" 0\n",
    ));
    let unicode = audit(
        &[
            "tests/semantic/усі-за-предикатом-law.lisp".into(),
            "tests/semantic/усі-за-предикатом-mutant.lisp".into(),
            "tests/semantic/існує-за-предикатом-law.lisp".into(),
            "tests/semantic/існує-за-предикатом-mutant.lisp".into(),
        ],
        &unicode_runner, ci, |_| true, |_| Ok(String::new()),
    );
    if !unicode.is_empty() {
        return Err(format!("Unicode paired witnesses: {unicode:?}"));
    }
    // Схоже ім'я змінної не доводить, що новий Lisp-закон справді виконується.
    let collision_runner = runner.replace(
        "sample \"$bundle\" 1", "sample \"$bundle_extra\" 1");
    let collision = audit(&["tests/semantic/sample-law.lisp".into()],
        &collision_runner, ci, |_| true, |_| Ok(String::new()));
    if !collision.iter().any(|e| e.contains("SENS_LAW_NOT_REGISTERED")) {
        return Err("lookalike Bash bundle falsely registered a Lisp law".into());
    }
    // Bash-форма ${bundle} залишається чинним посиланням на той самий bundle.
    let braced_runner = runner.replace(
        "sample \"$bundle\" 1", "sample \"${bundle}\" 1");
    let braced = audit(&["tests/semantic/sample-law.lisp".into(),
        "tests/semantic/sample-mutant.lisp".into()],
        &braced_runner, ci, |_| true, |_| Ok(String::new()));
    if !braced.is_empty() {
        return Err(format!("braced native Lisp bundle was rejected: {braced:?}"));
    }

    // Named runtime-error laws are semantic witnesses too: they travel through
    // the same Lisp -> T5M -> SENS corridor and must be discovered by this gate.
    let mut error_runner = runner.to_string();
    error_runner.push_str(
        "run_case run_division_by_zero_rejection d24-computed-zero-denominator \\\n",
    );
    error_runner.push_str(
        "  tests/semantic/d24-reader-zero-denominator-negative.lisp 'division by zero'\\\n",
    );
    let error_route = audit(
        &["tests/semantic/d24-reader-zero-denominator-negative.lisp".into()],
        &error_runner, ci, |_| true, |_| Ok(String::new()),
    );
    if !error_route.is_empty() {
        return Err(format!("typed-error witness route was rejected: {error_route:?}"));
    }

    let invalid = audit(&["tests/semantic/not-a-law.py".into()], runner, ci,
        |_| true, |_| Ok(String::new()));
    if !invalid.iter().any(|e| e.contains("HOST_SEMANTIC_TEST_ADDED")) {
        return Err("Python language oracle incorrectly admitted".into());
    }
    let orphan = audit(&["tests/semantic/orphan-law.lisp".into()], runner, ci,
        |_| true, |_| Ok(String::new()));
    if !orphan.iter().any(|e| e.contains("SENS_LAW_NOT_REGISTERED")) {
        return Err("unrouted Lisp law incorrectly admitted".into());
    }
    Ok(())
}

fn main() {
    let args: Vec<_> = env::args().collect();
    if args.iter().any(|s| s == "--self-test") {
        match self_test() {
            Ok(()) => { println!("SENS_NATIVE_GUARD_SELF_TEST PASS"); return; }
            Err(e) => { eprintln!("::error::SENS_NATIVE_GUARD_SELF_TEST {e}"); process::exit(2) }
        }
    }
    let Some(base) = args.windows(2).find(|a| a[0]=="--base").map(|a| a[1].as_str()) else {
        eprintln!("usage: guard-native-test-ownership --base SHA [--head SHA]"); process::exit(2)
    };
    let head = args.windows(2).find(|a| a[0]=="--head")
        .map(|a| a[1].as_str()).unwrap_or("HEAD");
    let result = (|| -> Result<_,String> {
        let changed = changed_since(base,head)?;
        let script = fs::read_to_string(RUNNER).map_err(|e| e.to_string())?;
        let ci = fs::read_to_string(CI).map_err(|e| e.to_string())?;
        let errs = audit(&changed,&script,&ci,file_exists,
            |path| fs::read_to_string(path).map_err(|e| e.to_string()));
        Ok((changed.len(),errs))
    })();
    match result {
        Ok((changed,errs)) => {
            for err in &errs { eprintln!("::error::REGRESSION layer=test-authority {err}"); }
            println!("SENS_LANGUAGE_OWNERSHIP_AUDIT changed={changed} rejected={} semantic=NOT_ASSERTED native_runner=REQUIRED owner=Rust",errs.len());
            if !errs.is_empty() { process::exit(1); }
        }
        Err(e) => { eprintln!("::error::SENS_LANGUAGE_OWNERSHIP_GATE_FAILURE actual={e}"); process::exit(2) }
    }
}
