//! Minimal sexpr reader/writer for the `swarm/1` wire protocol.
//! Deliberately separate from `my-lisp`'s own reader: this dialect never
//! needs numbers-as-values, macros, or evaluation — just atoms, strings,
//! and nested lists, line-framed exactly like the existing `:9999` protocol.

#[derive(Debug, Clone, PartialEq)]
pub enum Sexp {
    Atom(String),
    Str(String),
    List(Vec<Sexp>),
}

impl Sexp {
    pub fn atom(s: impl Into<String>) -> Sexp {
        Sexp::Atom(s.into())
    }
    pub fn string(s: impl Into<String>) -> Sexp {
        Sexp::Str(s.into())
    }
    pub fn list(items: Vec<Sexp>) -> Sexp {
        Sexp::List(items)
    }

    /// Treats self as a list of `(key ...rest)` forms and returns the tail
    /// of the first entry whose head atom matches `key`.
    pub fn field(&self, key: &str) -> Option<&[Sexp]> {
        let Sexp::List(items) = self else { return None };
        for item in items {
            if let Sexp::List(inner) = item {
                if let Some(Sexp::Atom(head)) = inner.first() {
                    if head == key {
                        return Some(&inner[1..]);
                    }
                }
            }
        }
        None
    }

    pub fn field_atom(&self, key: &str) -> Option<&str> {
        match self.field(key)?.first()? {
            Sexp::Atom(s) => Some(s.as_str()),
            Sexp::Str(s) => Some(s.as_str()),
            _ => None,
        }
    }

    pub fn head(&self) -> Option<&str> {
        match self {
            Sexp::List(items) => match items.first() {
                Some(Sexp::Atom(s)) => Some(s.as_str()),
                _ => None,
            },
            _ => None,
        }
    }

    pub fn to_text(&self) -> String {
        match self {
            Sexp::Atom(s) => s.clone(),
            Sexp::Str(s) => format!("\"{}\"", s.replace('\\', "\\\\").replace('"', "\\\"")),
            Sexp::List(items) => {
                let inner: Vec<String> = items.iter().map(|i| i.to_text()).collect();
                format!("({})", inner.join(" "))
            }
        }
    }
}

pub fn parse(input: &str) -> Result<Sexp, String> {
    let chars: Vec<char> = input.trim().chars().collect();
    let mut pos = 0usize;
    let value = parse_one(&chars, &mut pos)?;
    Ok(value)
}

/// Skips whitespace and `;`-to-end-of-line comments — needed to read
/// `tasks.lisp`-style durable files, which use the same comment convention
/// as the rest of this ecosystem's `.lisp` data files.
fn skip_ws(chars: &[char], pos: &mut usize) {
    loop {
        while *pos < chars.len() && chars[*pos].is_whitespace() {
            *pos += 1;
        }
        if *pos < chars.len() && chars[*pos] == ';' {
            while *pos < chars.len() && chars[*pos] != '\n' {
                *pos += 1;
            }
            continue;
        }
        break;
    }
}

fn parse_one(chars: &[char], pos: &mut usize) -> Result<Sexp, String> {
    skip_ws(chars, pos);
    if *pos >= chars.len() {
        return Err("unexpected end of input".to_string());
    }
    match chars[*pos] {
        '(' => {
            *pos += 1;
            let mut items = Vec::new();
            loop {
                skip_ws(chars, pos);
                if *pos >= chars.len() {
                    return Err("unclosed list".to_string());
                }
                if chars[*pos] == ')' {
                    *pos += 1;
                    return Ok(Sexp::List(items));
                }
                items.push(parse_one(chars, pos)?);
            }
        }
        '"' => {
            *pos += 1;
            let mut s = String::new();
            while *pos < chars.len() && chars[*pos] != '"' {
                if chars[*pos] == '\\' && *pos + 1 < chars.len() {
                    *pos += 1;
                }
                s.push(chars[*pos]);
                *pos += 1;
            }
            if *pos >= chars.len() {
                return Err("unclosed string".to_string());
            }
            *pos += 1;
            Ok(Sexp::Str(s))
        }
        ')' => Err("unexpected `)`".to_string()),
        _ => {
            let start = *pos;
            while *pos < chars.len()
                && !chars[*pos].is_whitespace()
                && chars[*pos] != '('
                && chars[*pos] != ')'
            {
                *pos += 1;
            }
            Ok(Sexp::Atom(chars[start..*pos].iter().collect()))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round_trips_nested_form() {
        let text = r#"(peer-hello (protocol swarm/1) (node cml-1) (epoch 17) (project cml))"#;
        let parsed = parse(text).unwrap();
        assert_eq!(parsed.head(), Some("peer-hello"));
        assert_eq!(parsed.field_atom("node"), Some("cml-1"));
        assert_eq!(parsed.field_atom("epoch"), Some("17"));
    }

    #[test]
    fn parses_quoted_strings_with_escapes() {
        let text = r#"(payload (artifact "evidence/G8/a \"b\" c.lisp"))"#;
        let parsed = parse(text).unwrap();
        assert_eq!(
            parsed.field_atom("artifact"),
            Some("evidence/G8/a \"b\" c.lisp")
        );
    }
}
