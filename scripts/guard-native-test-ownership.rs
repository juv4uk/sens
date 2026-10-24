//! Нативний Rust-охоронець власності мовних тестів.
//! Тільки механіка CI/шляхів; семантику й вердикт доводить Lisp → Zig/T5M → SENS.
use std::{collections::BTreeSet, env, fs, path::Path, process::{self, Command}};
const PREFIX: &str = "tests/semantic/";
const RUNNER: &str = "scripts/prove-lisp-semantic-t5m.sh";
const CI: &str = ".github/workflows/ci.yml";
const REMINT: &str = ".github/workflows/remint-drifted-pairs.yml";

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

// Шлях тесту береться лише з SOURCE, а не з EXPECTED чи тексту повідомлення.
fn source_arg(line: &str, position: usize) -> Option<&str> {
    line.split_whitespace().nth(position)
        .map(|token| token.trim_matches(|ch| ch == '"' || ch == '\''))
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
    for call in &calls {
        if let Some(source) = source_arg(call, 3) { result.extend(paths_in(source)); }
    }
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
        if calls.iter().any(|call| source_arg(call, 3)
            .is_some_and(|source| source == plain.as_str() || source == braced.as_str())) {
            result.extend(paths_in(line));
        }
    }
    result
}

// Незалежні check_lisp_law у CI виконують справжній SENS, але їхній
// прямий PASS не видаємо за фізичну T5M-атестацію.
fn direct_ci_routed(ci: &str) -> BTreeSet<String> {
    commands(ci).into_iter()
        .filter(|line| line.starts_with("check_lisp_law "))
        .flat_map(|line| source_arg(&line, 2).map(paths_in).unwrap_or_default())
        .collect()
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
    let direct_routes = direct_ci_routed(ci);
    let registered = |path: &str| routes.contains(path) || direct_routes.contains(path);
    let mut errs = Vec::new();
    let runner_call = "bash scripts/prove-lisp-semantic-t5m.sh";
    let call_with_args = format!("{runner_call} ");
    let native_runner_active = commands(ci).iter().any(|line|
        line.as_str() == runner_call || line.starts_with(call_with_args.as_str()));
    if !native_runner_active {
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
            if !registered(path) {
                errs.push(format!("SENS_LAW_NOT_REGISTERED id=semantic-law-route layer=test-authority input={path} source={path} expected=registered-native-SENS-route actual=absent"));
            }
            if let Some(other) = counterpart(path) {
                if !exists(&other) { errs.push(format!("SENS_LAW_MUTANT_MISSING source={path} expected={other}")); }
                else if !registered(&other) { errs.push(format!("SENS_LAW_MUTANT_NOT_ROUTED source={path} expected={other}")); }
            }
            let ps = positives(path);
            if !ps.is_empty() {
                let installed: Vec<_> = ps.iter().filter(|name| exists(name)).collect();
                if installed.is_empty() { errs.push(format!("SENS_LAW_POSITIVE_MISSING source={path}")); }
                else if !installed.iter().any(|name| registered(name)) {
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
            "--diff-filter=ACDMRT", base, head])
        .output().map_err(|e| e.to_string())?;
    if !out.status.success() { return Err(format!("git diff {}: {}",
        out.status, String::from_utf8_lossy(&out.stderr))); }
    out.stdout.split(|b| *b==0).filter(|part| !part.is_empty())
        .map(|part| String::from_utf8(part.to_vec()).map_err(|e| e.to_string()))
        .filter(|path| path.as_ref().is_ok_and(|path|
            path.starts_with(PREFIX) || path.starts_with("crates/")))
        .collect()
}

// Видалений тест є окремим Git-станом, а не «джерелом, що загубилося».
// Не послаблюємо перевірку наявності для доданих або змінених файлів.
fn deleted_since_in(repo: &Path, base: &str, head: &str) -> Result<BTreeSet<String>,String> {
    let out = Command::new("git").current_dir(repo)
        .args(["diff", "--no-ext-diff", "--name-only", "-z",
            "--diff-filter=D", base, head])
        .output().map_err(|e| e.to_string())?;
    if !out.status.success() {
        return Err(format!("git diff deleted {}: {}",
            out.status, String::from_utf8_lossy(&out.stderr)));
    }
    out.stdout.split(|b| *b == 0).filter(|part| !part.is_empty())
        .map(|part| String::from_utf8(part.to_vec()).map_err(|e| e.to_string()))
        .collect()
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
        fs::create_dir_all(dir.join("tests/fixtures")).map_err(|e| e.to_string())?;
        fs::create_dir_all(dir.join("crates/sens/tests")).map_err(|e| e.to_string())?;
        fs::write(dir.join("tests/semantic/old-law.lisp"), "(первинний-закон)\n")
            .map_err(|e| e.to_string())?;
        fs::write(dir.join("tests/semantic/moved-fixture.lisp"), "(вхідна-фікстура)\n")
            .map_err(|e| e.to_string())?;
        fs::write(dir.join("tests/semantic/deleted-law.lisp"), "; deleted-sentinel-only-234567890abcdef\n")
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
        fs::remove_file(dir.join("tests/semantic/deleted-law.lisp"))
            .map_err(|e| e.to_string())?;
        fs::rename(
            dir.join("tests/semantic/moved-fixture.lisp"),
            dir.join("tests/fixtures/moved-fixture.lisp"),
        ).map_err(|e| e.to_string())?;
        git(&["add", "-A"])?;
        git(&["-c", "user.name=SensGuard", "-c",
            "user.email=sens-guard@example.invalid", "commit", "-qm", "change"])?;
        let changed = changed_since_in(&dir, &base, "HEAD")?;
        for path in [
            "tests/semantic/old-law.lisp",
            "crates/sens/tests/carrier.rs",
            "tests/semantic/новий-law.lisp",
            "tests/semantic/deleted-law.lisp",
        ] {
            if !changed.iter().any(|item| item == path) {
                return Err(format!("Не побачено Git-зміну: {path}; знайдено={changed:?}"));
            }
        }
        if changed.len() != 4 {
            return Err(format!("Неочікуваний набір Git-змін: {changed:?}"));
        }
        let deleted = deleted_since_in(&dir, &base, "HEAD")?;
        if deleted.len() != 1 ||
           !deleted.contains("tests/semantic/deleted-law.lisp") {
            return Err(format!("Помилкова класифікація Git-видалень: {deleted:?}"));
        }
        if changed.iter().any(|item| item == "tests/semantic/moved-fixture.lisp") {
            return Err(format!("Перейменування назовні помилково лишило старий semantic шлях: {changed:?}"));
        }
        Ok(())
    })();
    let cleaned = fs::remove_dir_all(&dir).map_err(|e| e.to_string());
    tested?;
    cleaned?;
    Ok(())
}

