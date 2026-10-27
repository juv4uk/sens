//! Експериментальний, ЯВНО парний вузький зріз математики D5/D12+.
//!
//! `name.lisp` містить українську D5-голову та десяткові цілі операнди.
//! Адаптер формує exact D12+ до фізичного Zig T5M без host-float.
//! Машинні #d/#b/#q2 літерали не є людською виконуваною поверхнею.
//! Фізичний `name.sens` перевозить лише слова через Zig T5M.
//! ПРИМІТКА: сама ширина фізичного слова не надає числової D12+-тотожності.
//! Домен береться тільки з перевіреного SENS AST парного джерела;
//! байтове/словесне розходження закриває виконання.
//! Це не standalone T5M interpreter і не фізичний формат результату RATIO.
//! Вкладені D5-вирази з точними D12+ листками дозволені.
//! Одномісні D5:01011 і D5:10111 допускаються за чинним законом SENS.
//!
//! Виклик: sens-math-t5m encode source.lisp
//!         sens-math-t5m eval source.lisp

#[cfg(feature = "zig-transport")]
mod paired {
    use sens::{BinaryNumber, Expr, ExprKind, Session, Value};
    use sens_cli::zig_transport::{self, ExactT5MWord};
    use std::{
        env, fs,
        fs::OpenOptions,
        io::Write,
        path::{Path, PathBuf},
    };

    // The physical codec supplies widths and bits, never semantic admission.
    // D5 heads and D12+ leaf identity are selected by SENS lowering alone.
    fn admit(expr: &Expr, depth: usize) -> Result<(), String> {
        if depth > 64 {
            return Err("SENS admission: nested arithmetic exceeds depth limit".into());
        }
        match &expr.kind {
            ExprKind::BinaryNumber(value) if value.numeric_domain_width().is_some() => Ok(()),
            ExprKind::DomainCall(identity, args)
                if identity.width() == 5
                    // Arity is part of the physical admission law: a head is
                    // admitted only for the exact argument counts its D5 law
                    // defines. ZEROP and NUMBERP are strictly unary D5 laws;
                    // DIFFERENCE and QUOTIENT retain their existing unary
                    // forms alongside the binary form; ADD, MULTIPLY, LESS
                    // and GREATER are strictly binary.
                    && match identity.packed_bits() {
                        0b01000 | 0b01001 => args.len() == 1,
                        0b01011 | 0b10111 => args.len() == 1 || args.len() == 2,
                        0b01010 | 0b10110 | 0b11010 | 0b11011 => args.len() == 2,
                        _ => false,
                    } =>
            {
                // Atomic binary operands must carry the SAME admitted Dn.
                // Nested results (possibly widened by an earlier operation)
                // remain SENS evaluator authority, not host coercion.
                if args.len() == 2 {
                    if let (ExprKind::BinaryNumber(left), ExprKind::BinaryNumber(right)) =
                        (&args[0].kind, &args[1].kind)
                    {
                        if left.numeric_domain_width() != right.numeric_domain_width() {
                            return Err("SENS admission: mixed numeric domains are forbidden".into());
                        }
                    }
                }
                for arg in args.iter() { admit(arg, depth + 1)?; }
                Ok(())
            }
            _ => Err(format!(
                "SENS admission: only qualified D12+ atoms and admitted binary D5 math/predicate calls; actual={:?}",
                expr.kind
            )),
        }
    }

    fn qualify(source: &str) -> Result<Expr, String> {
        // The paired math/T5M executable surface starts source integers at D12.
        qualify_with_minimum_width(source, 12)
    }

