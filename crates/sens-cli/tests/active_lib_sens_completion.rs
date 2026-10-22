//! #1675: canonical completion gate for the active authored Lisp library.
//!
//! This test intentionally delegates "is this executable surface safely
//! convertible?" to the real `sens-to-sens` tool.  The older repository
//! inventories are conservative lexical ratchets and may still count names in
//! quote/data/shadowing positions.  Migration completion must not be faked by
//! rewriting those positions.

use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repo root")
}

fn tool() -> Command {
    Command::new(env!("CARGO_BIN_EXE_sens-to-sens"))
}

fn is_explicit_non_implementation(rel: &str) -> bool {
    rel.starts_with("lib/generated/")
        || rel.starts_with("lib/surface/")
        || rel == "lib/machine/encoding/coverage.lisp"
        || rel == "lib/machine/encoding/admitted-iclass-index.lisp"
        // Декларативні джерела: core4 — таблиця з колонками san/en/LISP/sym
        // і опкодами (класичні назви, не перейменовуються), yantra — зовнішні
        // формати (JSON-рядки, адреси). Обидва принципово не кодуються через
        // 128-символьну Д7 без руйнування вмісту, тож не є виконуваними
        // програмами укр-проєкції (як lib/domains/*).
        || rel == "lib/core4.lisp"
        || rel == "lib/yantra.lisp"
        // core-math і core2 — «опис принципів / профілю», навмисно без
        // виконуваних визначень (так само виключені у remint-drifted-pairs).
        || rel == "lib/core-math.lisp"
        || rel == "lib/core2.lisp"
}

/// The generated machine catalogue is data, not executable source. Validate
/// its current Ukrainian record shape so a filename/marker alone cannot hide
/// an appended executable form from the active-source scan.
fn is_generated_iclass_catalogue(rel: &str, source: &str) -> bool {
    if rel != "lib/machine/encoding/admitted-iclass-index.lisp" {
        return false;
    }

    let mut lines = source
        .lines()
        .map(str::trim)
        .filter(|line| !line.is_empty());
    if lines.next()
        != Some("; ЗГЕНЕРОВАНО scripts/generate-encoder-coverage-input.py -- не редагувати вручну.")
        || lines.next()
            != Some("; Компактна проєкція свідчень #175: без статусу, опкоду, семантичного ID чи політики.")
        || lines.next() != Some("(x86-admitted-iclass-index-2")
    {
        return false;
    }

    let count = match lines
        .next()
        .and_then(|line| line.strip_prefix("(pair-count "))
        .and_then(|bits| bits.strip_suffix(')'))
    {
        Some(count) if !count.is_empty() && count.bytes().all(|ch| ch.is_ascii_digit()) => {
            count.parse::<usize>().ok()
        }
        _ => None,
    };
    let Some(expected) = count else { return false };
    if expected == 0 {
        return false;
    }

    let mut observed = 0_usize;
    for line in &mut lines {
        if line == ")" {
            return observed == expected && lines.next().is_none();
        }
        let Some(rest) = line
            .strip_prefix("(пара ")
            .and_then(|line| line.strip_suffix(')'))
        else {
            return false;
        };
        let Some((feature, quoted)) = rest.split_once(" \"") else {
            return false;
        };
        let Some(iclass) = quoted.strip_suffix('"') else {
            return false;
        };
        if feature.is_empty()
            || iclass.is_empty()
            || !feature
                .bytes()
                .all(|b| b.is_ascii_uppercase() || b.is_ascii_digit() || b"-+._".contains(&b))
            || !iclass
                .bytes()
                .all(|b| b.is_ascii_uppercase() || b.is_ascii_digit() || b"_".contains(&b))
        {
            return false;
        }
        observed += 1;
        if observed > expected {
            return false;
        }
    }
    false // Missing close delimiter.
}

fn is_explicit_non_implementation_file(rel: &str, path: &Path) -> bool {
    if is_explicit_non_implementation(rel) {
        return true;
    }
    if rel == "lib/machine/encoding/admitted-iclass-index.lisp" {
        return fs::read_to_string(path)
            .is_ok_and(|source| is_generated_iclass_catalogue(rel, &source));
    }
    false
}

fn is_language_definition_file(rel: &str) -> bool {
    let Some(name) = rel.strip_prefix("lib/") else {
        return false;
    };
    name.starts_with("core") && name.ends_with(".lisp") && !name.contains('/')
}

fn active_lisp_files() -> Vec<(String, PathBuf)> {
    fn walk(root: &Path, dir: &Path, out: &mut Vec<(String, PathBuf)>) {
        for entry in fs::read_dir(dir).expect("read active lib directory") {
            let entry = entry.expect("read active lib entry");
            let path = entry.path();
            if path.is_dir() {
                walk(root, &path, out);
                continue;
            }
            if path.extension().and_then(|ext| ext.to_str()) != Some("lisp") {
                continue;
            }
            let rel = path
                .strip_prefix(root)
                .expect("active lib path under repo")
                .to_string_lossy()
                .replace('\\', "/");
            if !is_explicit_non_implementation_file(&rel, &path) {
                out.push((rel, path));
            }
        }
    }

    let root = repo_root();
    let mut files = Vec::new();
    walk(&root, &root.join("lib"), &mut files);
    files.sort_by(|left, right| left.0.cmp(&right.0));
    files
}

