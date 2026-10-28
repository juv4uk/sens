//! Structural classifier for reviewed data-only Lisp files.
//! Mechanism only: it never evaluates a form and never grants SENS callability.
//! A non-match returns failure so callers continue through the native SENS path.

use std::env;
use std::fs;
use std::path::Path;
use std::process;

const MAX_BYTES: usize = 1_048_576;
const SCHEMAS: &[&str] = &[
    "silent-fallback-inventory",
    "ft-2",
    "uk-surface-audit-2",
    "uk-sa-coverage",
    "machine-profile-1",
    "machine-domain-profile-3",
];

fn finish_token(
    token: &mut String,
    need_root: &mut bool,
    root_name: &mut Option<String>,
    expected: &str,
) -> bool {
    if token.is_empty() {
        return true;
    }
    let Some(first) = token.chars().next() else {
        return true;
    };
    // Reader constructors remain unknown; do not guess their meaning.
    if matches!(first as u32, 35 | 39 | 96 | 44 | 124 | 92) {
        return false;
    }
    if *need_root {
        if token != expected {
            return false;
        }
        *root_name = Some(token.clone());
        *need_root = false;
    }
    token.clear();
    true
}

fn is_single_data_schema(source: &str, expected: &str) -> bool {
    if source.contains('\0') || source.starts_with('\u{feff}') {
        return false;
    }

    let mut depth: i64 = 0;
    let mut roots = 0usize;
    let mut root_name: Option<String> = None;
    let mut token = String::new();
    let mut need_root = false;
    let mut in_string = false;
    let mut escaped = false;
    let mut in_comment = false;

    for ch in source.chars() {
        if in_comment {
            if ch == '\n' {
                in_comment = false;
            }
            continue;
        }
        if in_string {
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if ch == '"' {
                in_string = false;
            }
            continue;
        }

        if ch.is_whitespace() {
            if !finish_token(&mut token, &mut need_root, &mut root_name, expected) {
                return false;
            }
            continue;
        }
        if ch == ';' {
            if !finish_token(&mut token, &mut need_root, &mut root_name, expected) {
                return false;
            }
            in_comment = true;
            continue;
        }
        if ch == '"' {
            if !finish_token(&mut token, &mut need_root, &mut root_name, expected)
                || need_root
                || depth == 0
            {
                return false;
            }
            in_string = true;
            continue;
        }
        if ch == '(' {
            if !finish_token(&mut token, &mut need_root, &mut root_name, expected) || need_root {
                return false;
            }
            if depth == 0 {
                if roots > 0 {
                    return false;
                }
                roots += 1;
                need_root = true;
            }
            depth += 1;
            continue;
        }
        if ch == ')' {
            if !finish_token(&mut token, &mut need_root, &mut root_name, expected)
                || depth == 0
                || need_root
            {
                return false;
            }
            depth -= 1;
            continue;
        }
        if depth == 0 {
            return false;
        }
        token.push(ch);
        if token.len() > 65_536 {
            return false;
        }
    }

    !in_string
        && !escaped
        && !need_root
        && finish_token(&mut token, &mut need_root, &mut root_name, expected)
        && depth == 0
        && roots == 1
        && root_name.as_deref() == Some(expected)
}

fn run() -> Result<(), i32> {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.len() != 2 || !SCHEMAS.contains(&args[0].as_str()) {
        eprintln!("usage: lisp-data-schema-guard SCHEMA SOURCE.lisp");
        return Err(2);
    }

    let path = Path::new(&args[1]);
    if path.is_symlink() || !path.is_file() {
        return Err(1);
    }
    let metadata = fs::metadata(path).map_err(|_| 1)?;
    if metadata.len() > MAX_BYTES as u64 {
        return Err(1);
    }
    let bytes = fs::read(path).map_err(|_| 1)?;
    if bytes.len() > MAX_BYTES {
        return Err(1);
    }
    let source = std::str::from_utf8(&bytes).map_err(|_| 1)?;
    if is_single_data_schema(source, &args[0]) {
        Ok(())
    } else {
        Err(1)
    }
}

fn main() {
    if let Err(code) = run() {
        process::exit(code);
    }
}

