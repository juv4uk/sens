//! Механічна гігієна Zig-джерел; мовні закони визначає SENS.
use std::os::unix::fs::MetadataExt;
use std::{
    fs,
    path::{Path, PathBuf},
    process::Command,
};

fn markers(line: &str) -> Vec<(&'static str, String)> {
    let lower = line.to_ascii_lowercase();
    let mut found = vec![];
    for (reason, prefixes, suffixes, slash, left, digit_only) in [
        (
            "retired-eight-bit-identity",
            &["sens", "sid", "function", "func"][..],
            &["8"][..],
            true,
            false,
            true,
        ),
        (
            "retired-eight-bit-identity",
            &["w"][..],
            &["8"][..],
            true,
            true,
            true,
        ),
        (
            "retired-language-surface",
            &["my"][..],
            &["lisp"][..],
            true,
            true,
            false,
        ),
        (
            "retired-language-surface",
            &["core"][..],
            &["1"][..],
            true,
            true,
            false,
        ),
        (
            "retired-dispatch",
            &["old", "flat"][..],
            &["opcode", "registry", "dispatch", "identity"][..],
            false,
            true,
            false,
        ),
    ] {
        for (start, _) in lower.char_indices() {
            if found.iter().any(|(r, _)| *r == reason) {
                break;
            }
            // Історичні regex мали ASCII lookbehind для назв і Unicode \b
            // для dispatch. Зберігаємо обидві межі, не забороняючи сучасний D8.
            let previous = lower[..start].chars().next_back();
            if left
                && previous.is_some_and(|c| {
                    if reason == "retired-dispatch" {
                        c.is_alphanumeric() || c == '_'
                    } else {
                        c.is_ascii_alphanumeric()
                    }
                })
            {
                continue;
            }
            for prefix in prefixes {
                if !lower[start..].starts_with(prefix) {
                    continue;
                }
                let mut end = start + prefix.len();
                while let Some(c) = lower[end..].chars().next() {
                    if !(c.is_whitespace() || "._-".contains(c) || slash && c == '/') {
                        break;
                    }
                    end += c.len_utf8();
                }
                for suffix in suffixes {
                    if !lower[end..].starts_with(suffix) {
                        continue;
                    }
                    let stop = end + suffix.len();
                    let next = lower[stop..].chars().next();
                    let blocked = next.is_some_and(|c| {
                        if digit_only {
                            c.is_ascii_digit()
                        } else {
                            c.is_alphanumeric() || c == '_'
                        }
                    });
                    if !blocked {
                        found.push((reason, line[start..stop].to_owned()));
                        break;
                    }
                }
                if found.iter().any(|(r, _)| *r == reason) {
                    break;
                }
            }
        }
    }
    found
}

fn source_bytes(root: &Path, relative: &Path) -> Result<Vec<u8>, &'static str> {
    if relative.as_os_str().is_empty()
        || relative
            .components()
            .any(|c| !matches!(c, std::path::Component::Normal(_)))
    {
        return Err("invalid-zig-source-path");
    }
    let mut path = root.to_owned();
    for part in relative.components() {
        path.push(part);
        let meta = fs::symlink_metadata(&path).map_err(|_| "missing-or-nonregular-zig-source")?;
        if meta.file_type().is_symlink() {
            return Err("linked-zig-source");
        }
    }
    let before = fs::symlink_metadata(&path).map_err(|_| "unreadable-zig-source")?;
    if !before.is_file() {
        return Err("missing-or-nonregular-zig-source");
    }
    if before.nlink() != 1 {
        return Err("hardlinked-zig-source");
    }
    let mut file = fs::File::open(&path).map_err(|_| "unreadable-zig-source")?;
    let opened = file.metadata().map_err(|_| "unreadable-zig-source")?;
    let mut content = vec![];
    std::io::Read::read_to_end(&mut file, &mut content).map_err(|_| "unreadable-zig-source")?;
    let after = fs::symlink_metadata(&path).map_err(|_| "unreadable-zig-source")?;
    if after.file_type().is_symlink() {
        return Err("linked-zig-source");
    }
    if [&opened, &after].iter().any(|m| {
        !m.is_file()
            || m.nlink() != 1
            || m.dev() != before.dev()
            || m.ino() != before.ino()
            || m.len() != content.len() as u64
            || m.mtime() != before.mtime()
            || m.mtime_nsec() != before.mtime_nsec()
    }) || before.len() != content.len() as u64
    {
        return Err("changed-zig-source");
    }
    Ok(content)
}