fn run_check(files: &[PathBuf], language: bool) -> Output {
    let mut command = tool();
    command.current_dir(repo_root()).arg("--check");
    if language {
        command.arg("--language");
    }
    for file in files {
        command.arg(file);
    }
    command.output().expect("run canonical sens-to-sens check")
}

fn assert_no_convertible_surface_heads(label: &str, files: &[(String, PathBuf)], language: bool) {
    assert!(!files.is_empty(), "{label}: no files selected");

    let paths: Vec<PathBuf> = files.iter().map(|(_, path)| path.clone()).collect();
    let output = run_check(&paths, language);
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    // `sens-to-sens --check` exits 1 for either a convertible exact surface
    // or an unratified name. The first is this test's subject; the second is
    // not a parser-conversion candidate and must not be silently conflated
    // with domain identity or runtime call admission. Require a complete
    // report for every source and zero exact conversions, while preserving
    // the tool's unratified-head diagnostics for separate semantic work.
    assert!(stderr.is_empty(), "{label}: analyzer error:\n{stderr}");

    for (rel, _) in files {
        let marker = format!("{rel}: convertible=0");
        assert!(
            stdout.contains(&marker),
            "{label}: missing zero-conversion witness for {rel}\nstdout:\n{stdout}"
        );
    }
}

/// Owner canonical human Ukrainian compiler .lisp: verify the current D4
/// DEFINE/LAMBDA AST identities without rewriting the source into machine
/// words. The number of definitions follows the current source, not a stale
/// snapshot. This is neither physical .sens creation nor executable proof.
fn verify_ukrainian_compiler_heads(source: &str) -> Result<(), String> {
    let expected_definitions = source.matches("(визначити").count();
    if expected_definitions == 0
        || source.matches("(функція").count() != expected_definitions
        || source.contains("(0011 ")
        || source.contains("(0010 ")
    {
        return Err("expected matching Ukrainian compiler definitions and lambdas".into());
    }
    let forms = sens::parse_mixed_exact_domain(source)
        .map_err(|error| format!("exact source parser BLOCKED: {error}"))?;
    if forms.len() != expected_definitions {
        return Err(format!(
            "expected {expected_definitions} compiler forms, got {}",
            forms.len()
        ));
    }
    for (i, form) in forms.iter().enumerate() {
        let sens::ExprKind::List(definition) = &form.kind else {
            return Err(format!("compiler definition {i}: missing D2 list"));
        };
        if definition.len() != 3
            || !matches!(&definition[0].kind, sens::ExprKind::DomainIdentity(id)
                if id.width() == 4 && id.packed_bits() == 0b0011)
        {
            return Err(format!("compiler definition {i}: not exact D4 DEFINE"));
        }
        if matches!(
            &definition[1].kind,
            sens::ExprKind::DomainIdentity(_) | sens::ExprKind::Sid(_)
        ) {
            return Err(format!(
                "compiler definition {i}: binder retyped as callable"
            ));
        }
        let sens::ExprKind::List(lambda) = &definition[2].kind else {
            return Err(format!("compiler definition {i}: missing lambda"));
        };
        if lambda.len() < 3
            || !matches!(&lambda[0].kind, sens::ExprKind::DomainIdentity(id)
                if id.width() == 4 && id.packed_bits() == 0b0010)
        {
            return Err(format!("compiler definition {i}: not exact D4 LAMBDA"));
        }
        if let sens::ExprKind::List(parameters) = &lambda[1].kind {
            if parameters.iter().any(|param| {
                matches!(
                    &param.kind,
                    sens::ExprKind::DomainIdentity(_) | sens::ExprKind::Sid(_)
                )
            }) {
                return Err(format!(
                    "compiler definition {i}: lexical parameter is resident"
                ));
            }
        }
    }
    Ok(())
}

#[test]
fn active_authored_lib_has_no_parser_convertible_surface_heads() {
    let files = active_lisp_files();
    let (language, ordinary): (Vec<_>, Vec<_>) = files
        .into_iter()
        .partition(|(rel, _)| is_language_definition_file(rel));

    // Core family files define table-owned language functions.  The canonical
    // migration tool must inspect them in --language mode so recursive calls
    // through those first definitions are not hidden as ordinary shadowing.
    assert_no_convertible_surface_heads("language-definition lib", &language, true);

    // Only this canonical Ukrainian source uses exact AST projection instead of
    // the obsolete SID8 text rewriter. Keep it in the active files census.
    let (compiler, ordinary): (Vec<_>, Vec<_>) = ordinary
        .into_iter()
        .partition(|(rel, _)| rel == "lib/compiler-nucleus.lisp");
    assert_eq!(compiler.len(), 1, "exactly one active compiler source");
    let source = fs::read_to_string(&compiler[0].1).expect("read compiler source");
    verify_ukrainian_compiler_heads(&source)
        .expect("Ukrainian compiler must contain only exact D4 definitions");

    // Every other active source remains in the scan; exact convertible heads
    // and unratified/user-defined call names are reported as separate facts.
    assert_no_convertible_surface_heads("ordinary active lib", &ordinary, false);
}