// Обидва проходи remint мають однаково передавати залежності та очікувані помилки.
fn audit_remint_dispatch(workflow: &str) -> Result<(), String> {
    let lines: Vec<&str> = workflow.lines()
        .map(str::trim)
        .filter(|line| !line.is_empty() && !line.starts_with('#'))
        .collect();
    let mut blocks: Vec<Vec<&str>> = Vec::new();
    for (index, line) in lines.iter().enumerate() {
        if *line != "expect_args=()" {
            continue;
        }
        let start = index + 1;
        if lines.get(start).copied() != Some("case \"$f\" in") {
            return Err(format!("REMINT_DISPATCH_MALFORMED layer=CI start={index}"));
        }
        let end = (start + 1..lines.len())
            .find(|&i| lines[i] == "esac")
            .ok_or_else(|| "REMINT_DISPATCH_UNTERMINATED layer=CI".to_string())?;
        let arms = &lines[start + 1..end];
        if arms.is_empty() || arms.iter().any(|arm| !arm.ends_with(";;")) {
            return Err("REMINT_DISPATCH_INVALID_ARMS layer=CI".into());
        }
        blocks.push(arms.to_vec());
    }
    if blocks.len() != 2 {
        return Err(format!(
            "REMINT_DISPATCH_COUNT layer=CI expected=2 actual={}", blocks.len()
        ));
    }
    if blocks[0] != blocks[1] {
        let index = blocks[0].iter().zip(&blocks[1])
            .position(|(a, b)| a != b)
            .unwrap_or_else(|| blocks[0].len().min(blocks[1].len()));
        return Err(format!(
            "REMINT_DISPATCH_DRIFT layer=CI arm={index} expected={:?} actual={:?}",
            blocks[0].get(index), blocks[1].get(index)
        ));
    }
    Ok(())
}