fn quoted(text: &str) -> String {
    let mut out = String::from("\"");
    for c in text.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            c if c < ' ' => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

#[derive(Debug)]
struct Violation {
    path: String,
    line: usize,
    reason: &'static str,
    marker: String,
}

fn audit(root: &Path) -> Result<(usize, usize, Vec<Violation>), String> {
    let output = Command::new("git")
        .args(["ls-files", "-z", "--", "*.zig"])
        .current_dir(root)
        .output()
        .map_err(|e| e.to_string())?;
    if !output.status.success() {
        return Err("git ls-files завершився помилкою".into());
    }
    let mut paths: Vec<_> = output
        .stdout
        .split(|b| *b == 0)
        .filter(|p| !p.is_empty())
        .map(|p| std::str::from_utf8(p).map(str::to_owned))
        .collect::<Result<_, _>>()
        .map_err(|_| "не-UTF8 шлях Zig".to_owned())?;
    paths.sort();
    paths.dedup();
    let reference = paths
        .iter()
        .filter(|p| p.starts_with("research/zig-codecs/"))
        .count();
    let mut violations = vec![];
    if paths.is_empty() {
        violations.push(Violation {
            path: "*.zig".into(),
            line: 0,
            reason: "missing-reference-module",
            marker: String::new(),
        });
    }
    for path in &paths {
        match source_bytes(root, Path::new(path)) {
            Ok(bytes) => match std::str::from_utf8(&bytes) {
                Ok(source) => {
                    for (i, line) in source.lines().enumerate() {
                        for (reason, marker) in markers(line) {
                            violations.push(Violation {
                                path: path.clone(),
                                line: i + 1,
                                reason,
                                marker,
                            });
                        }
                    }
                }
                Err(_) => violations.push(Violation {
                    path: path.clone(),
                    line: 0,
                    reason: "non-utf8-zig-reference",
                    marker: String::new(),
                }),
            },
            Err(reason) => violations.push(Violation {
                path: path.clone(),
                line: 0,
                reason,
                marker: String::new(),
            }),
        }
    }
    Ok((paths.len(), reference, violations))
}

fn run() -> Result<bool, String> {
    let mut root = std::env::current_dir().map_err(|e| e.to_string())?;
    let mut report: Option<PathBuf> = None;
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--root" => root = args.next().ok_or("--root потребує шлях")?.into(),
            "--report" => report = Some(args.next().ok_or("--report потребує шлях")?.into()),
            _ => return Err(format!("невідомий аргумент: {arg}")),
        }
    }
    let (files, reference, violations) = audit(&root)?;
    if let Some(path) = report {
        let rows: Vec<_> = violations
            .iter()
            .map(|v| {
                format!(
                    "{{\"path\":{},\"line\":{},\"reason\":{},\"marker\":{}}}",
                    quoted(&v.path),
                    v.line,
                    quoted(v.reason),
                    quoted(&v.marker)
                )
            })
            .collect();
        let record = format!(
            concat!("{{\"schema\":\"sens-zig-ladder-cleanliness/v4\",",
            "\"kind\":\"source-hygiene-not-semantic-oracle\",\"scope\":\"all git-tracked *.zig\",",
            "\"language_roles_restricted\":false,\"all_tracked_zig_files\":{},",
            "\"reference_zig_files\":{},\"contamination_count\":{},\"violations\":[{}]}}\n"),
            files,
            reference,
            violations.len(),
            rows.join(",")
        );
        if let Some(parent) = path.parent().filter(|p| !p.as_os_str().is_empty()) {
            fs::create_dir_all(parent).map_err(|e| e.to_string())?;
        }
        fs::write(path, record).map_err(|e| e.to_string())?;
    }
    for v in &violations {
        eprintln!(
            "::error file={},line={}::ZIG_PURITY_FAIL reason={} marker={}",
            v.path, v.line, v.reason, v.marker
        );
    }
    println!(
        "ZIG_PURITY_{} files={files} contamination={} authority=SENS_CONTRACT roles=UNRESTRICTED",
        if violations.is_empty() {
            "PASS"
        } else {
            "FAIL"
        },
        violations.len()
    );
    Ok(violations.is_empty())
}

