//! Canonical visible-binary reader for SENS.
//!
//! This path is intentionally separate from the human/compatibility parser.
//! It consumes already-bounded binary source words, applies the ratified D2
//! structural law, and lifts W1 plus W3-W9 payloads directly into DomainIdentity.
//! D8/D9 stay domain-qualified; no unqualified flat-byte function identity is constructed.

use crate::syntax::ExprKind;
use crate::{
    parse_binary_source_words, BinarySourceToken, BinarySourceWord, ErrorKind, Expr, LanguageError,
    Span,
};
use std::rc::Rc;

const D2_SEPARATOR: u8 = 0b00;
const D2_CLOSE: u8 = 0b01;
const D2_OPEN: u8 = 0b10;
const D2_DOT: u8 = 0b11;

/// Parse canonical visible-binary SENS source directly into AST.
///
/// Human punctuation/names are not accepted by the underlying source-word
/// lexer. This function grants no callability: W1 plus W3-W9 payloads become
/// DomainIdentity nodes and later lowering/routing decides whether an identity
/// may head a call.
pub fn parse_canonical_binary(source: &str) -> Result<Vec<Expr>, LanguageError> {
    let tokens = parse_binary_source_words(source)?;
    CanonicalReader::new(&tokens, source.len()).parse_program()
}

/// Parse real packed binary payload bytes directly through the ratified D2 reader.
///
/// The `widths` schedule is **required framing metadata** supplied by the
/// caller, not a substitute semantic registry. A bare packed bitstream cannot
/// identify word boundaries by itself. No visible `0`/`1` text, ASCII token
/// parser, host Lisp surface, or historical SID8 route is constructed here.
///
/// The resulting AST spans refer to *physical byte ranges*, rounded outwards
/// at word boundaries: two adjacent words may therefore share the same byte
/// span. This is not a self-describing canonical file format.
pub fn parse_canonical_packed_words(
    packed: &crate::PackedBitstream,
    widths: &[usize],
) -> Result<Vec<Expr>, LanguageError> {
    let words = crate::unpack_binary_source_words(packed, widths).ok_or_else(|| {
        LanguageError::new(
            ErrorKind::Parse,
            "packed binary payload requires an exact, complete 1..9-bit word-boundary schedule",
            Span {
                start: 0,
                end: packed.byte_len(),
            },
        )
    })?;

    parse_canonical_word_sequence(&words)
}

/// Read an already-decoded sequence of *typed* binary domain words.
///
/// Each word carries its width, so reconstructing a second packed bitstream
/// and then unpacking it is unnecessary. The same D2 CanonicalReader owns all
/// structural syntax; this adapter adds no host-created language rules.
///
/// Spans use virtual dense-payload bytes, rounded outward, like the existing
/// packed-word adapter. They do NOT denote offsets in the ternary T5 file.
pub fn parse_canonical_word_sequence(
    words: &[BinarySourceWord],
) -> Result<Vec<Expr>, LanguageError> {
    let mut bit_offset = 0usize;
    let mut tokens = Vec::with_capacity(words.len());
    for &word in words {
        let start = bit_offset / 8;
        bit_offset = bit_offset.checked_add(word.width()).ok_or_else(|| {
            LanguageError::new(
                ErrorKind::Parse,
                "exact binary source word length overflow",
                Span { start, end: start },
            )
        })?;
        tokens.push(BinarySourceToken {
            word,
            span: Span {
                start,
                end: bit_offset.div_ceil(8),
            },
        });
    }
    CanonicalReader::new(&tokens, bit_offset.div_ceil(8)).parse_program()
}

/// Recognize a D2-framed Text7 identifier without changing the canonical D2 AST.
///
/// This helper is consumed only by contextual binding/call-head code. Ordinary
/// D2/W7 lists remain structural lists in the canonical reader itself.
pub(crate) fn text7_atom(expression: &Expr) -> Option<crate::Text7> {
    let ExprKind::List(items) = &expression.kind else {
        return None;
    };
    if items.is_empty() {
        return None;
    }
    let cells = items
        .iter()
        .map(|item| match &item.kind {
            ExprKind::DomainIdentity(crate::DomainIdentity::D7(word)) => {
                Some(word.word().packed_bits())
            }
            _ => None,
        })
        .collect::<Option<Vec<u8>>>()?;
    crate::Text7::from_cells(cells).ok()
}

/// Canonical internal binding key for a contextual Text7 identifier.
pub(crate) fn text7_binding_key(expression: &Expr) -> Option<Rc<str>> {
    text7_atom(expression).map(|text| Rc::from(text.to_canonical_wire_token()))
}

struct CanonicalReader<'a> {
    tokens: &'a [BinarySourceToken],
    cursor: usize,
    source_end: usize,
}

impl<'a> CanonicalReader<'a> {
    fn new(tokens: &'a [BinarySourceToken], source_end: usize) -> Self {
        Self {
            tokens,
            cursor: 0,
            source_end,
        }
    }

    fn parse_program(mut self) -> Result<Vec<Expr>, LanguageError> {
        let mut expressions = Vec::new();
        while self.cursor < self.tokens.len() {
            self.skip_separators();
            if self.cursor == self.tokens.len() {
                break;
            }
            expressions.push(self.parse_expr(0)?);
        }
        Ok(expressions)
    }