fn test_remint_dispatch() -> Result<(), String> {
    let fixture = r#"
        expect_args=()
        case "$f" in
          test-positive.lisp) bs=(--binding-source lib/a.lisp);;
          test-negative.lisp) expect_args=(--expect-error "car expects a non-empty list");;
          *) : ;;
        esac
        # other remint work
          expect_args=()
          case "$f" in
            test-positive.lisp) bs=(--binding-source lib/a.lisp);;
            test-negative.lisp) expect_args=(--expect-error "car expects a non-empty list");;
            *) : ;;
          esac
    "#;
    audit_remint_dispatch(fixture)?;
    let mutations = [
        fixture.replacen("--binding-source lib/a.lisp", "--binding-source lib/b.lisp", 1),
        fixture.replacen("car expects a non-empty list", "wrong error", 1),
        fixture.replacen("test-positive.lisp) bs=(--binding-source lib/a.lisp);;", "", 1),
        fixture.replacen("expect_args=()", "expect_args=(lost)", 1),
        fixture.replacen("esac", "", 1),
    ];
    for (index, mutant) in mutations.iter().enumerate() {
        if audit_remint_dispatch(mutant).is_ok() {
            return Err(format!("REMINT_DISPATCH_MUTANT_SURVIVED index={index}"));
        }
    }
    Ok(())
}

