use std::{
    collections::HashSet,
    env, fs,
    path::{Path, PathBuf},
    process::Command,
};

#[derive(Debug, Clone)]
enum Expr {
    Symbol(String),
    Text(String),
    List(Vec<Expr>),
}

#[derive(Debug, Clone, PartialEq)]
enum Token {
    Open,
    Close,
    Atom(String),
    Text(String),
}

fn tokenize(source: &str, label: &str) -> Vec<Token> {
    let mut chars = source.chars().peekable();
    let mut result = Vec::new();
    while let Some(ch) = chars.next() {
        match ch {
            ';' => while chars.next().is_some_and(|next| next != '\n') {},
            '(' => result.push(Token::Open),
            ')' => result.push(Token::Close),
            '"' => {
                let mut value = String::new();
                let mut closed = false;
                while let Some(next) = chars.next() {
                    match next {
                        '"' => {
                            closed = true;
                            break;
                        }
                        '\\' => {
                            let escaped = chars
                                .next()
                                .unwrap_or_else(|| panic!("{label}: dangling escape in string"));
                            value.push(match escaped {
                                'n' => '\n',
                                'r' => '\r',
                                't' => '\t',
                                '0' => '\0',
                                other => other,
                            });
                        }
                        other => value.push(other),
                    }
                }
                assert!(closed, "{label}: unterminated string");
                result.push(Token::Text(value));
            }
            ch if ch.is_whitespace() => {}
            first => {
                let mut atom = String::from(first);
                while chars.peek().is_some_and(|next| {
                    !next.is_whitespace() && *next != '(' && *next != ')' && *next != ';'
                }) {
                    atom.push(chars.next().expect("peeked character"));
                }
                result.push(Token::Atom(atom));
            }
        }
    }
    result
}

fn parse_expr(tokens: &[Token], cursor: &mut usize, label: &str) -> Expr {
    let token = tokens
        .get(*cursor)
        .unwrap_or_else(|| panic!("{label}: unexpected EOF"));
    *cursor += 1;
    match token {
        Token::Atom(value) => Expr::Symbol(value.clone()),
        Token::Text(value) => Expr::Text(value.clone()),
        Token::Open => {
            let mut values = Vec::new();
            while tokens.get(*cursor) != Some(&Token::Close) {
                assert!(*cursor < tokens.len(), "{label}: unterminated list");
                values.push(parse_expr(tokens, cursor, label));
            }
            *cursor += 1;
            Expr::List(values)
        }
        Token::Close => panic!("{label}: unexpected close parenthesis"),
    }
}

fn parse_all(source: &str, label: &str) -> Vec<Expr> {
    let tokens = tokenize(source, label);
    let mut cursor = 0;
    let mut forms = Vec::new();
    while cursor < tokens.len() {
        forms.push(parse_expr(&tokens, &mut cursor, label));
    }
    forms
}

fn symbol<'a>(expr: &'a Expr, label: &str) -> &'a str {
    match expr {
        Expr::Symbol(value) => value,
        _ => panic!("{label}: expected symbol, got {expr:?}"),
    }
}

fn rust_str(value: &str) -> String {
    format!("{:?}", value)
}

fn add_entry(
    out: &mut String,
    source: &str,
    domain: u16,
    bits: &str,
    column: &str,
    value: &Expr,
    label: &str,
) {
    let (kind, text) = match value {
        Expr::Symbol(value) => ("Symbol", value.as_str()),
        Expr::Text(value) => ("Text", value.as_str()),
        Expr::List(items) if items.is_empty() => {
            out.push_str(&format!("    Entry {{ source: ProjectionSource::{source}, domain: {domain}, bits: {}, column: {}, value: ProjectionValue::EmptyList }},\n", rust_str(bits), rust_str(column)));
            return;
        }
        Expr::List(_) => panic!("{label}: nested list is not a projection value: {value:?}"),
    };
    out.push_str(&format!("    Entry {{ source: ProjectionSource::{source}, domain: {domain}, bits: {}, column: {}, value: ProjectionValue::{kind}({}) }},\n", rust_str(bits), rust_str(column), rust_str(text)));
}