    // D12/T5M source admits signed decimal INTEGER lexemes only.
    // The human REPL may parse exact rationals (including Ukrainian comma
    // decimals and exponent notation), but those values must not cross this
    // integer-only physical operand boundary as if they were D12 words.
    fn contains_non_integer_numeric_lexeme(expr: &Expr, source: &str) -> bool {
        fn integer_token(token: &str) -> bool {
            let digits = token
                .strip_prefix('-')
                .or_else(|| token.strip_prefix('+'))
                .unwrap_or(token);
            !digits.is_empty() && digits.bytes().all(|byte| byte.is_ascii_digit())
        }

        fn numeric_fractional_spelling(expr: &Expr, source: &str) -> bool {
            // The general SENS REPL accepts exact decimal/exponent literals,
            // but this physical D12/T5M profile is deliberately integer-only.
            // Check the original source spelling even when the reader leaves a
            // numeric-looking token as Symbol (for example 0,5 under a
            // surface-specific read path). Otherwise the general REPL
            // projection can silently turn it into a D5 quotient call.
            let Some(token) = source.get(expr.span.start..expr.span.end) else {
                return false;
            };
            let unsigned = token
                .strip_prefix('-')
                .or_else(|| token.strip_prefix('+'))
                .unwrap_or(token);
            let starts_with_digit = unsigned
                .as_bytes()
                .first()
                .is_some_and(u8::is_ascii_digit);
            let comma_prefixed_digits = unsigned
                .strip_prefix(',')
                .is_some_and(|digits| {
                    !digits.is_empty() && digits.bytes().all(|byte| byte.is_ascii_digit())
                });
            let has_fractional_marker = unsigned
                .bytes()
                .any(|byte| matches!(byte, b',' | b'.' | b'e' | b'E'))
                || unsigned.contains('е')
                || unsigned.contains('Е');
            (starts_with_digit || comma_prefixed_digits)
                && has_fractional_marker
                && !integer_token(token)
        }

        // Validate the source lexeme before the REPL projection can normalize
        // an exact decimal into D5 QUOTIENT over D12+ components.
        if numeric_fractional_spelling(expr, source) {
            return true;
        }

        match &expr.kind {
            ExprKind::Rational(_) | ExprKind::Number(_, _) => {
                let Some(token) = source.get(expr.span.start..expr.span.end) else {
                    return true;
                };
                !integer_token(token)
            }
            ExprKind::List(items)
            | ExprKind::Call(_, items)
            | ExprKind::DomainCall(_, items) => items
                .iter()
                .any(|item| contains_non_integer_numeric_lexeme(item, source)),
            ExprKind::Pair(left, right) => {
                contains_non_integer_numeric_lexeme(left, source)
                    || contains_non_integer_numeric_lexeme(right, source)
            }
            _ => false,
        }
    }

    fn qualify_with_minimum_width(
        source: &str,
        minimum_width: usize,
    ) -> Result<Expr, String> {
        // Вхід — людський Lisp; encoded literals cannot grant numeric identity.
        if source.lines().any(|line| {
            let code = line.split(';').next().unwrap_or("");
            ["#d", "#b", "#q2"].iter().any(|tag| code.contains(*tag))
        }) {
            return Err("SENS admission: encoded literals forbidden in executable Lisp".into());
        }
        let parsed = sens::parse(source).map_err(|error| format!("SENS reader: {error}"))?;
        if parsed.iter().any(|expr| contains_non_integer_numeric_lexeme(expr, source)) {
            return Err(
                "SENS admission: the D12/T5M operand profile accepts signed decimal integers only; exact rationals remain REPL values"
                    .into(),
            );
        }
        // The SENS source projector owns numeric width selection; transport only
        // preserves the resulting explicit width and bits.
        let projected =
            sens::source_projection::project_ukr_decimal_integer_literals_with_minimum_width(
                &parsed,
                source,
                minimum_width,
            )
            .map_err(|error| format!("SENS decimal source: {error}"))?;
        let lowered = sens::lower_program(&projected);
        let [root] = lowered.as_slice() else {
            return Err("SENS admission: expected exactly one mathematical form".into());
        };
        if !matches!(&root.kind, ExprKind::DomainCall(_, _)) {
            return Err("SENS admission: bare numeric data is not executable".into());
        }
        admit(root, 0)?;
        Ok(root.clone())
    }

    fn word(width: usize, bits: Vec<u8>) -> Result<ExactT5MWord, String> {
        ExactT5MWord::new(width, bits)
    }

    // Existing D2 OPEN / D5 function / subexpressions / D2 CLOSE.
    // The T5M word schema and physical encoder remain unchanged.
    fn append_words(expr: &Expr, out: &mut Vec<ExactT5MWord>) -> Result<(), String> {
        match &expr.kind {
            ExprKind::BinaryNumber(number) => {
                let width = number
                    .numeric_domain_width()
                    .ok_or("SENS admission: unqualified numeric leaf")?;
                out.push(word(
                    width,
                    number
                        .exact_numeric_domain_bits()
                        .ok_or("SENS admission: missing numeric exact bits")?,
                )?);
            }
            ExprKind::DomainCall(identity, args) => {
                out.push(word(2, vec![1, 0])?);
                out.push(word(
                    5,
                    (0..5)
                        .rev()
                        .map(|n| ((identity.packed_bits() >> n) & 1) as u8)
                        .collect(),
                )?);
                for arg in args.iter() {
                    append_words(arg, out)?;
                }
                out.push(word(2, vec![0, 1])?);
            }
            _ => return Err("SENS admission: non-numeric AST".into()),
        }
        Ok(())
    }

    fn expected_words(root: &Expr) -> Result<Vec<ExactT5MWord>, String> {
        admit(root, 0)?;
        let mut out = Vec::new();
        append_words(root, &mut out)?;
        Ok(out)
    }