fn self_test() -> Result<(),String> {
    test_remint_dispatch()?;
    test_git_change_filter()?;
    test_triplet_census()?;
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
    // Прямий check_lisp_law — реальний SENS-шлях, хоча не T5M-сертифікація.
    // Зламана реєстрація повинна відхилити обидва змінені Lisp-свідки.
    let direct_ci = format!("{ci}\ncheck_lisp_law exact-arithmetic-positive tests/semantic/exact-arithmetic-laws.lisp '1'\ncheck_lisp_law exact-arithmetic-mutant tests/semantic/exact-arithmetic-mutant.lisp '0'\n");
    let direct = audit(
        &["tests/semantic/exact-arithmetic-laws.lisp".into(),
          "tests/semantic/exact-arithmetic-mutant.lisp".into()],
        runner, &direct_ci, |_| true, |_| Ok(String::new()),
    );
    if !direct.is_empty() {
        return Err(format!("registered direct SENS witnesses were rejected: {direct:?}"));
    }
    let commented_ci = format!("{ci}\n# check_lisp_law fake tests/semantic/exact-arithmetic-laws.lisp '1'\n");
    let commented = audit(
        &["tests/semantic/exact-arithmetic-laws.lisp".into()],
        runner, &commented_ci, |_| true, |_| Ok(String::new()),
    );
    if !commented.iter().any(|e| e.contains("SENS_LAW_NOT_REGISTERED")) {
        return Err("commented direct SENS route falsely registered a witness".into());
    }
    // Схоже ім'я змінної не доводить, що новий Lisp-закон справді виконується.
    let collision_runner = runner.replace(
        "sample \"$bundle\" 1", "sample \"$bundle_extra\" 1");
    let collision = audit(&["tests/semantic/sample-law.lisp".into()],
        &collision_runner, ci, |_| true, |_| Ok(String::new()));
    if !collision.iter().any(|e| e.contains("SENS_LAW_NOT_REGISTERED")) {
        return Err("lookalike Bash bundle falsely registered a Lisp law".into());
    }
    // SOURCE, а не EXPECTED: згадка bundle чи Lisp-шляху як еталону не запускає закон.
    let wrong_source = runner.replace(
        "sample \"$bundle\" 1", "sample tests/semantic/other.lisp \"$bundle\"");
    let misplaced = audit(&["tests/semantic/sample-law.lisp".into()],
        &wrong_source, ci, |_| true, |_| Ok(String::new()));
    if !misplaced.iter().any(|e| e.contains("SENS_LAW_NOT_REGISTERED")) {
        return Err("bundle in EXPECTED falsely registered an unrouted Lisp law".into());
    }
    let wrong_literal_runner = runner.replace(
        "sample \"$bundle\" 1", "sample tests/semantic/other.lisp tests/semantic/sample-law.lisp");
    let misplaced_literal = audit(&["tests/semantic/sample-law.lisp".into()],
        &wrong_literal_runner, ci, |_| true, |_| Ok(String::new()));
    if !misplaced_literal.iter().any(|e| e.contains("SENS_LAW_NOT_REGISTERED")) {
        return Err("Lisp path in EXPECTED falsely registered native SENS law".into());
    }
    let wrong_direct_runner = runner.replace(
        "sample \"$bundle\" 1", "sample tests/semantic/other.lisp 1");
    let wrong_direct_ci = format!("{ci}\ncheck_lisp_law misplaced tests/semantic/other.lisp tests/semantic/sample-law.lisp\n");
    let misplaced_direct = audit(&["tests/semantic/sample-law.lisp".into()],
        &wrong_direct_runner, &wrong_direct_ci, |_| true, |_| Ok(String::new()));
    if !misplaced_direct.iter().any(|e| e.contains("SENS_LAW_NOT_REGISTERED")) {
        return Err("Lisp path in EXPECTED falsely registered direct SENS law".into());
    }
    let false_ci = "# bash scripts/prove-lisp-semantic-t5m.sh\necho bash scripts/prove-lisp-semantic-t5m.sh\n";
    let inactive = audit(&[], runner, false_ci, |_| true, |_| Ok(String::new()));
    if !inactive.iter().any(|e| e == "NATIVE_LANGUAGE_RUNNER_NOT_IN_CI") {
        return Err("commented or echoed native runner falsely admitted".into());
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
        r#"
run_case run_division_by_zero_rejection d24-computed-zero-denominator tests/semantic/d24-reader-zero-denominator-negative.lisp 'division by zero'
"#,
    );
    let error_route = audit(
        &["tests/semantic/d24-reader-zero-denominator-negative.lisp".into()],
        &error_runner, ci, |_| true, |_| Ok(String::new()),
    );
    if !error_route.is_empty() {
        return Err(format!("typed-error witness route was rejected: {error_route:?}"));
    }
    let deleted = audit(
        &["tests/semantic/deleted-law.lisp".into()], runner, ci,
        |path| path != "tests/semantic/deleted-law.lisp", |_| Ok(String::new()),
    );
    if !deleted.iter().any(|err| err.contains("SENS_LAW_SOURCE_MISSING")) {
        return Err("deleted semantic source was silently treated as unchanged".into());
    }

    let invalid = audit(&["tests/semantic/not-a-law.py".into()], runner, ci,
        |_| true, |_| Ok(String::new()));
    if !invalid.iter().any(|e| e.contains("HOST_SEMANTIC_TEST_ADDED")) {
        return Err("Python language oracle incorrectly admitted".into());
    }
    let orphan = audit(&["tests/semantic/orphan-law.lisp".into()], runner, ci,
        |_| true, |_| Ok(String::new()));
    let Some(receipt) = orphan.iter().find(|e| e.contains("SENS_LAW_NOT_REGISTERED")) else {
        return Err("unrouted Lisp law incorrectly admitted".into());
    };
    // Кожен RED має сам пояснювати ідентичність, шар, вхід і розбіжність.
    for field in ["id=", "layer=", "input=", "expected=", "actual="] {
        if !receipt.contains(field) {
            return Err(format!("unrouted Lisp law receipt lacks {field}: {receipt}"));
        }
    }
    Ok(())
}

#[derive(Debug, PartialEq, Eq)]
struct TripletMissing {
    source: String,
    has_physical: bool,
    has_view: bool,
    semantic: bool,
}

#[derive(Debug, PartialEq, Eq)]
struct TripletCensus {
    lisp_sources: usize,
    physical_present: usize,
    view_present: usize,
    complete: usize,
    semantic_sources: usize,
    semantic_complete: usize,
    missing: Vec<TripletMissing>,
}

