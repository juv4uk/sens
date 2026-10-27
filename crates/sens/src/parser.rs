use crate::{ErrorKind, Exactness, Expr, ExprKind, LanguageError, Span};
use std::rc::Rc;

/// Folds `items` right-to-left onto `tail`, building nested `ExprKind::Pair`
/// nodes — `(a b . c)` becomes `Pair(a, Pair(b, c))`, the same shape `cons`
/// builds at runtime. Every node shares the whole list's span; only the
/// individual `items`/`tail` sub-expressions keep their own precise spans.
/// Враховує реальну глибину вузлів D2 (List/Pair), а не лише дужки
/// джерела. Явний стек потрібний, щоб сама перевірка була безпечною.
fn dotted_subtree_within_depth(expr: &Expr, depth: u32) -> bool {
    let mut pending = vec![(expr, depth)];
    while let Some((node, depth)) = pending.pop() {
        match &node.kind {
            ExprKind::List(items) => {
                if depth > crate::syntax::MAX_STRUCTURE_DEPTH {
                    return false;
                }
                pending.extend(items.iter().map(|item| (item, depth + 1)));
            }
            ExprKind::Pair(head, tail) => {
                if depth > crate::syntax::MAX_STRUCTURE_DEPTH {
                    return false;
                }
                pending.push((head, depth + 1));
                pending.push((tail, depth + 1));
            }
            _ => {}
        }
    }
    true
}

/// Плоска форма (a b ... . z) створює N вкладених Pair, хоча в
/// тексті має лише одну пару дужок. Перевірити майбутню глибину
/// ДО створення першої Pair; не допустити рекурсивний drop гігантського
/// Rc-ланцюга або переповнення стеку у споживачів AST.
fn dotted_list(
    items: Vec<Expr>,
    tail: Expr,
    start: usize,
    end: usize,
    containing_depth: u32,
) -> Result<Expr, LanguageError> {
    let max_depth = crate::syntax::MAX_STRUCTURE_DEPTH;
    let pairs_available = max_depth.saturating_sub(containing_depth) + 1;
    let admitted = containing_depth > 0
        && containing_depth <= max_depth
        && items.len() <= pairs_available as usize
        && items.iter().enumerate().all(|(index, item)| {
            dotted_subtree_within_depth(item, containing_depth + index as u32 + 1)
        })
        && dotted_subtree_within_depth(&tail, containing_depth + items.len() as u32);
    if !admitted {
        return Err(LanguageError::new(
            ErrorKind::Parse,
            "nesting exceeds reader limit · hlybyna vkladennia perevyshchuie mezhu chytacha · Verschachtelungstiefe überschreitet das Reader-Limit",
            Span { start, end },
        ));
    }

    let span = Span { start, end };
    Ok(items.into_iter().rev().fold(tail, |acc, item| Expr {
        kind: ExprKind::Pair(Rc::new(item), Rc::new(acc)),
        span,
    }))
}

/// Звичайний читач для історичних споживачів восьмибітного носія.
/// Він НЕ є авторитетом точних доменів.
pub fn parse(source: &str) -> Result<Vec<Expr>, LanguageError> {
    parse_with_mode(source, ReaderMode::LegacyCompatibility)
}

/// Незалежний читач точних слів D1–D10 для поетапного переходу
/// виконавців. Числова D24+ граматика має окремий носій;
/// жодне невідоме слово не перетворюється на Number або історичний CoreDomainIdentity.
///
/// Явний публічний вхід для міграції активних споживачів.
/// Історичний parse() поки відокремлений: дані W8 не стають D8 через
/// неявне вгадування вихідної епохи.
#[allow(dead_code)]
pub fn parse_exact_domain_source(source: &str) -> Result<Vec<Expr>, LanguageError> {
    parse_with_mode(source, ReaderMode::ExactDomain)
}

/// Читач канонічного *значення* D8 READ: точні біти D1–D10 є
/// тотожностями доменів, а математичні числа мають власний #q2-носій.
/// Не змінює сумісний Lisp parser і не надає словам права виклику.
pub(crate) fn parse_canonical_value_wire(source: &str) -> Result<Vec<Expr>, LanguageError> {
    parse_with_mode(source, ReaderMode::CanonicalValueWire)
}