#[test]
fn ukrainian_compiler_gate_rejects_english_binary_or_new_forms() {
    let source = fs::read_to_string(repo_root().join("lib/compiler-nucleus.lisp"))
        .expect("owner compiler source");
    verify_ukrainian_compiler_heads(&source).expect("owner source exact AST");
    for mutated in [
        source.replacen("(визначити", "(define", 1),
        source.replacen("(функція", "(lambda", 1),
        source.replacen("(визначити", "(0011", 1),
        source.replacen("(функція", "(0010", 1),
        format!("{source}\n(невідоме-додаткове-тіло 1)\n"),
    ] {
        assert!(
            verify_ukrainian_compiler_heads(&mutated).is_err(),
            "unproved English/legacy/extra source must not pass"
        );
    }
}

#[test]
fn generated_iclass_snapshot_is_data_only_when_full_record_contract_holds() {
    let rel = "lib/machine/encoding/admitted-iclass-index.lisp";
    let source_path = repo_root().join(rel);
    let source = fs::read_to_string(&source_path).expect("current generated owner catalogue");
    assert!(is_generated_iclass_catalogue(rel, &source));
    assert!(is_explicit_non_implementation_file(rel, &source_path));

    // A similar file, executable code, forged owner header or new root form
    // must remain in the active-language scan, NOT inherit an exemption.
    assert!(!is_generated_iclass_catalogue(
        "lib/machine/dispatch/native-first.lisp",
        &source
    ));
    assert!(!is_generated_iclass_catalogue(
        rel,
        &source.replace(
            "; ЗГЕНЕРОВАНО scripts/generate-encoder-coverage-input.py",
            "; переписано вручну",
        )
    ));
    assert!(!is_generated_iclass_catalogue(
        rel,
        &source.replace("(pair-count 1176)", "(pair-count 1177)",)
    ));
    assert!(!is_generated_iclass_catalogue(
        rel,
        &source.replacen("(пара X86-BASE \"AAA\")", "(інша X86-BASE \"AAA\")", 1,)
    ));
    assert!(!is_generated_iclass_catalogue(
        rel,
        &format!("{source}\n(запусти-зайве malicious ())\n"),
    ));
    assert!(!is_generated_iclass_catalogue(
        rel,
        source
            .trim_end()
            .strip_suffix(')')
            .expect("catalogue close"),
    ));
}

#[test]
fn active_compiler_and_native_first_are_never_catalogue_data() {
    for rel in [
        "lib/compiler-nucleus.lisp",
        "lib/machine/dispatch/native-first.lisp",
    ] {
        let path = repo_root().join(rel);
        let source = fs::read_to_string(&path).expect("active authored code");
        assert!(!is_explicit_non_implementation_file(rel, &path));
        assert!(!is_generated_iclass_catalogue(rel, &source));
    }
}

#[test]
fn actual_active_lib_collection_excludes_only_validated_generated_catalogue() {
    let selected: Vec<String> = active_lisp_files()
        .into_iter()
        .map(|(relative, _)| relative)
        .collect();
    assert!(!selected.contains(&"lib/machine/encoding/admitted-iclass-index.lisp".to_owned()));
    assert!(selected.contains(&"lib/compiler-nucleus.lisp".to_owned()));
    assert!(selected.contains(&"lib/machine/dispatch/native-first.lisp".to_owned()));
    assert!(selected.contains(&"lib/machine/layout/pair-x86-64.lisp".to_owned()));
}

#[test]
fn completion_gate_exclusions_are_narrow_and_explicit() {
    assert!(is_explicit_non_implementation(
        "lib/machine/encoding/coverage.lisp"
    ));
    assert!(is_explicit_non_implementation(
        "lib/machine/encoding/admitted-iclass-index.lisp"
    ));
    assert!(is_explicit_non_implementation(
        "lib/surface/uk-acceptance.lisp"
    ));
    assert!(is_explicit_non_implementation(
        "lib/generated/function-table.lisp"
    ));

    assert!(!is_explicit_non_implementation("lib/meta-eval.lisp"));
    assert!(!is_explicit_non_implementation(
        "lib/machine/dispatch/native-first-coverage.lisp"
    ));
    assert!(!is_explicit_non_implementation(
        "lib/machine/encoding/admitted-iclass-index-extra.lisp"
    ));
    // core4 і yantra — декларативні джерела, не виконувані програми.
    assert!(is_explicit_non_implementation("lib/core4.lisp"));
    assert!(is_explicit_non_implementation("lib/yantra.lisp"));
    assert!(is_explicit_non_implementation("lib/core-math.lisp"));
    assert!(is_explicit_non_implementation("lib/core2.lisp"));
    assert!(!is_explicit_non_implementation("lib/core.lisp"));
}