fn main() {
    match run() {
        Ok(true) => (),
        Ok(false) => std::process::exit(1),
        Err(error) => {
            eprintln!("ZIG_PURITY_FAIL: {error}");
            std::process::exit(2);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    struct Temp(PathBuf);
    impl Temp {
        fn new() -> Self {
            let nonce = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos();
            let path = std::env::temp_dir()
                .join(format!("sens-zig-purity-{}-{nonce}", std::process::id()));
            fs::create_dir(&path).unwrap();
            Self(path)
        }
    }
    impl Drop for Temp {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }

    #[test]
    fn regular_and_invalid_file_controls() {
        let temp = Temp::new();
        let root = &temp.0;
        fs::write(root.join("valid.zig"), b"pub const width: u8 = 7;\n").unwrap();
        assert!(source_bytes(root, Path::new("valid.zig")).is_ok());
        std::os::unix::fs::symlink(root.join("valid.zig"), root.join("linked.zig")).unwrap();
        fs::write(root.join("outside"), b"ContaminatedSens8Alias").unwrap();
        fs::hard_link(root.join("outside"), root.join("hardlinked.zig")).unwrap();
        fs::create_dir(root.join("source-dir")).unwrap();
        fs::write(root.join("source-dir/nested.zig"), b"const x = 1;").unwrap();
        std::os::unix::fs::symlink(root.join("source-dir"), root.join("linked-dir")).unwrap();
        for (path, reason) in [
            ("linked.zig", "linked-zig-source"),
            ("linked-dir/nested.zig", "linked-zig-source"),
            ("hardlinked.zig", "hardlinked-zig-source"),
            ("absent.zig", "missing-or-nonregular-zig-source"),
            ("source-dir", "missing-or-nonregular-zig-source"),
            ("../x", "invalid-zig-source-path"),
            ("/x", "invalid-zig-source-path"),
            ("", "invalid-zig-source-path"),
        ] {
            assert_eq!(source_bytes(root, Path::new(path)), Err(reason), "{path}");
        }
    }

    #[test]
    fn real_git_index_failures_are_not_silenced() {
        let temp = Temp::new();
        let root = &temp.0;
        assert!(Command::new("git")
            .args(["init", "-q"])
            .current_dir(root)
            .status()
            .unwrap()
            .success());
        assert_eq!(audit(root).unwrap().2[0].reason, "missing-reference-module");
        fs::write(root.join("sample.zig"), b"// D8:10000000\n").unwrap();
        assert!(Command::new("git")
            .args(["add", "sample.zig"])
            .current_dir(root)
            .status()
            .unwrap()
            .success());
        assert!(audit(root).unwrap().2.is_empty());
        fs::write(root.join("sample.zig"), b"// Sens8\n").unwrap();
        let (_, _, issues) = audit(root).unwrap();
        assert_eq!(issues[0].reason, "retired-eight-bit-identity");
        assert_eq!(issues[0].line, 1);
        fs::write(root.join("sample.zig"), [255]).unwrap();
        assert_eq!(audit(root).unwrap().2[0].reason, "non-utf8-zig-reference");
        fs::remove_file(root.join("sample.zig")).unwrap();
        assert_eq!(
            audit(root).unwrap().2[0].reason,
            "missing-or-nonregular-zig-source"
        );
    }

    #[test]
    fn diagnostic_and_json_boundaries() {
        assert_eq!(
            markers("// a SID / 8 here")[0],
            ("retired-eight-bit-identity", "SID / 8".into())
        );
        assert_eq!(markers("flat_dispatch")[0].0, "retired-dispatch");
        assert!(markers("flat/dispatch").is_empty());
        assert!(markers("αold dispatch").is_empty());
        assert_eq!(quoted("\"\\\n\tпривіт"), "\"\\\"\\\\\\u000a\\u0009привіт\"");
    }
    #[test]
    fn retired_markers_and_current_domains() {
        for bad in [
            "Sens8",
            "sid_8",
            "SID-8",
            "Function8",
            "W8",
            "KernelSid8",
            "ContaminatedSens8Alias",
            "Function8Old",
            "my-lisp",
            "core1",
            "flat dispatch",
        ] {
            assert!(!markers(bad).is_empty(), "не виявлено {bad}");
        }
        for good in [
            "D8:10000000 differs from D9:010000000",
            "lib/core.lisp",
            "const evaluator = @import(\"../../compiler/eval.zig\");",
            "sens80",
            "sid_89",
            "new8",
            "my-lispish",
            "old opcode2",
            "aw8",
        ] {
            assert!(markers(good).is_empty(), "помилкове відхилення {good}");
        }
    }
}