#[derive(Clone, Copy, Eq, PartialEq)]
enum ReaderMode {
    LegacyCompatibility,
    ExactDomain,
    CanonicalValueWire,
}

fn parse_with_mode(source: &str, mode: ReaderMode) -> Result<Vec<Expr>, LanguageError> {
    let mut parser = Parser {
        source,
        cursor: 0,
        depth: 0,
        mode,
    };
    let mut expressions = Vec::new();
    parser.skip_ignored();
    while parser.cursor < source.len() {
        let expression = parser.expression()?;
        expressions.push(expression);
        parser.skip_ignored();
    }
    Ok(expressions)
}

struct Parser<'a> {
    source: &'a str,
    cursor: usize,
    depth: u32,
    mode: ReaderMode,
}

impl Parser<'_> {
    fn expression(&mut self) -> Result<Expr, LanguageError> {
        self.skip_ignored();
        let start = self.cursor;
        if self.source[self.cursor..].starts_with("#i32(") {
            return self.numeric_buffer(start, false);
        }
        if self.source[self.cursor..].starts_with("#f32(") {
            return self.numeric_buffer(start, true);
        }
        match self.peek() {
            Some('(') => self.list(start),
            Some(')') => Err(self.error(
                "unexpected closing parenthesis · neochikuvana zakryvna duzhka · unerwartete schließende Klammer",
                start,
                start + 1,
            )),
            Some('"') => self.string(start),
            Some('\'') => self.quote_sugar(start),
            Some(_) => self.token(start),
            None => Err(self.error(
                "expected an expression · ochikuvavsia vyraz · Ausdruck erwartet",
                start,
                start,
            )),
        }
    }

    /// Reader sugar: 'form creates the ratified exact D3:001 QUOTE head.
    /// Apostrophes count as D2 list nesting. Accumulate consecutive prefixes
    /// on the heap, avoiding unbounded recursive calls to expression().
    fn quote_sugar(&mut self, start: usize) -> Result<Expr, LanguageError> {
        let mut quote_starts = Vec::new();
        loop {
            self.enter(self.cursor)?;
            quote_starts.push(self.cursor);
            self.bump();
            self.skip_ignored();
            if self.cursor >= self.source.len() {
                return Err(self.error(
                    "expected an expression after apostrophe · pislia apostrofa ochikuietsia vyraz · nach dem Apostroph wird ein Ausdruck erwartet",
                    start,
                    self.cursor,
                ));
            }
            if self.peek() != Some('\'') {
                break;
            }
        }

        // Keep all QUOTE layers charged while reading the operand. This also
        // caps mixed quote/list/numeric-buffer nesting at the shared limit.
        let result = self.expression();
        self.depth -= quote_starts.len() as u32;
        let mut quoted = result?;
        for quote_start in quote_starts.into_iter().rev() {
            quoted = Expr {
                kind: ExprKind::List(
                    vec![
                        Expr {
                            kind: ExprKind::DomainIdentity(crate::DomainIdentity::D3(
                                crate::Bija3::from_word(
                                    crate::Bit3::new(0b001).expect("ratified D3 QUOTE word"),
                                ),
                            )),
                            span: Span {
                                start: quote_start,
                                end: quote_start + 1,
                            },
                        },
                        quoted,
                    ]
                    .into(),
                ),
                span: Span {
                    start: quote_start,
                    end: self.cursor,
                },
            };
        }
        Ok(quoted)
    }

    fn numeric_buffer(&mut self, start: usize, f32_elements: bool) -> Result<Expr, LanguageError> {
        self.enter(start)?;
        self.cursor += 5;
        let result = (|| {
            let mut elements: Vec<Expr> = Vec::new();
            loop {
                self.skip_ignored();
                if self.peek() == Some(')') {
                    self.bump();
                    let buffer = if f32_elements {
                        let mut values = Vec::with_capacity(elements.len());
                        for element in elements {
                            let span = element.span;
                            let number = match element.kind {
                                ExprKind::Number(_, _) => {
                                    let spelling = &self.source[span.start..span.end];
                                    let spelling_with_dot =
                                        if spelling.contains(',') && !spelling.contains('.') {
                                            Some(spelling.replace(',', "."))
                                        } else {
                                            None
                                        };
                                    spelling_with_dot
                                        .as_deref()
                                        .unwrap_or(spelling)
                                        .parse::<f32>()
                                        .map(f64::from)
                                        .map_err(|_| {
                                            self.error(
                                                "#f32 expects numeric elements",
                                                span.start,
                                                span.end,
                                            )
                                        })?
                                }
                                ExprKind::Rational(value) => value.as_f64(),
                                _ => {
                                    return Err(self.error(
                                        "#f32 expects numeric elements",
                                        element.span.start,
                                        element.span.end,
                                    ))
                                }
                            };
                            let narrowed = number as f32;
                            if !number.is_finite() || !narrowed.is_finite() {
                                return Err(LanguageError::new(
                                    ErrorKind::NumericOverflow,
                                    "#f32 element is outside the finite binary32 domain",
                                    element.span,
                                ));
                            }
                            values.push(narrowed);
                        }
                        crate::NumericBuffer::F32(values.into())
                    } else {
                        let mut values = Vec::with_capacity(elements.len());
                        for element in elements {
                            let integer = match element.kind {
                                ExprKind::Number(value, Exactness::Exact)
                                    if value.fract() == 0.0 =>
                                {
                                    value as i64
                                }
                                ExprKind::Rational(value) if value.is_integer() => {
                                    value.as_precise_i64().ok_or_else(|| {
                                        LanguageError::new(
                                            ErrorKind::NumericOverflow,
                                            "#i32 element is outside the signed 32-bit range",
                                            element.span,
                                        )
                                    })?
                                }
                                _ => {
                                    return Err(self.error(
                                        "#i32 expects exact integer elements",
                                        element.span.start,
                                        element.span.end,
                                    ))
                                }
                            };
                            values.push(i32::try_from(integer).map_err(|_| {
                                LanguageError::new(
                                    ErrorKind::NumericOverflow,
                                    "#i32 element is outside the signed 32-bit range",
                                    element.span,
                                )
                            })?);
                        }
                        crate::NumericBuffer::I32(values.into())
                    };
                    return Ok(Expr {
                        kind: ExprKind::NumericBuffer(buffer),
                        span: Span {
                            start,
                            end: self.cursor,
                        },
                    });
                }
                if self.peek().is_none() {
                    return Err(self.error("unclosed numeric buffer", start, self.cursor));
                }
                elements.push(self.expression()?);
            }
        })();
        self.depth -= 1;
        result
    }

    fn enter(&mut self, span_start: usize) -> Result<(), LanguageError> {
        self.depth += 1;
        if self.depth > crate::syntax::MAX_STRUCTURE_DEPTH {
            return Err(self.error(
                "nesting exceeds reader limit · hlybyna vkladennia perevyshchuie mezhu chytacha · Verschachtelungstiefe überschreitet das Reader-Limit",
                span_start,
                span_start + 1,
            ));
        }
        Ok(())
    }

    fn list(&mut self, start: usize) -> Result<Expr, LanguageError> {
        self.enter(start)?;
        let result = self.list_inner(start);
        self.depth -= 1;
        result
    }

    fn list_inner(&mut self, start: usize) -> Result<Expr, LanguageError> {
        self.bump();
        let mut items = Vec::new();
        loop {
            self.skip_ignored();
            match self.peek() {
                Some(')') => {
                    self.bump();
                    return Ok(Expr {
                        kind: ExprKind::List(items.into()),
                        span: Span {
                            start,
                            end: self.cursor,
                        },
                    });
                }
                Some(_) => {
                    // `.` is reader punctuation (#1696): a lone dot in list
                    // context is recognised structurally and never becomes an
                    // expression, so no `Symbol(".")` is ever built.
                    if self.at_dot_marker() {
                        let dot_start = self.cursor;
                        self.bump();
                        if items.is_empty() {
                            return Err(self.error(
                                "unexpected '.' with nothing before it · neochikuvana '.' bez nichoho pered neiu · unerwartetes '.' ohne vorangehenden Ausdruck",
                                dot_start,
                                dot_start + 1,
                            ));
                        }
                        self.skip_ignored();
                        if matches!(self.peek(), None | Some(')')) {
                            return Err(self.error(
                                "expected an expression after '.' · ochikuvavsia vyraz pislia '.' · Ausdruck nach '.' erwartet",
                                self.cursor,
                                self.cursor,
                            ));
                        }
                        let tail = self.expression()?;
                        self.skip_ignored();
                        return match self.peek() {
                            Some(')') => {
                                self.bump();
                                dotted_list(items, tail, start, self.cursor, self.depth)
                            }
                            _ => Err(self.error(
                                "expected ')' after a dotted pair's tail · ochikuvalas ')' pislia khvosta dotted-pary · ')' nach dem Ende eines Dotted Pair erwartet",
                                self.cursor,
                                self.cursor,
                            )),
                        };
                    }

                    let item = self.expression()?;
                    items.push(item);
                }
                None => {
                    return Err(self.error(
                        "unclosed list · nezakrytyi spysok · nicht geschlossene Liste",
                        start,
                        self.cursor,
                    ))
                }
            }
        }
    }

    /// `true` when the next token is exactly the single character `.`, that is
    /// `.` followed by whitespace, a parenthesis, a comment or the end of input.
    /// Tokens such as `.5` or `..` are ordinary tokens and do not match.
    fn at_dot_marker(&self) -> bool {
        let rest = &self.source[self.cursor..];
        let Some(after) = rest.strip_prefix('.') else {
            return false;
        };
        match after.chars().next() {
            None => true,
            Some(next) => next.is_whitespace() || matches!(next, '(' | ')' | ';'),
        }
    }

    fn string(&mut self, start: usize) -> Result<Expr, LanguageError> {
        self.bump();
        let mut value = String::new();
        while let Some(character) = self.bump() {
            match character {
                '"' => {
                    return Ok(Expr {
                        kind: ExprKind::String(value.into()),
                        span: Span {
                            start,
                            end: self.cursor,
                        },
                    })
                }
                '\\' => match self.bump() {
                    Some('n') => value.push('\n'),
                    Some('t') => value.push('\t'),
                    Some('r') => value.push('\r'),
                    Some('"') => value.push('"'),
                    Some('\\') => value.push('\\'),
                    Some(other) => value.push(other),
                    None => {
                        return Err(self.error(
                            "unfinished string escape · nezavershena escape-poslidovnist · unvollständige Escape-Sequenz",
                            start,
                            self.cursor,
                        ))
                    }
                },
                other => value.push(other),
            }
        }
        Err(self.error(
            "unclosed string · nezakrytyi riadok · nicht geschlossene Zeichenkette",
            start,
            self.cursor,
        ))
    }

    fn token(&mut self, start: usize) -> Result<Expr, LanguageError> {
        while let Some(character) = self.peek() {
            if character.is_whitespace() || matches!(character, '(' | ')' | ';') {
                break;
            }
            self.bump();
        }
        let token = &self.source[start..self.cursor];

        // У точному Д1-читачі ратифіковані «ні»/«так» є бітовими
        // значеннями. Сумісний Lisp reader зберігає їх як лексичні Symbol:
        // Core4 містить локальні параметри «так»/«ні» і не може втрачати binder.
        // У eval сумісного джерела незв'язане ім'я проєктується на точний Д1.
        if self.mode == ReaderMode::ExactDomain {
            if let Some(identity) = crate::semantic_registry::d1_value_for_uk_surface(token) {
                return Ok(Expr {
                    kind: ExprKind::DomainIdentity(identity),
                    span: Span {
                        start,
                        end: self.cursor,
                    },
                });
            }
        }

        // A lone `.` outside a dotted pair is not an expression (#1696).
        if token == "." {
            return Err(self.error(
                "unexpected '.' outside a dotted pair · neochikuvana '.' poza dotted-paroiu · unerwartetes '.' außerhalb eines Dotted Pair",
                start,
                self.cursor,
            ));
        }

        // Перехідна текстова проєкція D1. В канонічному бінарному коді
        // тотожність уже є самим 1-бітовим словом 0/1. В історичному
        // текстовому читачі самі "0"/"1" залишаються числами.
        // Явний #d1:0/#d1:1 знімає неоднозначність БЕЗ нової операції,
        // без виклику ATOM/NOT та без ототожнення D1:NO з D3:EMPTY.
        if let Some(bit) = token.strip_prefix("#d1:") {
            if self.mode != ReaderMode::LegacyCompatibility || !matches!(bit, "0" | "1") {
                return Err(self.error(
                    "D1 textual projection requires exactly #d1:0 or #d1:1 in compatibility source",
                    start,
                    self.cursor,
                ));
            }
            let words = crate::parse_binary_source_words(bit)
                .map_err(|_| self.error("invalid one-bit domain identity", start, self.cursor))?;
            let word = words[0].word;
            return Ok(Expr {
                kind: ExprKind::DomainIdentity(crate::DomainIdentity::from_source_word(word)),
                span: Span {
                    start,
                    end: self.cursor,
                },
            });
        }

        // Числовий D24+ носій: явна кваліфікація домену й точного бітового
        // слова — "#d<width>:<bits>", де width кратна 24 і є 24*2^k, а bits
        // рівно width біт. Дзеркалить #d1: і знімає потребу «вгадувати» число.
        // Це і є міст «джерело -> D24-операнд» для математики: жоден
        // некваліфікований літерал не стає операндом.
        if let Some(rest) = token.strip_prefix("#d") {
            if let Some((width_text, bits)) = rest.split_once(':') {
                let width = width_text.parse::<usize>().ok();
                let ok = width.is_some_and(crate::BinaryNumber::is_numeric_domain_width)
                    && width.is_some_and(|w| w == bits.len())
                    && bits.bytes().all(|byte| matches!(byte, b'0' | b'1'));
                if !ok {
                    return Err(self.error(
                        "numeric domain carrier requires #d<24*2^k>:<exactly that many bits>",
                        start,
                        self.cursor,
                    ));
                }
                let words: Vec<u8> = bits.bytes().map(|byte| byte - b'0').collect();
                let number = crate::BinaryNumber::from_numeric_domain_bits(width.unwrap(), &words)
                    .ok_or_else(|| {
                        self.error("invalid exact numeric domain word", start, self.cursor)
                    })?;
                return Ok(Expr {
                    kind: ExprKind::BinaryNumber(number),
                    span: Span {
                        start,
                        end: self.cursor,
                    },
                });
            }
        }

        // В окремому exact-режимі біти означають виключно
        // ширино-залежну DomainIdentity. Історичний 8-бітний payload
        // тут не дає права на виклик; це вирішує окремий domain law.
        if matches!(
            self.mode,
            ReaderMode::ExactDomain | ReaderMode::CanonicalValueWire
        ) {
            if !token.is_empty() && token.bytes().all(|byte| matches!(byte, b'0' | b'1')) {
                let identity = if token.len() == 10 {
                    let coordinate =
                        crate::domain_ladder::DomainCoordinate::з_видимих_бітів(token).ok_or_else(
                            || self.error("непідтримане точне слово D10", start, self.cursor),
                        )?;
                    crate::DomainIdentity::from_coordinate(coordinate)
                } else {
                    let words = crate::parse_binary_source_words(token).map_err(|_| {
                        self.error(
                            "непідтримана точна ширина або невідоме доменне слово",
                            start,
                            self.cursor,
                        )
                    })?;
                    crate::DomainIdentity::from_source_word(words[0].word)
                };
                return Ok(Expr {
                    kind: ExprKind::DomainIdentity(identity),
                    span: Span {
                        start,
                        end: self.cursor,
                    },
                });
            }

            // Історичні десяткові, раціональні й #b/#d/#q2 проєкції
            // не мають права стати числами у поточній D1–D9 граматиці.
            // Числовий D24+ носій повинен бути кваліфікованим явно.
            let first = token.as_bytes().first().copied();
            let numeric_prefix = first.is_some_and(|b| b.is_ascii_digit())
                || matches!(first, Some(b'+' | b'-'))
                    && token.as_bytes().get(1).is_some_and(|b| b.is_ascii_digit());
            if numeric_prefix
                || token.starts_with("#b")
                || token.starts_with("#d")
                // #q2 is a value-level WRITE→READ carrier, not a program
                // literal. Admit it only in CanonicalValueWire mode.
                || (self.mode == ReaderMode::ExactDomain && token.starts_with("#q2:"))
            {
                return Err(self.error(
                    "арифметичні літерали поза явно кваліфікованим D24+ заборонені",
                    start,
                    self.cursor,
                ));
            }
        }

        if let Some(payload) = explicit_radix_payload(token, "#d") {
            let Some(rational) = crate::value::Rational::from_literal(payload, "1") else {
                return Err(self.error("invalid #d exact-integer projection", start, self.cursor));
            };
            let kind = match rational.as_precise_i64() {
                Some(value) => ExprKind::Number(value as f64, Exactness::Exact),
                None => ExprKind::Rational(rational),
            };
            return Ok(Expr {
                kind,
                span: Span {
                    start,
                    end: self.cursor,
                },
            });
        }

        if let Some(payload) = explicit_radix_payload(token, "#b") {
            let number = crate::BinaryNumber::parse(payload)
                .map_err(|_| self.error("invalid canonical binary Number", start, self.cursor))?;
            return Ok(Expr {
                kind: ExprKind::BinaryNumber(number),
                span: Span {
                    start,
                    end: self.cursor,
                },
            });
        }

        if let Some(wire) = token.strip_prefix("#q2:") {
            let Some((numerator, denominator)) = wire.split_once('/') else {
                return Err(self.error("invalid #q2 exact-rational wire", start, self.cursor));
            };
            let Some(rational) =
                crate::value::Rational::from_binary_wire_parts(numerator, denominator)
            else {
                return Err(self.error("invalid #q2 exact-rational wire", start, self.cursor));
            };
            let kind = match rational.as_precise_i64() {
                Some(value) => ExprKind::Number(value as f64, Exactness::Exact),
                None => ExprKind::Rational(rational),
            };
            return Ok(Expr {
                kind,
                span: Span {
                    start,
                    end: self.cursor,
                },
            });
        }

        // У чинному Contract 11.9 текст із восьми бітів НЕ є функцією:
        // семантичний код вимагає і ширини, і ратифікованого домену.
        // Історичний плоский запис лишається тільки інертним символом;
        // точне D8-слово розпізнає окремий доменний читач.
        if token.len() == 8 && token.bytes().all(|byte| matches!(byte, b'0' | b'1')) {
            return Ok(Expr {
                kind: ExprKind::Symbol(Rc::from(token)),
                span: Span {
                    start,
                    end: self.cursor,
                },
            });
        }

        let decimal_with_dot = if token.contains(',') && !token.contains('.') {
            Some(token.replace(',', "."))
        } else {
            None
        };
        let decimal_text = decimal_with_dot.as_deref().unwrap_or(token);
        let normalized_exponent = decimal_text.replace(['е', 'Е'], "e");
        // Surface spellings converge on a private numeric separator whose
        // codepoint is D7/W7 SYN (0010110). This does not alter D7 text data.
        let internal_exponent = normalized_exponent
            .chars()
            .map(|character| match character {
                'e' | 'E' => crate::value::NUMERIC_EXPONENT_SEPARATOR,
                other => other,
            })
            .collect::<String>();
        // `Rational::from_literal` parses arbitrary-precision numerator/denominator
        // text directly (see bignum.rs) — a token like `123456789012345678901/2`,
        // far too big for `i64`, is still an exact rational literal, not a symbol.
        // `Rational::from_literal` parsyt tekst chyselnyka/znamennyka dovilnoi
        // tochnosti napriamu (dyv. bignum.rs) — token na kshtalt
        // `123456789012345678901/2`, zavelykyi dlia `i64`, use odno tochnyi
        // ratsionalnyi literal, ne symvol.
        // `Rational::from_literal` parst Zähler-/Nenner-Text beliebiger Genauigkeit
        // direkt (siehe bignum.rs) — ein Token wie `123456789012345678901/2`, viel
        // zu groß für `i64`, ist weiterhin ein exaktes rationales Literal, kein Symbol.
        // Integer literal → exact; decimal or exponential-notation literal →
        let kind = if let Some((num, den)) = token.split_once('/') {
            if let Some(r) = crate::value::Rational::from_literal(num, den) {
                ExprKind::Rational(r)
            } else {
                ExprKind::Symbol(token.into())
            }
        } else if token.contains(['.', ',', 'e', 'E', 'е', 'Е']) {
            // У канонічному READ точні числа мають окремий #q2-носій.
            // Отже десятковий текст WRITE — саме скінченний inexact f64.
            // Звичайний Lisp-reader лишає десятковий синтаксис точним.
            if self.mode == ReaderMode::CanonicalValueWire {
                if let Ok(number) = normalized_exponent.parse::<f64>() {
                    if !number.is_finite() {
                        return Err(LanguageError::new(
                            ErrorKind::NumericOverflow,
                            "canonical inexact wire number must be finite",
                            Span {
                                start,
                                end: self.cursor,
                            },
                        ));
                    }
                    return Ok(Expr {
                        kind: ExprKind::Number(number, Exactness::Inexact),
                        span: Span {
                            start,
                            end: self.cursor,
                        },
                    });
                }
            }
            let kind = match crate::value::Rational::from_decimal_literal(&internal_exponent) {
                Ok(r) => match r.as_precise_i64() {
                    Some(value) => ExprKind::Number(value as f64, Exactness::Exact),
                    None => ExprKind::Rational(r),
                },
                Err(crate::value::DecimalLiteralError::InvalidSyntax) => {
                    ExprKind::Symbol(token.into())
                }
                Err(crate::value::DecimalLiteralError::ResourceLimitExceeded) => {
                    // S3: a syntactically valid numeric literal must never become
                    // an ordinary symbol just because a parser resource limit
                    // refused to build it - that would change the token's
                    // meaning silently. It fails named, `NumericOverflow`, the
                    // same category runtime arithmetic uses for exact results
                    // past `with_numeric_bit_limit`.
                    return Err(LanguageError::new(
                        ErrorKind::NumericOverflow,
                        "decimal literal exponent exceeds the parser resource limit / eksponenta desiatkovoho literala perevyshchuie resursnu mezhu parsera / der Exponent des Dezimalliterals ueberschreitet die Ressourcengrenze des Parsers",
                        Span {
                            start,
                            end: self.cursor,
                        },
                    ));
                }
            };
            return Ok(Expr {
                kind,
                span: Span {
                    start,
                    end: self.cursor,
                },
            });
        } else if let Some(r) = crate::value::Rational::from_literal(token, "1") {
            // Preserve the compact f64-backed representation only where it is
            // mathematically exact; larger integer literals enter the same
            // arbitrary-precision Rational path as n/1 arithmetic results.
            match r.as_precise_i64() {
                Some(value) => ExprKind::Number(value as f64, Exactness::Exact),
                None => ExprKind::Rational(r),
            }
        } else {
            ExprKind::Symbol(token.into())
        };
        Ok(Expr {
            kind,
            span: Span {
                start,
                end: self.cursor,
            },
        })
    }

    fn skip_ignored(&mut self) {
        loop {
            while self.peek().is_some_and(char::is_whitespace) {
                self.bump();
            }
            if self.peek() != Some(';') {
                break;
            }
            while self.peek().is_some_and(|character| character != '\n') {
                self.bump();
            }
        }
    }

    fn peek(&self) -> Option<char> {
        self.source[self.cursor..].chars().next()
    }

    fn bump(&mut self) -> Option<char> {
        let character = self.peek()?;
        self.cursor += character.len_utf8();
        Some(character)
    }

    fn error(&self, message: &str, start: usize, end: usize) -> LanguageError {
        LanguageError::new(ErrorKind::Parse, message, Span { start, end })
    }
}

fn explicit_radix_payload<'a>(token: &'a str, prefix: &str) -> Option<&'a str> {
    let payload = token.strip_prefix(prefix)?;
    let starts_explicitly = payload.is_empty()
        || payload.starts_with('+')
        || payload.starts_with('-')
        || payload.chars().next().is_some_and(|ch| ch.is_ascii_digit());
    starts_explicitly.then_some(payload)
}