    fn parse_expr(&mut self, depth: u32) -> Result<Expr, LanguageError> {
        let token = *self
            .tokens
            .get(self.cursor)
            .ok_or_else(|| self.error_at_end("expected canonical binary expression"))?;

        // The exact-domain reader has the same finite recursion contract as
        // the source AST parser. Unbounded D2 OPEN words must fail closed
        // instead of exhausting the evaluator's stack.
        if depth as usize > crate::MAX_EXACT_D2_READER_DEPTH {
            return Err(self.error("canonical D2 nesting exceeds AST depth limit", token.span));
        }

        match token.word {
            BinarySourceWord::W2(word) => match word.packed_bits() {
                D2_OPEN => self.parse_list(depth),
                D2_CLOSE => Err(self.error("unexpected D2 close word 01", token.span)),
                D2_DOT => Err(self.error("misplaced D2 dot word 11", token.span)),
                D2_SEPARATOR => Err(self.error(
                    "D2 separator word 00 cannot stand in expression position",
                    token.span,
                )),
                _ => unreachable!("Bit2 exhausts 00/01/10/11"),
            },
            _ => {
                self.cursor += 1;
                self.payload_expr(token)
            }
        }
    }

    fn payload_expr(&self, token: BinarySourceToken) -> Result<Expr, LanguageError> {
        if let BinarySourceWord::W3(word) = token.word {
            // Core.D3 000 is the ratified structural empty value, not a
            // callable identity and not PredicateBit zero.
            if word.packed_bits() == 0 {
                return Ok(Expr {
                    kind: ExprKind::List(Rc::from(Vec::<Expr>::new().into_boxed_slice())),
                    span: token.span,
                });
            }
        }

        // D2 has already been consumed structurally above. W1 and every
        // W3..W9 word carry exact ratified domain identity here; occupancy
        // and callability remain later law-owned decisions.
        let identity = crate::DomainIdentity::from_source_word(token.word);

        Ok(Expr {
            kind: ExprKind::DomainIdentity(identity),
            span: token.span,
        })
    }

    fn parse_list(&mut self, depth: u32) -> Result<Expr, LanguageError> {
        let open = self.tokens[self.cursor];
        debug_assert!(matches!(open.word, BinarySourceWord::W2(_)));
        self.cursor += 1;

        let mut items = Vec::new();

        loop {
            self.skip_separators();
            let Some(token) = self.tokens.get(self.cursor).copied() else {
                return Err(self.error(
                    "unterminated D2 structure opened by 10",
                    Span {
                        start: open.span.start,
                        end: self.source_end,
                    },
                ));
            };

            if let BinarySourceWord::W2(word) = token.word {
                match word.packed_bits() {
                    D2_CLOSE => {
                        self.cursor += 1;
                        let span = Span {
                            start: open.span.start,
                            end: token.span.end,
                        };

                        // D2 framing is structural, not a global Text7 symbol
                        // constructor. Only explicit binder/call-head contexts
                        // may request text7_binding_key from a D2/W7 list.
                        // A bare W7 or a W7 list keeps its domain identity.

                        return Ok(Expr {
                            kind: ExprKind::List(Rc::from(items.into_boxed_slice())),
                            span,
                        });
                    }
                    D2_DOT => {
                        if items.is_empty() {
                            return Err(self.error(
                                "D2 dot word 11 requires at least one head expression",
                                token.span,
                            ));
                        }
                        self.cursor += 1;
                        self.skip_separators();

                        let Some(tail_start) = self.tokens.get(self.cursor).copied() else {
                            return Err(self
                                .error("D2 dot word 11 requires one tail expression", token.span));
                        };
                        if is_d2(tail_start.word, D2_CLOSE) || is_d2(tail_start.word, D2_DOT) {
                            return Err(self.error(
                                "D2 dot word 11 requires one tail expression",
                                tail_start.span,
                            ));
                        }

                        let tail = self.parse_expr(depth + 1)?;
                        self.skip_separators();

                        let Some(close) = self.tokens.get(self.cursor).copied() else {
                            return Err(self.error(
                                "dotted D2 structure must end with close word 01",
                                Span {
                                    start: open.span.start,
                                    end: self.source_end,
                                },
                            ));
                        };
                        if !is_d2(close.word, D2_CLOSE) {
                            return Err(self.error(
                                "dotted D2 structure permits exactly one tail expression before 01",
                                close.span,
                            ));
                        }
                        self.cursor += 1;

                        let span = Span {
                            start: open.span.start,
                            end: close.span.end,
                        };
                        let mut result = tail;
                        for head in items.into_iter().rev() {
                            result = Expr {
                                kind: ExprKind::Pair(Rc::new(head), Rc::new(result)),
                                span,
                            };
                        }
                        return Ok(result);
                    }
                    D2_SEPARATOR => unreachable!("skip_separators consumed D2 00"),
                    D2_OPEN => {}
                    _ => unreachable!("Bit2 exhausts 00/01/10/11"),
                }
            }

            items.push(self.parse_expr(depth + 1)?);
        }
    }

    fn skip_separators(&mut self) {
        while self
            .tokens
            .get(self.cursor)
            .is_some_and(|token| is_d2(token.word, D2_SEPARATOR))
        {
            self.cursor += 1;
        }
    }

    fn error(&self, message: &'static str, span: Span) -> LanguageError {
        LanguageError::new(ErrorKind::Parse, message, span)
    }

    fn error_at_end(&self, message: &'static str) -> LanguageError {
        LanguageError::new(
            ErrorKind::Parse,
            message,
            Span {
                start: self.source_end,
                end: self.source_end,
            },
        )
    }
}

fn is_d2(word: BinarySourceWord, value: u8) -> bool {
    matches!(word, BinarySourceWord::W2(bits) if bits.packed_bits() == value)
}