    // Each numeric leaf is reconstructed FROM the actual Zig-restored bits.
    // The separately-validated source AST grants D5/D12+ identity and structure.
    fn reconstruct(
        source: &Expr,
        physical: &[ExactT5MWord],
        cursor: &mut usize,
    ) -> Result<Expr, String> {
        let kind = match &source.kind {
            ExprKind::BinaryNumber(number) => {
                let width = number
                    .numeric_domain_width()
                    .ok_or("SENS admission: missing numeric domain")?;
                let word = physical
                    .get(*cursor)
                    .ok_or("T5M_PAIR_MISMATCH: numeric leaf absent")?;
                *cursor += 1;
                if word.width != width {
                    return Err("T5M_PAIR_MISMATCH: different domain width".into());
                }
                ExprKind::BinaryNumber(
                    BinaryNumber::from_numeric_domain_bits(width, &word.bits)
                        .ok_or("SENS admission: invalid exact numeric bits")?,
                )
            }
            ExprKind::DomainCall(identity, args) => {
                if physical.get(*cursor + 1).is_none() {
                    return Err("T5M_PAIR_MISMATCH: missing call head".into());
                }
                *cursor += 2; // D2 OPEN and exact D5 head already compared
                let mut children = Vec::with_capacity(args.len());
                for arg in args.iter() {
                    children.push(reconstruct(arg, physical, cursor)?);
                }
                if physical.get(*cursor).is_none() {
                    return Err("T5M_PAIR_MISMATCH: missing D2 CLOSE".into());
                }
                *cursor += 1;
                ExprKind::DomainCall(*identity, children.into())
            }
            _ => return Err("SENS admission: cannot reconstruct this AST".into()),
        };
        Ok(Expr {
            kind,
            span: source.span,
        })
    }

    fn eval_verified(source: &str, physical: &[u8]) -> Result<Value, String> {
        let qualified = qualify(source)?;
        let expected = expected_words(&qualified)?;
        // Only Zig physically encodes or decodes T5M; no W1–W9 truncation.
        let restored = zig_transport::decode_t5m_exact_words(physical)?;
        if restored != expected {
            let index = restored.iter().zip(&expected).position(|(a, b)| a != b);
            return Err(format!(
                "T5M_PAIR_MISMATCH layer=transport index={index:?} expected_words={} actual_words={}; domain cannot be inferred from width",
                expected.len(), restored.len()
            ));
        }
        let mut cursor = 0usize;
        let expr = reconstruct(&qualified, &restored, &mut cursor)?;
        if cursor != restored.len() {
            return Err("T5M_PAIR_MISMATCH: trailing exact physical words".into());
        }
        sens::eval_parsed_expressions(&[expr], &mut Session::default())
            .map(|result| result.value)
            .map_err(|e| format!("SENS eval: {e}"))
    }

    fn sibling(path: &Path) -> Result<PathBuf, String> {
        if path.extension().and_then(|e| e.to_str()) != Some("lisp") {
            return Err("required explicitly qualified .lisp source companion".into());
        }
        Ok(path.with_extension("sens"))
    }

    fn run(args: &[String]) -> Result<(), String> {
        let [action, filename] = args else {
            return Err("usage: sens-math-t5m (encode|eval) source.lisp".into());
        };
        let path = Path::new(filename);
        let physical_path = sibling(path)?;
        let source = fs::read_to_string(path).map_err(|e| format!("read Lisp companion: {e}"))?;
        match action.as_str() {
            "encode" => {
                let admitted = qualify(&source)?;
                let expected = expected_words(&admitted)?;
                let physical = zig_transport::encode_t5m_exact_words(&expected)?;
                // Verify the same pair before publishing physical data.
                eval_verified(&source, &physical)?;
                let mut output = OpenOptions::new()
                    .write(true)
                    .create_new(true)
                    .open(&physical_path)
                    .map_err(|e| format!("create .sens (never overwrite): {e}"))?;
                output
                    .write_all(&physical)
                    .map_err(|e| format!("write physical T5M: {e}"))?;
                println!(
                    "T5M_PAIR_ENCODED physical_bytes={} words={}",
                    physical.len(),
                    expected.len()
                );
                Ok(())
            }
            "eval" => {
                let physical =
                    fs::read(&physical_path).map_err(|e| format!("read physical T5M: {e}"))?;
                let value = eval_verified(&source, &physical)?;
                println!("{value}");
                Ok(())
            }
            _ => Err("only explicit encode/eval commands are admitted".into()),
        }
    }

    pub fn main() {
        let args: Vec<_> = env::args().skip(1).collect();
        if let Err(error) = run(&args) {
            eprintln!("{error}");
            std::process::exit(1);
        }
    }

    }

#[cfg(feature = "zig-transport")]
fn main() {
    paired::main();
}

#[cfg(not(feature = "zig-transport"))]
fn main() {
    eprintln!("RUST_ZIG_ONLY: physical T5M paired execution requires Zig");
    std::process::exit(2);
}
