//! Minimal sexpr reader/writer for the `swarm-1` wire protocol.
//! Deliberately separate from `sens`'s own reader: this dialect never
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
            // Invalid atom spelling must not inject delimiters into a
            // newline-framed protocol. Emit it as a quoted text value,
            // which is deliberately not an atom on subsequent reads.
            Sexp::Atom(s)
                if s.is_empty()
                    || s.starts_with(';')
                    || s.chars().any(|ch| {
                        ch.is_whitespace() || ch.is_control() || matches!(ch, '(' | ')' | '"')
                    }) =>
            {
                Sexp::Str(s.clone()).to_text()
            }
            Sexp::Atom(s) => s.clone(),
            Sexp::Str(s) => {
                // One wire/journal record must stay on one physical line.
                let mut encoded = String::with_capacity(s.len() + 2);
                encoded.push('"');
                for ch in s.chars() {
                    match ch {
                        '\\' => encoded.push_str("\\\\"),
                        '"' => encoded.push_str("\\\""),
                        '\n' => encoded.push_str("\\n"),
                        '\r' => encoded.push_str("\\r"),
                        '\t' => encoded.push_str("\\t"),
                        c if c.is_control() => {
                            encoded.push_str(&format!("\\u{{{:X}}}", c as u32));
                        }
                        c => encoded.push(c),
                    }
                }
                encoded.push('"');
                encoded
            }
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
    // Один виклик — рівно один повний S-вираз. Інакше неперевірені
    // форми після першої губляться під час TCP-читання й імпорту tasks.
    skip_ws(&chars, &mut pos);
    if pos != chars.len() {
        return Err("unexpected trailing form or data".to_string());
    }
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
            while *pos < chars.len() {
                match chars[*pos] {
                    '"' => {
                        *pos += 1;
                        return Ok(Sexp::Str(s));
                    }
                    '\\' => {
                        *pos += 1;
                        let escaped = *chars
                            .get(*pos)
                            .ok_or_else(|| "trailing string escape".to_string())?;
                        let decoded = match escaped {
                            '\\' => '\\',
                            '"' => '"',
                            'n' => '\n',
                            'r' => '\r',
                            't' => '\t',
                            'u' => {
                                *pos += 1;
                                if chars.get(*pos) != Some(&'{') {
                                    return Err("malformed Unicode escape".to_string());
                                }
                                *pos += 1;
                                let start = *pos;
                                while chars
                                    .get(*pos)
                                    .is_some_and(|c| c.is_ascii_hexdigit())
                                {
                                    *pos += 1;
                                }
                                if *pos == start || chars.get(*pos) != Some(&'}') {
                                    return Err("malformed Unicode escape".to_string());
                                }
                                let hex: String = chars[start..*pos].iter().collect();
                                let code = u32::from_str_radix(&hex, 16)
                                    .map_err(|_| "invalid Unicode escape".to_string())?;
                                char::from_u32(code)
                                    .ok_or_else(|| "invalid Unicode scalar".to_string())?
                            }
                            // Preserve the original reader's unknown-escape
                            // behavior for hand-written legacy Lisp files.
                            other => other,
                        };
                        s.push(decoded);
                        *pos += 1;
                    }
                    ch => {
                        s.push(ch);
                        *pos += 1;
                    }
                }
            }
            Err("unclosed string".to_string())
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
        let text = r#"(peer-hello (protocol swarm-1) (node cml-1) (epoch 17) (project cml))"#;
        let parsed = parse(text).unwrap();
        assert_eq!(parsed.head(), Some("peer-hello"));
        assert_eq!(parsed.field_atom("node"), Some("cml-1"));
        assert_eq!(parsed.field_atom("epoch"), Some("17"));
    }

    #[test]
    fn rejects_second_top_level_form() {
        // Друга команда не може непомітно зникнути після першої.
        assert!(parse("(metrics) (emit (type evidence-created))").is_err());
    }

    #[test]
    fn rejects_unexpected_suffix() {
        assert!(parse("(metrics) invalid-tail").is_err());
    }

    #[test]
    fn accepts_only_whitespace_and_comments_after_form() {
        let parsed = parse("  (metrics) ; перший коментар\n ; другий коментар").unwrap();
        assert_eq!(parsed.head(), Some("metrics"));
    }

    #[test]
    fn text_roundtrip_preserves_control_characters() {
        let value = Sexp::list(vec![
            Sexp::atom("payload"),
            Sexp::string("перший\n(metrics)\r\nдругий\t\\n\\\" \u{0001}"),
        ]);
        let encoded = value.to_text();
        assert!(!encoded.contains('\n'));
        assert!(!encoded.contains('\r'));
        assert!(!encoded.contains('\t'));
        assert!(!encoded.contains('\u{0001}'));
        assert_eq!(parse(&encoded).unwrap(), value);
    }

    #[test]
    fn serialized_description_cannot_inject_new_frame() {
        let value = Sexp::list(vec![
            Sexp::atom("define-task"),
            Sexp::list(vec![
                Sexp::atom("description"),
                Sexp::string("text\n(complete-task (task X) (generation 1))"),
            ]),
        ]);
        let frame = format!("{}\n", value.to_text());
        assert_eq!(frame.as_bytes().iter().filter(|&&b| b == b'\n').count(), 1);
        assert_eq!(parse(frame.trim_end()).unwrap(), value);
    }

    #[test]
    fn malformed_atom_cannot_inject_a_second_message() {
        let msg = Sexp::list(vec![
            Sexp::atom("heartbeat"),
            Sexp::atom("bad\n(evict (node victim))"),
        ]);
        let line = msg.to_text();
        assert!(!line.contains('\n'));
        assert_eq!(parse(&line).unwrap().head(), Some("heartbeat"));
        assert_eq!(
            parse(&line).unwrap(),
            Sexp::list(vec![
                Sexp::atom("heartbeat"),
                Sexp::string("bad\n(evict (node victim))"),
            ])
        );
    }

    #[test]
    fn control_character_in_atom_is_not_sent_raw() {
        let value = Sexp::atom("peer\u{001B}name");
        let encoded = value.to_text();
        assert!(!encoded.contains('\u{001B}'));
        assert_eq!(parse(&encoded).unwrap(), Sexp::string("peer\u{001B}name"));
    }

    #[test]
    fn invalid_unicode_escape_fails_closed() {
        assert!(parse(r#"(x "\u{D800}")"#).is_err());
        assert!(parse(r#"(x "\u{}")"#).is_err());
        assert!(parse(r#"(x "\u{X}")"#).is_err());
    }

    #[test]
    fn legacy_literal_backslash_n_stays_literal() {
        let original = Sexp::string(r"legacy\ntext");
        assert_eq!(parse(&original.to_text()).unwrap(), original);
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