fn domain_tables(root: &Path, out: &mut String) {
    for domain in 1..=10u16 {
        let relative = format!("lib/domains/d{domain}.lisp");
        let path = root.join(&relative);
        println!("cargo:rerun-if-changed={}", path.display());
        let source =
            fs::read_to_string(&path).unwrap_or_else(|error| panic!("{relative}: {error}"));
        let forms = parse_all(&source, &relative);
        assert_eq!(forms.len(), 1, "{relative}: expected one root form");
        let Expr::List(root_form) = &forms[0] else {
            panic!("{relative}: expected root list")
        };
        assert_eq!(
            symbol(&root_form[0], &relative),
            "domain-table-1",
            "{relative}: unsupported table schema"
        );
        let mut count = 0usize;
        let mut coordinates = HashSet::new();
        for row in &root_form[1..] {
            let Expr::List(fields) = row else {
                panic!("{relative}: malformed row {row:?}")
            };
            assert_eq!(
                fields.len(),
                7,
                "{relative}: row must contain bits and six projections"
            );
            let bits = symbol(&fields[0], &relative);
            assert_eq!(
                bits.len(),
                usize::from(domain),
                "{relative}: wrong exact coordinate width {bits}"
            );
            assert!(
                bits.bytes().all(|bit| matches!(bit, b'0' | b'1')),
                "{relative}: non-binary coordinate {bits}"
            );
            assert!(
                coordinates.insert(bits.to_owned()),
                "{relative}: duplicate coordinate {bits}"
            );
            let mut columns = HashSet::new();
            for field in &fields[1..] {
                let Expr::List(pair) = field else {
                    panic!("{relative}: malformed projection {field:?}")
                };
                assert_eq!(
                    pair.len(),
                    2,
                    "{relative}: malformed projection pair {pair:?}"
                );
                let column = symbol(&pair[0], &relative);
                assert!(
                    columns.insert(column),
                    "{relative}: duplicate {column} projection at {bits}"
                );
                add_entry(
                    out,
                    "DomainTable",
                    domain,
                    bits,
                    column,
                    &pair[1],
                    &relative,
                );
            }
            assert_eq!(
                columns.len(),
                6,
                "{relative}: a row must include all six projections"
            );
            count += 1;
        }
        let expected = 1usize << domain;
        assert_eq!(
            count, expected,
            "{relative}: unexpected domain table occupancy"
        );
    }
}

fn binary_bootstrap_words(root: &Path, output: &Path) {
    for path in [
        ".zig-version",
        "bootstrap_t5m.zig",
        "lib/macro.sens",
        "lib/core3.sens",
        "lib/time.sens",
        "research/zig-codecs/t5m.zig",
        "research/zig-codecs/domain_ladder.zig",
        "research/zig-codecs/numeric_domains.zig",
        "research/zig-codecs/t5/t5.zig",
        "research/zig-codecs/transport/fields.zig",
    ] {
        println!("cargo:rerun-if-changed={}", root.join(path).display());
    }
    println!("cargo:rerun-if-env-changed=ZIG");
    println!("cargo:rerun-if-env-changed=PATH");
    println!("cargo:rerun-if-env-changed=LOCALAPPDATA");
    let pinned = include_str!("../../.zig-version").trim();
    let compiler = env::var_os("ZIG").unwrap_or_else(|| {
        #[cfg(windows)]
        if let Some(local_app_data) = env::var_os("LOCALAPPDATA") {
            let cached = PathBuf::from(local_app_data)
                .join("SENS/zig")
                .join(format!("zig-x86_64-windows-{pinned}"))
                .join("zig.exe");
            if cached.is_file() {
                return cached.into_os_string();
            }
        }
        "zig".into()
    });
    let version = Command::new(&compiler)
        .arg("version")
        .output()
        .expect("binary bootstrap requires pinned Zig; use ./guix/run dev or set ZIG");
    assert!(
        version.status.success(),
        "binary bootstrap: Zig version probe failed"
    );
    assert_eq!(
        std::str::from_utf8(&version.stdout)
            .expect("Zig version UTF-8")
            .trim(),
        pinned,
        "binary bootstrap requires the repository Zig pin"
    );
    // Генератор Zig отримує фізичний носій, а Rust — лише точні слова.
    // Жодного читання Lisp або запасного Rust-декодера.
    let restored = Command::new(&compiler)
        .current_dir(root)
        .args(["run", "bootstrap_t5m.zig", "-O", "ReleaseSafe"])
        .output()
        .expect("run pinned Zig T5M bootstrap decoder");
    assert!(
        restored.status.success(),
        "Zig T5M binary bootstrap rejected: {}",
        String::from_utf8_lossy(&restored.stderr)
    );
    assert!(
        !restored.stdout.is_empty(),
        "Zig returned no binary bootstrap words"
    );
    fs::write(output.join("binary_bootstrap_words.rs"), restored.stdout)
        .expect("write Zig-restored exact binary bootstrap words");
}

fn main() {
    let root =
        PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").expect("manifest dir")).join("../..");
    let output = PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR"));
    binary_bootstrap_words(&root, &output);
    let mut generated = String::from("pub(super) static ENTRIES: &[Entry] = &[\n");
    domain_tables(&root, &mut generated);
    generated.push_str("];\n");
    let destination = output.join("domain_projection_catalog.rs");
    fs::write(destination, generated).expect("write generated projection catalog");
}