// Raw filesystem census only: it never declares a Lisp file a program,
// validates encoded semantics, or grants release admission.
fn census_tracked_paths(
    tracked: &BTreeSet<String>,
    regular_file: impl Fn(&str) -> bool,
) -> TripletCensus {
    let mut result = TripletCensus {
        lisp_sources: 0,
        physical_present: 0,
        view_present: 0,
        complete: 0,
        semantic_sources: 0,
        semantic_complete: 0,
        missing: Vec::new(),
    };
    for source in tracked.iter().filter(|path| path.ends_with(".lisp")) {
        result.lisp_sources += 1;
        let stem = source.strip_suffix(".lisp").expect("suffix checked");
        let physical = format!("{stem}.sens");
        let has_physical = tracked.contains(&physical) && regular_file(&physical);
        let has_view = tracked.contains(stem) && regular_file(stem);
        result.physical_present += if has_physical { 1 } else { 0 };
        result.view_present += if has_view { 1 } else { 0 };
        let semantic = source.starts_with("tests/semantic/");
        if semantic {
            result.semantic_sources += 1;
        }
        if has_physical && has_view {
            result.complete += 1;
            if semantic {
                result.semantic_complete += 1;
            }
        } else {
            result.missing.push(TripletMissing {
                source: (*source).clone(),
                has_physical,
                has_view,
                semantic,
            });
        }
    }
    result
}

fn tracked_triplet_census(repo: &Path) -> Result<TripletCensus, String> {
    let out = Command::new("git").current_dir(repo)
        .args(["ls-files", "-z"])
        .output().map_err(|e| e.to_string())?;
    if !out.status.success() {
        return Err(format!("git ls-files: {}", String::from_utf8_lossy(&out.stderr)));
    }
    let tracked: BTreeSet<String> = out.stdout.split(|byte| *byte == 0)
        .filter(|item| !item.is_empty())
        .map(|item| String::from_utf8(item.to_vec()).map_err(|e| e.to_string()))
        .collect::<Result<_, _>>()?;
    Ok(census_tracked_paths(&tracked, |relative| {
        let path = repo.join(relative);
        path.symlink_metadata().is_ok_and(|metadata|
            metadata.is_file() && !metadata.file_type().is_symlink())
    }))
}

fn print_triplet_census(census: &TripletCensus) {
    println!(
        "SENS_TRIPLET_LAYOUT_CENSUS lisp_sources={} physical_present={} view_present={} complete={} raw_missing={} semantic_sources={} semantic_complete={} semantic_missing={}",
        census.lisp_sources,
        census.physical_present,
        census.view_present,
        census.complete,
        census.missing.len(),
        census.semantic_sources,
        census.semantic_complete,
        census.semantic_sources - census.semantic_complete,
    );
    for row in &census.missing {
        println!(
            "SENS_TRIPLET_LAYOUT_MISSING source={} physical={} view={} scope={}",
            row.source,
            if row.has_physical { "present" } else { "missing" },
            if row.has_view { "present" } else { "missing" },
            if row.semantic { "semantic-law" } else { "needs-classification" },
        );
    }
}

fn test_triplet_census() -> Result<(), String> {
    let tracked = BTreeSet::from([
        "lib/paired.lisp".to_string(),
        "lib/paired.sens".to_string(),
        "lib/paired".to_string(),
        "tests/semantic/unpaired.lisp".to_string(),
    ]);
    let census = census_tracked_paths(&tracked, |path| tracked.contains(path));
    if census.lisp_sources != 2
        || census.physical_present != 1
        || census.view_present != 1
        || census.complete != 1
        || census.semantic_sources != 1
        || census.semantic_complete != 0
        || census.missing != vec![TripletMissing {
            source: "tests/semantic/unpaired.lisp".into(),
            has_physical: false,
            has_view: false,
            semantic: true,
        }]
    {
        return Err(format!("triplet layout census misclassified fixture: {census:?}"));
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
        let census = tracked_triplet_census(Path::new("."))?;
        print_triplet_census(&census);
        let changed = changed_since(base,head)?;
        let deleted = deleted_since_in(Path::new("."), base, head)?;
        // Git-видалення зберігаємо в загальному changed-обліку, але не
        // вимагаємо існування його джерела в поточному дереві.
        let active: Vec<String> = changed.iter()
            .filter(|path| !deleted.contains(path.as_str()))
            .cloned().collect();
        let script = fs::read_to_string(RUNNER).map_err(|e| e.to_string())?;
        let ci = fs::read_to_string(CI).map_err(|e| e.to_string())?;
        let remint = fs::read_to_string(REMINT).map_err(|e| e.to_string())?;
        audit_remint_dispatch(&remint)?;
        let errs = audit(&active,&script,&ci,file_exists,
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
